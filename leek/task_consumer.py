# -*- coding:utf-8 -*-
# @Author cc
import json
import multiprocessing
import os
import platform
import signal
import threading

from multiprocessing import Process

from py_log import get_logger
from retrying import retry

from leek import default_config, TaskPublisher
from leek.custom_gevent import CustomGeventPoolExecutor
from leek.custom_thread import CustomThreadPoolExecutor
from leek.kafka_queue import KafkaQueue
from leek.memery_queue import MemoryQueue
from leek.middleware_eum import MiddlewareEum
from leek.redis_queue import RedisQueue
from leek.sqllite_queue import SqlliteQueue

# from gevent import monkey
# monkey.patch_all()

__author__ = 'cc'

import time
import traceback
from collections import Callable

from leek.utils import str_sha256, get_now_millseconds, sort_dict

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
except ModuleNotFoundError:
    logger.warning('未读取redis_queue_tool_config.py自定义配置文件,使用默认配置文件')
except AttributeError:
    logger.warning('未读取redis_queue_tool_config.py自定义连接属性,使用默认属性')


def init_redis_config(host, password, port, db):
    default_config.redis_host = host
    default_config.redis_password = password
    default_config.redis_port = port
    default_config.redis_db = db
    logger.info('使用猴子补丁配置')


