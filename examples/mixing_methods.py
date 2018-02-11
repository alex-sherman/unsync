import time

from unsync import unsync

# All Unfutures are compatible regardless of how they were started

@unsync
def non_async_function(num):
    """A non-async function that is IO bound we want to parallelize
       This gets executed in the ThreadPoolExecutor unsync.executor"""
    time.sleep(0.1)
    return num, num + 1


def result_continuation(task):
    """A preliminary result processor we'll chain on to the original task
       This will get executed wherever the source task was executed, in this
       case one of the threads in the ThreadPoolExecutor"""
    num, res = task.result()
    return num, res * 2

@unsync
async def result_processor(tasks):
    """An async result aggregator that combines all the results
       This gets executed in unsync.loop and unsync.thread"""
    output = {}
    for task in tasks:
        num, res = await task
        output[num] = res
    return output

start = time.time()
print(result_processor([non_async_function(i).then(result_continuation) for i in range(10)]).result())
print('Executed in {} seconds'.format(time.time() - start))
