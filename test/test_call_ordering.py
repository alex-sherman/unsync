from unittest import TestCase
import asyncio

from unsync import unsync


class CallOrderingTests(TestCase):
    def test_simple_call(self):
        @unsync
        async def faff():
            await asyncio.sleep(0.1)
            return True

        self.assertTrue(faff().result())

    def test_nested_blocking_on_result(self):
        @unsync
        async def other():
            await asyncio.sleep(0.1)
            return 'faff'

        @unsync
        async def long(task):
            return task().result()

        with self.assertRaises(asyncio.InvalidStateError):
            self.assertEqual('faff', long(other).result())

    def test_nested_unsync(self):
        @unsync
        async def long():
            @unsync
            async def other():
                await asyncio.sleep(0.1)
                return 'faff'
            return other().result()

        with self.assertRaises(asyncio.InvalidStateError):
            self.assertEqual('faff', long().result())

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
