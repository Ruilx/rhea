# -*- coding: utf-8 -*-
import types
from itertools import islice
from typing import Callable, Optional

from src.framework.dry.base.types import NumberType, ContainerType
from util.dump.formatter.plain_formatter import PlainFormatter
from util.dump.node import Node
from util.helper import str_escape


class DumpColor(object): ...


class Dump(object):
    MagicMethods = {
        *(object().__dir__()),
        *((lambda: ...).__dir__()),
        *(filter(lambda x: x.startswith("__"), type.__dict__.keys())),
        "__func__",
        "__self__",
        "__weakref__",
        "__set__",
        "__delete__",
        "__objclass__",
        "__wrapped__",
        "__mro_entries__",
        "__getitem__",
        "__getattr__",
        "__slots__",
        "__len__",
        "__contains__",
        "__reserved__",
        "__reversed__",
        "__bool__",
        "__iter__",
    }

    LenStr = "__len__"
    SizeofStr = "__sizeof__"

    def __init__(self):
        self.in_detail = False

        self.handles: dict[type, Callable[[Node, object, int], Node]] = {
            dict: self._dump_dict,
            list: self._dump_container,
            tuple: self._dump_container,
            set: self._dump_container,
            str: self._dump_str,
            bool: self._dump_bool,
            int: self._dump_number,
            float: self._dump_number,
            complex: self._dump_number,
            None: self._dump_none,
            Ellipsis: self._dump_ellipsis,
            BaseException: self._dump_base_exception,
            type: self._dump_type,
            object: self._dump_object,
        }

        self.attr_config = {
            dict: {
                "@": self._get_object_id,
                "__len__": lambda o: o.__len__(),
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            list: {
                "@": self._get_object_id,
                "__len__": lambda o: o.__len__(),
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            tuple: {
                "@": self._get_object_id,
                "__len__": lambda o: o.__len__(),
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            set: {
                "@": self._get_object_id,
                "__len__": lambda o: o.__len__(),
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            str: {
                "@": self._get_object_id,
                "__len__": lambda o: o.__len__(),
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            bool: {},
            int: {
                "@": self._get_object_id,
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            float: {
                "@": self._get_object_id,
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            complex: {
                "@": self._get_object_id,
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            None: {},
            Ellipsis: {},
            BaseException: {
                "@": self._get_object_id,
                "msg": lambda o: str_escape(o.__str__()),
            },
            type: {
                "@": self._get_object_id,
                "__sizeof__": lambda o: o.__sizeof__(),
            },
            object: {
                "@": self._get_object_id,
                "__sizeof__": lambda o: o.__sizeof__(),
            },
        }

        self.id_table: dict[int, object] = {}

        # 是否只显示前head_count项，防止项目数过多，导致打印卡住。None就不限制，可能有打印卡住的危险。
        self.head_count: int | None = 100

        # 是否只向下挖掘depth深度，防止递归次数过多。None就不限制，可能结构会出现混乱。
        self.depth: int | None = 5

        # 如果发现循环引用的变量，是显示明细还是直接显示"..."
        self.str_if_recur: Optional[str | Ellipsis] = None

    def _build_prefix_indent(self, indent: int, /, inline=False) -> str:
        if inline or indent <= 0:
            return ""
        elif indent == 1:
            return self.indent_prefix
        else:
            return f"{self.indent_gap * (indent - 1)}{self.indent_prefix}"

    def _check_obj_is_new(self, obj: object):
        if isinstance(obj, (int, float, complex, bool, str, bytes)):
            # 值对象不做记录处理。
            return True
        if self.id_table.__contains__(id(obj)):
            return False
        else:
            self.id_table[id(obj)] = obj
            return True

    def set_in_detail(self, in_detail: bool):
        """
        是否使用树形优美打印方案，将会单独处理dict、list等带有特殊str的描述的内容。
        :param in_detail: bool
        :return: None
        """
        self.in_detail = in_detail

    def set_indent_length(self, indent_length: int):
        """
        设置缩进长度，默认为4
        :param indent_length:
        :return:
        """
        self.indent_length = indent_length

    def set_indent_prefix(self, indent_prefix: str):
        """
        设置缩进前缀，默认是“+-- ”
        :param indent_prefix:
        :return:
        """
        self.indent_prefix = indent_prefix

    def set_indent_gap(self, indent_gap: str):
        """
        设置缩进前缀前的空格，默认是indent_length * " "
        :param indent_gap:
        :return:
        """
        self.indent_gap = indent_gap

    def _get_attrs(self, t: type, obj: object) -> dict[str, str]:
        if t not in self.attr_config:
            return {'noattr': ""}
        # return dict(map(lambda d, (d[0], d[1](obj) if callable(d[1]) else str(d[1])), self.attr_config[t].items()))
        return {k: v(obj) if callable(v) else v for k, v in self.attr_config[t].items()}

    def _check_head_count(self, index: int) -> bool:
        return isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index

    def register_handle(self, t: type, handle: Callable[[Node, object, int], Node]):
        self.handles[t] = handle

    @staticmethod
    def _get_object_id(obj: object, hex_format: bool = True) -> str:
        return hex(id(obj)) if hex_format else str(id(obj))

    @staticmethod
    def _get_type_module_str(t: type) -> str:
        t_module = t.__module__
        if t_module == "builtins" and not t.__flags__ & (1 << 9):
            return t.__qualname__
        return f"{t_module}.{t.__qualname__}"

    @staticmethod
    def _get_obj_class_str(obj: object) -> str:
        obj_class = obj.__class__
        return Dump._get_type_module_str(obj_class)

    @staticmethod
    def _str_escape(s: str) -> str:
        return s.encode("unicode_escape").decode()

    def _dump_dict(self, node: Node, obj: dict, depth: int = 0):
        rest_len = obj.__len__() - self.head_count
        node.set_prop("type", "dict")
        if self.in_detail:
            node.set_attrs(self._get_attrs(dict, obj))
            if self.depth is not None and depth <= self.depth:
                for index, (key, value) in enumerate(obj.items()):
                    if self._check_head_count(index):
                        child_node = Node()
                        child_node.set_key(key)
                        self._dump2(child_node, value, depth + 1)
                        node.append_node(child_node)
                    else:
                        more_node = Node()
                        more_node.set_prop("type", f"More {rest_len} items...")
                        node.append_node(more_node)
                        break
        else:
            node.set_value(f"{dict(islice(obj.items(), self.head_count))!s}{f' and more {rest_len} items...' if rest_len > 0 else ''}")
        return node

    def _dump_container(self, node: Node, obj: ContainerType, depth: int = 0):
        rest_len = obj.__len__() - self.head_count
        t = obj.__class__
        node.set_prop("type", t.__name__)
        if self.in_detail:
            node.set_attrs(self._get_attrs(t, obj))
            if self.depth is not None and depth <= self.depth:
                for index, value in enumerate(obj):
                    if self._check_head_count(index):
                        child_node = Node()
                        child_node.set_key(f"[{index}]")
                        self._dump2(child_node, value, depth + 1)
                        node.append_node(child_node)
                    else:
                        more_node = Node()
                        more_node.set_prop("type", f"More {rest_len} items...")
                        node.append_node(more_node)
                        break
        else:
            node.set_value(
                f"{obj.__class__(islice(obj, self.head_count))!s}{f' and more {rest_len} items...' if rest_len > 0 else ''}")
        return node

    def _dump_str(self, node: Node, obj: str, depth: int = 0):
        rest_chars = obj.__len__() - self.head_count
        node.set_prop("type", "str")
        node.set_attrs(self._get_attrs(str, obj))
        node.set_value(f"{''.join(islice(obj, self.head_count))}{f'...(more {rest_chars} chars)' if rest_chars > 0 else ''}")
        return node

    def _dump_bool(self, node: Node, obj: str, depth: int = 0):
        node.set_prop("type", "bool")
        node.set_attrs(self._get_attrs(bool, obj))
        node.set_value(obj.__str__())
        return node

    def _dump_number(self, node: Node, obj: NumberType, depth: int = 0):
        t = obj.__class__
        node.set_prop("type", t.__name__)
        node.set_attrs(self._get_attrs(t, obj))
        node.set_value(obj.__str__())
        return node

    def _dump_none(self, node: Node, obj: None, depth: int = 0):
        node.set_value("None")
        return node

    def _dump_ellipsis(self, node: Node, obj: types.EllipsisType, depth: int = 0):
        node.set_value("...")
        return node

    def _dump_base_exception(self, node: Node, obj: BaseException, depth: int = 0):
        node.set_prop("type", self._get_obj_class_str(obj))
        node.set_attr("msg", str_escape(obj.__str__()))
        return node

    def _dump_type(self, node: Node, t: type, depth: int = 0):
        node.set_prop("title", "class")
        node.set_prop("type", self._get_type_module_str(t))
        dict_list = t.__dict__
        for index, (attr, value) in enumerate(dict_list.items()):
            if attr in self.MagicMethods:
                continue
            if self._check_head_count(index):
                child_node = Node()
                child_node.set_key(attr)
                self._dump2(child_node, value, depth + 1)
                node.append_node(child_node)
            else:
                more_node = Node()
                more_node.set_prop("type", f"More {dict_list.__len__() - self.head_count} items...")
                node.append_node(more_node)
                break
        return node

    def _dump_object(self, node: Node, obj: object, depth: int = 0):
        node.set_prop("title", self._get_obj_class_str(obj))
        node.set_prop("type", "obj")
        node.set_attrs(self._get_attrs(object, obj))
        members = obj.__dir__()
        for index, member in enumerate(members):
            if member in self.MagicMethods:
                continue
            if self._check_head_count(index):
                child_node = Node()
                child_node.set_key(member)
                self._dump2(child_node, getattr(obj, member), depth + 1)
                node.append_node(child_node)
            else:
                more_node = Node()
                more_node.set_prop("type", f"More {members.__len__() - self.head_count} items...")
                node.append_node(more_node)
                break
        return node

    def _dump2(self, node: Node, obj: object, depth: int) -> Node:
        if not self._check_obj_is_new(obj):
            if self.str_if_recur is Ellipsis:
                node.set_key("...")
            elif isinstance(self.str_if_recur, str):
                node.set_key(self.str_if_recur)
            else:
                node.set_prop("type", obj.__class__.__name__)
                node.set_attr("Ref@", self._get_object_id(obj))
        for mro_item in obj.__class__.__mro__:
            if self.handles.__contains__(mro_item):
                self.handles[mro_item](node, obj, depth)
                break
        else:
            node.set_prop("title", self._get_obj_class_str(obj))
            node.set_prop("type", "object")
            node.set_attrs(self._get_attrs(object, obj))
        return node

    def dump(self, obj: object) -> Node:
        self.id_table.clear()
        root_node = Node()
        return self._dump2(root_node, obj, 0)


if __name__ == "__main__":
    class A:
        PROP1 = "abc"
        PROP2 = [12, 34, 56]
        PROP3 = {"a": 1, "b": 2}

        def __init__(self):
            self.member1 = 1
            self.member2 = 2 + 3j
            self.member3 = "ABCDEFG"
            self.member4 = object()
            self.member5 = [5, 6, 7, 8]
            self.member6 = (5, 6, 7, 8)
            self.member7 = lambda x: x
            self.member8 = type
            self.member9 = range(100)

        class B:
            class C:
                PROP = "Hello, World!"

        PROP = B()


    d = Dump()
    d.set_in_detail(True)
    d.head_count = 100
    pf = PlainFormatter()
    for l in pf.render(d.dump(A())):
        print(l)
