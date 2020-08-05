# -*- coding:utf-8 -*-
# @Author cc
import inspect
import json
import multiprocessing
import platform
import threading
from functools import update_wrapper

from multiprocessing import Process

from py_log import get_logger
from retrying import retry

from redis_queue_tool import default_config
from redis_queue_tool.custom_gevent import CustomGeventPoolExecutor
from redis_queue_tool.custom_thread import CustomThreadPoolExecutor
from redis_queue_tool.kafka_queue import KafkaQueue
from redis_queue_tool.memery_queue import MemoryQueue
from redis_queue_tool.middleware_eum import MiddlewareEum
from redis_queue_tool.redis_queue import RedisQueue
from redis_queue_tool.sqllite_queue import SqlliteQueue

# from gevent import monkey
# monkey.patch_all()

__author__ = 'cc'

import time
import queue
import traceback
from collections import Callable
from tomorrow3 import threads as tomorrow_threads

from redis_queue_tool.utils import str_sha256, get_now_millseconds, get_day_formate

logger = get_logger(__name__, formatter_template=5)

# 配置连接信息
try:
    import redis_queue_tool_config

    default_config.redis_host = redis_queue_tool_config.redis_host
    default_config.redis_password = redis_queue_tool_config.redis_password
    default_config.redis_port = redis_queue_tool_config.redis_port
    default_config.redis_db = redis_queue_tool_config.redis_db
    default_config.kafka_host = redis_queue_tool_config.kafka_host
    default_config.kafka_port = redis_queue_tool_config.kafka_port
    default_config.kafka_username = redis_queue_tool_config.kafka_port
    default_config.kafka_password = redis_queue_tool_config.kafka_password
    logger.info('读取到redis_queue_tool_config.py配置,使用自定义配置')
except:
    logger.warning('未读取redis_queue_tool_config.py自定义配置,使用默认配置')


def init_redis_config(host, password, port, db):
    default_config.redis_host = host
    default_config.redis_password = password
    default_config.redis_port = port
    default_config.redis_db = db
    logger.info('使用猴子补丁配置')


