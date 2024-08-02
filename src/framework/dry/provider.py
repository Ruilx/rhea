# -*- coding: utf-8 -*-
from src.framework.dry.base.driver.base_driver import BaseDriver
from src.framework.dry.base.singleton import singleton


@singleton
class Provider(object):
    def __init__(self):
        self.drivers = {}

    def has(self, name: str):
        return name in self.drivers

    def get(self, name: str):
        if name in self.drivers:
            return self.drivers[name]

    def has(self):
        ...

    def register_driver(self, name: str, driver: BaseDriver):
        self.drivers[name] = driver


def cal(s, i, *l):
    assert l.__len__() > i
    test = l[i]
    print(f"{s=}, {i=}, {test=}")
    if len(l) > 1:
        newl = []
        for ii, x in enumerate(l):
            if ii != i:
                newl.append(x)
        print(newl)
        try:
            res = cal(s - test, 0, *newl)
            print(res)
            return res
        except FileNotFoundError:
            try:
                res = cal(s + test, 0, *newl)
                print(res)
                return res
            except FileNotFoundError:
                try:
                    res = cal(s / test, 0, *newl)
                    print(res)
                    return res
                except FileNotFoundError:
                    try:
                        res = cal(s * test, 0, *newl)
                        print(res)
                        return res
                    except FileNotFoundError:
                        try:
                            res = cal(s, i+1, *l)
                            print(res)
                            return res
                        except AssertionError:
                            raise FileNotFoundError from None
    else:
        if s - test == 0:
            return test, '+'
        elif s + test == 0:
            return test, '-'
        elif s / test == 0:
            return test, '*'
        elif s * test == 0:
            return test, '/'
        else:
            raise FileNotFoundError


cal(24, 0, 5, 6, 7, 8)
