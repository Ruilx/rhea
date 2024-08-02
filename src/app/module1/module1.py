# -*- coding: utf-8 -*-
from src.framework.dry.base.action.item_action import ItemAction


class Module1(ItemAction):
    def action(self):
        return "This is module1"
