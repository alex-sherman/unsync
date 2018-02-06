import asyncio
import concurrent
from asyncio import compat
from threading import Thread


class Unfuture:
    def __init__(self, coro, loop):
        self.future = asyncio.ensure_future(coro, loop=loop)
        self.loop = loop

        future = concurrent.futures.Future()

        def callback():
            try:
                asyncio.futures._chain_future(self.future, future)
            except Exception as exc:
                if future.set_running_or_notify_cancel():
                    future.set_exception(exc)
                raise

        loop.call_soon_threadsafe(callback)
        self.con_future = future

    def __iter__(self):
        yield from self.future.__iter__()

    if compat.PY35:
        __await__ = __iter__

    def result(self):
        return self.con_future.result()

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

    def __call__(self, *args, **kwargs):
        #return asyncio.ensure_future(self.f(*args, **kwargs), loop=self.loop)
        return Unfuture(self.f(*args, **kwargs), self.loop)


unsync.thread = Thread(target=unsync.thread_target, args=(unsync.loop,), daemon=True)
unsync.thread.start()
