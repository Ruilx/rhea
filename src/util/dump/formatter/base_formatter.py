# -*- coding: utf-8 -*-
import abc
from typing import Generator, Callable, Optional, Any, NoReturn

from pygments.styles.dracula import yellow

from ..node import Node


class Formatter(metaclass=abc.ABCMeta):
    def __init__(self):
        self.config = {
            "attr_key_rename": {}
        }

    @abc.abstractmethod
    def _format_key(self, node: Node) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def _format_props(self, node: Node) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def _format_attrs(self, node: Node) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def _format_value(self, node: Node) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def _format_header(self, key: str, props: str, attrs: str, value: str, indent: int, printer: Callable[[str], None]):
        raise NotImplementedError

    @abc.abstractmethod
    def _arrange(self, s: list[str]):
        raise NotImplementedError

    def _pre_node(self, node: Node, printer: Callable[[str], None]):
        ...

    def _post_node(self, node: Node, printer: Callable[[str], None]):
        ...

    def _pre_render(self, node: Node):
        ...

    def _post_render(self, node: Node):
        ...

    def _printer(self, target: list[str]):
        def _(s: str):
            target.append(s)
        return _

    def _format_node(self, node: Node, indent: int):
        s: list[str] = []
        self._pre_node(node, self._printer(s))
        key = self._format_key(node)
        props = self._format_props(node)
        attrs = self._format_attrs(node)
        value = self._format_value(node)
        self._format_header(key, props, attrs, value, indent, self._printer(s))
        if node.children.__len__() > 0:
            for child_node in node.iter_children():
                yield from self._format_node(child_node, indent + 1)
        self._post_node(node, self._printer(s))
        yield self._arrange(s)

    def _render(self, node: Node) -> Generator[Generator[Any, Any, None] | None, None, None]:
        pre = self._pre_render(node)
        if pre:
            yield pre
        yield from self._format_node(node, 0)
        post = self._post_render(node)
        if post is not None or post is not NoReturn:
            yield post

    def render(self, node: Node):
        yield from self._render(node)
