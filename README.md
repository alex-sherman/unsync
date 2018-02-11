# unsync
Unsynchronize `asyncio` by using an ambient event loop in a separate thread.

# Rules for unsync
1. Mark all async functions with `@unsync`. May also mark regular functions to execute in a separate thread.
    * All `@unsync` functions, async or not, return an `Unfuture`
2. All `Futures` must be `Unfutures` which includes the result of an `@unsync` function call,
    or wrapping `Unfuture(asyncio.Future)` or `Unfuture(concurrent.Future)`.
    `Unfuture` combines the behavior of `asyncio.Future` and `concurrent.Future`:
    * `Unfuture.set_value` is threadsafe unlike `asyncio.Future`
    * `Unfuture` instances can be awaited, even if made from `concurrent.Future`
    * `Unfuture.result()` is a blocking operation *except* in `unsync.loop`/`unsync.thread` where
    it behaves like `asyncio.Future.result` and will throw an exception if the future is not done.
3. All `@unsync` async functions will execute in `unsync.thread`.
    All `@unsync` regular function will execute in `unsync.executor`.
4. `unsync` is only useful for IO-bound workloads, it will offer
    no speedup for CPU-bound workloads.


# Examples
## Simple Sleep
A simple sleeping example with `asyncio`:
```python
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
@unsync
async def unsync_async():
    await asyncio.sleep(0.1)
    return 'I like decorators'

print(unsync_async().result())
```

## Threading a synchronous function
Synchronous functions can be made to run asynchronously by executing them in a `concurrent.ThreadPoolExecutor`.
This can be easily accomplished by marking the regular function `@unsync`.
```python
@unsync
def non_async_function(seconds):
    time.sleep(seconds)
    return 'Run in parallel!'

start = time.time()
tasks = [non_async_function(0.1) for _ in range(10)]
print([task.result() for task in tasks])
print('Executed in {} seconds'.format(time.time() - start))
```

## Continuations
Using Unfuture.then chains asynchronous calls and returns an Unfuture that wraps both the source, and continuation.
The continuation is invoked with the source Unfuture as the first argument.
```python
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
```
Which prints:

    8
    Executed in 0.20314741134643555 seconds

## Mixing methods

We'll start by converting a regular synchronous function into a threaded `Unfuture` which will begin our request.
```python
@unsync
def non_async_function(num):
    time.sleep(0.1)
    return num, num + 1
```
We may want to refine the result in another function, so we define the following continuation
```python
def result_continuation(task):
    num, res = task.result()
    return num, res * 2
```
We then aggregate all the results into a single dictionary in an async function
```python
@unsync
async def result_processor(tasks):
    output = {}
    for task in tasks:
        num, res = await task
        output[num] = res
    return output
```
Executing the full chain of `non_async_function`&rightarrow;`result_continuation`&rightarrow;`result_processor` would look like:
```python
start = time.time()
print(result_processor([non_async_function(i).then(result_continuation) for i in range(10)]).result())
print('Executed in {} seconds'.format(time.time() - start))
```

Which prints:

    {0: 2, 1: 4, 2: 6, 3: 8, 4: 10, 5: 12, 6: 14, 7: 16, 8: 18, 9: 20}
    Executed in 0.11106109619140625 seconds