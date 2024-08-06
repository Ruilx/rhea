# -*- coding: utf-8 -*-
from src.framework.dry.base.action.item_action import ItemAction


class Action1(ItemAction):
    def action(self):
        return "This is module1/con1/action1 executor"
