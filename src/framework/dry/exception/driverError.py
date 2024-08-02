# -*- coding: utf-8 -*-

class DriverError(Exception):
    def __init__(self, msg: str | None = None):
        super().__init__(msg)
