# -*- coding: utf-8 -*-

import logging
import os
import sys
from typing import Literal, Union

from src.framework.dry.base.singleton import singleton

LogLevel = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
}

LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LogPathType = Union[os.PathLike, Literal["_stderr"], Literal["_stdout"]]

LogFormatter = "[%(asctime)s] %(levelname)s(%(process)d@%(threadName)s): %(filename)s:%(lineno)s: %(name)s: %(message)s"

Logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LogFormatter,
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

@singleton
class Logger(object):
    def __init__(self):
        self.loggers = {}
        self.level = logging.DEBUG
        self.streams = set()
        self.dict_config = Logging_config

    def set_level(self, level):
        assert level in LogLevel, f'Invalid log level: {level}'
        self.level = level

    def get_level(self):
        return self.level

    def add_stream(self, stream: LogPathType):
        self.streams.add(stream)

    def get_streams(self):
        return self.streams

    def add_logger(self, name, level: logging.DEBUG):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        self._setup(logger)
        self.loggers[name] = logger

    def get_logger(self, name):
        if name not in self.loggers:
            self.add_logger(name, self.level)
        return logging.getLogger(name)

    def _setup(self, logger):
        formatter = logging.Formatter(LogFormatter)
        if len(self.streams) < 1:
            print("Program has no logging stream, no logs will output.", file=sys.stderr)
            print("Note: Please use '--log=_stderr' log to the stderr.", file=sys.stderr)

        if '_stderr' in self.streams and '_stdout' in self.streams:
            print("There has stdout and stderr logging exist in log streams, only stderr output will affect.")
            self.streams.remove("-")

        for item in self.streams:
            assert isinstance(item, str), f"Every stream item needs string type, but '{type(item)}' found."
            if item == "_stdout":
                handler = logging.StreamHandler(stream=sys.stdout)
                for _, v in self.dict_config['handlers'].items():
                    v['class'] = "logging.StreamHandler"
                    v['stream'] = "ext://sys.stdout"
            elif item == "_stderr":
                handler = logging.StreamHandler(stream=sys.stderr)
                for _, v in self.dict_config['handlers'].items():
                    v['class'] = "logging.StreamHandler"
                    v['stream'] = "ext://sys.stderr"
            else:
                handler = logging.FileHandler(item, encoding="utf-8", delay=True)
                for _, v in self.dict_config['handlers'].items():
                    v['class'] = "logging.FileHandler"
                    v['filename'] = item
                    v['encoding'] = 'utf-8'

            if handler is not None:
                handler.setFormatter(formatter)
                logger.handlers.append(handler)

    @property
    def dict_logger(self):
        return self.dict_config


def setup_loggers(logger: Logger, logs: list[str] | tuple[str] | Literal["_stderr", "_stdout"], level_str: str = 'DEBUG'):
    logger.set_level(level_str)
    if isinstance(logs, (list, tuple)):
        for log in logs:
            logger.add_stream(log)
    else:
        logger.add_stream(logs)
