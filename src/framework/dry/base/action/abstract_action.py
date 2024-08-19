# -*- coding:utf-8 -*-
import abc
from enum import Enum, auto
from typing import Any, Union
from fastapi.responses import Response

from src.framework.dry.base.types import SerializableType, StructType
from src.framework.dry.common.context import Context
from src.framework.dry.logger import Logger
from src.util import helper

ResponseType = Union[None | Response | list[SerializableType] | dict[str, SerializableType] |
                     tuple[SerializableType] | str | int | float | bool]


class ActionStateCause(Enum):
    ActionCoolStart = auto()
    ActionStageAttach = auto()
    ActionStageDetach = auto()
    ActionShutdown = auto()


class AbstractAction(object, metaclass=abc.ABCMeta):
    def __init__(self):
        self.logger = Logger().get_logger(__name__)
        self._data: Context = Context({})
        self._launched = False
        self._ready = False

    def __del__(self):
        self.shutdown(ActionStateCause.ActionShutdown)

    def init(self, cause: ActionStateCause):
        if self._launched:
            raise RuntimeError("Action already launched")
        try:
            return self._on_init(cause)
        finally:
            self._launched = True

    def _on_init(self, cause: ActionStateCause):
        """
        This function will call while action instance created.
        """
        ...

    def is_launched(self):
        return self._launched

    def shutdown(self, cause: ActionStateCause):
        if not self._launched:
            # raise RuntimeError("Action not launched")
            return
        try:
            return self._on_shutdown(cause)
        finally:
            self._launched = False

    def _on_shutdown(self, cause: ActionStateCause):
        """
        This function will call while action instance destroyed.
        """
        ...

    def before_action(self):
        """
        This function will call while action execute before.
        Default: does nothing
        """
        ...

    @abc.abstractmethod
    def action(self) -> ResponseType:
        """
        This function will call while action doing.
        """
        raise NotImplementedError

    def after_action(self, result: ResponseType):
        """
        This function will call before response send.
        Default: does nothing
        """
        ...

    def recover(self, e: Exception):
        """
        This function will call after an exception occurred.
        """
        ...

    @abc.abstractmethod
    def response(self, result: ResponseType):
        ...

    @abc.abstractmethod
    def output(self, code: int = 0, msg: str = '', data: ResponseType = None) -> ResponseType:
        """
        This function will call when response need to be created.
        This function need implement by every special actions
        """
        raise NotImplementedError

    def execute(self):
        assert self._launched, "This action has not inited"
        assert self._ready, "This action is not ready"
        try:
            self.before_action()
            result: ResponseType = self.action()
            self.after_action(result)
            return self.response(result)
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} raised an unhandled exception: {e!s}")
            helper.log_exception(e, self.logger.error)
            self.recover(e)
            raise
        finally:
            self._ready = False

    def __getstate__(self):
        return self._data

    def __setstate__(self, state):
        self._data = state
