### 任务发布消费中间件
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
        当函数运行出错，会立即重试指定的次数，达到最大次重试数后任务会进入死信队列
     
     任务可视化：
        可以通过redis web版管理工具实时查看当前任务消费情况                  
#### 版本说明
* 支持版本: python 3.0+

#### pip安装
```shell
pip install leek
```

##### 1.发布任务和消费任务
```python
from leek import get_consumer

def f(a, b):
    print(f"a:{a},b:{b}")

cunsumer = get_consumer('test12', consuming_function=f, process_num=3, ack=True, batch_id='2021042401')

for i in range(1, 200):
    cunsumer.task_publisher.pub(a=i, b=i)

cunsumer.start()
```