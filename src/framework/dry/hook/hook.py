# -*- coding: utf-8 -*-
from collections import OrderedDict
from enum import IntEnum, auto
from typing import Callable

from src.framework.dry.base.singleton import singleton
from src.framework.dry.common.context import Context
from src.framework.dry.common.tool.event_loop import EventLoop
from src.framework.dry.exception.hookError import HookError
from src.framework.dry.logger import Logger
from src.util import helper


class HookName(IntEnum):
    OnSystemStart = auto()
    OnSystemExit = auto()
    OnSystemConfigLoad = auto()
    OnAppStart = auto()
    OnAppShutdown = auto()
    OnDriverLoad = auto()
    OnDriverUnload = auto()
    OnDriverItemLoad = auto()
    OnDriverItemUnload = auto()
    OnRouterBuild = auto()
    OnServerListening = auto()
    OnHttpException = auto()
    OnActionBegin = auto()
    OnActionFinish = auto()
    OnActionException = auto()


@singleton
class Hook(object):
    def __init__(self):
        self.hooks: dict[HookName, OrderedDict[str, Callable]] = {}
        self.event_loop: EventLoop | None = None
        for hook_name in HookName:
            self.hooks[hook_name] = OrderedDict()
        self.logger = Logger().get_logger(__name__)

    def has(self, hook_name: HookName, name: str):
        return hook_name in self.hooks and name in self.hooks[hook_name]

    def register_hook(self, hook_name: HookName, name: str, hook_func: Callable):
        if self.has(hook_name, name):
            raise HookError(f"Hook '{name}' already registered")
        self.hooks[hook_name][name] = hook_func

    def unregister_hook(self, hook_name: HookName, name: str):
        if not self.has(hook_name, name):
            raise HookError(f"Hook '{name}' not registered")
        self.hooks[hook_name].pop(name)

    def run_hook(self, hook_name: HookName, context: Context):
        if hook_name not in self.hooks:
            return
        self.logger.debug(f"Running hook {hook_name.name}...")
        for name, hook_func in self.hooks[hook_name].items():
            try:
                context.set('_hook', {
                    'hook_name': hook_name,
                    'name': name,
                })
                hook_func(context)
            except Exception as e:
                helper.log_exception(e, self.logger.error)
                continue
