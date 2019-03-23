
redis高并发队列
##### [介绍文档]

* 支持版本: python 3.6


### 下载安装

* 下载源码:

```shell
git clone https://github.com/abo123456789/RedisQueue.git
```

* 安装依赖:

```shell
pip install -r requirements.txt
```

* 配置config.py:

```shell
# config.py 为数据库配置文件

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
    quenen_name = 'test1'
    redis_pub = RedisPublish(queue_name=quenen_name, max_push_size=5)

    result = [str(i) for i in range(1, 101)]

    for zz in result:
        redis_pub.publish_redispy(zz)  # 多线程单条记录写入

    redis_pub.publish_redispy_list(result)  # 单线程批量写入1

    for zz in result:
        redis_pub.publish_redispy_mutil(zz)  # 单线程批量写入2


    def print_msg(msg):
        print(msg)


    # 多线程消费
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg, threads_num=100)
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
2019-03-23 新增单线程异步批量提交功能

```