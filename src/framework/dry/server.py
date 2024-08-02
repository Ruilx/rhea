#!/usr/bin/env python3
# -*- coding: utf-8

from src.framework.dry.config import Config
from src.framework.dry.base.singleton import singleton
from src.framework.server import ruvicorn


@singleton
class Server(object):
    def __init__(self, conf: Config):
        self.config = conf

    def run(self):
        app = self.config.get_config('app')
        assert app, "'app' entry module not found in conf"
        ruvicorn.run(app, self.config)
