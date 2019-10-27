
redis高并发队列
##### [介绍文档]

* 支持版本: python 3.6+

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


```python
    from redis_queue_tool import RedisQueue
    from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer
    

    # redis连接配置
    RedisQueue.redis_host = '127.0.0.1'
    RedisQueue.redis_password = ''
    RedisQueue.redis_port = 6379
    RedisQueue.redis_db = 0
    
    quenen_name = 'test1'
    # 初始化发布队列 fliter_rep=True任务自动去重
    redis_pub = RedisPublish(queue_name=quenen_name, fliter_rep=False)
    
    result = [str(i) for i in range(1, 101)]
    
    for zz in result:
        redis_pub.publish_redispy(c=zz, b=zz, a=zz)  # 写入字典任务 {"c":zz,"b":zz,"a":zz}

    for zz in result:
        redis_pub.publish_redispy_str(zz)  # 写入字符串任务

    redis_pub.publish_redispy_list(result)  # 批量提交任务1

    for zz in result:
        redis_pub.publish_redispy_mutil(zz)  # 批量提交任务2
        
    def print_msg(msg):
        print(msg)


    # 多线程消费
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg, threads_num=100,max_retry_times=5)
    print(redis_customer.threads_num)
    redis_customer.start_consuming_message()

```


### 使用场景说明


```shell
1 . 高并发分布式爬虫

2 . 分布式数据清洗

3 . 其它使用场景扩展中

```

### 更新说明


```java
2019-10-14 新增消费函数错误重试机制,默认重试3次

2019-10-12 任务去重忽略参数顺序

2019-09-27 修复提交列表任务BUG

2019-05-25 新增添加任务时动态传参

2019-04-06 新增爬取任务自动去重功能

2019-03-23 新增单线程异步批量提交功能
```