class RedisCustomer(object):
    """reids队列消费类"""

    def __init__(self, queue_name, consuming_function: Callable = None, process_num=1, threads_num=50,
                 max_retry_times=3, func_timeout=None, is_support_mutil_param=True, qps=0,
                 middleware=MiddlewareEum.REDIS,
                 specify_threadpool=None, customer_type='thread', fliter_rep=False, max_push_size=50, ack=False):
        """
        redis队列消费程序
        :param queue_name: 队列名称
        :param consuming_function: 队列消息取出来后执行的方法
        :param threads_num: 启动多少个线程(档customer_type=gevent时为协程数量)
        :param max_retry_times: 错误重试次数
        :param func_timeout: 函数超时时间(秒)
        :param is_support_mutil_param: 消费函数是否支持多个参数,默认True
        :param qps: 每秒限制消费任务数量,默认0不限
        :param middleware: 消费中间件,默认redis 支持sqlite ,kafka
        :param specify_threadpool: 外部传入线程池
        :param customer_type: 消费者类型 string 支持('thread','gevent') 默认thread
        :param fliter_rep: 消费任务是否去重 bool True:去重 False:不去重
        :param max_push_size : 每次批量推送任务数量 默认值50
        :param ack : 是否需要确认消费 默认值False
        """
        if middleware == MiddlewareEum.SQLITE:
            self._redis_quenen = SqlliteQueue(queue_name=queue_name)
        elif middleware == MiddlewareEum.KAFKA:
            self._redis_quenen = KafkaQueue(queue_name=queue_name, host=default_config.kafka_host,
                                            port=default_config.kafka_port)
        elif middleware == MiddlewareEum.MEMORY:
            self._redis_quenen = MemoryQueue(queue_name=queue_name)
        else:
            self._redis_quenen = RedisQueue(queue_name, host=default_config.redis_host, port=default_config.redis_port,
                                            db=default_config.redis_db,
                                            password=default_config.redis_password)
        self._consuming_function = consuming_function
        self.queue_name = queue_name
        self.process_num = process_num
        self.threads_num = threads_num
        self.customer_type = customer_type
        if self.customer_type == 'gevent':
            self._threadpool = CustomGeventPoolExecutor(threads_num)
        else:
            self._threadpool = specify_threadpool if specify_threadpool else CustomThreadPoolExecutor(threads_num)
        self.max_retry_times = max_retry_times
        self.func_timeout = func_timeout
        self.is_support_mutil_param = is_support_mutil_param
        self.qps = qps
        self.fliter_rep = fliter_rep
        self.max_push_size = max_push_size
        self.ack = ack
        self.middleware = middleware

    def _start_consuming_message_thread(self):
        current_customer_count = 0
        get_queue_begin_time = time.time()
        while True:
            try:
                time_begin = time.time()
                message = self._redis_quenen.get()
                get_message_cost = time.time() - time_begin
                if message:
                    if self.ack:
                        self._redis_quenen.un_ack(message)
                    if isinstance(message, list):
                        for msg in message:
                            if self.qps != 0:
                                if self.qps < 5:
                                    sleep_seconds = (1 / self.qps) * self.process_num - get_message_cost if (
                                                                                                                    1 / self.qps) * self.process_num > get_message_cost else 0
                                    time.sleep(sleep_seconds)
                                else:
                                    current_customer_count = current_customer_count + 1
                                    if current_customer_count == int(self.qps / self.process_num):
                                        sleep_time = 1 - (time.time() - get_queue_begin_time)
                                        time.sleep(sleep_time if sleep_time > 0 else 0)
                                        current_customer_count = 0
                                        get_queue_begin_time = time.time()
                            self._threadpool.submit(self._consuming_exception_retry, msg)
                    else:
                        if self.qps != 0:
                            if self.qps < 5:
                                sleep_seconds = (1 / self.qps) * self.process_num - get_message_cost if (
                                                                                                                1 / self.qps) * self.process_num > get_message_cost else 0
                                time.sleep(sleep_seconds)
                            else:
                                current_customer_count = current_customer_count + 1
                                if current_customer_count == int(self.qps / self.process_num):
                                    sleep_time = 1 - (time.time() - get_queue_begin_time)
                                    time.sleep(sleep_time if sleep_time > 0 else 0)
                                    current_customer_count = 0
                                    get_queue_begin_time = time.time()

                        self._threadpool.submit(self._consuming_exception_retry, message)
                else:
                    time.sleep(0.5)
            except:
                logger.error(traceback.format_exc())
                time.sleep(0.5)

    def start(self):
        self.start_consuming_message()

    def start_consuming_message(self):
        if self.ack:
            threading.Thread(target=self._heartbeat_check).start()
        cpu_count = multiprocessing.cpu_count()
        if (platform.system() == 'Darwin' or platform.system() == 'Linux') and self.process_num > 1:
            for i in range(0, min(self.process_num, cpu_count)):
                logger.info(
                    f'start consuming message  process:{i + 1},{self.customer_type}_num:{self.threads_num},system:{platform.system()}')
                Process(target=self._start_consuming_message_thread).start()
        else:
            logger.info(
                f'start consuming message {self.customer_type}, {self.customer_type}_num:{self.threads_num},system:{platform.system()}')
            threading.Thread(target=self._start_consuming_message_thread).start()

    def _consuming_exception_retry(self, message):
        try:
            @retry(stop_max_attempt_number=self.max_retry_times)
            def consuming_exception_retry(message):
                if type(message) == dict:
                    self._consuming_function(**message)
                else:
                    dit_message = json.loads(message)
                    if type(dit_message) == dict:
                        self._consuming_function(**dit_message)
                    else:
                        self._consuming_function(dit_message)

            consuming_exception_retry(message)
            if self.ack:
                self._redis_quenen.ack(message)
        except:
            logger.error(traceback.format_exc())
        else:
            if self.fliter_rep:
                if self.middleware == MiddlewareEum.REDIS:
                    hash_value = str_sha256(json.dumps(message) if isinstance(message, dict) else message)
                    self._redis_quenen.add_customer_task(hash_value)

    def _heartbeat_check(self):
        """
        心跳检查用程序
        """
        if self.middleware == MiddlewareEum.REDIS:
            logger.info('启动redis心跳检查程序')
            while True:
                try:
                    if self._redis_quenen.getdb().hexists(self._redis_quenen.heartbeat_key,
                                                          self._redis_quenen.heartbeat_field) is False:
                        self._redis_quenen.getdb().hset(self._redis_quenen.heartbeat_key,
                                                        self._redis_quenen.heartbeat_field, get_now_millseconds())
                    hash_all_data = self._redis_quenen.getdb().hgetall(self._redis_quenen.heartbeat_key)
                    if hash_all_data:
                        for key in hash_all_data:
                            heart_field = key.decode()
                            heart_value = int(hash_all_data[key].decode())
                            if get_now_millseconds() - heart_value > 10500:
                                queue_name = heart_field.split(':heartbeat_')[0]
                                un_ack_sets_name = f"{heart_field}:unack_message"
                                for i in self._redis_quenen.getdb().sscan_iter(un_ack_sets_name):
                                    self._redis_quenen.getdb().lpush(queue_name, i.decode())
                                    self._redis_quenen.getdb().srem(un_ack_sets_name, i)
                                self._redis_quenen.getdb().hdel(self._redis_quenen.heartbeat_key, heart_field)
                            else:
                                self._redis_quenen.getdb().hset(self._redis_quenen.heartbeat_key,
                                                                heart_field,
                                                                get_now_millseconds())
                except Exception as ex:
                    logger.error(ex)
                    time.sleep(10)
                else:
                    time.sleep(10)


