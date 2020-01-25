import time

from unsync import unsync


# Convert synchronous functions into Unfutures to be executed in `unsync.executor`

@unsync
def non_async_function(seconds):
    time.sleep(seconds)
    return 'Run in parallel!'


start = time.time()
tasks = [non_async_function(0.1) for _ in range(10)]
print([task.result() for task in tasks])
print('Executed in {} seconds'.format(time.time() - start))

# Use the decorator on existing functions

unsync_sleep = unsync(time.sleep)

start = time.time()
tasks = [unsync_sleep(0.1) for _ in range(10)]
print([task.result() for task in tasks])
print('Executed in {} seconds'.format(time.time() - start))
