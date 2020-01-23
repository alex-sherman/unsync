from unittest import TestCase
import asyncio
import time

from unsync import unsync


class ThreadedTests(TestCase):

    def test_unsync_threaded(self):
        @unsync
        def non_async_work():
            time.sleep(0.1)
            return 'faff'

        self.assertEqual('faff', non_async_work().result())

    def test_unsync_threaded_with_await(self):
        def non_async_work():
            time.sleep(0.1)
            return 'faff'

        @unsync
        async def wait(_future):
            await asyncio.sleep(0.1)
            return await _future

        future = unsync(non_async_work)()
        self.assertEqual('faff', wait(future).result())

    def test_unsync_threaded_multiple(self):
        def non_async_work():
            time.sleep(0.1)
            return 'faff'

        @unsync
        async def wait(_futures):
            return [await _future for _future in _futures]

        futures = [unsync(non_async_work)() for _ in range(20)]
        self.assertTrue(all([res == 'faff' for res in wait(futures).result()]))

    def test_unsync_threaded_decorator(self):
        @unsync
        def non_async_work():
            time.sleep(0.1)
            return 'faff'

        @unsync
        async def wait(_futures):
            return [await _future for _future in _futures]

        futures = [non_async_work() for _ in range(20)]
        self.assertTrue(all([res == 'faff' for res in wait(futures).result()]))

    def test_unsync_threaded_decorator_args(self):
        @unsync
        def non_async_work(arg, kwarg=None):
            time.sleep(0.1)
            return str(arg) + str(kwarg)

        @unsync
        async def wait(_futures):
            return [await _future for _future in _futures]

        futures = [non_async_work('fa', kwarg='ff') for _ in range(20)]
        self.assertTrue(all([res == 'faff' for res in wait(futures).result()]))
