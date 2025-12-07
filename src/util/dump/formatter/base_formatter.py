# -*- coding: utf-8 -*-
import abc


class Formatter(metaclass=abc.ABCMeta):
    def __init__(self, root: List[Node]):
        self.root = root

    @abc.abstractmethod
    def render(self) -> str:
        raise NotImplementedError
