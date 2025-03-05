# -*- coding: utf-8 -*-
from src.framework.dry.base.driver.base_driver import BaseDriver
from src.framework.dry.base.singleton import singleton


@singleton
class Provider(object):
    def __init__(self):
        self.drivers = {}

    def has(self, name: str):
        return name in self.drivers

    def get(self, name: str):
        if name in self.drivers:
            return self.drivers[name]

    def register_driver(self, name: str, driver: BaseDriver):
        self.drivers[name] = driver
