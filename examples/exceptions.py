import asyncio

from unsync import unsync


# Exceptions are thrown when results are observed

@unsync
async def throws_exception():
    await asyncio.sleep(0.1)
    raise NotImplementedError


# No exception is thrown here
task = throws_exception()

# The exception is emitted when result is observed
try:
    task.result()
except NotImplementedError:
    print("Delayed result() exception!")


# The same applies to async functions awaiting methods
@unsync
async def calls_throws_exception():
    # No exception is thrown here
    task = throws_exception()
    # The exception is emitted when task is awaited
    try:
        await task
    except NotImplementedError:
        print("Delayed awaited exception!")


calls_throws_exception().result()
