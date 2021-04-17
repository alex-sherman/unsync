from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
import asyncio
import time

from unsync import unsync, Unfuture


class FutureTests(TestCase):
    @staticmethod
    def executor():
        return ThreadPoolExecutor()

    @staticmethod
    def concurrent_future(result='faff'):
        def wait():
            time.sleep(0.1)
            return result

        return Unfuture(FutureTests.executor().submit(wait))

    def test_future_reuse(self):
        calls = []

        @unsync
        async def other():
            calls.append('b')
            await asyncio.sleep(0.1)
            calls.append('c')
            return 'faff'

        @unsync
        async def long(task):
            calls.append('a')
            t = task()
            await t
            await t
            result = t.result()
            calls.append('d')
            return result

        o = other
        self.assertEqual('faff', long(o).result())
        self.assertEqual(['a', 'b', 'c', 'd'], calls)

    def test_async_continuation(self):
        @unsync
        async def continuation(result):
            await asyncio.sleep(0.1)
            return result + 'derp'

        @unsync
        async def source():
            await asyncio.sleep(0.1)
            return 'faff'

        res = source().then(continuation)
        self.assertEqual('faffderp', res.result())

    def test_sync_continuation(self):
        def continuation(result):
            return result + 'derp'

        @unsync
        async def source():
            await asyncio.sleep(0.1)
            return 'faff'

        res = source().then(continuation)
        self.assertEqual('faffderp', res.result())

    def test_chained_continuation(self):
        def cont_gen(text):
            def continuation(result):
                return result + text

            return continuation

        @unsync
        async def source():
            await asyncio.sleep(0.1)
            return 'faff'

        res = source().then(cont_gen('a')).then(cont_gen('b')).then(cont_gen('c'))
        self.assertEqual('faffabc', res.result())

    def test_from_result(self):
        future = Unfuture.from_value('faff')
        self.assertEqual('faff', future.result())

    def test_await_from_result(self):
        future = Unfuture.from_value('faff')

        @unsync
        async def wait(_future):
            return await _future

        self.assertEqual('faff', wait(future).result())

    def test_from_concurrent_future(self):
        self.concurrent_future().result(timeout=0.2)

    def test_await_from_concurrent_future(self):
        future = self.concurrent_future()

        @unsync
        async def wait(_future):
            return await _future

        self.assertEqual('faff', wait(future).result())
