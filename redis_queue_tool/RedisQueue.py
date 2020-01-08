#-*- coding:utf-8 -*-
import json
import multiprocessing
import platform
import threading

from multiprocessing import Process
from retrying import retry

__author__ = 'cc'

from functools import wraps

import redis
import time
import queue
import traceback
from loguru import logger
from collections import Callable
from concurrent.futures import ThreadPoolExecutor
from tomorrow3 import threads as tomorrow_threads

# redis配置连接信息
redis_host = '127.0.0.1'
redis_password = ''
redis_port = 6379
redis_db = 0

redis_conn_instance = {}


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, name, fliter_rep=False ,namespace='', **redis_kwargs):
        """
        
        :param name: 队列名称
        :param fliter_rep: 是否开始重复任务过滤
        :param namespace: 队列名前缀
        :param redis_kwargs: redis连接动态参数
        """
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        if 'redis_conn' in redis_conn_instance:
            # print('****已经初始化过redis队列连接****')
            self.__db = redis_conn_instance.get('redis_conn')
        else:
            # print('****新初始化发布队列redis连接****')
            self.__db = redis.Redis(**redis_kwargs)
            redis_conn_instance['redis_conn'] = self.__db
        if namespace:
            self.key = '%s:%s' % (namespace, name)
        else:
            self.key = name
        self.fliter_rep = fliter_rep
        if fliter_rep:
            self.key_sets = self.key+':sets'

    def getdb(self):
        return self.__db

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def isempty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        if self.fliter_rep:
            if self.__db.sismember(self.key_sets, item) is False:
                self.__db.lpush(self.key, item)
                self.__db.sadd(self.key_sets, item)
        else:
            self.__db.lpush(self.key, item)

    def clear(self):
        """delete the queue."""
        self.__db.delete(self.key)
        if self.key_sets:
            self.__db.delete(self.key_sets)

    def get(self, block=False, timeout=None):
        """Remove and return an item from the queue.
        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.brpop(self.key, timeout=timeout)
        else:
            item = self.__db.rpop(self.key)
        if item:
            item = item.decode('utf-8')
        return item


class RedisCustomer(object):
    """reids队列消费类"""

    def __init__(self, queue_name, consuming_function: Callable = None,process_num=1,threads_num=50,max_retry_times=3,is_support_mutil_param=False):
        """
        redis队列消费程序
        :param queue_name: 队列名称
        :param consuming_function: 队列消息取出来后执行的方法
        :param threads_num: 启动多少个队列线程
        :param max_retry_times: 错误重试次数
        :param is_support_mutil_param: 消费函数是否支持多个参数,默认False
        """
        self.redis_quenen = RedisQueue(queue_name, host=redis_host, port=redis_port, db=redis_db,
                                       password=redis_password)
        self._consuming_function = consuming_function
        self.process_num = process_num
        self.threads_num = threads_num
        self.threadpool = BoundedThreadPoolExecutor(threads_num)
        self.max_retry_times = max_retry_times
        self.is_support_mutil_param = is_support_mutil_param

    def _start_consuming_message_thread(self):
        logger.info(f'start consuming message mutil_thread, threads_num:{self.threads_num}')
        while True:
            try:
                message = self.redis_quenen.get()
                if message:
                    if self.is_support_mutil_param:
                       message = json.loads(message)
                       if type(message)!=dict:
                          raise Exception('请发布【字典】类型消息,当前消息是【字符串】类型')
                    self.threadpool.submit(self._consuming_exception_retry, message)
                else:
                    time.sleep(0.1)
            except:
                s = traceback.format_exc()
                logger.error(s)
                time.sleep(0.1)

    def start_consuming_message(self):
        cpu_count = multiprocessing.cpu_count()
        logger.info(f'start consuming message  mutil_process,process_num:{min(self.process_num,cpu_count)},system:{platform.system()}')
        if platform.system()=='Darwin' or platform.system()=='Linux':
            for i in range(0,min(self.process_num,cpu_count)):
                Process(target=self._start_consuming_message_thread).start()
        else:
            threading.Thread(target=self._start_consuming_message_thread).start()

    def _consuming_exception_retry(self,message):
        @retry(stop_max_attempt_number=self.max_retry_times)
        def consuming_exception_retry(message):
            if type(message)==dict:
                self._consuming_function(**message)
            else:
                self._consuming_function(message)
        consuming_exception_retry(message)


class RedisPublish(object):
    """redis入队列类"""

    def __init__(self, queue_name, fliter_rep=False, max_push_size=1):
        """
        初始化消息发布队列
        :param queue_name: 队列名称(不包含命名空间)
        :param fliter_rep: 队列任务是否去重 True:去重  False:不去重
        :param threads_num: 并发线程数
        :param max_push_size: 
        """
        self.redis_quenen = RedisQueue(queue_name,fliter_rep=fliter_rep, host=redis_host, port=redis_port, db=redis_db,
                                       password=redis_password)
        # self.threads_num = threads_num
        self.max_push_size = max_push_size
        self.local_quenen = queue.Queue(maxsize=max_push_size + 1)
        self.pipe = self.redis_quenen.getdb().pipeline()

    @tomorrow_threads(50)
    def publish_redispy(self,*args,**kwargs):
        """
        将多参数写入消息队列
        :param kwargs: 待写入参数 (a=3,b=4)
        :return: None
        """
        # logger.info(f"args:{args},kwargs:{kwargs}")
        dict_msg = None
        if kwargs:
            dict_msg = dict(sorted(kwargs.items(), key=lambda d: d[0]))
        elif args:
            dict_msg = args[0]
        else:
            logger.warning('参数非法')
        if dict_msg:
            self.redis_quenen.put(json.dumps(dict_msg))

    @tomorrow_threads(50)
    def publish_redispy_str(self, msg:str):
        """
        将字符串写入消息队列
        :param msg: 待写入消息字符串
        :return: None
        """
        self.redis_quenen.put(msg)

    def publish_redispy_list(self, msgs: list, publish_size=50):
        """
        批量写入redis队列
        :param msgs: 待写入字符串列表
        :param publish_size: 每次批量提交数量
        :return: 
        """
        pipe = self.redis_quenen.getdb().pipeline()
        for id in msgs:
            pipe.lpush(self.redis_quenen.key, id)
            if len(pipe) == publish_size:
                pipe.execute()
                logger.info(str(publish_size).center(20,'*') + 'commit')
        if len(pipe)>0:
            pipe.execute()

    def publish_redispy_mutil(self, msg: str):
        """
        单笔写入,批量提交
        :param msg: 待写入字符串
        :return: None
        """
        self.local_quenen.put(msg)
        # logger.info(f'self.local_quenen.size:{self.local_quenen.qsize()}')
        if self.local_quenen.qsize() >= self.max_push_size:
            try:
                while self.local_quenen.qsize() > 0:
                    self.pipe.lpush(self.redis_quenen.key, self.local_quenen.get_nowait())
            except:
                logger.error(traceback.format_exc())
            self.pipe.execute()
            logger.info('commit'.center(16, '*'))

    def clear_quenen(self):
        """
        清空当前队列
        :return: 
        """
        self.redis_quenen.clear()


class BoundedThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        super().__init__(max_workers, thread_name_prefix)
        self._work_queue = queue.Queue(max_workers * 1)

    def submit(self, fn, *args, **kwargs):
        fn_deco = self._deco(fn)
        super().submit(fn_deco, *args, **kwargs)

    def _deco(self,f):
        @wraps(f)
        def __deco(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(e)
        return __deco


if __name__ == '__main__':
    redis_host = '127.0.0.1'
    redis_password = ''
    redis_port = 6379
    redis_db = 8

    quenen_name = 'test1'
    # 初始化发布队列 fliter_rep=True任务自动去重
    redis_pub = RedisPublish(queue_name=quenen_name,fliter_rep=False, max_push_size=50)

    result = [str(i) for i in range(1, 501)]

    def print_msg_str(msg):
        print(f"msg_str:{msg}")

    for zz in result:
        redis_pub.publish_redispy_str(zz)  # 写入字符串任务

    # 多线程消费字符串任务
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg_str, process_num=5, threads_num=100,
                                   max_retry_times=5)
    redis_customer.start_consuming_message()

    for zz in result:
        redis_pub.publish_redispy(c=zz, b=zz, a=zz)  # 写入字典任务 {"c":zz,"b":zz,"a":zz}

    # redis_pub.publish_redispy_list(result)  # 批量提交任务1

    def print_msg_dict(a,b,c):
        print(f"msg_dict:{a},{b},{c}")

    # 多线程消费字典任务
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg_dict,process_num=5,threads_num=100,
                                   max_retry_times=5,is_support_mutil_param=True)
    redis_customer.start_consuming_message()



