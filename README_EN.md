
redis High Concurrent Queues
 #####[ Introduction Document]

 * Support version: python 3.0

 ### download installation

 * pip installation:
```shell
 pip install redis-queue-tool
```

 * Download source code:

```shell
 git clone https://github.com/abo123456789/RedisQueue.git
```

 ###DEMO Notes

 #####1. Publish the consumption string type task
```python
 from redis_queue_tool.RedisQueue import RedisPublish,RedisCustomer,init_redis_config

 # redis Connection Configuration
 init_redis_config (host ='127.0.0.1', password=', port=6379, db=8)

 for zz in range(1,501)：
 # publish string task queue_name publish queue name fliter_rep=True task automatically deid (default False)
 RedisPublish (test1',fliter_rep=False). publish_redispy_str (zz)


 def print_msg_str (msg):
  print (f "msg_str :{ msg }")


 # consumption string task queue_name consumption queue name process_num number of processes (default 1) threads_num number of threads (default 50) maximum number of automatic retry errors (default 3)
 RedisCustomer (queue_name =' test1',consuming_function=print_msg_str,process_num=2, threads_num=100,
 max_retry_times=5, is_support_mutil_parammax_retry_times=False). start_consuming_message()
```

 #####2. Publish consumption multiparameter type tasks
```python
 from redis_queue_tool.RedisQueue import RedisPublish,RedisCustomer,init_redis_config

 # redis Connection Configuration
 init_redis_config (host ='127.0.0.1', password=', port=6379, db=8)


 for zz in range(1,501)：
   # Write dictionary task {a "：zz," b "：zz," c "：zz}"
 param ={ a "：zz," b "：zz," c "：zz}"
RedisPublish (test2'). publish_redispy (param)


 def print_msg_dict (a, b, c):
 print (f "msg_dict :{ a },{ b },{ c }")


 # Number of consumption tasks per second (no limit by default) qps consumption multiparameter task queue_name consumption queue name
 RedisCustomer =' test2',consuming_function=print_msg_dict, of queue_name
 qps=50). start_consuming_message()
```

 #####3. Bulk task consumption

```python
 from redis_queue_tool.RedisQueue import RedisPublish,RedisCustomer,init_redis_config
 from gevent import monkey
 monkey.patch_all()

 # redis Connection Configuration
 init_redis_config (host ='127.0.0.1', password=', port=6379, db=8)

 #####3. Bulk submission tasks
  result =[ a'：i,' b'：i,' c'：i}for i in range(1,501)]]
 # Batch commit task queue_name commit task queue name max_push_size number of batch commit records per time (default value 50)
 RedisPublish (queue_name =' test3',max_push_size=100). publish_redispy_list (result)
 def print_msg_dict1(a, b, c):
 print (f "msg_dict1:{ a },{ b },{ c }")
 # Consumer Type string Support (' thread','gevent') Default thread, If you use it, add from gevent import monkey monkey.patch_all() at the beginning of the code:
 RedisCustomer =' test3',consuming_function=print_msg_dict1,customer_type=' gevent',.
 qps=50). start_consuming_message()
```

 #####4. Switching task queue middleware to sqlite (default redis)

```python
  from redis_queue_tool.RedisQueue import RedisPublish,RedisCustomer

 for zz in range(1,101)：
 RedisPublish (queue_name =' test4',middleware='sqlite'). publish_redispy (a =zz,b=zz,c=zz)

 def print_msg_dict2(a, b, c):
 print (f "msg_dict :{ a },{ b },{ c }")

 RedisCustomer =' test4',consuming_function=print_msg_dict2,middleware='sqlite',.
 qps=50). start_consuming_message()

```


 ### use scenarios and features
######[1 minute to be proficient in using the framework to crawl data without learning complex documents. Easy extension of middleware]

 ```shell
 1. High Concurrency Distributed Crawler (Verified by Online Data Crawling)

 2. Distributed Data Cleaning (Automatic Deweighting of Cleaning, Support for Continuous Cleaning after Any Break)

 3. short video processing (video download upload, bandwidth enough without waiting)

 4. asynchronous real-time online query interface (up to millisecond speed)

 5. other usage scenario extensions

```

 ### update note


```java
 New support gevent co-process consumption parameter customer_type=' gevent' for version 4.1.5 2020-06-11

 Time-out Time-out Parameters for New Consumption Function 2020-05-20

 2020-05-10 New sqlite middleware support

 Number of new automatic control lines in consumption function 2020-04-13

 2020-04-10 Consumption Function New Limit Parameters

 2020-01-08 Consumption Function Support Multiparameter Type

 2019-12-06 Simplified Multithreaded Consumer Queues

 2019-10-14 new consumption function error retry mechanism, default retry 3 times

 The 2019-10-12 task ignores the order of parameters

 2019-09-27 Repair Submission List Task BUG

 Dynamic parameters for new add-on tasks 2019-05-25

 2019-04-06 New Crawling Task Auto Removing Function

 2019-03-23 New single-thread asynchronous batch submission feature
```