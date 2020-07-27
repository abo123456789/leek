# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:42
import json
import redis

from redis_queue_tool.base_queue import BaseQueue


class RedisQueue(BaseQueue):
    redis_conn_instance = {}

    def _getconn(self, **kwargs):
        if 'redis_conn' in self.redis_conn_instance:
            self.__db = self.redis_conn_instance.get('redis_conn')
        else:
            self.__db = redis.Redis(**kwargs)
            self.redis_conn_instance['redis_conn'] = self.__db

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

    def get(self, block=False, timeout=None):
        if block:
            item = self.__db.brpop(self.queue_name, timeout=timeout)
        else:
            item = self.__db.rpop(self.queue_name)
        if item:
            item = item.decode('utf-8')
        return item

    def check_has_customer(self, hash_value):
        return self.getdb().sismember(self.key_sets, hash_value)

    def add_customer_task(self, hash_value):
        self.getdb().sadd(self.key_sets, hash_value)

    def ack(self, message):
        self.getdb().srem(self.un_ack_sets, json.dumps(message) if isinstance(message, dict) else message)

    def un_ack(self, message):
        self.getdb().sadd(self.un_ack_sets, json.dumps(message) if isinstance(message, dict) else message)


if __name__ == '__main__':
    redis_host = '127.0.0.1'
    redis_password = ''
    redis_port = 6379
    redis_db = 0
    r_queue = RedisQueue('test', host=redis_host, port=redis_port, db=redis_db,
                         password=redis_password)
    r_queue.put('123')
    print(r_queue.qsize())
    r_queue.put('456')
    print(r_queue.get())
    r_queue.clear()
    print(r_queue.qsize())
    print(r_queue.check_has_customer('123'))
    r_queue.un_ack('66666')
    # r_queue.ack('123456')
