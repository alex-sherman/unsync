from unittest import TestCase
from unsync import unsync
import asyncio


class DecoratorTests(TestCase):
    def test_1(self):
        @unsync
        async def faff():
            await asyncio.sleep(0.01)
            return True
        self.assertTrue(faff().result())

    def test_call_blocking(self):
        calls = []

        @unsync
        async def other():
            calls.append('a')
            await asyncio.sleep(0.01)
            calls.append('c')
            return True

        @unsync
        async def long(task):
            calls.append('b')
            await task
            calls.append('d')
            return True
        o = other()
        long(o).result()
        self.assertEqual(['a', 'b', 'c', 'd'], calls)
