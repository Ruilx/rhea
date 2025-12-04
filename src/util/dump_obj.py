# -*- coding: utf-8 -*-
import sys
import types
from types import FunctionType, CodeType
from typing import overload, Callable, TypeVar

import fastapi
import typing_extensions
from starlette.requests import Request

from src.framework.dry.base.types import NumberType
from util.helper import get_object_id, get_obj_class_str, get_ref_info, str_escape


class Dump(object):
    T = TypeVar("T")

    MagicMethods = [
        *(object().__dir__()),
    ]

    def __init__(self):
        self.pretty_print = False

        self.handles : dict[type, Callable[[object, int], str]] = {
            dict: self._dump_dict,
            list: self._dump_list,
            tuple: self._dump_tuple,
            set: self._dump_set,
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
        self.str_if_recur = Ellipsis

    def _build_prefix_indent(self, indent: int) -> str:
        if indent <= 0:
            return ""
        elif indent == 1:
            return self.indent_prefix
        else:
            return f"{self.indent_gap * (indent - 1)}{self.indent_prefix}"

    def _check_obj_is_new(self, obj: object):
        if self.id_table.__contains__(id(obj)):
            return False
        else:
            self.id_table[id(obj)] = obj
            return True

    def set_pretty_print(self, pretty_print: bool):
        """
        是否使用树形优美打印方案，将会单独处理dict、list等带有特殊str的描述的内容。
        :param pretty_print: bool
        :return: None
        """
        self.pretty_print = pretty_print

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

    def register_handle(self, t: T, handle: Callable[[object, int], str]):
        self.handles[t] = handle


    def _dump_dict(self, obj: dict, indent: int = 0) -> str:
        if self.pretty_print:
            pstr = [f"{self._build_prefix_indent(indent)}<dict @={get_object_id(obj)} __sizeof__={obj.__sizeof__()} __len__={obj.__len__()}>"]
            indent += 1
            for index, (key, value) in enumerate(obj.items()):
                if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                    pstr.append(f"{self._build_prefix_indent(indent)}[{key}] = {self._dump(value, indent=indent)}")
                else:
                    pstr.append(f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count} items...]")
                    break
            return "\n".join(pstr)
        return f"<dict> {obj.__str__()}"

    def _dump_list(self, obj: list, indent: int = 0) -> str:
        if self.pretty_print:
            pstr = [f"{self._build_prefix_indent(indent)}<list @={get_object_id(obj)} __sizeof__={obj.__sizeof__()} __len__={obj.__len__()}>"]
            indent += 1
            for index, value in enumerate(obj):
                if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                    pstr.append(f"{self._build_prefix_indent(indent)}[{index}] = {self._dump(value, indent=indent)}")
            return "\n".join(pstr)
        return f"<list> {obj.__str__()}"

    def _dump_tuple(self, obj: tuple, indent: int = 0) -> str:
        if self.pretty_print:
            pstr = [f"{self._build_prefix_indent(indent)}<tuple @={get_object_id(obj)} __sizeof__={obj.__sizeof__()} __len__={obj.__len__()}>"]
            indent += 1
            for index, value in enumerate(obj):
                pstr.append(f"{self._build_prefix_indent(indent)}[index] = {self._dump(value, indent=indent)}")
            return "\n".join(pstr)
        return f"<tuple> {obj.__str__()}"

    def _dump_set(self, obj: set, indent: int = 0) -> str:
        if self.pretty_print:
            pstr = [f"{self._build_prefix_indent(indent)}<set @={get_object_id(obj)} __sizeof__={obj.__sizeof__()} __len__={obj.__len__()}>"]
            indent += 1
            for index, value in enumerate(obj):
                pstr.append(f"{self._build_prefix_indent(indent)}[index] = {self._dump(value, indent=indent)}")
            return "\n".join(pstr)
        return f"<set> {obj.__str__()}"

    def _dump_str(self, obj: str, indent: int = 0) -> str:
        # str.encode().decode() maybe leak some performance
        return f"<str @={get_object_id(obj)} __sizeof__={obj.__sizeof__()} __len__={obj.__len__()}> {str_escape(obj)}"

    def _dump_bool(self, obj: bool, indent: int = 0) -> str:
        return f"<bool> {obj.__str__()}"

    def _dump_number(self, obj: NumberType, indent: int = 0) -> str:
        return f"<{obj.__class__.__name__} __sizeof__={obj.__sizeof__()}> {obj.__str__()}"

    def _dump_none(self, obj: None, indent: int = 0) -> str:
        return "<None>"

    def _dump_ellipsis(self, obj: types.EllipsisType, indent: int = 0) -> str:
        return "..."

    def _dump_base_exception(self, obj: BaseException, indent: int = 0) -> str:
        return f"<{get_obj_class_str(obj)} @={get_object_id()} msg={str_escape(obj.__str__())}>"

    def _dump_type(self, t: type, indent: int = 0) -> str:
        module = t.__module__
        if module == "builtins" and not t.__flags__ & 0x200:
            return f"<class '{t.__qualname__}'>"
        return f"<class '{t.__module__}.{t.__qualname__}'>"

    def _dump_object(self, obj: object, indent: int = 0) -> str:
        if self.pretty_print:
            return f"<object !pretty print>"
        return f"<object>"

    def _dump(self, obj: object, indent: int) -> str:
        if self.depth is not None and indent > self.depth:
            return ""
        if not self._check_obj_is_new(obj):
            if self.str_if_recur is not Ellipsis:
                return f"{self._build_prefix_indent(indent)}<{obj.__class__.__name__} {get_ref_info(obj)}>"
            else:
                return str(self.str_if_recur)
        for mro_item in obj.__class__.__mro__:
            print(f"finding {mro_item} in self.handles...")
            if self.handles.__contains__(mro_item):
                print(f"found! {mro_item} in self.handles. value={self.handles[mro_item]}")
                return self.handles[mro_item](obj, indent)
        return f"<{self._build_prefix_indent(indent)}{get_obj_class_str(obj)} object @={get_object_id(obj)} __sizeof__={obj.__sizeof__()}>"

    def dump(self, obj: object, /, indent: int = 0, printer: Callable[..., None | int] = print) :
        printer(self._dump(obj, indent))


