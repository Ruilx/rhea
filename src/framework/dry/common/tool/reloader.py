# -*- coding: utf-8 -*-
import pathlib

from watchfiles import Change

from src.framework.dry.logger import Logger
from src.framework.dry.router.action_manager import ActionManager


class Reloader(object):
    def __init__(self, action_manager: ActionManager):
        self.action_manager = action_manager
        self._logger = Logger().get_logger(__name__)

    def reload(self, change: Change, path: pathlib.Path):
        if change == Change.added:
            self.action_manager.load_file(path)
            self._logger.info(f"file: {path} is reloaded.")
        elif change == Change.modified:
