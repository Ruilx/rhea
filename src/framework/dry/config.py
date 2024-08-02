# -*- coding: utf-8
import os
from pathlib import Path
from typing import Any

import ujson
from pyhocon import ConfigFactory, ConfigTree, HOCONConverter

from src.framework.dry.base.singleton import singleton
from src.framework.dry.base.types import StructType
from src.framework.dry.common.context import SerializableContext
from src.framework.dry.logger import Logger

ConfigType = int | float | str | bool | None | list[...] | dict[str, ...]


@singleton
class Config(object):
    def __init__(self, config_file: os.PathLike | None = None):
        self._config_file: Path | None = None
        self._config: ConfigTree | None = None
        self._settings = SerializableContext({})
        if config_file is not None:
            self.set_config_file(config_file)
        self.logger = Logger().get_logger(__name__)

    def set_config_file(self, config_file: os.PathLike):
        self._config_file = config_file

    def load_config(self, reload=False):
        if self._config_file is None:
            assert self._config_file is not None, "Config file is not set"

        if self._config is None or reload:
            config = ConfigFactory.parse_file(self._config_file)
            assert isinstance(config, ConfigTree), "Config file is not a valid HOCON file"
            self._config = config
            self.logger.info(f"Loaded config file: {self._config_file}")

    def get_config(self, key: str, default: str | None = None) -> Any | None:
        self.load_config()
        return self._config.get(key, default)

    def get_config_obj(self, key: str, default: str | None = None) -> ConfigType:
        self.load_config()
        # ujson deep copy will slowly
        return ujson.loads(HOCONConverter.to_json(self._config.get(key, default), compact=True, indent=0))

    def reload(self):
        self.load_config(reload=True)

    @property
    def settings(self):
        return self._settings

    def get_setting(self, key: str, default: StructType | None = None) -> StructType:
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: StructType):
        self._settings[key] = value

    def __getstate__(self):
        return {
            '_config_file': self._config_file,
            '_config': HOCONConverter.to_json(self._config, compact=True, indent=0),
            '_settings': self._settings
        }

    def __setstate__(self, state):
        self._config_file = state['_config_file']
        self._config = ConfigFactory.parse_string(state['_config'])
        self._settings = state['_settings']
