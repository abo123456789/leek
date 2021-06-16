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

from leek.utils import str_sha256, get_now_millseconds, get_now_seconds

logger = get_logger(__name__, formatter_template=5)

# 配置连接信息
try:
    import leek_config
    default_config.redis_host = leek_config.redis_host
    default_config.redis_password = leek_config.redis_password
    default_config.redis_port = leek_config.redis_port
    default_config.redis_db = leek_config.redis_db
    default_config.redis_ssl = leek_config.redis_ssl
    logger.info('读取到leek_config.py redis配置')
except ModuleNotFoundError:
    logger.warning('未读取到leek_config.py redis配置.')
except AttributeError:
    logger.warning('未读取到leek_config.py redis配置。')

try:
    import leek_config
    default_config.kafka_host = leek_config.kafka_host
    default_config.kafka_port = leek_config.kafka_port
    default_config.kafka_username = leek_config.kafka_username
    default_config.kafka_password = leek_config.kafka_password
    logger.info('读取到leek_config.py kafka配置,使用自定义配置')
except ModuleNotFoundError:
    logger.warning('未读取到leek_config.py kafka配置.')
except AttributeError:
    logger.warning('未读取到leek_config.py kafka配置。')


class TaskConsumer(object):
    """reids队列消费类"""

    def __init__(self, queue_name, consuming_function: Callable = None, process_num=1, threads_num=8,
                 max_retry_times=3, func_timeout=None, is_support_mutil_param=True, qps=50,
                 middleware=MiddlewareEum.REDIS,
                 specify_threadpool=None, customer_type='thread', fliter_rep=False, max_push_size=50, ack=True,
                 priority=None, task_expires=None, batch_id=None, re_queue_exception: tuple = None):
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
        :param ack : 是否需要确认消费 默认值True
        :param priority : 队列优先级 int[0-4]
        :param task_expires : 任务过期时间 单位秒
        :param batch_id : 批次ID
        :re_queue_exception : 需要重入队列的异常
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
                                            password=default_config.redis_password,
                                            ssl=default_config.redis_ssl)
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
        self.re_queue_exception = re_queue_exception
        self.task_publisher = TaskPublisher(queue_name, fliter_rep=fliter_rep,
                                            priority=priority,
                                            middleware=MiddlewareEum.REDIS,
                                            consuming_function=consuming_function,
                                            max_retry_times=max_retry_times,
                                            task_expires=task_expires + get_now_seconds() if task_expires else None,
                                            batch_id=batch_id)

    def start(self):
        if self.ack:
            threading.Thread(target=self._heartbeat_check).start()
        cpu_count = multiprocessing.cpu_count()
        if (platform.system() == 'Darwin' or platform.system() == 'Linux') and self.process_num >= 1:
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

    # noinspection PyBroadException
    def _consuming_exception_retry(self, message):
        try:
            @retry(stop_max_attempt_number=self.max_retry_times, wait_random_min=700, wait_random_max=1700)
            def consuming_exception_retry(message2):
                task_dict = message2 if isinstance(message2, dict) else json.loads(message2)
                task_body = task_dict['body']
                self._consuming_function.meta = task_dict['meta']
                task_expires_now = task_dict['meta'].get('task_expires')
                if task_expires_now and task_expires_now < get_now_seconds():
                    logger.warning(f"task has expired:{task_dict}")
                    return
                if self.re_queue_exception:
                    try:
                        if task_dict['meta']['msg_type'] == 'params':
                            self._consuming_function(**task_body)
                        else:
                            self._consuming_function(task_body)
                    except self.re_queue_exception as e:
                        logger.error(e)
                        retry_left_times = task_dict['meta']['max_retry_times']
                        task_dict['meta']['max_retry_times'] = retry_left_times - 1
                        # logger.debug(task_dict)
                        if task_dict['meta']['max_retry_times'] > 0:
                            self._redis_quenen.getdb().lpush(self.queue_name, json.dumps(task_dict))
                        else:
                            # self._redis_quenen.un_ack(task_dict)
                            dlq_message = json.dumps(task_dict) if isinstance(task_dict, dict) else task_dict
                            self._redis_quenen.getdb().lpush(f'dlq:{self._redis_quenen.queue_name}', dlq_message)

                else:
                    if task_dict['meta']['msg_type'] == 'params':
                        self._consuming_function(**task_body)
                    else:
                        self._consuming_function(task_body)

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
                    time.sleep(60)
                else:
                    time.sleep(60)

    def _heartbeat_check_common(self, is_break=False):
        logger.info('_heartbeat_check_common {}'.format(self.queue_name))
        redis_db = self._redis_quenen.getdb()
        redis_heartbeat_key = self._redis_quenen.heartbeat_key
        if is_break:
            un_ack_sets_name = f"unack_message:{self.queue_name}"
            dlq_queue_name = f"dlq:{self.queue_name}"
            for msg in redis_db.sscan_iter(un_ack_sets_name):
                redis_db.lpush(dlq_queue_name, msg.decode())
                redis_db.srem(un_ack_sets_name, msg)
        else:
            redis_db.hset(redis_heartbeat_key,
                          self._redis_quenen.heartbeat_field, get_now_millseconds())

    # noinspection PyMethodMayBeStaticx
    def _clear_process(self):
        try:
            self._redis_quenen.getdb().delete(self._redis_quenen.heartbeat_key)
        except:
            pass
        pid = os.getpid()
        logger.warning(f'{pid} process is KeyboardInterrupt and kill')
        os.kill(pid, signal.SIGTERM)


def get_consumer(queue_name,
                 consuming_function: Callable = None,
                 priority=None,
                 process_num=1,
                 threads_num=8,
                 max_retry_times=3,
                 qps=50,
                 middleware=MiddlewareEum.REDIS,
                 specify_threadpool=None,
                 customer_type='thread',
                 fliter_rep=False,
                 task_expires=None,
                 batch_id=None,
                 re_queue_exception: tuple = None,
                 ack=True, *consumer_args,
                 **consumer_init_kwargs) -> TaskConsumer:
    consumer = TaskConsumer(queue_name, process_num=process_num, threads_num=threads_num, middleware=middleware,
                            qps=qps,
                            consuming_function=consuming_function, specify_threadpool=specify_threadpool,
                            customer_type=customer_type, task_expires=task_expires, batch_id=batch_id,
                            fliter_rep=fliter_rep, ack=ack, max_retry_times=max_retry_times, priority=priority,
                            re_queue_exception=re_queue_exception,
                            *consumer_args, **consumer_init_kwargs)
    return consumer


if __name__ == '__main__':
    def f(a, b):
        print(f"a:{a},b:{b}")
        # c = 1/0
        # print(c)
        time.sleep(1)
        print(f.meta)


    consumer = get_consumer('test12', middleware='kafka', consuming_function=f, ack=True, process_num=1,
                            batch_id='2021042401-003', max_retry_times=3,
                            re_queue_exception=(ZeroDivisionError,))

    # for i in range(1, 10):
    #     consumer.task_publisher.pub(a=i, b=i)

    dict_list = [dict(a=i, b=i) for i in range(1, 11)]
    consumer.task_publisher.pub_list(dict_list)

    consumer.start()
