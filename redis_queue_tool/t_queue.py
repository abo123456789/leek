# -*- coding: utf-8 -*-
# @Time    : 2020/7/17 19:30
# @Author  : CC
# @Desc    : t_queue.py
from redis_queue_tool import task_deco


def t_demo1():
    @task_deco('test1', qps=10, threads_num=10, max_retry_times=3)  # 消费函数上新增任务队列装饰器
    def f1(a, b):
        print(f"a:{a},b:{b}")

    # 发布任务
    for i in range(1, 51):
        f1.pub(i, i + 1)  # 或者 f1.publish_redispy(i,i+1)

    # 消费任务
    f1.start()


def t_demo2():
    from redis_queue_tool import RedisPublish, RedisCustomer

    for zz in range(1, 51):
        # 写入字典任务 {"a":zz,"b":zz,"c":zz}
        param = {"a": zz, "b": zz, "c": zz}
        RedisPublish(queue_name='test2', fliter_rep=True).publish_redispy(param)

    def print_msg_dict(a, b, c):
        print(f"msg_dict:{a},{b},{c}")

    # 消费多参数类型任务 queue_name消费队列名称 qps每秒消费任务数(默认没有限制)
    RedisCustomer(queue_name='test2', consuming_function=print_msg_dict,
                  qps=50, fliter_rep=True).start_consuming_message()


def t_demo3():
    from redis_queue_tool import RedisPublish, RedisCustomer
    from gevent import monkey
    monkey.patch_all()

    # #### 3.批量提交任务
    result = [{'a': i, 'b': i, 'c': i} for i in range(1, 51)]
    # 批量提交任务 queue_name提交任务队列名称 max_push_size每次批量提交记录数(默认值50)
    RedisPublish(queue_name='test3', max_push_size=100).publish_redispy_list(result)

    def print_msg_dict1(a, b, c):
        print(f"msg_dict1:{a},{b},{c}")

    # 消费者类型 string 支持('thread','gevent') 默认thread，若使用gevent请在代码开头加入：from gevent import monkey monkey.patch_all()
    RedisCustomer(queue_name='test3', consuming_function=print_msg_dict1, customer_type='gevent',
                  qps=50).start_consuming_message()


def t_demo4():
    from redis_queue_tool import RedisPublish, RedisCustomer

    for zz in range(1, 51):
        RedisPublish(queue_name='test4', middleware='sqlite', fliter_rep=True).publish_redispy(a=zz, b=zz, c=zz)

    def print_msg_dict2(a, b, c):
        print(f"msg_dict:{a},{b},{c}")

    RedisCustomer(queue_name='test4', consuming_function=print_msg_dict2, middleware='sqlite',
                  qps=50, fliter_rep=True).start_consuming_message()


def t_demo5():
    from redis_queue_tool import task_deco

    @task_deco('test5', fliter_rep=True)  # 消费函数上新增任务队列装饰器
    def f(a, b):
        print(f"a:{a},b:{b}")
        # raise Exception('测试异常输出' * 5)

    # 发布任务
    for i in range(1, 51):
        f.publish_redispy(a=i, b=i)  # 或者 f.pub(a=i, b=i)

    # 消费任务
    f.start_consuming_message()  # 或者 f.start()


if __name__ == '__main__':
    pass
    # t_demo1()
    # t_demo2()
    # t_demo3()
    # t_demo4()
    t_demo5()
