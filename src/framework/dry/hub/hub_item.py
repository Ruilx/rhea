# -*- coding: utf-8 -*-

import importlib


class HubItem(object):
    def __init__(self, module_path: str, class_name: str):
        self.module_path = module_path
        self.class_name = class_name

    def get_class(self):
        assert self.module_path, "module_path is empty"
        assert self.class_name, "class_name is empty"

        try:
            module = importlib.import_module(self.module_path)
        except ModuleNotFoundError as e:
            if e != self.module_path:
                raise e from None
            raise ImportError(f"Could not import module {self.module_path}.")

        instance = module
        try:
            for attr_str in self.class_name.split('.'):
                instance = getattr(instance, attr_str)
        except AttributeError:
            raise ImportError(f"Could not import class {self.class_name} from module {self.module_path}.")

        return instance

    def get_module_path(self):
        return self.module_path

    def get_class_name(self):
        return self.class_name

    def __getstate__(self):
        return self.module_path, self.class_name

    def __setstate__(self, state):
        self.module_path, self.class_name = state
