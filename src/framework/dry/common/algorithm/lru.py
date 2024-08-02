# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable

from src.framework.dry.common.tool.timeout_lock import TimeoutLock


class LruItem(object):
    __slots__ = ('key', 'value', 'expire')
    key: str
    value: Any
    expire: datetime


class LruEvent(Enum):
    ManualSet = auto()
    AutoSet = auto()
    ValueChanged = auto()
    ResetExpire = auto()
    Expired = auto()
    ManualDeleted = auto()
    Advanced = auto()


class Lru(object):
    def __init__(self, capacity: int = 500):
        assert capacity > 0, 'capacity must be greater than 0'
        self._capacity = capacity
        self._table: dict[str, LruItem] = {}
        self._lru: list[str] = []
        self._expire_table: dict[datetime, list[str]] = {}
        self._lock = TimeoutLock(True, 3)
        self._lock_blocking = True
        self._lock_timeout = 3
        self._clean_when_query = True
        self._event_hook: list[Callable[[LruItem, LruEvent], None]] = []
        # self._event_loop = asyncio.new_event_loop()

    def __del__(self):
        # if not self._event_loop.is_closed():
        #     try:
        #         if self._event_loop.is_running():
        #             self._event_loop.stop()
        #         self.clear()
        #     finally:
        #         self._event_loop.close()
        self.clear()

    @property
    def capacity(self):
        return self._capacity

    # def _trigger_event(self, item: LruItem, event: LruEvent):
    #     for cb in self._event_hook:
    #         if callable(cb):
    #             self._event_loop.call_soon_threadsafe(cb, (item, event))
    #
    # def _run_event_loop(self):
    #     if self._event_loop.is_running():
    #         return
    #     self._event_loop.stop()
    #     self._event_loop.run_forever()

    def append_event_handler(self, cb: Callable[[LruItem, LruEvent], None]):
        self._event_hook.append(cb)

    def _trigger_event(self, item: LruItem, event: LruEvent):
        for cb in self._event_hook:
            if callable(cb):
                cb(item, event)

    def _do_del_from_expire_table(self, dt: datetime, key: str):
        if self._expire_table.__contains__(dt):
            if self._expire_table[dt].__contains__(key):
                self._expire_table[dt].remove(key)

    def _do_set_from_expire_table(self, dt: datetime, key: str):
        if not self._expire_table.__contains__(dt) or not isinstance(self._expire_table[dt], list):
            self._expire_table[dt] = []
        if not self._expire_table[dt].__contains__(key):
            self._expire_table[dt].append(key)

    def _do_del_from_lru(self, key: str):
        if key in self._lru:
            self._lru.remove(key)

    def _do_del(self, key: str) -> bool:
        if key in self._table:
            item = self._table[key]
            if hasattr(item, 'expire'):
                self._do_del_from_expire_table(item.expire, key)
            self._do_del_from_lru(key)
            del self._table[key]
            # TODO: async call deleted
            self._trigger_event(item, LruEvent.ManualDeleted)
            return True
        return False

    def _update_lru(self, key: str):
        if key in self._lru:
            i = self._lru.index(key)
            if i >= 0:
                self._lru.remove(key)
                self._lru.append(key)
                item = self._table[key]
                # TODO : async call action_hook
                self._trigger_event(item, LruEvent.Advanced)

    def _do_set(self, key: str, value: Any, expire: int) -> bool:
        dt = datetime.now() + timedelta(seconds=expire)
        if key in self._table:
            item = self._table[key]
            item.value = value
            if hasattr(item, 'expire'):
                self._do_del_from_expire_table(item.expire, key)
            if expire > 0:
                self._do_set_from_expire_table(dt, key)
            item.expire = dt
            # TODO: async called changed
            self._trigger_event(item, LruEvent.ValueChanged)
            self._update_lru(key)
        else:
            if not self._arrange():
                return False
            item = LruItem()
            item.key = key
            item.value = value
            self._table[key] = item
            if expire > 0:
                self._do_set_from_expire_table(dt, key)
            self._lru.append(key)
            # TODO: async call appended
            self._trigger_event(item, LruEvent.ManualSet)
        return True

    def _do_get(self, key: str):
        if key in self._table:
            item = self._table[key]
            if hasattr(item, 'expire'):
                if not isinstance(item.expire, datetime) or item.expire >= datetime.now():
                    self._update_lru(key)
                    return item.value
                else:
                    if self._clean_when_query:
                        self._do_del(key)
            else:
                self._update_lru(key)
                return item.value
        return None

    def _do_expire(self, key: str, expire: int) -> bool:
        dt = datetime.now() + timedelta(seconds=expire)
        if key in self._table:
            item = self._table[key]
            if hasattr(item, 'expire'):
                if item.expire >= datetime.now():
                    if expire > 0:
                        self._do_set_from_expire_table(dt, key)
                    else:
                        self._do_del_from_expire_table(dt, key)
                    item.expire = dt
                else:
                    if self._clean_when_query:
                        self._do_del(key)
                    return False
            else:
                if expire > 0:
                    self._expire_table[dt].append(key)
                    item.expire = dt
                # TODO: async call changed
                self._trigger_event(item, LruEvent.ResetExpire)
        return True

    def _remove_with_expired(self, count: int):
        dt = datetime.now()
        deleting_keys = []
        for expire, keys in self._expire_table.items():
            if expire < dt:
                for key in keys:
                    deleting_keys.append(key)
                    count -= 1
                    if count <= 0:
                        break
                if count <= 0:
                    break
        for key in deleting_keys:
            self._do_del(key)
        return count

    def _remove_with_lru(self, count: int):
        deleting_keys = []
        for key in self._lru:
            if count > 0:
                deleting_keys.append(key)
                count -= 1
            else:
                break
        for key in deleting_keys:
            self._do_del(key)
        return count

    def _arrange(self) -> bool:
        over_count = self._table.__len__() - self._capacity + 1
        if over_count > 0:
            over_count = self._remove_with_expired(over_count)
        if over_count > 0:
            over_count = self._remove_with_lru(over_count)
        if over_count > 0:
            raise RuntimeWarning(f"LRU cannot remove any more {over_count} items.")
        return True

    # def register_event_hook(self, cb: Callable[[LruItem, LruEvent], None]):
    #     self._event_hook.append(cb)

    def clear(self) -> None:
        with self._lock:
            self._lru.clear()
            self._expire_table.clear()
            self._table.clear()
            # TODO: cleared

    def set(self, key: str, value: Any, expire: int = 0) -> bool:
        with self._lock:
            if key.__len__() <= 0:
                return False
            return self._do_set(key, value, expire)

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key.__len__() <= 0:
                return None
            return self._do_get(key)

    def expire(self, key: str, expire: int) -> bool:
        with self._lock:
            if key.__len__() <= 0:
                return False
            return self._do_expire(key, expire)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key.__len__() <= 0:
                return False
            return self._do_del(key)

    def set_capacity(self, capacity: int):
        with self._lock:
            assert capacity > 0, f"capacity must be greater than 0, get: {capacity}"
            self._capacity = capacity
            if capacity < self._table.__len__():
                self._arrange()
            # TODO: resized

    def get_lru(self) -> list[str]:
        return self._lru
