# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import pathlib

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.framework.dry.base.endpoint import env_handler, favicon_handler, index_handler, not_found_handler, \
    robots_handler, system_error_handler, service_error_handler, info_handler
from src.framework.dry.common.context import Context
from src.framework.dry.common.tool.event_loop import EventLoopThread, EventLoop
from src.framework.dry.exception.httpError import HttpError, NotFoundError
from src.framework.dry.hook.hook import Hook, HookName
from src.framework.dry.logger import Logger, setup_loggers
from src.framework.dry.router.router import Router
from src.util import helper


class Application(FastAPI):
    def __init__(self, conf: dict[str, str], settings: Context | None = None):
        super().__init__(**conf)
        if settings is None:
            settings = Context({})
        self.settings = settings
        self.event_loop: asyncio.BaseEventLoop | None = None
        self.event_loop_thread: EventLoopThread | None = None
        self._setup_logger()
        self.logger = Logger().get_logger(__name__)
        self.logger.debug(f"Application start at PID:{os.getpid()} from PPID:{os.getppid()}")
        self.logger.debug(f"Application Conf: \n{helper.dump_obj(conf)}")
        self._run_hook(HookName.OnAppStart, Context({}))
        self._setup_event_loop()
        self._setup_exceptions()
        self._setup_statics()
        assert 'app_dir' in conf and isinstance(conf['app_dir'], str) and conf['app_dir'].__len__() > 0, "conf has no 'app_dir' or 'app_dir' is empty"
        self._setup_app_env(conf['app_dir'])
        self.app_router = Router(pathlib.Path(conf['app_dir']))
        self._setup_routers()
        self._setup_app_observer()

    def __del__(self):
        self._shutdown()

    def _shutdown(self):
        if hasattr(self, 'app_router'):
            self.app_router.shutdown()
        if isinstance(self.event_loop_thread, EventLoopThread):
            if self.event_loop_thread.is_running():
                self.logger.info("Event loop thread is running... waiting for stop in 30 seconds...")
                self.event_loop_thread.stop(30)
                self.logger.info("Event loop thread joined.")
        self._run_hook(HookName.OnAppShutdown, Context({}))

    def _setup_event_loop(self):
        try:
            self.event_loop = asyncio.get_running_loop()
            self.logger.info("Using running eventloop.")
        except RuntimeError:
            try:
                self.event_loop = asyncio.get_event_loop()
                self.logger.info("Using registered eventloop.")
            except RuntimeError:
                self.event_loop = asyncio.new_event_loop()
                self.logger.info("Using new eventloop.")
                asyncio.set_event_loop(self.event_loop)
        if not self.event_loop.is_running():
            # new thread to run eventloop forever
            self.logger.info("Starting eventloop thread...")
            eventloop = EventLoop(self.event_loop)
            self.event_loop_thread = EventLoopThread(eventloop)
            self.event_loop_thread.start()
            self.logger.info("Eventloop thread started.")

    def _setup_logger(self):
        if 'log' in self.settings and isinstance(self.settings['log'], dict):
            setup_loggers(Logger(), self.settings['log']['log'], self.settings['log']['log_level'])

    def _setup_app_env(self, app_entry: str):
        sys.path.insert(0, app_entry)

    def _setup_app_observer(self):
        ...

    def _setup_exceptions(self):
        self.add_exception_handler(404, not_found_handler)
        self.add_exception_handler(NotFoundError, not_found_handler)
        self.add_exception_handler(HttpError, service_error_handler)
        self.add_exception_handler(Exception, system_error_handler)

    def _setup_statics(self):
        self.mount(self.extra['static_url'], StaticFiles(directory=self.extra['static_dir']), name="static")
        self.add_api_route('/favicon.ico', favicon_handler)
        self.add_api_route('/robots.txt', robots_handler)

    def _setup_index(self):
        self.add_api_route('/', index_handler)
        self.add_api_route('/_info', info_handler)
        self.add_api_route('/_env', env_handler)

    def _setup_routers(self):
        self._setup_index()
        self.add_api_route('/{_module_name}', self.app_router.route_handler, methods=["GET", "POST"])
        self.add_api_route('/{_module_name}/{_controller_name}', self.app_router.route_handler, methods=["GET", "POST"])
        self.add_api_route('/{_module_name}/{_controller_name}/{_action_name}', self.app_router.route_handler, methods=["GET", "POST"])

    def _run_hook(self, hook_name: HookName, context: Context):
        Hook().run_hook(hook_name, context)
