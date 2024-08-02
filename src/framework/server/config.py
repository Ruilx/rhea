# -*- coding: utf-8 -*-
import asyncio
import inspect
from typing import Callable, Any, Optional

import ssl

from starlette.middleware.wsgi import WSGIMiddleware
from uvicorn._types import ASGIApplication
from uvicorn.config import Config as UvicornConfig, create_ssl_context, HTTP_PROTOCOLS, WS_PROTOCOLS, LIFESPAN
from uvicorn.importer import ImportFromStringError, import_from_string
from uvicorn.logging import TRACE_LOG_LEVEL
from uvicorn.middleware.asgi2 import ASGI2Middleware
from uvicorn.middleware.message_logger import MessageLoggerMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.framework.dry.assets.about import About
from src.framework.dry.base.types import StructType
from src.framework.dry.common.context import Context, SerializableContext
from src.framework.dry.logger import Logger


class Config(UvicornConfig):
    def __init__(self, app: ASGIApplication | Callable[..., Any] | str, conf: dict[str, Any], settings: Context):
        self.http_protocol_class = None
        self.ws_protocol_class = None
        self.lifespan_class = None
        self.ssl = None
        self.loaded_app = None
        self.logger = Logger().get_logger("uvicorn.error")

        if not conf:
            conf = {}
        self.conf = conf

        if settings is None:
            settings = SerializableContext({})
        self.settings = settings

        if "app_conf" in conf:
            if "app_dir" not in conf['app_conf'] and "app_dir" not in conf:
                self.logger.error("Needs to pass app_dir in conf['app_conf'] to specify application's path")
                raise SystemExit("Needs to pass app_dir in conf['app_conf'] to specify application's path")
            elif "app_dir" in conf and "app_dir" not in conf['app_conf']:
                conf['app_conf']['app_dir'] = conf['app_dir']
                del conf['app_dir']
        else:
            conf['app_conf'] = {}
            if "app_dir" in conf:
                conf['app_conf']['app_dir'] = conf['app_dir']
                del conf['app_dir']

        if 'app_conf' in conf:
            self.app_conf = conf['app_conf']
            del conf['app_conf']
        if 'log_config' not in conf or conf['log_config'] is None:
            conf['log_config'] = Logger().dict_config

        super().__init__(app, **conf)

    def load(self) -> None:
        assert not self.loaded

        if self.is_ssl:
            assert self.ssl_certfile
            self.ssl: ssl.SSLContext | None = create_ssl_context(
                keyfile=self.ssl_keyfile,
                certfile=self.ssl_certfile,
                password=self.ssl_keyfile_password,
                ssl_version=self.ssl_version,
                cert_reqs=self.ssl_cert_reqs,
                ca_certs=self.ssl_ca_certs,
                ciphers=self.ssl_ciphers,
            )

        encoded_headers = [(key.lower().encode("latin1"), value.encode("latin1")) for key, value in self.headers]
        self.encoded_headers = (
            [(b"server",
              (About.name().encode() if About.name() else b"ruvicorn") +
              ((b'/' + About.version().encode()) if About.version() else b''))] + encoded_headers
            if b"server" not in dict(encoded_headers) and self.server_header
            else encoded_headers
        )

        if isinstance(self.http, str):
            http_protocol_class = import_from_string(HTTP_PROTOCOLS[self.http])
            self.http_protocol_class: type[asyncio.Protocol] = http_protocol_class
        else:
            self.http_protocol_class = self.http

        if isinstance(self.ws, str):
            ws_protocol_class = import_from_string(WS_PROTOCOLS[self.ws])
            self.ws_protocol_class: type[asyncio.Protocol] | None = ws_protocol_class
        else:
            self.ws_protocol_class = self.ws

        self.lifespan_class = import_from_string(LIFESPAN[self.lifespan])

        try:
            self.loaded_app = import_from_string(self.app)
        except ImportFromStringError as exc:
            self.logger.error("Error loading ASGI app. %s" % exc)
            raise SystemExit("Error loading ASGI app.") from exc

        try:
            self.loaded_app = self.loaded_app(self.app_conf, self.settings)
        except TypeError as exc:
            if self.factory:
                self.logger.error("Error loading ASGI app factory: %s", exc)
                raise SystemExit("Error loading ASGI app factory.") from exc
        else:
            if not self.factory:
                self.logger.warning(
                    "ASGI app factory detected. Using it, " "but please consider setting the --factory flag explicitly."
                )

        if self.interface == "auto":
            if inspect.isclass(self.loaded_app):
                use_asgi_3 = hasattr(self.loaded_app, "__await__")
            elif inspect.isfunction(self.loaded_app):
                use_asgi_3 = asyncio.iscoroutinefunction(self.loaded_app)
            else:
                call = getattr(self.loaded_app, "__call__", None)
                use_asgi_3 = asyncio.iscoroutinefunction(call)
            self.interface = "asgi3" if use_asgi_3 else "asgi2"

        if self.interface == "wsgi":
            self.loaded_app = WSGIMiddleware(self.loaded_app)
            self.ws_protocol_class = None
        elif self.interface == "asgi2":
            self.loaded_app = ASGI2Middleware(self.loaded_app)

        if self.logger.getEffectiveLevel() <= TRACE_LOG_LEVEL:
            self.loaded_app = MessageLoggerMiddleware(self.loaded_app)
        if self.proxy_headers:
            self.loaded_app = ProxyHeadersMiddleware(self.loaded_app, trusted_hosts=self.forwarded_allow_ips)

        self.loaded = True
