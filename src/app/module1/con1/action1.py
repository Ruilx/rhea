# -*- coding: utf-8 -*-
from src.framework.dry.base.action.item_action import ItemAction


class Action1(ItemAction):
    def action(self):
        method = self.request.method
        return f"This is {method} module1/con1/action1 executor"
