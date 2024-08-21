# -*- coding: utf-8 -*-
import asyncio
import enum
from pathlib import Path

import inflection
from threading import Lock

from src.framework.dry.base.action.abstract_action import ActionStateCause
from src.framework.dry.base.action.base_action import BaseAction
from src.framework.dry.common.algorithm.lru import Lru
from src.framework.dry.exception.httpError import NotFoundError, SysError
from src.framework.dry.logger import Logger
from src.util import helper


class ActionLoadType(enum.Enum):
    Load4Startup = enum.auto()
    Load4Reload = enum.auto()

class ActionManager(object):
    def __init__(self, app_path: Path, action_lru: Lru):
        self.app_path = app_path
        self.action_lru = action_lru
        self.actions: [str, dict[str, dict[str, dict[str, ...]]]] = {}
        self.event_loop = asyncio.get_running_loop()
        self.logger = Logger().get_logger(__name__)

    def _arrange_module(self, path: Path):
        mod_path = path.relative_to(self.app_path).with_suffix('')
        mod_parts = mod_path.parts
        return mod_parts

    def _arrange_module_parts(self, mod_parts: tuple[str, ...]):
        if mod_parts.__len__() < 0 or mod_parts.__len__() > 3:
            self.logger.error(f"invalid module parts '{'.'.join(mod_parts)}'")
            self.logger.error("rhea only support that route path is less/equal than 3 steps.")
            return

        if mod_parts.__len__() == 2:
            if mod_parts[0] == mod_parts[1]:
                new_mod_parts = (mod_parts[0], '', '')
            else:
                new_mod_parts = (*mod_parts, '', '')
        elif mod_parts.__len__() == 3:
            if mod_parts[1] == mod_parts[2]:
                new_mod_parts = (mod_parts[0], mod_parts[1], '')
            else:
                new_mod_parts = mod_parts
        else:
            new_mod_parts = mod_parts

        return new_mod_parts

    def _set_router(self, module, controller, action, module_path, class_name, file_path: Path, load_type: ActionLoadType):
        if module not in self.actions:
            self.actions[module] = {}
        if controller not in self.actions[module]:
            self.actions[module][controller] = {}
        if action in self.actions[module][controller]:
            self._unset_router(module, controller, action, load_type)
            # if current_action_inst and isinstance(current_action_inst, BaseAction) and current_action_inst.is_launched():
            #     current_action_inst.shutdown(ActionStateCause.ActionShutdown)
            # self.action_lru.delete(current_action['module_path'])
        self.actions[module][controller][action] = {
            'file_path': str(file_path),
            'module': module,
            'controller': controller,
            'action': action,
            'module_path': module_path,
            'class_name': class_name,
            'class_cls': None,
        }

    def _unset_router(self, module, controller, action, load_type: ActionLoadType):
        if module not in self.actions:
            raise ValueError(f"module '{module}' not found in router")
        if controller not in self.actions[module]:
            raise ValueError(f"controller '{module}.{controller}' not found in router")
        if action not in self.actions[module][controller]:
            raise ValueError(f"action '{module}.{controller}.{action}' not found in router")
        current_action = self.actions[module][controller][action]
        action_inst = self.action_lru.get(current_action['module_path'])
        if not isinstance(action_inst, BaseAction):
            raise ValueError(f"action_lru key '{current_action['module_path']}' is not a BaseAction.")
        if action_inst.is_launched():
            self.event_loop.call_soon_threadsafe(action_inst.shutdown, ActionStateCause.ActionShutdown if load_type == ActionLoadType.Load4Startup else ActionStateCause.ActionStageDetach)
        self.action_lru.delete(current_action['module_path'])
        if load_type == ActionLoadType.Load4Startup:
            del self.actions[module][controller][action]
        else:
            current_action['class_cls'] = None

    def load_dir(self, path: Path):
        for p in path.rglob('*.py'):
            if path.name == '__init__.py':
                continue
            self.load_file(p)
        self.logger.debug(f"router load path '{path}' finished.")

    def load_file(self, path: Path):
        if path.name == '__init__.py':
            self.logger.error("cannot import file: __init__.py, not supported.")
            return
        mod_parts = self._arrange_module(path)
        new_mod_parts = self._arrange_module_parts(mod_parts)
        self._set_router(*new_mod_parts, '.'.join(mod_parts), inflection.camelize(mod_parts[-1]), path)

    def unload_file(self, path: Path):
        if path.name == '__init__.py':
            self.logger.error("cannot unload file: __init__.py, not supported.")
            return
        new_mod_parts = self._arrange_module_parts(self._arrange_module(path))
        self._unset_router(*new_mod_parts, load_type=ActionLoadType.Load4Startup)

    def get_action(self, module, controller, action):
        if module not in self.actions:
            raise NotFoundError("module not found.")
        if controller not in self.actions[module]:
            raise NotFoundError("controller not found.")
        if action not in self.actions[module][controller]:
            raise NotFoundError("action not found.")
        handler = self.actions[module][controller][action]

        inst = self.action_lru.get(handler['module_path'])
        if inst is None:
            if handler['class_cls'] is None:
                cls = helper.import_class(handler['module_path'], handler['class_name'])
                handler['class_cls'] = cls
                cause = ActionStateCause.ActionCoolStart
            else:
                cls = handler['class_cls']
                cause = ActionStateCause.ActionStageAttach
            if not issubclass(cls, BaseAction):
                raise SysError("action is not valid")

            inst = cls()
            inst.init(cause)

            self.action_lru.set(handler['module_path'], inst)

        return inst

    def dump_router(self):
        self.logger.info('↓\n' + helper.dump_obj(self.actions))
