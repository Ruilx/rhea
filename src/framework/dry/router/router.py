# -*- coding: utf-8 -*-
import inflection
from pathlib import Path

from starlette.requests import Request
from uvicorn.importer import import_from_string

from src.framework.dry.base.action.base_action import BaseAction, ActionStateCause
from src.framework.dry.common.algorithm.lru import Lru, LruEvent, LruItem
from src.framework.dry.exception.httpError import HttpError, SysError, NotFoundError
from src.framework.dry.logger import Logger
from src.util import helper


class Router(object):
    def __init__(self, app_path: Path):
        self.app_path = app_path
        self.router: [str, dict[str, dict[str, dict[str, ...]]]] = {}
        self.action_instances: Lru = Lru(500)
        self.action_instances.append_event_handler(self.on_lru_event)
        self.logger = Logger().get_logger(__name__)
        self._walk_actions()

    def __del__(self):
        self.shutdown()

    def on_lru_event(self, item: LruItem, event: LruEvent):
        match event:
            case LruEvent.ManualDeleted:
                self.logger.info(f"action {item.key} is removed from lru")
            case LruEvent.ManualSet:
                self.logger.info(f"action {item.key} is set to lru")
            case LruEvent.Expired:
                self.logger.info(f"action {item.key} is expired from lru")
            case LruEvent.Advanced:
                self.logger.info(f"action {item.key} is advanced from lru")
            case LruEvent.ValueChanged:
                self.logger.info(f"action {item.key} is changed from lru")
            case LruEvent.ResetExpire:
                self.logger.info(f"action {item.key} is reset expire from lru")
            case LruEvent.AutoSet:
                self.logger.info(f"action {item.key} is auto set to lru")
            case _:
                self.logger.info(f"action {item.key} is unknown event from lru")

    def shutdown(self):
        # for module_name, module in self.router.items():
        #     for controller_name, controller in module.items():
        #         for action_name, action in controller.items():
        #             if isinstance(action['inst'], BaseAction):
        #                 action['inst'].shutdown(ActionStateCause.ActionShutdown)
        #                 self.action_instances.delete(action['module_path'])
        for action in self.action_instances.get_lru():
            inst = self.action_instances.get(action)
            if isinstance(inst, BaseAction):
                inst.shutdown(ActionStateCause.ActionShutdown)
        self.action_instances.clear()


    def _register_router(self, module, controller, action, module_path, class_name, file_path: Path):
        if module not in self.router:
            self.router[module] = {}
        if controller not in self.router[module]:
            self.router[module][controller] = {}
        if action not in self.router[module][controller]:
            self.router[module][controller][action] = {
                'file_path': file_path,
                'module': module,
                'controller': controller,
                'action': action,
                'module_path': module_path,
                'class_name': class_name,
                'class_cls': None,
            }

    def dump_router(self):
        self.logger.info('↓\n' + helper.dump_obj(self.router))

    def _walk_actions(self):
        for path in self.app_path.rglob("*.py"):
            if path.name == "__init__.py":
                continue

            mod_path = path.relative_to(self.app_path).with_suffix('')
            mod_parts = mod_path.parts
            if mod_parts.__len__() < 0 or mod_parts.__len__() > 3:
                self.logger.error(f"router {mod_path} (from file: {path}) has more than 3 steps and it's not supported.")
                continue

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

            self._register_router(*new_mod_parts, '.'.join(mod_parts), inflection.camelize(mod_parts[-1]), path)

    def route_handler(self, request: Request):
        try:
            route_params = request.path_params
            module_name = route_params.get('_module_name', '')
            controller_name = route_params.get('_controller_name', '')
            action_name = route_params.get('_action_name', '')

            assert module_name, 'module_name is empty'

            if module_name not in self.router:
                raise NotFoundError('module_not found.')
            if controller_name not in self.router[module_name]:
                raise NotFoundError('controller not found.')
            if action_name not in self.router[module_name][controller_name]:
                raise NotFoundError('action not found.')
            handler = self.router[module_name][controller_name][action_name]

            instance = self.action_instances.get(handler['module_path'])
            if instance is None:
                if handler['class_cls'] is None:
                    cls = import_from_string(f"{handler['module_path']}:{handler['class_name']}")
                    handler['class_cls'] = cls
                    cause = ActionStateCause.ActionCoolStart
                else:
                    cls = handler['class_cls']
                    cause = ActionStateCause.ActionStageAttach

                if not issubclass(cls, BaseAction):
                    raise SysError("action is not valid")

                instance = cls()
                instance.init(cause)
                self.action_instances.set(handler['module_path'], instance)

            return instance.deal_request(request)
        except HttpError as e:
            helper.log_exception(e, self.logger.error)
            raise
        except Exception as e:
            helper.log_exception(e, self.logger.error)
            raise SysError from e
