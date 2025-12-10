# python
# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("colortty")
    except PackageNotFoundError:
        __version__ = "0.0.0"
except BaseException:
    __version__ = "0.0.0"

__author__ = "Ruilx"
__email__ = "RuilxAlxa@qq.com"
__license__ = "MIT"
__url__ = "https://github.com/Ruilx/colortty"
__description__ = "终端颜色输出工具包"

if TYPE_CHECKING:
    from .colortty import ColorTTY, colortty


def __getattr__(name: str):
    if name in {"ColorTTY", "colortty"}:
        from .colortty import ColorTTY, colortty
        return {"ColorTTY": ColorTTY, "colortty": colortty}[name]
    raise AttributeError(f"module 'colortty' has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + ["ColorTTY", "colortty"])


__all__ = ["ColorTTY", "colortty"]
