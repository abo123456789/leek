# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:42
import redis

from redis_queue_tool.base_queue import BaseQueue


class RedisQueue(BaseQueue):
    redis_conn_instance = {}
    middleware_name = 'redis'

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


if __name__ == '__main__':
    redis_host = '127.0.0.1'
    redis_password = ''
    redis_port = 6379
    redis_db = 0
    redis_queue = RedisQueue(RedisQueue('test', host=redis_host, port=redis_port, db=redis_db,
                                        password=redis_password))
    redis_queue.put('123')
    print(redis_queue.qsize())
    redis_queue.put('456')
    print(redis_queue.get())
    redis_queue.clear()
    print(redis_queue.qsize())
