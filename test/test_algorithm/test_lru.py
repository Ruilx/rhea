#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import time
from typing import Any
from src.framework.dry.common.algorithm.lru import Lru, LruItem


class TestLru(unittest.TestCase):
    def lru_item_equal(self, item: LruItem, key: str, value: Any, expire: int):
        if hasattr(item, 'key'):
            self.assertEqual(item.key, key)
        if hasattr(item, 'value'):
            self.assertEqual(item.value, value)
        if hasattr(item, 'expire'):
            self.assertEqual(item.expire, expire)

    def lru_table_equal(self, table, d: dict[str, tuple[str, Any, int | None]]):
        for k, i in table.items():
            self.assertIn(k, d)
            item = d[k]
            self.lru_item_equal(i, item[0], item[1], item[2])

    def test_lru(self):
        lru = Lru(2)
        lru.clear()

        lru.set("key1", "value1")
        lru_data = lru.get_lru()
        self.assertEqual(lru_data, ["key1"])
        self.lru_table_equal(lru._table, {
            'key1': ('key1', 'value1', None),
        })

        lru.set("key2", "value2")
        lru_data = lru.get_lru()
        self.assertEqual(lru_data, ["key1", "key2"])
        self.lru_table_equal(lru._table, {
            'key1': ('key1', 'value1', None),
            'key2': ('key2', 'value2', None),
        })

        lru.set("key3", "value3")
        lru_data = lru.get_lru()
        self.assertEqual(lru_data, ["key2", "key3"])
        self.lru_table_equal(lru._table, {
            'key2': ('key2', 'value2', None),
            'key3': ('key3', 'value3', None),
        })

    def test_lru_expire(self):
        lru = Lru(2)
        lru.clear()

        lru.set("key1", "value1")
        value1 = lru.get("key1")
        self.assertEqual(value1, "value1")

        lru.set("key2", "value2")
        lru_data = lru.get_lru()
        self.assertEqual(lru_data, ['key1', 'key2'])
        value2 = lru.get("key2")
        self.assertEqual(value2, "value2")

        lru.set("key1", "VALUE1", 10)
        value1 = lru.get("key1")
        self.assertEqual(value1, "VALUE1")

        lru_data = lru.get_lru()
        self.assertEqual(lru_data, ['key2', 'key1'])

        print("Sleep 10 seconds to waiting for key1 empired")
        for i in range(10):
            print(f"{10 - i}", end=' ', flush=True)
            time.sleep(1)
        print()

        value1 = lru.get("key1")
        self.assertEqual(value1, None)
