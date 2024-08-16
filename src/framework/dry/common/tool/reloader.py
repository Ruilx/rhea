# -*- coding: utf-8 -*-
import pathlib

from watchfiles import Change

from src.framework.dry.common.algorithm.lru import Lru
from src.framework.dry.logger import Logger


class Reloader(object):
    def __init__(self, router_map: dict, action_instances: Lru):
        self.router_map = router_map
        self.action_instances: Lru = action_instances
        self._logger = Logger().get_logger(__name__)

    def _reload_to_router(self, file_path: str):
        empty_router_part = False
        assert module.strip().__len__() > 0, "module name can not be empty"
        if module not in self.router_map:
            self.router_map[module] = {}
        c = self.router_map[module]
        if controller.strip().__len__() <= 0:
            empty_router_part = True
        if controller not in c:
            c[controller] = {}
        a = c[controller]
        if empty_router_part and action.strip().__len__() <= 0:
            raise ValueError(f"module: {module} has a empty controller, action must be stay empty.")
        if action not in a:
            a[action] = {
                'file_path': file_path,
                'module': module,
                'controller': controller,
                'action': action,
                'module_path':
            }




    def reload(self, change: Change, path: pathlib.Path):
        if change == Change.added or change == Change.modified:
