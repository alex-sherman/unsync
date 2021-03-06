# unsync
Unsynchronize `asyncio` by using an ambient event loop, or executing in separate threads or processes.

# Quick Overview

Functions marked with the `@unsync` decorator will behave in one of the following ways:
* `async` functions will run in the `unsync.loop` event loop executed from `unsync.thread`
* Regular functions will execute in `unsync.thread_executor`, a `ThreadPoolExecutor`
  * Useful for IO bounded work that does not support `asyncio`
* Regular functions marked with `@unsync(cpu_bound=True)` will execute in `unsync.process_executor`, a `ProcessPoolExecutor`
  * Useful for CPU bounded work

All `@unsync` functions will return an `Unfuture` object.
This new future type combines the behavior of `asyncio.Future` and `concurrent.Future` with the following changes:
* `Unfuture.set_result` is threadsafe unlike `asyncio.Future`
* `Unfuture` instances can be awaited, even if made from `concurrent.Future`
* `Unfuture.result()` is a blocking operation *except* in `unsync.loop`/`unsync.thread` where
    it behaves like `asyncio.Future.result` and will throw an exception if the future is not done

# Examples
## Simple Sleep
A simple sleeping example with `asyncio`:
```python
async def sync_async():
    await asyncio.sleep(1)
    return 'I hate event loops'


async def main():
    future1 = asyncio.create_task(sync_async())
    future2 = asyncio.create_task(sync_async())

    await future1, future2

    print(future1.result() + future2.result())

asyncio.run(main())
# Takes 1 second to run
```

Same example with `unsync`:
```python
@unsync
async def unsync_async():
    await asyncio.sleep(1)
    return 'I like decorators'

unfuture1 = unsync_async()
unfuture2 = unsync_async()
print(unfuture1.result() + unfuture2.result())
# Takes 1 second to run
```

## Multi-threading an IO-bound function
Synchronous functions can be made to run asynchronously by executing them in a `concurrent.ThreadPoolExecutor`.
This can be easily accomplished by marking the regular function `@unsync`.
```python
@unsync
def non_async_function(seconds):
    time.sleep(seconds)
    return 'Run concurrently!'

start = time.time()
tasks = [non_async_function(0.1) for _ in range(10)]
print([task.result() for task in tasks])
print('Executed in {} seconds'.format(time.time() - start))
```
Which prints:

    ['Run concurrently!', 'Run concurrently!', ...]
    Executed in 0.10807514190673828 seconds

## Continuations
Using `Unfuture.then` chains asynchronous calls and returns an `Unfuture` that wraps both the source, and continuation.
The continuation is invoked with the source Unfuture as the first argument.
Continuations can be regular functions (which will execute synchronously), or `@unsync` functions.
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
We may want to refine the result in another function, so we define the following continuation.
```python
@unsync
async def result_continuation(task):
    await asyncio.sleep(0.1)
    num, res = task.result()
    return num, res * 2
```
We then aggregate all the results into a single dictionary in an async function.
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
    Executed in 0.22115683555603027 seconds

## Preserving typing
As far as we know it is not possible to change the return type of a method or function using a decorator.
Therefore, we need a workaround to properly use IntelliSense. You have three options in general:

1. Ignore type warnings.
2. Use a suppression statement where you reach the type warning.

    A. When defining the unsynced method by changing the return type to an `Unfuture`.
    
    B. When using the unsynced method.
    
3. Wrap the function without a decorator. Example:
    ```python 
    def function_name(x: str) -> Unfuture[str]:
        async_method = unsync(__function_name_synced)
        return async_method(x)

    def __function_name_synced(x: str) -> str:
        return x + 'a'

    future_result = function_name('b')
    self.assertEqual('ba', future_result.result())
   ```

## Custom Event Loops
In order to use custom event loops, be sure to set the event loop policy before calling any `@unsync` methods.
For example, to use `uvloop` simply:

```python
import unsync
import uvloop

@unsync
async def main():
    # Main entry-point.
    ...

uvloop.install() # Equivalent to asyncio.set_event_loop_policy(EventLoopPolicy())
main()
```