[![Supported Versions](https://img.shields.io/pypi/pyversions/leek.svg)](https://pypi.org/project/leek)
### Task publishing and consumption middleware
#### Function description
* A distributed crawler framework that is more flexible than scrapy and easier to use than celery. Do the most things in the easiest way with the least amount of code
* You can use this framework to crawl data skillfully within 1 minute without learning complex documents. Easily expand various middleware
             
Feature Description:
 
     Supports multiple middleware:
        Supports four kinds of middleware: reids, kafka, sqlite memory (redis is the first, supports batch publishing tasks, and distributed consumption is lightning fast)
        
     Concurrency support:
        Support three concurrent consumption modes of process threading gevent (can be mixed)
     
     Frequency control and current limit:
        Precisely control how many times a function runs in 1 second
     
     Deduplication of tasks:
        If the task with successful consumption is repeatedly pushed, the task will be automatically filtered out
     
     Consumption confirmation:
        When consumption confirmation is enabled, the consumption task is manually terminated when the task is down, and the task will not be lost.
     
     number of retries:
        When the function runs with an error, it will immediately retry the specified number of times. After the maximum number of retries is reached, the task will enter the dead letter queue.
     
     Task expiration mechanism:
        If a task expiration time is set, and the task has not been consumed after the set expiration time, the task will be automatically discarded
     
     Dead letter queue task re-consumption
        Entering the dead letter queue task supports manual re-entry queue re-consumption
     
#### pip install
```shell
pip install leek
````

##### 1. Publish tasks and consume tasks
````python
from leek import TaskPublisher, TaskConsumer

for zz in range(1, 11):
    TaskPublisher(queue_name='test1').pub(a=zz, b=zz)

def print_msg_dict(a, b):
    print(f"t_demo1:{a},{b}")

TaskConsumer(queue_name='test1', consuming_function=print_msg_dict).start()
````

##### 2. Publish tasks and consume tasks (more parameter examples)
````python
from leek import get_consumer

def f(a, b):
    print(f"a:{a},b:{b}")
    print(f.meta)

consumer = get_consumer('test2', consuming_function=f, process_num=3, ack=True, task_expires=10, batch_id='2021042401')

for i in range(1, 200):
    consumer.task_publisher.pub(a=i, b=i)

consumer.start()
````
##### 3. Publish tasks and consume tasks (decorator version)
````python
from leek import task_deco

@task_deco('test3') # Add a task queue decorator to the consumer function
def f3(a, b):
    print(f"t_demo3,a:{a},b:{b}")

# publish task
for i in range(1, 51):
    f3.pub(a=i, b=i)

# consume tasks
f3.start()
````

#### Detailed explanation of consumption function parameters
````
get_consumer(queue_name='test11', consuming_function=f, process_num=2, threads_num=30, max_retry_times=5, qps=10, task_expires=60, batch_id='test_v1.0')
:param queue_name: queue name
:param consuming_function: The method to be executed after the queue message is taken out
:param process_num: Number of processes to start (default: 1)
:param threads_num: Number of threads to start (default: 8)
:param max_retry_times: number of error retries (default: 3)
:param qps: limit the number of consumption tasks per second (default 50)
:param middleware: consumption middleware, default redis supports sqlite, kafka, memory
:param customer_type: consumer type string support ('thread','gevent') default thread
:param fliter_rep: Whether the consumption task is de-duplicated bool True: de-duplication False: no de-duplication
:param max_push_size : the number of tasks to be pushed in batches. The default value is 50
:param ack : Whether to confirm the consumption default value True
:param task_expires : task expiration time unit/second
:param batch_id : batch id
:param re_queue_exception : the exception that needs to be requeued
````

#### [redisweb](https://github.com/abo123456789/redisweb) View task consumption through browser
[![avatar](https://camo.githubusercontent.com/46204ab1c85e52dec751a715ebc08daf6fb63f0ca1dd1e3fc77ee42b68a67145/68747470733a2f2f73312e617831782e636f6d2f323032302f30372f30372f5541494846652e6a7067)](https://github.com/abo123456789/redisweb)