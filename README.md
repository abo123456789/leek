
redis高并发队列
##### [介绍文档]

* 支持版本: python 3.0+

### 下载安装

* pip安装:
```shell
pip install redis-queue-tool
```

* 下载源码:

```shell
git clone https://github.com/abo123456789/RedisQueue.git
```

* 安装依赖:

```shell
pip install -r requirements.txt
```

* 配置redis连接:

```shell
# 配置Redis
redis_host = '127.0.0.1'
redis_password = ''
redis_port = 6379
redis_db = 0


# redis没有设置密码,默认配置''

```

* 启动:

```shell
# 如果你的依赖已经安全完成并且具备运行条件,可以直接运行RedisQueue.py
>>>python RedisQueue.py

# 如果运行成功,会自动启动添加任务和消费任务demo

```

### 运行DEMO说明

##### 1.发布消费字符串类型任务
```python
    from redis_queue_tool import RedisQueue
    from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer


    # redis连接配置
    RedisQueue.redis_host = '127.0.0.1'
    RedisQueue.redis_password = ''
    RedisQueue.redis_port = 6379
    RedisQueue.redis_db = 8

    # 初始化发布队列 queue_name发布队列名称 fliter_rep=True任务自动去重
    redis_pub = RedisPublish(queue_name='test1', fliter_rep=False)

    for zz in range(1, 501):
        redis_pub.publish_redispy_str(str(zz))  # 发布字符串任务


    def print_msg_str(msg):
        print(f"msg_str:{msg}")


    # 消费字符串任务 quenen_name消费队列名称
    RedisCustomer(quenen_name='test1', consuming_function=print_msg_str, process_num=2, threads_num=100,
                  max_retry_times=5).start_consuming_message()
```

##### 2.发布消费多参数类型任务
```python
   from redis_queue_tool import RedisQueue
   from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer


    # redis连接配置
    RedisQueue.redis_host = '127.0.0.1'
    RedisQueue.redis_password = ''
    RedisQueue.redis_port = 6379
    RedisQueue.redis_db = 8

    # 初始化发布队列 quenen_name发布队列名称 fliter_rep=True任务自动去重
    redis_pub2 = RedisPublish(queue_name='test2', fliter_rep=False)

    for zz in range(1, 501):
        redis_pub2.publish_redispy(c=str(zz), b=str(zz), a=str(zz))  # 写入字典任务 {"c":zz,"b":zz,"a":zz}


    def print_msg_dict(a, b, c):
        print(f"msg_dict:{a},{b},{c}")


    # 消费多参数类型任务 quenen_name消费队列名称 is_support_mutil_param=True 消费函数支持多参数
    RedisCustomer('test2', consuming_function=print_msg_dict, process_num=2, threads_num=100,
                  max_retry_times=5, is_support_mutil_param=True, qps=10).start_consuming_message()
```

##### 3.批量提交任务

```python
    from redis_queue_tool import RedisQueue
    from redis_queue_tool.RedisQueue import RedisPublish

    # redis连接配置
    RedisQueue.redis_host = '127.0.0.1'
    RedisQueue.redis_password = ''
    RedisQueue.redis_port = 6379
    RedisQueue.redis_db = 8

    result = [str(i) for i in range(1, 501)]
    # 批量提交任务 queue_name提交任务队列名称 max_push_size每次批量提交记录数(默认值50)
    RedisPublish(queue_name='test3', max_push_size=100).publish_redispy_list(result)

```


### 使用场景说明


```shell
1 . 高并发分布式爬虫

2 . 分布式数据清洗

3 . 其它使用场景扩展中

```

### 更新说明


```java
2020-04-10 消费函数新增限频参数

2020-01-08 消费函数支持多参数类型

2019-12-06 简化多线程消费队列类

2019-10-14 新增消费函数错误重试机制,默认重试3次

2019-10-12 任务去重忽略参数顺序

2019-09-27 修复提交列表任务BUG

2019-05-25 新增添加任务时动态传参

2019-04-06 新增爬取任务自动去重功能

2019-03-23 新增单线程异步批量提交功能
```
