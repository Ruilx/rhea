# -*- coding: utf-8 -*-
import abc

from src.framework.dry.hub.hub_item import HubItem


class BaseHub(metaclass=abc.ABCMeta):
    def __init__(self):
        self.modules = {}

    def has(self, name: str):
        return name in self.modules

    def set(self, name: str, item: HubItem):
        if not self.has(name):
            self.modules[name] = item
            return
        raise ValueError(f"module name '{name}' already set.")

    def get(self, name: str):
        if not self.has(name):
            raise ValueError(f"module name '{name}' not found.")
        module = self.modules[name]
        assert isinstance(module, HubItem)
        cls = module.get_class()
        self._check_model_item_class(cls)
        return cls

    def __getstate__(self):
        return self.modules

    def __setstate__(self, state):
        self.modules = state

    @abc.abstractmethod
    def _check_model_item_class(self, cls):
        raise NotImplementedError
