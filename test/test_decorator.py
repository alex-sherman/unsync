from unittest import TestCase
from pytest import raises
from unsync import unsync
import asyncio

from unsync.unsync import Unfuture


class DecoratorTests(TestCase):
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

        with raises(TestException) as r:
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
        self.assertEqual('PENDING', result.state)
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
        self.assertEqual('PENDING', result.state)
        unfuture.set_result('faff')
        self.assertEqual('faff', result.result(timeout=0.1))
