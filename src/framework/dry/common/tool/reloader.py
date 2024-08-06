# -*- coding: utf-8 -*-
from watchfiles import Change

from src.framework.dry.common.algorithm.lru import Lru
from src.framework.dry.logger import Logger


class Reloader(object):
    def __init__(self, router_map: dict, action_instances: Lru):
        self.router_map = router_map
        self.action_instances: Lru = action_instances
        self._logger = Logger().get_logger(__name__)

    def _reload_to_router(self, module: str, controller: str | None = None, action: str | None = None):
        ...

    def reload(self, change: Change, path: str):
        if change == Change.added or change == Change.modified:
            ...
