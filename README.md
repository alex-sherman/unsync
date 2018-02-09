# unsync
Unsynchronize `asyncio` by using an ambient event loop in a separate thread.

# Rules for unsync
1. Mark all `async` functions with `@unsync`
2. All `Futures` must either be `Unfutures` which includes
    the result of an `@unsync` `async` function call,
    or an `asyncio.Future` with the loop set to `unsync.loop`
3. All `async` functions will execute in `unsync.thread`
4. `asyncio.Future` instances are not thread safe, so `set_value`
    must not be called on them from anywhere but `unsync.thread`.
    `Unfuture` instances `set_value` functions are thread safe.


# Examples
## Simple Sleep
A simple sleeping example with `asyncio`:
```python
import asyncio

async def sync_async():
    await asyncio.sleep(0.1)
    return 'I hate event loops'

annoying_event_loop = asyncio.get_event_loop()
future = asyncio.ensure_future(sync_async(), loop=annoying_event_loop)
annoying_event_loop.run_until_complete(future)
print(future.result())
```

Same example with `unsync`:
```python
from unsync import unsync

@unsync
async def unsync_async():
    await asyncio.sleep(0.1)
    return 'I like decorators'

print(unsync_async().result())
```