class RedisPublish(object):
    """redis入队列类"""

    def __init__(self, queue_name, fliter_rep=False, max_push_size=50, middleware=MiddlewareEum.REDIS,
                 consuming_function: Callable = None):
        """
        初始化消息发布队列
        :param queue_name: 队列名称(不包含命名空间)
        :param fliter_rep: 队列任务是否去重 True:去重  False:不去重
        :param max_push_size: 使用批量提交时,每次批量提交数量
        :param middleware: 中间件,默认redis 支持sqlite,kafka
        :param consuming_function: 消费函数名称
        """
        if middleware == MiddlewareEum.SQLITE:
            self._redis_quenen = SqlliteQueue(queue_name=queue_name)
        elif middleware == MiddlewareEum.KAFKA:
            self._redis_quenen = KafkaQueue(queue_name=queue_name, host=default_config.kafka_host,
                                            port=default_config.kafka_port)
        elif middleware == MiddlewareEum.MEMORY:
            self._redis_quenen = MemoryQueue(queue_name=queue_name)
        else:
            self._redis_quenen = RedisQueue(queue_name, host=default_config.redis_host,
                                            port=default_config.redis_port,
                                            db=default_config.redis_db,
                                            password=default_config.redis_password)
        self.redis_quenen = self._redis_quenen
        self.queue_name = queue_name
        self.max_push_size = max_push_size
        self._local_quenen = None
        self._pipe = None
        self.middleware = middleware
        self.consuming_function = consuming_function
        self.fliter_rep = fliter_rep

    @tomorrow_threads(50)
    def publish_redispy(self, *args, **kwargs):
        """
        将多参数写入消息队列
        :param kwargs: 待写入参数 (a=3,b=4)
        :return: None
        """
        # logger.info(f"args:{args},kwargs:{kwargs}")
        dict_msg = None
        if self.consuming_function:
            keys = inspect.getargspec(self.consuming_function).args[0:]
            if kwargs:
                dict_msg = dict(sorted(kwargs.items(), key=lambda d: d[0]))
            if args:
                param = dict() if dict_msg is None else dict_msg
                try:
                    for i in range(0, len(args)):
                        param[keys[i]] = args[i]
                    dict_msg = param
                except:
                    raise Exception('发布任务和消费函数参数不一致,请仔细核对')
            dict_msg = dict(sorted(dict_msg.items(), key=lambda d: d[0]))
        else:
            if kwargs:
                dict_msg = dict(sorted(kwargs.items(), key=lambda d: d[0]))
            elif args:
                dict_msg = args[0]
        if self.fliter_rep:
            hash_value = str_sha256(json.dumps(dict_msg) if isinstance(dict_msg, dict) else dict_msg)
            if dict_msg and self._redis_quenen.check_has_customer(hash_value) is False:
                self._redis_quenen.put(json.dumps(dict_msg))
            else:
                logger.warning(f'{dict_msg} is repeat task!!')
        else:
            if dict_msg:
                self._redis_quenen.put(json.dumps(dict_msg))

    pub = publish_redispy
    publish_redispy_dict = publish_redispy

    @tomorrow_threads(50)
    def publish_redispy_str(self, msg: str):
        """
        将字符串写入消息队列
        :param msg: 待写入消息字符串
        :return: None
        """
        self._redis_quenen.put(msg)

    def publish_redispy_list(self, msgs: list):
        """
        批量写入redis队列
        :param msgs: 待写入列表数据
        :return: 
        """
        if self.middleware == MiddlewareEum.REDIS:
            pipe = self._redis_quenen.getdb().pipeline()
            for id in msgs:
                pipe.lpush(self._redis_quenen.queue_name, json.dumps(id))
                if len(pipe) == self.max_push_size:
                    pipe.execute()
                    logger.info(str(self.max_push_size).center(20, '*') + 'commit')
            if len(pipe) > 0:
                pipe.execute()
        else:
            raise Exception('sqlite 不支持批量提交,请使用单个提交方法')

    pub_list = publish_redispy_list

    def publish_redispy_mutil(self, msg: str):
        """
        单笔写入,批量提交
        :param msg: 待写入字符串
        :return: None
        """
        if self._local_quenen is None:
            self._local_quenen = queue.Queue(maxsize=self.max_push_size + 1)
        if self._pipe is None:
            self._pipe = self._redis_quenen.getdb().pipeline()
        self._local_quenen.put(msg)
        if self._local_quenen.qsize() >= self.max_push_size:
            try:
                while self._local_quenen.qsize() > 0:
                    self._pipe.lpush(self._redis_quenen.key, self._local_quenen.get_nowait())
            except:
                logger.error(traceback.format_exc())
            self._pipe.execute()
            logger.info('commit'.center(16, '*'))

    def clear_quenen(self):
        """
        清空当前队列
        :return: 
        """
        self._redis_quenen.clear()

    def qsize(self):
        """
        获取当前队列任务数量
        :return: int 队列中任务数量
        """
        return self._redis_quenen.qsize()


