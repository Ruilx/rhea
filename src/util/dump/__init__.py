# -*- coding: utf-8 -*-
"""
Package: pydump
"""

from __future__ import annotations

import io
from typing import Any, List, TYPE_CHECKING
import importlib

try:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("dump")
    except PackageNotFoundError:
        __version__ = "0.0.0"
except BaseException:
    __version__ = "0.0.0"

__author__ = "Ruilx"
__email__ = "RuilxAlxa@qq.com"
__license__ = "MIT"
__url__ = "https://github.com/Ruilx/pydump"
__description__ = "Python object dump tool"

# Public API surface
__all__ = [
    "Dump",
    "Node",
    "BaseFormatter",
    "PlainFormatter",
    "dump_to",
]

if TYPE_CHECKING:
    from util.dump.dump import Dump as Dump  # noqa: F401
    from util.dump.node import Node as Node  # noqa: F401
    from util.dump.formatter.base_formatter import Formatter as BaseFormatter
    from util.dump.formatter.plain_formatter import PlainFormatter as PlainFormatter  # noqa: F401

# Lazy attribute loading (PEP 562)
_module_map = {
    "Dump": ("dump.dump", "Dump"),
    "Node": ("dump.node", "Node"),
    "BaseFormatter": ("dump.formatter.base_formatter", "Formatter"),
    "PlainFormatter": ("dump.formatter.plain_formatter", "PlainFormatter"),

}


def __getattr__(name: str):  # pragma: no cover
    if name in _module_map:
        mod_name, attr_name = _module_map[name]
        module = importlib.import_module(mod_name)
        return getattr(module, attr_name)
    raise AttributeError(f"module 'dump' has no attribute '{name}'")


def __dir__():  # pragma: no cover
    return sorted(list(globals().keys()) + __all__)


def dump_to(obj: Any, *, in_detail: bool = True, head_count: int | None = 100, depth: int | None = 5, formatter: str = None, to_stream: io.TextIOWrapper) -> List[str]:
    """
    Dump an object and render it into plain-text lines.

    Parameters:
        obj: The Python object to inspect.
        in_detail: Whether to render detailed tree structures (dict/list/etc.).
        head_count: Limit items displayed per container; None for unlimited.
        depth: Limit recursion depth; None for unlimited.

    Returns:
        List[str]: Rendered plain-text lines.
    """
    # Lazy imports to keep __init__ lightweight
    Dump_ = __getattr__("Dump")
    PlainFormatter_ = __getattr__("PlainFormatter")

    d = Dump_()
    d.set_in_detail(in_detail)
    d.head_count = head_count if head_count is not None else d.head_count
    d.depth = depth if depth is not None else d.depth

    formatter = PlainFormatter_()
    to_stream.writelines(formatter.render(d.dump(obj)))
