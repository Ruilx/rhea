# -*- coding: utf-8 -*-

import asyncio
from threading import Thread
from asyncio import AbstractEventLoop
from typing import Callable


class EventLoop(object):
    def __init__(self, loop: AbstractEventLoop | None = None):
        if loop is None:
            self.loop = asyncio.new_event_loop()
        else:
            self.loop = loop

    def __del__(self):
        self.stop()
        self._close()

    def _close(self):
        if not self.loop.is_closed():
            self.loop.close()

    def call_soon(self, cb: Callable, *args, context=None):
        self.loop.call_soon(cb, *args, context=context)

    def call_soon_threadsafe(self, cb: Callable, *args, context=None):
        self.loop.call_soon_threadsafe(cb, *args, context=context)

    emit = call_soon_threadsafe

    def call_later(self, delay: float, cb: Callable, *args, context=None):
        self.loop.call_later(delay, cb, *args, context=context)

    def stop(self):
        if self.is_running():
            self.loop.stop()
        # else:
        #     raise RuntimeError("Event loop is not running.")

    quit = stop

    def scheduled_stop(self):
        self.loop.stop()

    def is_running(self):
        return self.loop.is_running()

    def elapsed(self) -> float:
        return self.loop.time()

    def exec(self):
        if not self.loop.is_running():
            self.loop.run_forever()
        else:
            raise RuntimeError("Event loop is already running.")


class EventLoopThread(object):
    def __init__(self, loop: EventLoop | None = None):
        self.loop = loop if isinstance(loop, EventLoop) else EventLoop()
        self.thread = Thread(group=None, target=self.run, name="event_loop_thread", daemon=True)

    def run(self):
        if not self.loop.is_running():
            self.loop.exec()
        raise RuntimeError("Event loop is already running.")

    def start(self):
        if not self.thread.is_alive():
            self.thread.start()
        raise RuntimeError("Event loop thread is already running.")

    def get_event_loop(self):
        return self.loop

    def stop(self, timeout: float | None = None):
        self.loop.stop()
        if self.thread.is_alive():
            self.thread.join(timeout)

    def is_running(self):
        return self.thread.is_alive()
