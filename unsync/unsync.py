import asyncio
import concurrent
from functools import wraps
from threading import Thread


class Unfuture:
    def __init__(self, future=None):
        self.future = future or asyncio.Future(loop=unsync.loop)
        concurrent_future = concurrent.futures.Future()

        def callback():
            try:
                asyncio.futures._chain_future(self.future, concurrent_future)
            except Exception as exc:
                if concurrent_future.set_running_or_notify_cancel():
                    concurrent_future.set_exception(exc)
                raise

        self.future._loop.call_soon_threadsafe(callback)
        self.concurrent_future = concurrent_future

    def __iter__(self):
        return self.future.__iter__()

    __await__ = __iter__

    def result(self, *args, **kwargs):
        return self.concurrent_future.result(*args, **kwargs)

    @property
    def state(self):
        return self.future._state

    def set_result(self, value):
        return self.future._loop.call_soon_threadsafe(lambda: self.future.set_result(value))


class unsync(object):
    loop = asyncio.new_event_loop()
    thread = None

    @staticmethod
    def thread_target(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.f = args[0]
        wraps(self.__call__)(self.f)

    def __call__(self, *args, **kwargs):
        return Unfuture(asyncio.ensure_future(self.f(*args, **kwargs), loop=self.loop))


unsync.thread = Thread(target=unsync.thread_target, args=(unsync.loop,), daemon=True)
unsync.thread.start()
