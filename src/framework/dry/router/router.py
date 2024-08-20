# -*- coding: utf-8 -*-
from pathlib import Path

from starlette.requests import Request

from src.framework.dry.base.action.base_action import BaseAction, ActionStateCause
from src.framework.dry.common.algorithm.lru import Lru, LruEvent, LruItem
from src.framework.dry.exception.httpError import HttpError, SysError, RejectedError
from src.framework.dry.logger import Logger
from src.framework.dry.router.action_manager import ActionManager
from src.util import helper


class Router(object):
    def __init__(self, app_path: Path):
        self.app_path = app_path
        self.action_lru: Lru = Lru(500)
        self.action_manager = ActionManager(app_path, self.action_lru)
        self.action_lru.append_event_handler(self.on_lru_event)
        self.logger = Logger().get_logger(__name__)
        self.action_manager.load_dir(self.app_path)
        self.action_manager.dump_router()

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
        for action in self.action_lru.get_lru():
            inst = self.action_lru.get(action)
            if isinstance(inst, BaseAction):
                inst.shutdown(ActionStateCause.ActionShutdown)
        self.action_lru.clear()

    def route_handler(self, request: Request):
        try:
            route_params = request.path_params
            module_name = route_params.get('_module_name', '')
            controller_name = route_params.get('_controller_name', '')
            action_name = route_params.get('_action_name', '')

            if not module_name:
                raise RejectedError('module_name is empty')

            return self.action_manager.get_action(module_name, controller_name, action_name).deal_request(request)
        except HttpError as e:
            helper.log_exception(e, self.logger.error)
            raise
        except Exception as e:
            helper.log_exception(e, self.logger.error)
            raise SysError from e
