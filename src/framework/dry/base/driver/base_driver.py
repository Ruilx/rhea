# -*- coding: utf-8 -*-
import abc

from src.framework.dry.base.component.base_metadata import BaseMetadata
from src.framework.dry.config import Config
from src.framework.dry.exception.driverError import DriverError


class BaseDriver(BaseMetadata, metaclass=abc.ABCMeta):
    def __init__(self, conf: Config):
        self._conf = conf
        self._valid = False
        super().__init__(**conf.get_config_obj('metadata'))

    @abc.abstractmethod
    def _setup(self):
        """
        Setup function will run after server started.
        """
        ...

    @abc.abstractmethod
    def _shutdown(self):
        """
        Shutdown function will run before server shutting.
        """
        ...

    @abc.abstractmethod
    def _recover(self, e: BaseException):
        """
        Recover function will run when driver occurred calling exceptions.
        """
        ...

    def pre_call(self, *args, **kwargs):
        if not self._valid:
            raise DriverError(f"driver '{self.name}' is not loaded")

    def post_call(self, *args, **kwargs):
        ...

    def load(self):
        self._setup()
        self._valid = True

    def unload(self):
        self._shutdown()
        self._valid = False
