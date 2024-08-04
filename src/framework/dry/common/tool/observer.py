# -*- coding: utf-8 -*-
import pathlib
from threading import Event
from typing import Generator

from watchfiles import watch, Change


class Observer(object):
    def __init__(self, config: dict):
        self._config = config
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
                    self._config['reload'](changes)
