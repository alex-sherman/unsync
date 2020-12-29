from functools import wraps
from unittest import TestCase
import asyncio
import concurrent
import time

from unsync import unsync
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

    def test_apply_to_function(self):
        async def sleep():
            await asyncio.sleep(0.1)
            return "derp"
        unsync_sleep = unsync(sleep)

        self.assertEqual(unsync_sleep().result(), "derp")

    def test_apply_to_built_in(self):
        unsync_sleep = unsync(time.sleep)

        unsync_sleep(0.1).result()

    def test_future_integration(self):
        asyncio_future = asyncio.Future(loop=unsync.loop)

        @unsync
        async def wrapper(_future):
            return await _future

        result = wrapper(asyncio_future)
        with self.assertRaises(concurrent.futures.TimeoutError):
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
        with self.assertRaises(concurrent.futures.TimeoutError):
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

    def test_implementation_without_decorator(self):
        """
        This implementation is useful to preserve type hints without an ignore statement.
        """
        def function_name(x: str) -> Unfuture[str]:
            async_method = unsync(__function_name_synced)
            return async_method(x)

        def __function_name_synced(x: str) -> str:
            return x + 'a'

        future_result = function_name('b')
        self.assertEqual('ba', future_result.result())


def set_attr(attr_value):
    """
    Sample decorator for testing nested unsync decorators.
    """

    @wraps(attr_value)
    def wrapper(f):
        f.attr = attr_value
        return f

    return wrapper


class NestedDecoratorTests(TestCase):
    def test_nested_decorator_retains_wrapped_function_attributes(self):
        @unsync
        @set_attr("faff")
        async def wrapped_func(): pass

        assert wrapped_func.__name__ == "wrapped_func"
        assert wrapped_func.attr == "faff"

    def test_nested_decorator_retains_wrapped_class_method_attributes(self):
        class Class:

            @unsync
            @set_attr("faff")
            async def wrapped_func(self): pass

        instance = Class()
        assert instance.wrapped_func.__name__ == "wrapped_func"
        assert instance.wrapped_func.attr == "faff"
