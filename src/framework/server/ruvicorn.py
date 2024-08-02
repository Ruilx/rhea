# -*- coding: utf-8 -*-
import logging
import os.path
import sys
from typing import Callable, Any

from uvicorn import Server
from uvicorn._types import ASGIApplication
from uvicorn.main import STARTUP_FAILURE
from uvicorn.supervisors import ChangeReload, Multiprocess

from src.framework.dry.assets.about import About
from src.framework.dry.config import Config
from src.framework.dry.logger import Logger
from src.framework.server.config import Config as ServerConfig


def run(app: ASGIApplication | Callable[..., Any] | str, conf: Config):
    # if conf.get('app_dir') is not None:
    #     sys.path.insert(0, conf['app_dir'])

    logger = Logger().get_logger(__name__)

    server_conf = conf.get_config_obj("server")

    config = ServerConfig(app, server_conf, conf.settings)
    server = Server(config=config)

    if (config.reload or config.workers > 1) and not isinstance(app, str):
        logger.error("You must pass the application as an import string to enable 'reload' or " "'workers'.")
        raise SystemExit("You must pass the application as an import string to enable 'reload' or " "'workers'.")

    About.banner_to_io(sys.stdout, True)

    try:
        if config.should_reload:
            sock = config.bind_socket()
            ChangeReload(config, target=server.run, sockets=[sock]).run()
        elif config.workers > 1:
            sock = config.bind_socket()
            Multiprocess(config, target=server.run, sockets=[sock]).run()
        else:
            server.run()
    finally:
        if config.uds and os.path.exists(config.uds):
            os.remove(config.uds)

    if not server.started and not config.should_reload and config.workers == 1:
        sys.exit(STARTUP_FAILURE)
