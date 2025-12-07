# -*- coding: utf-8 -*-
import sys
import types
from typing import Callable, TypeVar, Optional, Literal, Self, Iterator, Any

from src.framework.dry.base.types import NumberType
from util.helper import get_object_id, get_obj_class_str, get_ref_info, str_escape


class DumpColor(object):
    ...

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
    }

    LenStr = '__len__'
    SizeofStr = '__sizeof__'

    def __init__(self):
        self.in_detail = False

        self.handles : dict[type, Callable[[object, int, int, bool], str]] = {
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
        self.str_if_recur: Optional[str | Ellipsis] = None

        # 打印颜色(未实现)
        # Plain: 原始字符串输出。
        # TTYColor： 终端颜色输出，使用ANSI转义码。
        # HTML： 使用"<span class="...">...</span>"的方式来在网页上显示。
        # JSON： 使用JSON格式输出，适合机器读取。
        # XML： 使用XML格式输出，适合机器读取。
        self.format: Literal["Plain", "TTYColor", "HTML", "JSON", "XML"] = "Plain"

    def _build_prefix_indent(self, indent: int, /, inline = False) -> str:
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

    def register_handle(self, t: T, handle: Callable[[object, int, int, bool], str]):
        self.handles[t] = handle


    def _dump_dict(self, obj: dict, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        if self.in_detail:
            pstr = [f"{self._build_prefix_indent(indent, inline)}<dict @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"]
            if self.depth is not None and depth <= self.depth:
                indent += 1
                for index, (key, value) in enumerate(obj.items()):
                    if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                        pstr.append(f"{self._build_prefix_indent(indent)}[{key}] = {self._dump(value, indent, depth + 1, True)}")
                    else:
                        pstr.append(f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count} items...]")
                        break
            return "\n".join(pstr)
        return f"<dict> {obj.__str__()}"

    def _dump_dict2(self, obj: dict):
        if self.in_detail:
            node = Dump.Node()
            node.title

    def _dump_list(self, obj: list, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        if self.in_detail:
            pstr = [f"{self._build_prefix_indent(indent, inline)}<list @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"]
            if self.depth is not None and depth <= self.depth:
                indent += 1
                for index, value in enumerate(obj):
                    if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                        pstr.append(f"{self._build_prefix_indent(indent)}[{index}] = {self._dump(value, indent, depth + 1, True)}")
                    else:
                        pstr.append(f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count} items...]")
                        break
            return "\n".join(pstr)
        return f"<list> {obj.__str__()}"

    def _dump_tuple(self, obj: tuple, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        if self.in_detail:
            pstr = [f"{self._build_prefix_indent(indent, inline)}<tuple @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"]
            if self.depth is not None and depth <= self.depth:
                indent += 1
                for index, value in enumerate(obj):
                    if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                        pstr.append(f"{self._build_prefix_indent(indent)}[index] = {self._dump(value, indent, depth + 1, True)}")
                    else:
                        pstr.append(f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count}] items...")
                        break
            return "\n".join(pstr)
        return f"<tuple> {obj.__str__()}"

    def _dump_set(self, obj: set, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        if self.in_detail:
            pstr = [f"{self._build_prefix_indent(indent, inline)}<set @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}>"]
            if self.depth is not None and depth <= self.depth:
                indent += 1
                for index, value in enumerate(obj):
                    if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                        pstr.append(f"{self._build_prefix_indent(indent)}[index] = {self._dump(value,  indent, depth + 1, True)}")
                    else:
                        pstr.append(f"{self._build_prefix_indent(indent)}[More {obj.__len__() - self.head_count}] items...")
                        break
            return "\n".join(pstr)
        return f"<set> {obj.__str__()}"

    def _dump_str(self, obj: str, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        # str.encode().decode() maybe leak some performance
        return f"<str @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()} {self.LenStr}={obj.__len__()}> {str_escape(obj)}"

    def _dump_bool(self, obj: bool, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        return f"<bool> {obj.__str__()}"

    def _dump_number(self, obj: NumberType, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        return f"<{obj.__class__.__name__} {self.SizeofStr}={obj.__sizeof__()}> {obj.__str__()}"

    def _dump_none(self, obj: None, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        return "<None>"

    def _dump_ellipsis(self, obj: types.EllipsisType, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        return "..."

    def _dump_base_exception(self, obj: BaseException, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        return f"<{get_obj_class_str(obj)} @={get_object_id(obj)} msg={str_escape(obj.__str__())}>"

    def _dump_type(self, t: type, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        module = t.__module__
        pstr = []

        if module == "builtins" and not t.__flags__ & (1 << 9):
            pstr.append(f"{self._build_prefix_indent(indent, inline)}<class '{t.__qualname__}'>")
        else:
            pstr.append(f"{self._build_prefix_indent(indent, inline)}<class '{t.__module__}.{t.__qualname__}'>")
        indent += 1
        dict_list = t.__dict__
        for index, (attr, value) in enumerate(dict_list.items()):
            if attr in self.MagicMethods:
                continue
            if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                pstr.append(f"{self._build_prefix_indent(indent)}{attr} = {self._dump(value, indent, depth + 1, True)}")
            else:
                pstr.append(f"{self._build_prefix_indent(indent)} [More {dict_list.__len__() - self.head_count} items...]")
                break
        return "\n".join(pstr)


    def _dump_object(self, obj: object, indent: int = 0, depth: int = 0, inline: bool = False) -> str:
        pstr = [f"{self._build_prefix_indent(indent, inline)}<{get_obj_class_str(obj)} obj @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()}>"]
        indent += 1
        members = obj.__dir__()
        for index, member in enumerate(members):
            if member in self.MagicMethods:
                continue
            if isinstance(self.head_count, int) and self.head_count > 0 and self.head_count > index:
                pstr.append(f"{self._build_prefix_indent(indent)}{member} = {self._dump(getattr(obj, member), indent, depth + 1, True)}")
            else:
                pstr.append(f"{self._build_prefix_indent(indent)} [More {members.__len__() - self.head_count} items...]")
                break
        return "\n".join(pstr)

    def _dump(self, obj: object, indent: int, depth: int, inline: bool) -> str:
        if not self._check_obj_is_new(obj):
            if self.str_if_recur is Ellipsis:
                return "..."
            elif isinstance(self.str_if_recur, str):
                return self.str_if_recur
            else:
                return f"{self._build_prefix_indent(indent, inline)}<{obj.__class__.__name__} {get_ref_info(obj)}>"
        for mro_item in obj.__class__.__mro__:
            if self.handles.__contains__(mro_item):
                return self.handles[mro_item](obj, indent, depth, inline)
        return f"{self._build_prefix_indent(indent)}<{get_obj_class_str(obj)} object @={get_object_id(obj)} {self.SizeofStr}={obj.__sizeof__()}>"

    def dump(self, obj: object, /, printer: Callable[..., None | int] = print, **kwargs) :
        indent = 0
        self.id_table.clear()
        if "indent" in kwargs and isinstance(kwargs['indent'], int) and kwargs['indent'] >= 0:
            indent = kwargs['indent']
        printer(self._dump(obj, indent, 0, False))


if __name__ == "__main__":
    class A:
        PROP1 = "abc"
        PROP2 = [12,34,56]
        PROP3 = {'a': 1, 'b': 2}

        def __init__(self):
            self.member1 = 1
            self.member2 = 2 + 3j
            self.member3 = "ABCDEFG"
            self.member4 = object()
            self.member5 = [5,6,7,8]
            self.member6 = (5,6,7,8)
            self.member7 = lambda x: x
            self.member8 = type
        class B:
            class C:
                PROP = "Hello, World!"
        PROP = B()

    d = Dump()
    #d.set_in_detail(True)
    d.dump(A)
    print("===================")
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
