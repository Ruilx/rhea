# -*- coding: utf-8 -*-
from enum import Enum

from src.framework.dry.base.driver.base_driver import BaseDriver
from src.framework.dry.base.singleton import singleton
from src.framework.dry.hub.base_hub import BaseHub


class DriverType(Enum):
    ServiceDriver = 1
    MethodDriver = 2
    MiddlewareDriver = 3
    HookDriver = 4
    CronDriver = 5

@singleton
class DriverHub(BaseHub):
    def __init__(self):
        super().__init__()

    def _check_model_item_class(self, cls):
        assert issubclass(cls, BaseDriver)
