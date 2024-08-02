# -*- coding: utf-8 -*-
from abc import ABCMeta
from typing import Final

from starlette.responses import Response

from src.framework.dry.base.action.abstract_action import ResponseType
from src.framework.dry.base.action.base_action import BaseAction


class ItemAction(BaseAction, metaclass=ABCMeta):
    def response(self, result: ResponseType):
        if isinstance(result, Response):
            return result
        return self.output(data=result)
