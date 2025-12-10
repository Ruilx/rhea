# -*- coding: utf-8 -*-
from typing import Callable, Any

from .base_formatter import Formatter
from ..node import Node


class PlainFormatter(Formatter):

    def __init__(self):
        super().__init__()
        self.indent_len = 4
        self.indent_prefix = " " * self.indent_len
        self.indent_tree = "+-- "
        self.kv_sep = " = "

    def _build_prefix_indent(self, indent: int) -> str:
        if indent == 0:
            return ""
        elif indent == 1:
            return self.indent_tree
        else:
            return f"{self.indent_prefix * (indent - 1)}{self.indent_tree}"

    def _format_key(self, node: Node) -> str:
        return node.get_key()

    def _format_props(self, node: Node) -> str:
        title = node.get_prop("title")
        type = node.get_prop("type")
        if title:
            return f"{title} {type}"
        else:
            return type

    def _format_attrs(self, node: Node) -> str:
        s = []
        for k, v in node.get_attrs().items():
            key = self.config['attr_key_rename'][k] if k in self.config['attr_key_rename'] else k
            s.append(f"{key}={v!s}")
        return " ".join(s)

    def _format_value(self, node: Node):
        return node.get_value()

    def _format_header(self, key: str, props: str, attrs: str, value: str, indent: int, context: dict[str, Any]):
        s = [self._build_prefix_indent(indent)]
        if key:
            s.append(key)
            s.append(self.kv_sep)
        if props:
            s.append(f"<{props}")
            if attrs:
                s.append(f" {attrs}")
            s.append(">")
        if value:
            s.append(f" {value}")
        return "".join(s)
