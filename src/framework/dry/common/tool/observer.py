# -*- coding: utf-8 -*-

from watchfiles import watch


class Observer(object):
    def __init__(self, config: dict):
        self._config = config
        self._observer = watch()
