[中文文档](README.md)  | [English Docs](README_EN.md)  
## Redis high concurrency queue
 
#### Functional description
* A distributed crawler framework that is more flexible than scrapy and easier to use than Celery. Do the most with the least code and the simplest way
* Can skillfully use the framework to crawl data within 1 minute, without learning complex documents. Easily expand various middleware  
Feature description:
 
      Support middleware:
         Support reids kafka sqlite memory  four kinds of middleware (redis is the first choice, support batch publishing tasks, distributed consumption is lightning fast)
        
      Concurrent support:
         Support process threading gevent three concurrent consumption modes (can be mixed)
     
      Frequency control and current limit:
         Precisely control how many functions are run in 1 second
     
      Task deduplication:
         If you repeatedly push the successfully consumed task, the task will be automatically filtered out
      
      Consumption confirmation:
        When consumption confirmation is enabled, and the consumption task is stopped manually, the task will not be lost
      
      Number of retries:
         When the function fails, it will retry the specified number of times immediately, and the consumption will be confirmed when the maximum number of retries is reached
     
      Task visualization:
         You can view the current task consumption in real time through the redis web version management tool

#### version description
* Supported version: Python 3.0+

#### Pip installation
```shell
pip install redis-queue-tool
```

#### DEMO description
[All demo](https://github.com/abo123456789/redis-queue-tool/blob/master/redis_queue_tool/test_demo.py)

##### 1. Release tasks and consumer tasks (functional version)
```python
from redis_queue_tool import get_consumer
def f11(a: int = 1, b: int = 1):
     print(f"t_demo11,a:{a},b:{b}")

customer = get_consumer('test11', consuming_function=f11)

for i in range(1, 200):
     customer.publisher_queue.pub(a=i, b=i)

customer.start()
```

##### 2. Release tasks and consumer tasks (decorator version)
```python
from redis_queue_tool import task_deco

@task_deco('test0') # Added task queue decorator on consumption function
def f0(a, b):
    print(f"t_demo0,a:{a},b:{b}")

# Post task
for i in range(1, 51):
    f0.pub(i, i)

# Consumer task
f0.start()
```
##### 3. Publish consumer tasks (use extra parameters)
```python
from redis_queue_tool import task_deco

@task_deco('test1', qps=30, threads_num=30, max_retry_times=3, ack=True)
def f1(a, b):
    print(f"t_demo1,a:{a},b:{b}")

# Post task
for i in range(1, 31):
    f1.pub(i, i + 1) # or f1.publish_redispy(i,i+1)

# Consumer task
f1.start()

# DLQ message re queue
f1.publisher.dlq_re_queue()
```

##### 4. Publish consumer tasks (non-decorator version)
```python
from redis_queue_tool import RedisPublish, RedisCustomer


for zz in range(1, 501):
    param = {"a": zz, "b": zz, "c": zz}
    RedisPublish(queue_name='test2').publish_redispy(param)


def print_msg_dict(a, b, c):
    print(f"msg_dict:{a},{b},{c}")


# Consumption of multi-parameter type tasks queue_name Consumption queue name qps The number of consumption tasks per second (there is no limit by default)
RedisCustomer(queue_name='test2', consuming_function=print_msg_dict,
              qps=50).start_consuming_message()
```

##### 5. Batch submit task consumption(consumption using coroutine)

```python 
from redis_queue_tool import task_deco
from gevent import monkey
monkey.patch_all()

# #### 3. Submit tasks in batches
result = [{'a': i,'b': i,'c': i} for i in range(1, 51)]

# customer_type Consumer type (default thread), max_push_size the number of records submitted in batches each time (default value 50)
# If you use gevent, please add at the beginning of the code: from gevent import monkey monkey.patch_all()
@task_deco('test3', qps=50, customer_type='gevent', max_push_size=100) # Added task queue decorator on the consumption function
def f3(a, b, c):
    print(f"t_demo3:{a},{b},{c}")

# Post task
f3.pub_list(result)

# Consumer task
f3.start()
```

##### 6. Switch task queue middleware to sqlite (default is redis)

```python
from redis_queue_tool import task_deco, MiddlewareEum

@task_deco('test4', middleware=MiddlewareEum.SQLITE, qps=10)
def f4(a, b, c):
    print(f"t_demo4:{a},{b},{c}")

for zz in range(1, 51):
    f4.pub(zz, zz, zz)

f4.start()
```
#### Detailed explanation of consumption function parameters
```
get_consumer(queue_name='test11', consuming_function=f11, process_num=2, threads_num=30, max_retry_times=5, qps=10)
:param queue_name: queue name
:param consuming_function: The method to be executed after the queue message is taken out
:param process_num: number of started processes (default: 1)
:param threads_num: how many threads to start (default: 50)
:param max_retry_times: number of error retries (default: 3)
:param qps: limit the number of consumer tasks per second (default 0 is unlimited)
:param middleware: consumer middleware, default redis supports sqlite, kafka, memory
:param specify_threadpool: external incoming thread pool
:param customer_type: consumer type string support ('thread','gevent') default thread
:param fliter_rep: Whether to de-duplicate consumer tasks bool True: de-duplicate False: do not de-duplicate
:param max_push_size: the number of batch push tasks each time the default value is 50
:param ack: Do you need to confirm consumption? Default value is False
:param priority: queue priority int[0-4]
```

#### Reids install
[reids install](https://www.runoob.com/redis/redis-install.html)

reids docker install
```shell
docker run  -d -p 6379:6379 redis
```

redis web manage tool [redisweb](https://github.com/abo123456789/redisweb)
![avatar](https://s1.ax1x.com/2020/07/07/UAIHFe.jpg)


#### Usage scenarios and features

```shell
1. Highly concurrent distributed crawler (verified by tens of millions of online data crawling verification)

2. Distributed data cleaning (automatic deduplication of cleaning, support to continue cleaning after interruption at any time)

3. Short video processing (video download and upload, bandwidth is sufficient without waiting)

4. Asynchronous real-time online query interface (speed reaches millisecond level)

5. Other usage scenarios are being expanded

```


#### Release Notes


```java
2020-12-18  pip installation version is upgraded to 4.8.0, and the priority queue parameter is added

2020-06-11 Version 4.1.5 Added support for gevent coroutine consumption parameter customer_type='gevent'

2020-05-20 Added consumption function timeout time parameter

2020-05-10 Added sqlite middleware support

2020-04-13 The consumption function adds automatic control of the number of threads

2020-04-10 New frequency limiting parameter for consumption function

2020-01-08 Consumer function supports multiple parameter types

2019-12-06 Simplified multi-threaded consumer queue class

2019-10-14 Added consumption function error retry mechanism, retry by default 3 times

2019-10-12 Task deduplication ignores parameter order

2019-09-27 Fix the bug of submitting list task

2019-05-25 Added dynamic parameter transfer when adding tasks

2019-04-06 Added automatic deduplication function for crawling tasks

2019-03-23 ​​Added single-thread asynchronous batch submission function
```