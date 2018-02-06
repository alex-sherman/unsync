from unittest import TestCase
from unsync import unsync
import asyncio


class DecoratorTests(TestCase):
    def test_1(self):
        @unsync
        async def faff():
            await asyncio.sleep(0)
            return True
        self.assertTrue(faff().result())
        pass
