# -*- coding: utf-8 -*-
from typing import Callable

from .base_formatter import Formatter
from ..node import Node

'''
Plain formatter output like below:

<__main__.A obj @=0x1b547355730 __sizeof__=16>
+-- member1 = <int __sizeof__=28> 1
+-- member2 = <complex __sizeof__=32> (2+3j)
+-- member3 = <str @=0x1b547c09a70 __sizeof__=48 __len__=7> ABCDEFG
+-- member4 = <builtins.object obj @=0x1b526bbf050 __sizeof__=16>
+-- member5 = <list> [5, 6, 7, 8]
+-- member6 = <tuple> (5, 6, 7, 8)
+-- member7 = <builtins.function obj @=0x1b547349620 __sizeof__=144>
+-- member8 = <class 'type'>
    +-- mro = <builtins.method_descriptor obj @=0x1b526b449f0 __sizeof__=56>
+-- PROP1 = <str @=0x7ffffc7561f0 __sizeof__=44 __len__=3> abc
+-- PROP2 = <list> [12, 34, 56]
+-- PROP3 = <dict> {'a': 1, 'b': 2}
+-- B = <class '__main__.A.B'>
    +-- C = <class '__main__.A.B.C'>
        +-- PROP = <str @=0x1b547c048f0 __sizeof__=54 __len__=13> Hello, World!
+-- PROP = <__main__.A.B obj @=0x1b547c0b980 __sizeof__=16>
    +-- C = <type ... Ref@=0x1b547572c90>
'''


class PlainFormatter(Formatter):

    def __init__(self):
        super().__init__()
        self.indent_len = 4
        self.indent_prefix = " " * self.indent_len
        self.indent_tree = "+-- "
        self.kv_sep = " = "

    def _build_prefix_indent(self, indent: int) -> str:
        if indent == 1:
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

    def _format_header(self, key: str, props: str, attrs: str, value: str, indent: int, printer: Callable[[str], None]):
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
        printer("".join(s))

    def _arrange(self, s: list[str]):
        return "\n".join(s)