def task_deco(queue_name, *consumer_args, **consumer_init_kwargs):
    """
    support by ydf
    装饰器方式添加任务，如果有人过于喜欢装饰器方式，例如celery 装饰器方式的任务注册，觉得黑科技，那就可以使用这个装饰器。此种方式不利于ide代码自动补全不推荐。
    :param queue_name:
    :param consumer_init_kwargs:
    :return:

    使用方式例如：

    @task_deco('queue_test_f01', qps=0.2，)
    def f(a, b):
        print(a + b)

    f(5, 6)  # 可以直接调用

    for i in range(10, 20):
        f.pub(a=i, b=i * 2)

    f.consume()

    """

    def _deco(func):
        cs = RedisCustomer(queue_name, consuming_function=func, *consumer_args, **consumer_init_kwargs)
        if 'consuming_function' in consumer_init_kwargs:
            consumer_init_kwargs.pop('consuming_function')
        func.consumer = cs
        # 下面这些连等主要是由于元编程造成的不能再ide下智能补全，参数太长很难手动拼写出来
        func.start_consuming_message = func.consume = func.start = cs.start_consuming_message

        publisher = RedisPublish(queue_name=queue_name, consuming_function=cs._consuming_function,
                                 fliter_rep=cs.fliter_rep, max_push_size=cs.max_push_size, middleware=cs.middleware)
        func.publisher = publisher
        func.pub = func.publish = func.publish_redispy = publisher.publish_redispy
        func.pub_list = func.publish_list = publisher.publish_redispy_list
        func.pub_str = func.publish_redispy_str = publisher.publish_redispy_str

        def __deco(*args, **kwargs):
            return func(*args, **kwargs)

        return update_wrapper(__deco, func)

    return _deco


if __name__ == '__main__':
    # #装饰器使用方式
    @task_deco('test1')  # 消费函数上新增任务队列装饰器
    def f(a, b):
        print(f"a:{a},b:{b}")


    # 发布任务
    for i in range(1, 51):
        f.pub(a=1, b=1)

    # 消费任务
    f.start()

    # #非装饰器版使用demo
    for zz in range(1, 51):
        RedisPublish(queue_name='test2').pub(a=zz, b=zz, c=zz)


    def f2(a, b, c):
        print(f"f2:{a},{b},{c}")


    # 消费多参数类型任务 queue_name消费队列名称 qps每秒消费任务数(默认没有限制)
    RedisCustomer(queue_name='test2', consuming_function=f2,
                  qps=50).start()
