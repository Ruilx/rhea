# -*- coding: utf-8 -*-
from src.framework.dry.base.action.item_action import ItemAction


# a function to calculate the datetime with giving UTC timestamp.
def calculate_datetime(timestamp: int):
    import datetime
    return datetime.datetime.utcfromtimestamp(timestamp)

# a function to calculate the datetime with giving UTC timestamp but not to use python datetime libraries.



class Action1(ItemAction):
    def action(self):
        method = self.request.method
        return f"This is {method} module1/con1/action1 executor"