if __name__ == "__main__":
    class A:
        ...

    d = Dump()
    d.register_handle(A, lambda o, i: "Hello, world!")
    d.dump(A())

# Dump太费事了, 不想写了

# class VarDump(object):
#     def __init__(self):
#         self.cached_ids = []
#
#     def _dump(self, v: ..., indent=0, ):
#
#     def dump(self, v: ...) -> str:
#         if isinstance(v, NumberType):
#             return v
#         elif isinstance(v, list):
#             res = []
#             for vv in v:
#                 res.append(self.dump(vv))
#             return ', '.join(res).join(("[", "]"))
#         elif isinstance(v, dict):
#             res =

# class DumpRequest(object):
#
#     @staticmethod
#     def dump_req(req: Request):
#         return {
#             '': f"{req!s}",
#             'app': DumpRequest.dump_req_app(req),
#             'auth': DumpRequest.dump_req_auth(req),
#             'base_url': DumpRequest.dump_req_base_url(req),
#             'client': DumpRequest.dump_req_client(req),
#             'cookies': DumpRequest.dump_req_cookies(req),
#             'headers': DumpRequest.dump_req_headers(req),
#             'method': DumpRequest.dump_req_method(req),
#             'path_params': DumpRequest.dump_req_path_params(req),
#             'query_params': DumpRequest.dump_req_query_params(req),
#             'scope': DumpRequest.dump_req_scope(req),
#             'session': DumpRequest.dump_req_session(req),
#             'state': DumpRequest.dump_req_state(req),
#             'url': DumpRequest.dump_req_url(req),
#             'user': DumpRequest.dump_req_user(req),
#         }
#
#     @staticmethod
#     def dump_req_app(req: Request):
#         try:
#             app = req.app
#         except Exception as e:
#             return {'': e.__str__()}
#
#
#
#     @staticmethod
#     def dump_req_auth(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_base_url(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_client(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_cookies(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_headers(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_method(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_path_params(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_query_params(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_scope(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_session(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_state(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_url(req: Request):
#         ...
#
#     @staticmethod
#     def dump_req_user(req: Request):
#         ...
