# -*- coding: utf-8 -*-
from pathlib import Path


class Loader(object):
    def __init__(self):
        self.actions: [str, dict[str, dict[str, dict[str, ...]]]] = {}
        self.action_instances = Lru = Lru(500)

    def load_dir(self, path: Path):
        ...

    def load_file(self, path: Path):
