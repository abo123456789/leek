#-*- coding:utf-8 -*-
from Redis_Bloomfilter import BloomFilter

__author__ = 'cc'

from functools import wraps

import redis
import time
import queue
import traceback
from collections import Callable
from concurrent.futures import ThreadPoolExecutor, Future
from concurrent.futures.thread import _WorkItem
from tomorrow3 import threads as tomorrow_threads

from app import config


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, name, fliter_rep=True ,namespace='', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        if namespace:
            self.key = '%s:%s' % (namespace, name)
        else:
            self.key = name
        self.fliter_rep = fliter_rep
        if fliter_rep:
            self.key_sets = self.key+':sets'
            self.bloom_fliter = BloomFilter(blockNum=1, key=self.key_sets,**redis_kwargs)

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
            if self.bloom_fliter.isContains(item) is False:
               self.__db.lpush(self.key, item)
               self.bloom_fliter.insert(item)
        else:
            self.__db.lpush(self.key, item)

    def clear(self):
        """delete the queue."""
        self.__db.delete(self.key)

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

    def __init__(self, queue_name, consuming_function: Callable = None, threads_num=50):
        """
        redis队列消费程序
        :param queue_name: 队列名称
        :param consuming_function: 队列消息取出来后执行的方法
        :param threads_num: 启动多少个队列线程
        """
        self.redis_quenen = RedisQueue(queue_name, host=config.redis_host, port=config.redis_port, db=config.db,
                                       password=config.redis_password)
        self.consuming_function = consuming_function
        self.threads_num = threads_num
        self.threadpool = BoundedThreadPoolExecutor(threads_num)

    def start_consuming_message(self):
        print('*' * 50)
        while True:
            try:
                message = self.redis_quenen.get()
                if message:
                    self.threadpool.submit(self.consuming_function, message)
                else:
                    time.sleep(0.1)
            except:
                s = traceback.format_exc()
                print(s)

    @staticmethod
    def test_custom():
        def _print_(msg):
            print(msg)

        redis_customer = RedisCustomer('test', consuming_function=_print_)
        redis_customer._start_consuming_message()


class RedisPublish(object):
    """redis入队列类"""

    def __init__(self, queue_name, max_push_size=1):
        """

        :param queue_name: 队列名称(不包含命名空间)
        :param threads_num: 并发线程数
        :param max_push_size: 
        """
        self.redis_quenen = RedisQueue(queue_name, host=config.redis_host, port=config.redis_port, db=config.db,
                                       password=config.redis_password)
        # self.threads_num = threads_num
        self.max_push_size = max_push_size
        self.local_quenen = queue.Queue(maxsize=max_push_size + 1)
        self.pipe = self.redis_quenen.getdb().pipeline()

    @tomorrow_threads(50)
    def publish_redispy(self, msg: str):
        """
        单个写入消息队列
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
        left_size = len(msgs) % publish_size
        list_len = len(msgs)
        for id in msgs:
            pipe.lpush(self.redis_quenen.key, id)
            if len(pipe) == publish_size:
                pipe.execute()
                print(f'*' * 10 + str(publish_size) + '*' * 10 + 'commit')
            else:
                print(left_size, list_len)
                if left_size == list_len and left_size != 0:
                    pipe.execute()
                    print(f'*' * 10 + str(left_size) + '*' * 10 + 'commit')
            list_len = list_len - 1

    def publish_redispy_mutil(self, msg: str):
        """
        单笔写入,批量提交
        :param msg: 待写入字符串
        :return: None
        """
        self.local_quenen.put(msg)
        print(f'self.local_quenen.size:{self.local_quenen.qsize()}')
        if self.local_quenen.qsize() >= self.max_push_size:
            try:
                while self.local_quenen.qsize() > 0:
                    self.pipe.lpush(self.redis_quenen.key, self.local_quenen.get_nowait())
            except:
                traceback.print_exc()
            self.pipe.execute()
            print('commit'.center(16, '*'))

    def clear_quenen(self):
        """
        清空当前队列
        :return: 
        """
        self.redis_quenen.clear()


class BoundedThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers=None, thread_name_prefix=''):
        super().__init__(max_workers, thread_name_prefix)
        self._work_queue = queue.Queue(max_workers * 2)

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            f = Future()
            fn_deco = _deco(fn)
            w = _WorkItem(f, fn_deco, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


def _deco(f):
    @wraps(f)
    def __deco(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(e)

    return __deco


if __name__ == '__main__':
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
