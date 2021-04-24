# -*- coding: utf-8 -*-
# @Time    : 2020/8/3 22:30
# @Author  : CC
# @Desc    : memery_queue.py
from queue import Queue

from pypattyrn.structural.flyweight import FlyweightMeta


class MemoryQueue(metaclass=FlyweightMeta):

    def __init__(self, queue_name, fliter_rep=False, namespace='', **kwargs):
        self.queue = Queue(maxsize=100000)
        self.queue_set = set()
        self.queue_name = queue_name
        self.fliter_rep = fliter_rep
        self.namespace = namespace

    def _getconn(self, **kwargs):
        pass

    def getdb(self):
        pass

    def qsize(self):
        return self.queue.qsize()

    def isempty(self):
        return self.queue.empty()

    def put(self, item):
        self.queue.put_nowait(item)

    def clear(self):
        self.queue = Queue()
        self.queue_set = set()

    def ack(self, value):
        pass

    def un_ack(self, value):
        pass

    def add_customer_task(self, hash_value):
        self.queue_set.add(hash_value)

    def check_has_customer(self, hash_value):
        return hash_value in self.queue_set

    # noinspection PyBroadException
    def get(self, block=False, timeout=None):
        try:
            return self.queue.get(block=block, timeout=timeout)
        except Exception:
            return None


if __name__ == '__main__':
    queue = MemoryQueue('name1')
    print(id(queue))
    for i in range(0, 1):
        queue.put('123456')
    queue.add_customer_task('123456')
    print(queue.check_has_customer('123456'))
    print(queue.get())
    print(queue.get())
    print(queue.isempty())
    print(queue.qsize())
    queue.clear()
    print(queue.isempty())
    queue2 = MemoryQueue('name1')
    print(id(queue2))
