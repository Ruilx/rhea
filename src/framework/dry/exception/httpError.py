# -*- coding: utf-8 -*-

from fastapi.exceptions import HTTPException


class HttpError(HTTPException):
    Code = 0
    Msg = "HTTP错误"
    StatusCode = 200
    Headers = {
        'Content-Type': "application/json; charset=utf-8"
    }

    def __init__(self, msg: str | None = None, code: int | None = None, headers: dict[str, str] | None = None):
        if msg is not None:
            self.Msg = msg
        if code is not None:
            self.Code = code
        super().__init__(self.__class__.StatusCode, self.Msg, headers if headers is not None else self.__class__.Headers)

    def __str__(self):
        return f"Sythen {self.__class__.__name__}({self.Code}): {self.Msg}"

    def __repr__(self):
        return f"<HttpError {self.Code}: {self.Msg}>"


class RejectedError(HttpError):
    Code = 4000
    Msg = "拒绝访问"


class ParamsError(HttpError):
    Code = 4001
    Msg = "参数无效"


class NotLoginError(HttpError):
    Code = 4002
    Msg = "用户未登录"


class AuthError(HttpError):
    Code = 4003
    Msg = "认证失败"


class NoPermit(HttpError):
    Code = 4004
    Msg = "无权访问"


class NotFoundError(HttpError):
    Code = 4005
    Msg = "找不到资源"


class InsufficientError(HttpError):
    Code = 4011
    Msg = "余额不足"


class SysError(HttpError):
    Code = 5000
    Msg = "系统错误"


class DBError(HttpError):
    Code = 5001
    Msg = "数据库错误"


class CacheError(HttpError):
    Code = 5002
    Msg = "缓存错误"


class ServiceError(HttpError):
    Code = 5003
    Msg = "服务调用失败"


class LogicError(HttpError):
    Code = 5004
    Msg = "逻辑错误"
