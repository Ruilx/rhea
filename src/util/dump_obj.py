# -*- coding: utf-8 -*-
from typing import overload

import fastapi
from starlette.requests import Request

from src.framework.dry.base.types import NumberType

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
