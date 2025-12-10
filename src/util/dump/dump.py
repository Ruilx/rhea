# -*- coding: utf-8 -*-
import sys
import types
from itertools import islice
from typing import Callable, TypeVar, Optional, Literal

from fastapi.dependencies.utils import check_file_field

from src.framework.dry.base.types import NumberType, ContainerType
from util.dump.formatter.plain_formatter import PlainFormatter
from util.dump.node import Node
from util.helper import get_object_id, get_obj_class_str, get_ref_info, str_escape


class DumpColor(object): ...


class Dump(object):
    T = TypeVar("T")

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

        # self.handles: dict[type, Callable[[object, int, int, bool], str]] = {
        #     dict: self._dump_dict,
        #     list: self._dump_list,
        #     tuple: self._dump_tuple,
        #     set: self._dump_set,
        #     str: self._dump_str,
        #     bool: self._dump_bool,
        #     int: self._dump_number,
        #     float: self._dump_number,
        #     complex: self._dump_number,
        #     None: self._dump_none,
        #     Ellipsis: self._dump_ellipsis,
        #     BaseException: self._dump_base_exception,
        #     type: self._dump_type,
        #     object: self._dump_object,
        # }

        self.handles2: dict[type, Callable[[Node, object, int], Node]] = {
            dict: self._dump_dict2,
            list: self._dump_container,
            tuple: self._dump_container,
            set: self._dump_container,
            str: self._dump_str2,
            bool: self._dump_bool2,
            int: self._dump_number2,
            float: self._dump_number2,
            complex: self._dump_number2,
            None: self._dump_none2,
            Ellipsis: self._dump_ellipsis2,
            BaseException: self._dump_base_exception2,
            type: self._dump_type2,
            object: self._dump_object2,
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

        self.hex_id_format = True

        self.indent_length = 4
        self.indent_prefix = "+-- "
        self.indent_gap = " " * self.indent_length

        # 是否只显示前head_count项，防止项目数过多，导致打印卡住。None就不限制，可能有打印卡住的危险。
        self.head_count: int | None = 100

        # 是否只向下挖掘depth深度，防止递归次数过多。None就不限制，可能结构会出现混乱。
        self.depth: int | None = 5

        # 如果发现循环引用的变量，是显示明细还是直接显示"..."
        self.str_if_recur: Optional[str | Ellipsis] = None

        # 打印颜色(未实现)
        # Plain: 原始字符串输出。
        # TTYColor： 终端颜色输出，使用ANSI转义码。
        # HTML： 使用"<span class="...">...</span>"的方式来在网页上显示。
        # JSON： 使用JSON格式输出，适合机器读取。
        # XML： 使用XML格式输出，适合机器读取。
        self.format: Literal["Plain", "TTYColor", "HTML", "JSON", "XML"] = "Plain"
        self.formatter = PlainFormatter

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

    def register_handle(self, t: T, handle: Callable[[object, int, int, bool], str]):
        self.handles[t] = handle

    @staticmethod
    def _get_object_id(obj: object, hex_format: bool = True) -> str:
        return hex(id(obj)) if hex_format else str(id(obj))

    @staticmethod
    def _get_type_module_str(t: type):
        t_module = t.__module__
        if t_module == "builtins" and not t.__flags__ & (1 << 9):
            return t.__qualname__
        return f"{t_module}.{t.__qualname__}"

    @staticmethod
    def _get_obj_class_str(obj: object):
        obj_class = obj.__class__
        return Dump._get_type_module_str(obj_class)

    # def _dump_dict(self, obj: dict, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     if self.in_detail:
    #         pstr = [
    #             f"{self._build_prefix_indent(indent, inline)}<dict @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"
    #         ]
    #         if self.depth is not None and depth <= self.depth:
    #             indent += 1
    #             for index, (key, value) in enumerate(obj.items()):
    #                 if (isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index):
    #                     pstr.append(f"{self._build_prefix_indent(indent)}[{key}] = {self._dump(value, indent, depth + 1, True)}")
    #                 else:
    #                     pstr.append(f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count} items...]")
    #                     break
    #         return "\n".join(pstr)
    #     return f"<dict> {obj.__str__()}"

    def _dump_dict2(self, node: Node, obj: dict, depth: int = 0):
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

    # def _dump_list(self, obj: list, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     if self.in_detail:
    #         pstr = [f"{self._build_prefix_indent(indent, inline)}<list @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"]
    #         if self.depth is not None and depth <= self.depth:
    #             indent += 1
    #             for index, value in enumerate(obj):
    #                 if (
    #                         isinstance(self.head_count, int)
    #                         and self.head_count > 0
    #                         and self.head_count > index
    #                 ):
    #                     pstr.append(
    #                         f"{self._build_prefix_indent(indent)}[{index}] = {self._dump(value, indent, depth + 1, True)}"
    #                     )
    #                 else:
    #                     pstr.append(
    #                         f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count} items...]"
    #                     )
    #                     break
    #         return "\n".join(pstr)
    #     return f"<list> {obj.__str__()}"

    # def _dump_list2(self, node: Node, obj: list, depth: int = 0) -> Node:
    #     rest_len = obj.__len__() - self.head_count
    #     node.set_prop("type", "list")
    #     if self.in_detail:
    #         node.set_attrs(self._get_attrs(list, obj))
    #         if self.depth is not None and depth <= self.depth:
    #             for index, value in enumerate(obj):
    #                 if self._check_head_count(index):
    #                     child_node = Node()
    #                     child_node.set_key(f"[{index}]")
    #                     self._dump2(child_node, value, depth + 1)
    #                     node.append_node(child_node)
    #                 else:
    #                     more_node = Node()
    #                     more_node.set_prop("type", f"More {rest_len} items...")
    #                     node.append_node(more_node)
    #                     break
    #     else:
    #         node.set_value(f"{list(islice(obj, self.head_count))!s}{f' and more {rest_len} items...' if rest_len > 0 else ''}")
    #     return node

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

    # def _dump_tuple(self, obj: tuple, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     if self.in_detail:
    #         pstr = [
    #             f"{self._build_prefix_indent(indent, inline)}<tuple @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"
    #         ]
    #         if self.depth is not None and depth <= self.depth:
    #             indent += 1
    #             for index, value in enumerate(obj):
    #                 if (
    #                         isinstance(self.head_count, int)
    #                         and self.head_count > 0
    #                         and self.head_count > index
    #                 ):
    #                     pstr.append(
    #                         f"{self._build_prefix_indent(indent)}[index] = {self._dump(value, indent, depth + 1, True)}"
    #                     )
    #                 else:
    #                     pstr.append(
    #                         f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count}] items..."
    #                     )
    #                     break
    #         return "\n".join(pstr)
    #     return f"<tuple> {obj.__str__()}"

    # def _dump_tuple2(self, node: Node, obj: list, depth: int = 0) -> Node:
    #     rest_len = obj.__len__() - self.head_count
    #     node.set_prop("type", "tuple")
    #     if self.in_detail:
    #         node.set_attrs(self._get_attrs(tuple, obj))
    #         if self.depth is not None and depth <= self.depth:
    #             for index, value in enumerate(obj):
    #                 if self._check_head_count(index):
    #                     child_node = Node()
    #                     child_node.set_key(f"[{index}]")
    #                     self._dump2(child_node, value, depth + 1)
    #                     node.append_node(child_node)
    #                 else:
    #                     more_node = Node()
    #                     more_node.set_prop("type", f"More {rest_len} items...")
    #                     node.append_node(more_node)
    #                     break
    #     else:
    #         node.set_value(f"{tuple(islice(obj, self.head_count))!s}{f' and more {rest_len} items...' if rest_len > 0 else ''}")
    #     return node

    # def _dump_set(self, obj: set, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     if self.in_detail:
    #         pstr = [
    #             f"{self._build_prefix_indent(indent, inline)}<set @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"
    #         ]
    #         if self.depth is not None and depth <= self.depth:
    #             indent += 1
    #             for index, value in enumerate(obj):
    #                 if (
    #                         isinstance(self.head_count, int)
    #                         and self.head_count > 0
    #                         and self.head_count > index
    #                 ):
    #                     pstr.append(
    #                         f"{self._build_prefix_indent(indent)}[index] = {self._dump(value, indent, depth + 1, True)}"
    #                     )
    #                 else:
    #                     pstr.append(
    #                         f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count}] items..."
    #                     )
    #                     break
    #         return "\n".join(pstr)
    #     return f"<set> {obj.__str__()}"

    # def _dump_set2(self, node: Node, obj: set, depth: int = 0) -> Node:
    #     rest_len = obj.__len__() - self.head_count
    #     node.set_prop("type", "set")
    #     if self.in_detail:
    #         node.set_attrs(self._get_attrs(set, obj))
    #         if self.depth is not None and depth <= self.depth:
    #             for index, value in enumerate(obj):
    #                 if self._check_head_count(index):
    #                     child_node = Node()
    #                     child_node.set_key(f"[{index}]")
    #                     self._dump2(child_node, value, depth + 1)
    #                     node.append_node(child_node)
    #                 else:
    #                     more_node = Node()
    #                     more_node.set_prop("type", f"More {rest_len} items...")
    #                     node.append_node(more_node)
    #                     break
    #     else:
    #         node.set_value(f"{set(islice(obj, self.head_count))!s}{f' and more {rest_len} items...' if rest_len > 0 else ''}")
    #     return node

    # def _dump_str(self, obj: str, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     # str.encode().decode() maybe leak some performance
    #     return f"<str @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}> {str_escape(obj)}"

    def _dump_str2(self, node: Node, obj: str, depth: int = 0):
        rest_chars = obj.__len__() - self.head_count
        node.set_prop("type", "str")
        node.set_attrs(self._get_attrs(str, obj))
        node.set_value(f"{''.join(islice(obj, self.head_count))}{f'...(more {rest_chars} chars)' if rest_chars > 0 else ''}")
        return node

    # def _dump_bool(self, obj: bool, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     return f"<bool> {obj.__str__()}"

    def _dump_bool2(self, node: Node, obj: str, depth: int = 0):
        node.set_prop("type", "bool")
        node.set_attrs(self._get_attrs(bool, obj))
        node.set_value(obj.__str__())
        return node

    # def _dump_number(self, obj: NumberType, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     return f"<{obj.__class__.__name__} {self.SizeofStr}={obj.__sizeof__()}> {obj.__str__()}"

    def _dump_number2(self, node: Node, obj: NumberType, depth: int = 0):
        t = obj.__class__
        node.set_prop("type", t.__name__)
        node.set_attrs(self._get_attrs(t, obj))
        node.set_value(obj.__str__())
        return node

    # def _dump_none(self, obj: None, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     return "<None>"

    def _dump_none2(self, node: Node, obj: None, depth: int = 0):
        node.set_value("None")
        return node

    # def _dump_ellipsis(self,obj: types.EllipsisType,indent: int = 0, depth: int = 0, inline: bool = False,) -> str:
    #     return "..."

    def _dump_ellipsis2(self, node: Node, obj: types.EllipsisType, depth: int = 0):
        node.set_value("...")
        return node

    # def _dump_base_exception(self, obj: BaseException, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     return f"<{get_obj_class_str(obj)} @={get_object_id(obj)} msg={str_escape(obj.__str__())}>"

    def _dump_base_exception2(self, node: Node, obj: BaseException, depth: int = 0):
        node.set_prop("type", self._get_obj_class_str(obj))
        node.set_attr("msg", str_escape(obj.__str__()))
        return node

    # def _dump_type(self, t: type, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
    #     module = t.__module__
    #     pstr = []
    #
    #     if module == "builtins" and not t.__flags__ & (1 << 9):
    #         pstr.append(
    #             f"{self._build_prefix_indent(indent, inline)}<class '{t.__qualname__}'>"
    #         )
    #     else:
    #         pstr.append(
    #             f"{self._build_prefix_indent(indent, inline)}<class '{t.__module__}.{t.__qualname__}'>"
    #         )
    #     indent += 1
    #     dict_list = t.__dict__
    #     for index, (attr, value) in enumerate(dict_list.items()):
    #         if attr in self.MagicMethods:
    #             continue
    #         if (
    #                 isinstance(self.head_count, int)
    #                 and self.head_count > 0
    #                 and self.head_count > index
    #         ):
    #             pstr.append(
    #                 f"{self._build_prefix_indent(indent)}{attr} = {self._dump(value, indent, depth + 1, True)}"
    #             )
    #         else:
    #             pstr.append(
    #                 f"{self._build_prefix_indent(indent)}[More {dict_list.__len__() - self.head_count} items...]"
    #             )
    #             break
    #     return "\n".join(pstr)

    def _dump_type2(self, node: Node, t: type, depth: int = 0):
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

    def _dump_object(
            self, obj: object, indent: int = 0, depth: int = 0, inline: bool = False
    ) -> str:
        pstr = [
            f"{self._build_prefix_indent(indent, inline)}<{get_obj_class_str(obj)} obj @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()}>"
        ]
        indent += 1
        members = obj.__dir__()
        for index, member in enumerate(members):
            if member in self.MagicMethods:
                continue
            if (
                    isinstance(self.head_count, int)
                    and self.head_count > 0
                    and self.head_count > index
            ):
                pstr.append(
                    f"{self._build_prefix_indent(indent)}{member} = {self._dump(getattr(obj, member), indent, depth + 1, True)}"
                )
            else:
                pstr.append(
                    f"{self._build_prefix_indent(indent)}[More {members.__len__() - self.head_count} items...]"
                )
                break
        return "\n".join(pstr)

    def _dump_object2(self, node: Node, obj: object, depth: int = 0):
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

    # def _dump(self, obj: object, indent: int, depth: int, inline: bool) -> str:
    #     if not self._check_obj_is_new(obj):
    #         if self.str_if_recur is Ellipsis:
    #             return "..."
    #         elif isinstance(self.str_if_recur, str):
    #             return self.str_if_recur
    #         else:
    #             return f"{self._build_prefix_indent(indent, inline)}<{obj.__class__.__name__} {get_ref_info(obj)}>"
    #     for mro_item in obj.__class__.__mro__:
    #         if self.handles.__contains__(mro_item):
    #             return self.handles[mro_item](obj, indent, depth, inline)
    #     return f"{self._build_prefix_indent(indent)}<{get_obj_class_str(obj)} object @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()}>"

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
            if self.handles2.__contains__(mro_item):
                self.handles2[mro_item](node, obj, depth)
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
    # for l in pf.render(d.dump(A)):
    #     print(l)
    # print("=====================")
    for l in pf.render(d.dump(A())):
        print(l)
