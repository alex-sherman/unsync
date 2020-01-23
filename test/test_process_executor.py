from unittest import TestCase
import time

from unsync import unsync


@unsync(cpu_bound=True)
def cpu_bound(duration):
    start = time.time()
    faff = 0
    while time.time() - start < duration:
        faff += 1
    return 'faff'


class ProcessTests(TestCase):
    def test_raw_cpu_bound(self):
        cpu_bound(0.01).result()

    def test_cpu_bound(self):
        @unsync
        async def aggregator(tasks):
            return [await task for task in tasks]

        start = time.time()
        tasks = [cpu_bound(0.01) for _ in range(100)]
        self.assertTrue(all([result == 'faff' for result in aggregator(tasks).result()]))
        print(time.time() - start)

        start = time.time()
        tasks = [cpu_bound(0.01) for _ in range(100)]
        self.assertTrue(all([result == 'faff' for result in aggregator(tasks).result()]))
        print(time.time() - start)
