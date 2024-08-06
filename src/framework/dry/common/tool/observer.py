# -*- coding: utf-8 -*-
import pathlib
from threading import Event
from typing import Generator

from watchfiles import watch, Change

from src.framework.dry.logger import Logger
from src.util import helper


class Observer(object):
    def __init__(self, config: dict):
        self._config = config
        self._logger = Logger().get_logger(__name__)
        assert 'path' in config, "Observer config 'path' is required"
        if 'watch_filter' in config and not callable(config['watch_filter']):
            raise ValueError("Observer config 'watch_filter' must be callable")
        self._observer: Generator | None = None
        self._stop = Event()

    def watch_filter(self, change: Change, path: str):
        p = pathlib.Path(path).relative_to(self._config['path'])
        if p.is_file() and p.suffix.lower() in ('.py', '.pyd', '.so'):
            return True
        return False

    def stop(self):
        self._stop.set()

    def daemon(self):
        if not isinstance(self._observer, Generator):
            self._observer = watch(
                self._config['path'],
                watch_filter=self._config.get('watch_filter', self.watch_filter),
                stop_event=self._stop)
        while not self._stop.set():
            try:
                changes = next(self._observer)
                if changes:
                    try:
                        for change in changes:
                            self._config['reload'](*change)
                    except BaseException as e:
                        self._logger.error("Error while handle watch file event callback at:")
                        helper.log_exception(e, self._logger.error)
                        continue

            except KeyboardInterrupt:
                self.stop()
                self._logger.info("receive keyboard interrupt, stop observing...")
                break
            except BaseException as e:
                self.stop()
                self._logger.error(f"Observer system error: {e!r}")
                helper.log_exception(e, self._logger.error)
