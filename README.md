 [中文文档](https://github.com/abo123456789/RedisQueue/blob/master/README.md)  | [English Docs](https://github.com/abo123456789/RedisQueue/blob/master/README_EN.md)  
### redis高并发队列  
#### 功能描述
* 比scrapy更灵活,比celery更容易上手的分布式爬虫框架。用最少的代码,用最简单的方式,做最多的事情
* 1分钟内能熟练运用该框架爬取数据,无需学习复杂文档.轻松扩展各种中间件  
             
特色说明： 
 
     支持中间件：
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
        当函数运行出错，会立即重试指定的次数，达到最大次重试数后就确认消费了
     
     任务可视化：
        可以通过redis web版管理工具实时查看当前任务消费情况                  
#### 版本说明
* 支持版本: python 3.0 - 3.7

#### pip安装
```shell
pip install redis-queue-tool
```

#### DEMO说明

##### 0.发布任务和消费任务(装饰器版)
```python
from redis_queue_tool import task_deco

@task_deco('test0')  # 消费函数上新增任务队列装饰器
def f0(a, b):
    print(f"t_demo0,a:{a},b:{b}")

# 发布任务
for i in range(1, 51):
    f0.pub(i, i)

# 消费任务
f0.start()
```
##### 1.发布消费任务(额外参数)
```python
from redis_queue_tool import task_deco

@task_deco('test1', qps=30, threads_num=30, max_retry_times=3, ack=True)
def f1(a, b):
    print(f"t_demo1,a:{a},b:{b}")

# 发布任务
for i in range(1, 31):
    f1.pub(i, i + 1)  # 或者 f1.publish_redispy(i,i+1)

# 消费任务
f1.start()
```

##### 2.发布消费任务(非装饰器版)
```python
from redis_queue_tool import RedisPublish, RedisCustomer


for zz in range(1, 501):
    param = {"a": zz, "b": zz, "c": zz}
    RedisPublish(queue_name='test2').publish_redispy(param)


def print_msg_dict(a, b, c):
    print(f"msg_dict:{a},{b},{c}")


# 消费多参数类型任务 queue_name消费队列名称 qps每秒消费任务数(默认没有限制)
RedisCustomer(queue_name='test2', consuming_function=print_msg_dict,
              qps=50).start_consuming_message()
```

##### 3.批量提交任务(使用协程消费)

```python
from redis_queue_tool import task_deco
from gevent import monkey
monkey.patch_all()

# #### 3.批量提交任务
result = [{'a': i, 'b': i, 'c': i} for i in range(1, 51)]

# customer_type 消费者类型(默认thread)，max_push_size每次批量提交记录数(默认值50)
# 若使用gevent请在代码开头加入：from gevent import monkey monkey.patch_all()
@task_deco('test3', qps=50, customer_type='gevent', max_push_size=100)  # 消费函数上新增任务队列装饰器
def f3(a, b, c):
    print(f"t_demo3:{a},{b},{c}")

# 发布任务
f3.pub_list(result)

# 消费任务
f3.start()
```

##### 4.切换任务队列中间件为sqlite(默认为redis)

```python
from redis_queue_tool import task_deco, MiddlewareEum

@task_deco('test4', middleware=MiddlewareEum.SQLITE, qps=10)
def f4(a, b, c):
    print(f"t_demo4:{a},{b},{c}")

for zz in range(1, 51):
    f4.pub(zz, zz, zz)

f4.start()
```

#### reids安装
[reids 普通安装](https://www.runoob.com/redis/redis-install.html)

reids docker安装
```shell
docker run  -d -p 6379:6379 redis
```

redis web版管理工具 [redisweb](https://github.com/abo123456789/redisweb)
![avatar](https://s1.ax1x.com/2020/07/07/UAIHFe.jpg)


#### 特色说明

```shell
1 . 高并发分布式爬虫(经过线上千万级数据爬取验证)

2 . 分布式数据清洗(清洗自动去重,支持任意时刻中断后继续清洗)

3 . 短视频处理(视频下载上传,带宽足够无需等待)

4 . 异步实时在线查询接口(速度达到毫秒级别)

5 . 其它使用场景扩展中

```

#### 更新说明


```java
2020-11-01 版本4.6.9 新增支持DLQ死信队列支持,当ack=True消费失败消息都会进入死信队列

2020-06-11 版本4.1.5 新增支持gevent协程消费参数 customer_type='gevent'

2020-05-20 新增消费函数超时时间参数

2020-05-10 新增sqlite中间件支持

2020-04-13 消费函数新增自动控制线程数

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
