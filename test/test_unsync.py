from functools import wraps
from unittest import TestCase

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

        with self.assertRaises(TestException):
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
        with self.assertRaises(asyncio.TimeoutError):
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
        with self.assertRaises(asyncio.TimeoutError):
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

    def test_passing_arguments(self):
        @unsync(faff='faff')
        def cpu_bound():
            return 'faff'

        self.assertEqual('faff', cpu_bound().result())

    def test_nested_decorator_retains_wrapped_function_attributes(self):
        def on(attr_value):
            @wraps(attr_value)
            def wrapper(f):
                f.attr_name = attr_value
                return f

            return wrapper

        @on("faff")
        @unsync
        def some_func(): pass

        assert some_func.attr_name == "faff"
        assert some_func.__name__ == "some_func"
