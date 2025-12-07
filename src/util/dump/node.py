# -*- coding: utf-8 -*-

from .formatter.base_formatter import Formatter

class Node(object):
    def __init__(self, title: str):
        self.title: str = title
        self.kv_sep: str = " = "
        self.attrs: dict[str, Any] = {}
        self.children: list[Node] = []

    def set_title(self, title: str) -> Self:
        self.title = title
        return self

    def get_title(self):
        return self.title

    def set_kv_sep(self, kv_sep: str) -> Self:
        self.kv_sep = kv_sep
        return self

    def get_kv_sep(self):
        return self.kv_sep

    def set_attr(self, key: str, value: Any) -> Self:
        self.attrs[key] = value
        return self

    def get_attrs(self):
        return self.attrs

    def append(self, node: Self):
        self.children.append(node)

    def iter(self) -> Iterator[Self]:
        return iter(self.children)

    def render(self, formatter: "Formatter"):
        ...
