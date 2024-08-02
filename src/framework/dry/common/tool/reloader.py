# -*- coding: utf-8 -*-
from src.framework.dry.common.algorithm.lru import Lru
from src.framework.dry.logger import Logger


class Reloader(object):
    def __init__(self, router_map: dict, action_instances: Lru):
        self.router_map = router_map
        self._setup_config()
        self._logger = Logger().get_logger(__name__)

    def _setup_config(self):
        ...
