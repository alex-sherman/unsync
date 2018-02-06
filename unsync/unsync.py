import asyncio
from threading import Thread


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
        return asyncio.run_coroutine_threadsafe(self.f(*args, **kwargs), self.loop)


unsync.thread = Thread(target=unsync.thread_target, args=(unsync.loop,), daemon=True)
unsync.thread.start()
