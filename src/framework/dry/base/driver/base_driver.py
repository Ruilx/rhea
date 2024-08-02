# -*- coding: utf-8 -*-
from src.framework.dry.base.component.base_metadata import BaseMetadata
from src.framework.dry.config import Config
from src.framework.dry.exception.driverError import DriverError


class BaseDriver(BaseMetadata):
    def __init__(self, conf: Config):
        self._conf = conf
        self._valid = False
        super().__init__(**conf.get_config_obj('metadata'))

    def setup(self):
        ...

    def shutdown(self):
        ...

    def recover(self):
        ...

    def pre_call(self, *args, **kwargs):
        if not self._valid:
            raise DriverError(f"driver '{self.name}' is not loaded")

    def post_call(self, *args, **kwargs):
        ...
