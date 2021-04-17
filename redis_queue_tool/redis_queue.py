# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:42
import json
import os

import redis
from redis_queue_tool.utils import get_host_ip, get_day_str

from redis_queue_tool.base_queue import BaseQueue


class RedisQueue(BaseQueue):
    redis_conn_instance = {}

    def __init__(self, queue_name: str, fliter_rep: bool = False, priority: int = None, namespace='', **kwargs):
        """

        :param name: 队列名称
        :param priority: 优先级
        :param fliter_rep: 是否开始重复任务过滤
        :param namespace: 队列名命名空间
        :param kwargs: db连接动态参数
        """
        super().__init__(queue_name, fliter_rep, namespace=namespace, **kwargs)
        if namespace:
            self.queue_name = '%s:%s' % (namespace, queue_name)
        else:
            self.queue_name = queue_name
        self.priority = priority
        if self.priority is not None:
            self.queue_name = f"{self.priority}_{self.queue_name}"
        self.fliter_rep = fliter_rep
        self.key_sets = self.queue_name + ':filter'
        self.heartbeat_field = f"{self.queue_name}:heartbeat_{os.getpid()}_{get_host_ip()}_{get_day_str()}"
        self.un_ack_sets = f"{self.heartbeat_field}:unack_message"
        self.heartbeat_key = f"tasks:heartbeat:check"

        self._db = self._getconn(**kwargs)
        self._init_queues = [f"{4 - a}_{queue_name}" for a in range(0, 5)]

    def _getconn(self, **kwargs):
        if 'redis_conn' in self.redis_conn_instance:
            self.__db = self.redis_conn_instance.get('redis_conn')
        else:
            self.__db = redis.Redis(**kwargs)
            self.redis_conn_instance['redis_conn'] = self.__db
        return self.__db

    def getdb(self):
        return self.__db

    def qsize(self):
        return self.__db.llen(self.queue_name)

    def isempty(self):
        return self.qsize() == 0

    def put(self, item):
        if self.fliter_rep:
            if self.__db.sismember(self.key_sets, item) is False:
                self.__db.lpush(self.queue_name, item)
                self.__db.sadd(self.key_sets, item)
        else:
            self.__db.lpush(self.queue_name, item)

    def clear(self):
        self.__db.delete(self.queue_name)
        if self.key_sets:
            self.__db.delete(self.key_sets)
        self.__db.delete('dlq:'+self.queue_name)

    def get(self, block=False, timeout=None):
        if block:
            if self.priority is None:
                item = self.__db.brpop(self.queue_name, timeout=timeout)
            else:
                item = self.__db.brpop(self._init_queues, timeout=timeout)
        else:
            item = self.__db.rpop(self.queue_name)
        if item:
            item = item[1].decode('utf-8') if isinstance(item, tuple) else item.decode('utf-8')
        return item

    def check_has_customer(self, hash_value):
        return self.getdb().sismember(self.key_sets, hash_value)

    def add_customer_task(self, hash_value):
        self.getdb().sadd(self.key_sets, hash_value)

    def ack(self, message):
        self.getdb().srem(self.un_ack_sets, json.dumps(message) if isinstance(message, dict) else message)

    def un_ack(self, message):
        self.getdb().sadd(self.un_ack_sets, json.dumps(message) if isinstance(message, dict) else message)

    def dlq_re_consume(self):
        all_queues = [self.queue_name]
        if self.priority is not None:
            all_queues = self._init_queues
        for queue_name in all_queues:
            dlq_queue_name = f'dlq:{queue_name}'
            dlq_queue_length = self.getdb().llen(dlq_queue_name)
            for aa in range(0, dlq_queue_length):
                dql_message = self.getdb().rpop(dlq_queue_name)
                print(aa)
                self.getdb().lpush(queue_name, dql_message)


if __name__ == '__main__':
    redis_host = '127.0.0.1'
    redis_password = ''
    redis_port = 6379
    redis_db = 0
    r_queue = RedisQueue('test12', host=redis_host, port=redis_port, db=redis_db,
                         password=redis_password)
    for i in range(1, 10):
        r_queue.put('123456')
    print(r_queue.qsize())
    r_queue.put('456')
    print(r_queue.get())
    r_queue.clear()
    print(r_queue.qsize())
    print(r_queue.check_has_customer('123'))
    r_queue.un_ack('66666')
    r_queue.ack('123456')
    r_queue.dlq_re_consume()
