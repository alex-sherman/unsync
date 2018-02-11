from unittest import TestCase

import time
from pytest import raises
from unsync import unsync
import asyncio
from unsync.unsync import Unfuture


class DecoratorTests(TestCase):

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
