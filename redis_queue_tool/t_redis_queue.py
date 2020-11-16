# -*- coding: utf-8 -*-
# @Time    : 2020/11/16 22:48
# @Author  : CC
# @Desc    : test_redis_queue.py
from redis_queue_tool import RedisQueue

if __name__ == '__main__':
    redis_host = '127.0.0.1'
    redis_password = ''
    redis_port = 6379
    redis_db = 0
    r_queue = RedisQueue('test1', host=redis_host, port=redis_port, db=redis_db,
                         password=redis_password)
    for i in range(10):
        ss = r_queue.getdb().brpop(['test1', 'test2'])
        print(ss)
