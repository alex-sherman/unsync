from unittest import TestCase
import asyncio

from unsync import unsync


class EventLoopTestPolicy(asyncio.DefaultEventLoopPolicy):
    def new_event_loop(self):
        loop = super().new_event_loop()
        loop.derp = "faff"
        return loop

asyncio.set_event_loop_policy(EventLoopTestPolicy())


class CustomEventTest(TestCase):
    def test_custom_event_loop(self):
        @unsync
        async def method():
            return True

        self.assertTrue(method().result())
        self.assertEqual(unsync.loop.derp, "faff")
