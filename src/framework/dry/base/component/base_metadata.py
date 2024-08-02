# -*- coding: utf-8 -*-
from src.framework.dry.base.types import SerializableType


class BaseMetadata(object):
    RequiredMetadata = [
        'name',
        'display_name'
        'description',
        'version',
        'author',
        'organization'
        'email',
    ]

    def __init__(self, **metadata):
        for field in BaseMetadata.RequiredMetadata:
            if field not in metadata:
                raise KeyError(f"missing required metadata field: {field}")
        self._metadata: [str, SerializableType] = metadata

    def set_metadata(self, name: str, value: SerializableType):
        self._metadata[name] = value

    def has_metadata(self, name: str):
        return name in self._metadata

    def get_metadata(self, name: str):
        if name in self._metadata:
            return self._metadata[name]
        return None

    def name(self):
        return self.get_metadata('name')

    def version(self):
        return self.get_metadata('version')

    def display_name(self):
        return self.get_metadata('display_name')

    def description(self):
        return self.get_metadata('description')

    def author(self):
        return self.get_metadata('author')

    def organization(self):
        return self.get_metadata('organization')

    def email(self):
        return self.get_metadata('email')

    def __getstate__(self):
        return self._metadata

    def __setstate__(self, state):
        self._metadata = state
