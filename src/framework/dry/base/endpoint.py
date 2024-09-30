# -*- coding: utf-8 -*-
import os

from starlette.exceptions import HTTPException
from fastapi import Request
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response

from src.framework.dry.assets.about import __slogan__
from src.framework.dry.exception import httpError
from src.framework.dry.exception.httpError import HttpError, RejectedError, NotFoundError, NoPermit, AuthError


async def index_handler(request: Request) -> Response:
    return PlainTextResponse(__slogan__)


async def info_handler(request: Request) -> Response:
    res = {}
    res['app'] = {
        '_': f"{request.app!s}",
        'app_router': {
            '_': f"{request.app.app_router}"
        }
    }
    return JSONResponse("INFO PLACEHOLDER")


async def env_handler(request: Request) -> Response:
    return JSONResponse(dict(os.environ))


async def favicon_handler(request: Request) -> Response:
    return FileResponse("public/favicon.ico", media_type='image/x-icon')


async def robots_handler(request: Request) -> Response:
    return FileResponse("public/robots.txt", media_type='text/plain')


HttpErrorTable = {
    400: RejectedError,
    401: AuthError,
    403: NoPermit,
    404: NotFoundError,
    405: 4999,
}


def http_exception_handler(request: Request, e: HTTPException) -> Response:
    error_or_int = HttpErrorTable.get(e.status_code, 6999)
    code = error_or_int.Code if hasattr(error_or_int, 'Code') else int(error_or_int)
    return JSONResponse(
        status_code=e.status_code,
        content={
            'msg': e.detail,
            'code': code,
            'data': {}
        }
    )


def http_error_handler(request: Request, e: HttpError) -> Response:
    return JSONResponse(
        status_code=200,
        content={
            'msg': e.Msg,
            'code': e.Code,
            'data': {},
            'meta': {
                'request_uri': request.url.__str__()[:256],
                'request_method': request.method,
                # 'request_trace_id': request.app
            }
        }
    )


def system_error_handler(request: Request, e: Exception) -> Response:
    return JSONResponse(
        status_code=200,
        content={
            'msg': e.__str__(),
            'code': 5000,
            'data': {},
            'meta': {
                'request_uri': request.url.__str__()[:256],
                'request_method': request.method,
                # 'request_trace_id': request.app
            }
        }
    )


def common_http_exception(request: Request, e: Exception) -> Response:
    if isinstance(e, HTTPException):
        return http_exception_handler(request, e)
    else:
        return system_error_handler(request, e)


def not_found_handler(request: Request, e: Exception) -> Response:
    if isinstance(e, HTTPException):
        return http_exception_handler(request, e)
    else:
        return system_error_handler(request, e)


def service_error_handler(request: Request, e: Exception) -> Response:
    if isinstance(e, HttpError):
        return http_error_handler(request, e)
    else:
        return system_error_handler(request, e)
