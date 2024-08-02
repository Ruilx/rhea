# -*- coding: utf-8 -*-
from src.framework.dry.base.action.base_action import BaseAction
from src.framework.dry.base.singleton import singleton
from src.framework.dry.hub.base_hub import BaseHub


@singleton
class ActionHub(BaseHub):
    def __init__(self):
        super().__init__()

    def _check_model_item_class(self, cls):
        assert issubclass(cls, BaseAction)
