#-*- coding:utf-8 -*-
__author__ = 'cc'

import config
import redis
import time
import queue
import traceback
from collections import Callable
from concurrent.futures import ThreadPoolExecutor
from tomorrow3 import threads as tomorrow_threads


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, name, namespace='', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        if namespace:
            self.key = '%s:%s' % (namespace, name)
        else:
            self.key = name

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
        :param threads_num: 启动多少个队列消费线程
        """
        if config.redis_password:
            self.redis_quenen = RedisQueue(queue_name, host=config.redis_host, port=config.redis_port, db=config.redis_db,password=config.redis_password)
        else:
            self.redis_quenen = RedisQueue(queue_name, host=config.redis_host, port=config.redis_port,db=config.redis_db)
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

    def __init__(self, queue_name, threads_num=50, max_push_size=1):
        """
        
        :param queue_name: 队列名称(不包含命名空间)
        :param threads_num: 并发线程数
        :param max_push_size: 
        """

        if config.redis_password:
            self.redis_quenen = RedisQueue(queue_name, host=config.redis_host, port=config.redis_port, db=config.redis_db,password=config.redis_password)
        else:
            self.redis_quenen = RedisQueue(queue_name, host=config.redis_host, port=config.redis_port,db=config.redis_db)
        self.threads_num = threads_num
        self.max_push_size = max_push_size

    @tomorrow_threads(50)
    def publish_redispy(self, msg: str):
        """
        单个写入消息队列
        :param msg: 待写入消息字符串
        :return: 
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

    def clear_quenen(self):
        """
        清空当前队列
        :return: 
        """
        self.redis_quenen.clear()

    @staticmethod
    def test_pub():
        redis_pub = RedisPublish('test')
        result = [str(i) for i in range(1, 508)]
        redis_pub.publish_redispy_list(result)


class BoundedThreadPoolExecutor(ThreadPoolExecutor):
    """线程池"""
    def __init__(self, max_workers=None, thread_name_prefix=''):
        super().__init__(max_workers, thread_name_prefix)
        self._work_queue = queue.Queue(max_workers * 2)

if __name__ == '__main__':
    quenen_name = 'test'

    #批量写入队列
    result = [str(i) for i in range(1, 5008)]
    redis_pub = RedisPublish(quenen_name)
    redis_pub.publish_redispy_list(result)

    #单条记录入队列
    for zz in result:
        redis_pub.publish_redispy(zz)

    def print_msg(msg):
        print(msg)

    #多线程消费队列
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg,threads_num=100)
    print(redis_customer.threads_num)
    redis_customer.start_consuming_message()

