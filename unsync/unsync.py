import asyncio
import concurrent
import inspect
import threading
from functools import wraps
from threading import Thread


class unsync(object):
    executor = concurrent.futures.ThreadPoolExecutor()
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

    def __call__(self, *args, **kwargs):
        if inspect.iscoroutinefunction(self.f):
            future = self.f(*args, **kwargs)
        else:
            future = unsync.executor.submit(self.f, *args, **kwargs)
        return Unfuture(future)

    def __get__(self, instance, owner):
        return lambda *args, **kwargs: self(instance, *args, **kwargs)


class Unfuture:
    @staticmethod
    def from_value(value):
        future = Unfuture()
        future.set_result(value)
        return future

    def __init__(self, future=None):
        def callback(source, target):
            try:
                asyncio.futures._chain_future(source, target)
            except Exception as exc:
                if self.concurrent_future.set_running_or_notify_cancel():
                    self.concurrent_future.set_exception(exc)
                raise

        if asyncio.iscoroutine(future):
            future = asyncio.ensure_future(future, loop=unsync.loop)
        if isinstance(future, concurrent.futures.Future):
            self.concurrent_future = future
            self.future = asyncio.Future(loop=unsync.loop)
            self.future._loop.call_soon_threadsafe(callback, self.concurrent_future, self.future)
        else:
            self.future = future or asyncio.Future(loop=unsync.loop)
            self.concurrent_future = concurrent.futures.Future()
            self.future._loop.call_soon_threadsafe(callback, self.future, self.concurrent_future)

    def __iter__(self):
        return self.future.__iter__()

    __await__ = __iter__

    def result(self, *args, **kwargs):
        # The asyncio Future may have completed before the concurrent one
        if self.future.done():
            return self.future.result()
        # Don't allow waiting in the unsync.thread loop since it will deadlock
        if threading.current_thread() == unsync.thread and not self.concurrent_future.done():
            raise asyncio.InvalidStateError
        # Wait on the concurrent Future outside unsync.thread
        return self.concurrent_future.result(*args, **kwargs)

    def done(self):
        return self.future.done() or self.concurrent_future.done()

    def set_result(self, value):
        return self.future._loop.call_soon_threadsafe(lambda: self.future.set_result(value))

    @unsync
    async def then(self, continuation):
        await self
        result = continuation(self)
        if hasattr(result, '__await__'):
            return await result
        return result


asyncio.set_event_loop(unsync.loop)
unsync.thread = Thread(target=unsync.thread_target, args=(unsync.loop,), daemon=True)
unsync.thread.start()
