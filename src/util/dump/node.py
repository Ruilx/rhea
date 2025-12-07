# -*- coding: utf-8 -*-
import enum
from typing import Any, Self, Iterator

from black.nodes import NodeType

from .formatter.base_formatter import Formatter


'''
<__main__.A obj  @=0x1b547355730 __sizeof__=16>
|TITLE     |TYPE| ATTR1         |ATTR2        |

 member3 = <str   @=0x1b547c09a70 __sizeof__=48 __len__=7> ABCDEFG
|KEY    |  |TITLE| ATTR1         | ATTR2       | ATTR3    | TEXT
'''

class Node(object):

    class NodeType(enum.Enum):
        NodeType_Root = enum.auto()
        NodeType_Value = enum.auto()

    def __init__(self, title: str):
        self.title = ""
        self.key = ""
        self.type: NodeType = NodeType.NodeType_Root
        self.attrs: dict[str, Any] = {}
        self.text = ""
        self.children: list[Node] = []
        self.set_title(title)

    def set_title(self, title: str) -> Self:
        self.title = title
        return self

    def get_title(self):
        return self.title

    def set_key(self, key: str) -> Self:
        self.key = key
        return self

    def get_key(self):
        return self.key

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
