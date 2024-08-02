# -*- coding: utf-8 -*-

from threading import Lock, RLock


class TimeoutLock(object):
    def __init__(self, blocking: bool = True, timeout: float = -1):
        self._lock = Lock()
        self._blocking = True
        self._timeout = -1
        self.blocking = blocking
        self.timeout = timeout

    def _set_blocking(self, blocking: bool):
        self._blocking = blocking

    @property
    def blocking(self):
        return self._blocking

    @blocking.setter
    def blocking(self, blocking: bool):
        self._set_blocking(blocking)

    def _set_timeout(self, timeout: float):
        if timeout < 0:
            timeout = -1
        self._timeout = timeout

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: float):
        self._set_timeout(timeout)

    def __enter__(self):
        acq = self._lock.acquire(self._blocking, self._timeout)
        if not acq:
            raise RuntimeError(f"lock acquire timeout in {self._timeout} second{'s' if self._timeout != 1 else ''}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lock.locked():
            self._lock.release()


class TimeoutRLock(object):
    def __init__(self, blocking: bool = True, timeout: float = -1):
        self._lock = RLock()
        self._blocking = True
        self._timeout = -1
        self.blocking = blocking
        self.timeout = timeout
        self._lock_count = 0

    @property
    def blocking(self):
        return self._blocking

    @blocking.setter
    def blocking(self, blocking: bool):
        self._blocking = blocking

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: float):
        if timeout < 0:
            timeout = 0
        self._timeout = timeout

    def __enter__(self):
        acq = self._lock.acquire(self._blocking, self._timeout)
        if not acq:
            raise RuntimeError(f"lock acquire timeout in {self._timeout} second{'s' if self._timeout != 1 else ''}")
        self._lock_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lock_count > 0:
            self._lock_count -= 1
            self._lock.release()
