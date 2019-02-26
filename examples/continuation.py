import asyncio
import time

from unsync import unsync

# Using Unfuture.then chains asynchronous calls and returns an Unfuture that wraps both the source, and continuation

@unsync
async def initiate(request):
    await asyncio.sleep(0.1)
    return request + 1

@unsync
async def process(task):
    await asyncio.sleep(0.1)
    return task.result() * 2

start = time.time()
print(initiate(3).then(process).result())
print('Executed in {} seconds'.format(time.time() - start))
