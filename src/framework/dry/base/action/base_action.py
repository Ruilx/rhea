# -*- coding:utf-8 -*-
from abc import ABCMeta
from fastapi.requests import Request
from fastapi.responses import Response, UJSONResponse
from src.framework.dry.base.action.abstract_action import AbstractAction, ActionStateCause, ResponseType


__all__ = ['BaseAction', 'ActionStateCause']

from src.framework.dry.common.context import Context

from src.framework.dry.hook.hook import Hook, HookName


class BaseAction(AbstractAction, metaclass=ABCMeta):
    def __init__(self):
        self.request: Request | None = None
        self._module_name: str = ''
        self._controller_name: str = ''
        self._action_name: str = ''
        self._status_code: int = 200
        self._cookie: dict[str, str] = {}
        self._response_headers: dict[str, str] = {}
        self._background_tasks: list = []
        super().__init__()

    def _set_request(self, request: Request):
        self.request = request
        url_params = request.path_params
        self._module_name = url_params['_module_name']
        self._controller_name = url_params.get('_controller_name', '')
        self._action_name = url_params.get('_action_name', '')

    @property
    def module(self):
        return self._module_name

    @property
    def controller(self):
        return self._controller_name

    @property
    def action(self):
        return self._action_name

    @property
    def url(self):
        return self.request.url

    def response_header(self, name: str | None = None, value: str | None = None) -> None | str | dict[str, str]:
        """
        get/set/update/delete response header

        | name  | value | means                         |
        |-------|-------|-------------------------------|
        | =None | =None | get all headers               |
        | STR   | =None | get name header               |
        | =None | STR   | delete name is value's header |
        | STR   | STR   | set name header value's value |
        """
        if name is None and value is None:
            return self._response_headers
        if name is None and value is not None:
            if value in self._response_headers:
                del self._response_headers[value]
            return
        if name is not None and value is None:
            if name in self._response_headers:
                return self._response_headers[name]
            else:
                return None
        if name is not None and value is not None:
            self._response_headers[name] = value
            return

    def register_background_task(self):
        ...

    def output(self, code: int = 0, msg: str = '', data: ResponseType = None) -> ResponseType:
        if isinstance(data, Response):
            return data
        # TODO: background tasks assign

        response = UJSONResponse({
            'code': code,
            'msg': msg,
            'data': data if data is not None else {}
        }, status_code=self._status_code, headers=self._response_headers)

        if self._cookie:
            for key, value in self._cookie.items():
                response.set_cookie(key, value)

        return response

    def deal_request(self, request: Request):
        self._set_request(request)
        self._ready = True
        Hook().run_hook(HookName.OnActionBegin, Context({'request': request, 'data': self._data}))
        result = self.execute()
        Hook().run_hook(HookName.OnActionFinish, Context({'request': request, 'data': self._data}))
        return result
