[![Supported Versions](https://img.shields.io/pypi/pyversions/leek.svg)](https://pypi.org/project/leek)
 
 [中文文档](https://github.com/abo123456789/leek)  | [English Docs](https://github.com/abo123456789/leek/blob/leek/README_EN.md)  
### 任务发布消费中间件
#### 功能描述
* 比scrapy更灵活,比celery更容易上手的分布式爬虫框架。用最少的代码,用最简单的方式,做最多的事情
* 1分钟内能熟练运用该框架爬取数据,无需学习复杂文档.轻松扩展各种中间件  
             
特色说明： 
 
     支持多中间件：
        支持reids kafka sqlite memory 四种中间件(首推redis,支持批量发布任务,分布式消费快如闪电)
        
     并发支持：
        支持process threading gevent三种并发消费模式(可混合使用)
     
     控频限流：
        精确控制1秒钟运行多少次函数
     
     任务去重：
        如果重复推送消费成功的任务,自动过滤掉该任务
     
     消费确认：
        启用消费确认,消费任务宕机手动终止情况,任务不会丢失
     
     重试次数：
        当函数运行出错，会立即重试指定的次数，达到最大次重试数后任务会进入死信队列                  
     
     任务过期机制：
        如果设定某个任务过期时间,任务超过设定过期时间还未消费,则会自动丢弃该任务
     
     死信队列任务重新消费
        进入死信队列任务支持手动重入队列重新消费
     
#### pip安装
```shell
pip install leek
```

##### 1.发布任务和消费任务
```python
from leek import TaskPublisher, TaskConsumer

for zz in range(1, 11):
    TaskPublisher(queue_name='test1').pub(a=zz, b=zz)

def print_msg_dict(a, b):
    print(f"t_demo1:{a},{b}")

TaskConsumer(queue_name='test1', consuming_function=print_msg_dict).start()
```

##### 2.发布任务和消费任务(更多参数实例)
```python
from leek import get_consumer

def f(a, b):
    print(f"a:{a},b:{b}")
    print(f.meta)

consumer = get_consumer('test2', consuming_function=f, process_num=3, ack=True, task_expires=10, batch_id='2021042401')

for i in range(1, 200):
    consumer.task_publisher.pub(a=i, b=i)

consumer.start()
```
##### 3.发布任务和消费任务(装饰器版本)
```python
from leek import task_deco

@task_deco('test3')  # 消费函数上新增任务队列装饰器
def f3(a, b):
    print(f"t_demo3,a:{a},b:{b}")

# 发布任务
for i in range(1, 51):
    f3.pub(a=i, b=i)

# 消费任务
f3.start()
```

#### 消费函数参数详解
```
get_consumer(queue_name='test11', consuming_function=f, process_num=2, threads_num=30, max_retry_times=5, qps=10, task_expires=60, batch_id='test_v1.0')
:param queue_name: 队列名称
:param consuming_function: 队列消息取出来后执行的方法
:param process_num: 启动进程数量(默认值:1)
:param threads_num: 启动线程数(默认值:8)
:param max_retry_times: 错误重试次数(默认值:3)
:param qps: 每秒限制消费任务数量(默认50)
:param middleware: 消费中间件,默认redis 支持sqlite ,kafka, memory
:param customer_type: 消费者类型 string 支持('thread','gevent') 默认thread
:param fliter_rep: 消费任务是否去重 bool True:去重 False:不去重
:filter_field: 消费任务去重的字段,当fliter_rep为True时有效
:param max_push_size : 每次批量推送任务数量 默认值50
:param ack : 是否需要确认消费 默认值True
:param task_expires : 任务过期时间 单位/秒
:param batch_id : 批次id
:param re_queue_exception : 需要重入队列的异常
```

#### [redisweb](https://github.com/abo123456789/redisweb) 通过浏览器查看任务消费情况
[![avatar](https://camo.githubusercontent.com/46204ab1c85e52dec751a715ebc08daf6fb63f0ca1dd1e3fc77ee42b68a67145/68747470733a2f2f73312e617831782e636f6d2f323032302f30372f30372f5541494846652e6a7067)](https://github.com/abo123456789/redisweb)

