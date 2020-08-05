# -*- coding: utf-8 -*-
# @Time    : 2020/7/17 19:30
# @Author  : CC
# @Desc    : t_queue.py
import json
import time


def t_demo0():
    from redis_queue_tool import task_deco

    @task_deco('test0', fliter_rep=True)  # 消费函数上新增任务队列装饰器
    def f0(a, b):
        print(f"t_demo0,a:{a},b:{b}")

    # 发布任务
    for i in range(1, 51):
        f0.pub(i, i + 1)

    # 消费任务
    f0.start()


def t_demo1():
    from redis_queue_tool import task_deco

    @task_deco('test1', qps=30, threads_num=30, max_retry_times=3, ack=True)  # 消费函数上新增任务队列装饰器
    def f1(a, b):
        time.sleep(5)
        print(f"t_demo1,a:{a},b:{b}")

    # 发布任务
    for i in range(1, 31):
        f1.pub(i, i + 1)  # 或者 f1.publish_redispy(i,i+1)

    # 消费任务
    f1.start()


def t_demo2():
    from redis_queue_tool import RedisPublish, RedisCustomer

    for zz in range(1, 51):
        # 写入字典任务 {"a":zz,"b":zz,"c":zz}
        param = {"a": zz, "b": zz, "c": zz}
        RedisPublish(queue_name='test2').publish_redispy(param)

    def print_msg_dict(a, b, c):
        print(f"t_demo2:{a},{b},{c}")

    # 消费多参数类型任务 queue_name消费队列名称 qps每秒消费任务数(默认没有限制)
    RedisCustomer(queue_name='test2', consuming_function=print_msg_dict,
                  qps=50, fliter_rep=True).start_consuming_message()


def t_demo3():
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


def t_demo4():
    from redis_queue_tool import task_deco

    @task_deco('test4', middleware='sqlite')
    def f4(a, b, c):
        print(f"t_demo4:{a},{b},{c}")

    for zz in range(1, 51):
        f4.pub(zz, zz, zz)

    f4.start()


def t_demo5():
    from redis_queue_tool import task_deco, MiddlewareEum

    @task_deco('test5', middleware=MiddlewareEum.KAFKA, fliter_rep=True)
    def f5(a, b, c):
        print(f"t_demo5:{a},{b},{c}")

    for zz in range(1, 51):
        f5.pub(zz, zz, zz)

    f5.start()


def t_demo6():
    from redis_queue_tool import task_deco, MiddlewareEum

    @task_deco('test6', middleware=MiddlewareEum.MEMORY)
    def f6(a, b, c):
        print(f"t_demo6:{a},{b},{c}")

    for zz in range(1, 51):
        f6.pub(zz, zz, zz)

    f6.start()


def t_demo7():
    from redis_queue_tool import task_deco

    @task_deco('test7')
    def f7(a):
        print(f"t_demo7:{a}")

    list_result = []
    for zz in range(1, 51):
        list_result.append(json.dumps({"a": zz, "b": zz, "c": zz}))
        list_result.append(str(zz))
        f7.pub(str(zz+100))
    f7.pub_list(list_result)

    f7.start()


if __name__ == '__main__':
    pass
    # t_demo0()
    # t_demo1()
    # t_demo2()
    # t_demo3()
    # t_demo4()
    # t_demo5()
    # t_demo6()
    t_demo7()
