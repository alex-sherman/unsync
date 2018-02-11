from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
import time
from pytest import raises, fixture
from unsync import unsync
import asyncio
from unsync.unsync import Unfuture


class DecoratorTests(TestCase):
    @staticmethod
    def executor():
        return ThreadPoolExecutor()

    @staticmethod
    def concurrent_future(result='faff'):
        def wait():
            time.sleep(0.1)
            return result
        return Unfuture(DecoratorTests.executor().submit(wait))

    def test_simple_call(self):
        @unsync
        async def faff():
            await asyncio.sleep(0.1)
            return True
        self.assertTrue(faff().result())

    def test_call_blocking(self):
        calls = []

        @unsync
        async def other():
            calls.append('a')
            await asyncio.sleep(0.1)
            calls.append('c')
            return 'faff'

        @unsync
        async def long(task):
            calls.append('b')
            result = await task
            calls.append('d')
            return result
        o = other()
        self.assertEqual('faff', long(o).result())
        self.assertEqual(['a', 'b', 'c', 'd'], calls)

    def test_nested_calling(self):
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
            result = await task()
            calls.append('d')
            return result
        o = other
        self.assertEqual('faff', long(o).result())
        self.assertEqual(['a', 'b', 'c', 'd'], calls)

    def test_nested_blocking_on_result(self):
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
            result = task().result()
            calls.append('d')
            return result
        o = other

        with raises(asyncio.InvalidStateError):
            self.assertEqual('faff', long(o).result())
        self.assertEqual(['a', 'b'], calls)

    def test_nested_blocking_on_result_after_await(self):
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
            result = t.result()
            calls.append('d')
            return result
        o = other
        self.assertEqual('faff', long(o).result())
        self.assertEqual(['a', 'b', 'c', 'd'], calls)

    def test_exception(self):
        class TestException(Exception):
            pass

        @unsync
        async def error():
            await asyncio.sleep(0.1)
            raise TestException

        with raises(TestException):
            error().result()

    def test_parallelism(self):
        calls = []

        @unsync
        async def sleep():
            calls.append('a')
            await asyncio.sleep(0.1)
            calls.append('b')

        results = []
        for _ in range(100):
            results.append(sleep())
        for result in results:
            result.result()
        self.assertEqual(list(sorted(calls)), calls)

    def test_future_integration(self):
        asyncio_future = asyncio.Future(loop=unsync.loop)

        @unsync
        async def wrapper(_future):
            return await _future

        result = wrapper(asyncio_future)
        with raises(asyncio.TimeoutError):
            result.result(timeout=0.1)
        self.assertFalse(result.done())
        unsync.loop.call_soon_threadsafe(lambda: asyncio_future.set_result('faff'))
        self.assertEqual('faff', result.result(timeout=0.1))

    def test_unfuture_integration(self):
        unfuture = Unfuture()

        @unsync
        async def wrapper(_future):
            result = await _future
            return result

        result = wrapper(unfuture)
        with raises(asyncio.TimeoutError):
            result.result(timeout=0.1)
        self.assertFalse(result.done())
        unfuture.set_result('faff')
        self.assertEqual('faff', result.result(timeout=0.1))

    def test_instance_methods(self):
        class Class:
            @unsync
            async def wait(self):
                await asyncio.sleep(0.1)
                return 'faff'

        self.assertEqual('faff', Class().wait().result())

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
        async def continuation(task):
            await asyncio.sleep(0.1)
            return task.result() + 'derp'

        @unsync
        async def source():
            await asyncio.sleep(0.1)
            return 'faff'
        res = source().then(continuation)
        self.assertEqual('faffderp', res.result())

    def test_sync_continuation(self):
        def continuation(task):
            return task.result() + 'derp'

        @unsync
        async def source():
            await asyncio.sleep(0.1)
            return 'faff'
        res = source().then(continuation)
        self.assertEqual('faffderp', res.result())

    def test_chained_continuation(self):
        def cont_gen(text):
            def continuation(task):
                return task.result() + text
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