class TaskConsumer(object):
    """reids队列消费类"""

    def __init__(self, queue_name, consuming_function: Callable = None, process_num=1, threads_num=50,
                 max_retry_times=3, func_timeout=None, is_support_mutil_param=True, qps=0,
                 middleware=MiddlewareEum.REDIS,
                 specify_threadpool=None, customer_type='thread', fliter_rep=False, max_push_size=50, ack=False,
                 priority=None, task_expires=None, batch_id=None):
        """
        redis队列消费程序
        :param queue_name: 队列名称
        :param consuming_function: 队列消息取出来后执行的方法
        :param process_num: 启动进程数量
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
        :param priority : 队列优先级 int[0-4]
        :param task_expires : 任务过期时间 单位秒
        :param batch_id : 批次ID
        """
        if middleware == MiddlewareEum.SQLITE:
            self._redis_quenen = SqlliteQueue(queue_name=queue_name)
        elif middleware == MiddlewareEum.KAFKA:
            self._redis_quenen = KafkaQueue(queue_name=queue_name, host=default_config.kafka_host,
                                            port=default_config.kafka_port)
        elif middleware == MiddlewareEum.MEMORY:
            self._redis_quenen = MemoryQueue(queue_name=queue_name)
        else:
            self._redis_quenen = RedisQueue(queue_name, priority=priority, host=default_config.redis_host,
                                            port=default_config.redis_port,
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
        self.task_publisher = TaskPublisher(queue_name, fliter_rep=fliter_rep,
                                            priority=priority,
                                            middleware=MiddlewareEum.REDIS,
                                            consuming_function=consuming_function,
                                            max_retry_times=max_retry_times,
                                            task_expires=task_expires,
                                            batch_id=batch_id)

    # noinspection PyBroadException
    def _start_consuming_message_thread(self):
        current_customer_count = 0
        get_queue_begin_time = time.time()
        while True:
            try:
                time_begin = time.time()
                message = self._redis_quenen.get(block=True, timeout=20)
                get_message_cost = time.time() - time_begin
                if message:
                    if self.ack:
                        self._redis_quenen.un_ack(message)
                    if isinstance(message, list):
                        for msg in message:
                            if self.qps != 0:
                                if self.qps < 5:
                                    sleep_seconds = (1 / self.qps) * self.process_num - get_message_cost \
                                        if (1 / self.qps) * self.process_num > get_message_cost else 0
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
                                sleep_seconds = (1 / self.qps) * self.process_num - get_message_cost \
                                    if (1 / self.qps) * self.process_num > get_message_cost else 0
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
                    time.sleep(0.3)
            except KeyboardInterrupt:
                heartbeat_check_queue_name = f"_heartbeat_check_common:{self._redis_quenen.queue_name}"
                if self._redis_quenen.getdb().setnx(heartbeat_check_queue_name, 1):
                    self._redis_quenen.getdb().expire(heartbeat_check_queue_name, 10)
                    self._heartbeat_check_common(is_break=True)
                self._clear_process()
            except Exception:
                logger.error(traceback.format_exc())
                time.sleep(0.5)

    def start(self):
        self.start_consuming_message()

    def start_consuming_message(self):
        if self.ack:
            threading.Thread(target=self._heartbeat_check).start()
        cpu_count = multiprocessing.cpu_count()
        if (platform.system() == 'Darwin' or platform.system() == 'Linux') and self.process_num > 1:
            for pn in range(0, min(self.process_num, cpu_count)):
                logger.info(
                    f'start consuming message  process:{pn + 1},{self.customer_type}_num:'
                    f'{self.threads_num},system:{platform.system()}')
                p = Process(target=self._start_consuming_message_thread)
                p.start()
        else:
            logger.info(
                f'start consuming message {self.customer_type}, {self.customer_type}_num:{self.threads_num}'
                f',system:{platform.system()}')
            threading.Thread(target=self._start_consuming_message_thread).start()

    # noinspection PyBroadException
    def _consuming_exception_retry(self, message):
        try:
            @retry(stop_max_attempt_number=self.max_retry_times)
            def consuming_exception_retry(message2):
                if type(message2) == dict:
                    task_body = message2['body']
                    self._consuming_function(**task_body)
                else:
                    dit_message = json.loads(message2)
                    if type(dit_message) == dict:
                        task_body = dit_message['body']
                        self._consuming_function(**task_body)
                    else:
                        self._consuming_function(dit_message)

            consuming_exception_retry(message)
            if self.ack:
                self._redis_quenen.ack(message)
        except Exception:
            logger.error(traceback.format_exc())
            if self.ack:
                if self.middleware == MiddlewareEum.REDIS:
                    dlq_message = json.dumps(message) if isinstance(message, dict) else message
                    self._redis_quenen.getdb().lpush(f'dlq:{self._redis_quenen.queue_name}', dlq_message)
            logger.warning('consuming_exception_retry faliture')
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
                    self._heartbeat_check_common()
                except KeyboardInterrupt:
                    logger.info('redis队列心跳检查程序退出')
                except Exception as ex:
                    logger.error(ex)
                    time.sleep(10)
                else:
                    time.sleep(10)

    def _heartbeat_check_common(self, is_break=False):
        logger.info('_heartbeat_check_common')
        if self._redis_quenen.getdb().hexists(self._redis_quenen.heartbeat_key,
                                              self._redis_quenen.heartbeat_field) is False:
            self._redis_quenen.getdb().hset(self._redis_quenen.heartbeat_key,
                                            self._redis_quenen.heartbeat_field, get_now_millseconds())
        hash_all_data = self._redis_quenen.getdb().hgetall(self._redis_quenen.heartbeat_key)
        if hash_all_data:
            for key in hash_all_data:
                heart_field = key.decode()
                heart_value = int(hash_all_data[key].decode())
                if is_break or get_now_millseconds() - heart_value > 10500:
                    queue_name = heart_field.split(':heartbeat_')[0]
                    un_ack_sets_name = f"{heart_field}:unack_message"
                    dlq_queue_name = f"dlq:{queue_name}"
                    for msg in self._redis_quenen.getdb().sscan_iter(un_ack_sets_name):
                        self._redis_quenen.getdb().lpush(dlq_queue_name, msg.decode())
                        self._redis_quenen.getdb().srem(un_ack_sets_name, msg)
                    self._redis_quenen.getdb().hdel(self._redis_quenen.heartbeat_key, heart_field)
                else:
                    self._redis_quenen.getdb().hset(self._redis_quenen.heartbeat_key,
                                                    heart_field,
                                                    get_now_millseconds())

    # noinspection PyMethodMayBeStatic
    def _clear_process(self):
        pid = os.getpid()
        logger.warning(f'{pid} process is KeyboardInterrupt and kill')
        os.kill(pid, signal.SIGTERM)


def get_consumer(queue_name,
                 consuming_function: Callable = None,
                 priority=None,
                 process_num=1,
                 threads_num=50,
                 max_retry_times=3,
                 qps=0,
                 middleware=MiddlewareEum.REDIS,
                 specify_threadpool=None,
                 customer_type='thread',
                 fliter_rep=False,
                 task_expires=None,
                 batch_id=None,
                 ack=False, *consumer_args,
                 **consumer_init_kwargs) -> TaskConsumer:
    consumer = TaskConsumer(queue_name, process_num=process_num, threads_num=threads_num, middleware=middleware,
                            qps=qps,
                            consuming_function=consuming_function, specify_threadpool=specify_threadpool,
                            customer_type=customer_type, task_expires=task_expires, batch_id=batch_id,
                            fliter_rep=fliter_rep, ack=ack, max_retry_times=max_retry_times, priority=priority,
                            *consumer_args, **consumer_init_kwargs)
    return consumer


if __name__ == '__main__':
    def f(a, b):
        print(f"a:{a},b:{b}")


    cunsumer = get_consumer('test12', consuming_function=f, process_num=3, ack=True, batch_id='2021042401')

    for i in range(1, 200):
        cunsumer.task_publisher.pub(a=i, b=i)

    cunsumer.start()