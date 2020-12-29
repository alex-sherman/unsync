import time

from unsync import unsync


def cpu_bound_function(operations):
    for i in range(int(operations)):
        pass
    return 'Run in parallel!'

# Could also be applied as a decorator above
unsync_cpu_bound_function = unsync(cpu_bound=True)(cpu_bound_function)

if __name__ == "__main__":
    start = time.time()
    print([cpu_bound_function(5e7) for _ in range(10)])
    print('Non-unsync executed in {} seconds'.format(time.time() - start))

    start = time.time()
    tasks = [unsync_cpu_bound_function(5e7) for _ in range(10)]
    print([task.result() for task in tasks])
    print('unsync executed in {} seconds'.format(time.time() - start))