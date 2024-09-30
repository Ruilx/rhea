# -*- coding: utf-8 -*-
import traceback
from typing import Callable

from uvicorn.importer import import_from_string


def log_exception(e: BaseException, logger_func: Callable, with_traceback: bool = True):
    logger_func(f"{e.__class__.__name__}: {e!r}")
    if with_traceback:
        log_traceback(e.__traceback__, logger_func)


def log_traceback(tb: "traceback", logger_func: Callable):
    for line in traceback.format_tb(tb):
        logger_func(line.strip())


def get_stack(ignore=1):
    stack = traceback.extract_stack()[:-ignore]
    data = []
    for filename, line_number, function_name, text in stack:
        data.append({
            "filename": filename,
            "line_no": line_number,
            "func_name": function_name,
            "text": text
        })
    return data


def log_stack(logger_func: Callable):
    for stack_item in get_stack(2):
        logger_func(f"file: {stack_item['filename']}:{stack_item['line_no']} in {stack_item['func_name']}:{stack_item['text']}")


SpecialString = {
    '': '<Empty>',
    None: '<None>'
}


def dump_obj(obj):
    line = []

    def dump_recur(o, depth=0, prefix='+-- '):
        if isinstance(o, dict):
            if not o:
                line.append(f"{'    ' * (depth - 1)}{prefix if depth > 0 else ''}{{}}")
                return
            for k, v in o.items():
                line.append(f"{'    ' * (depth - 1)}{prefix if depth > 0 else ''}{SpecialString[k] if k in SpecialString else k}: ")
                dump_recur(v, depth + 1, prefix)
        elif isinstance(o, list | tuple | set):
            if not o:
                line.append(f"{'    ' * (depth - 1)}{prefix if depth > 0 else ''}[]")
                return
            for i, v in enumerate(o):
                line.append(f"{'    ' * (depth - 1)}{prefix if depth > 0 else ''}[{i}]: ")
                dump_recur(v, depth + 1, prefix)
        elif isinstance(o, str):
            line[-1] += f"\"{o}\""
        else:
            line[-1] += f"{o!s}"

    dump_recur(obj)
    return '\n'.join(line)


def import_class(module_path: str, class_name: str):
    return import_from_string(f"{module_path}:{class_name}")
