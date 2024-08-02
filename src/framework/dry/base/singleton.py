# -*- coding: utf-8 -*-
from functools import wraps
from threading import Lock


def singleton(cls):
    instance = {}
    lock = Lock()

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instance:
            with lock:
                if cls not in instance:
                    instance[cls] = cls(*args, **kwargs)
        return instance[cls]

    return get_instance
