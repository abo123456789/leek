# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:41
import json
import os
import traceback

import persistqueue

from redis_queue_tool.base_queue import BaseQueue


class SqlliteQueue(BaseQueue):
    def __init__(self, queue_name, fliter_rep=False, namespace='', **kwargs):
        super().__init__(queue_name, fliter_rep, namespace, **kwargs)
        self._db = self._getconn(**kwargs)

    def qsize(self):
        return self._db.qsize()

    def isempty(self):
        return True if self.qsize() == 0 else False

    def _getconn(self, **kwargs):
        current_path = os.path.abspath(os.path.dirname(__file__))
        return persistqueue.SQLiteAckQueue(path=f'{current_path}/sqllite_queues', name=self.queue_name,
                                           auto_commit=True,
                                           multithreading=True, serializer=json)

    # noinspection PyBroadException
    def clear(self):
        try:
            sql = f'{"DELETE"}  {"FROM"} ack_queue_{self.queue_name}'
            self._db._getter.execute(sql)
            self._db._getter.commit()
            self._db.total = 0
        except Exception:
            traceback.print_exc()

    def getdb(self):
        return self._db

    def put(self, item):
        self._db.put(item)

    # noinspection PyBroadException
    def get(self, block=False, timeout=10):
        try:
            if self.qsize() > 0:
                item = self._db.get(block, timeout)
                self._db.ack(item)
                return item
        except Exception:
            return None
        return None


if __name__ == '__main__':
    lite_queue = SqlliteQueue(queue_name='test')
    lite_queue.put('12345')
    lite_queue.put(json.dumps({'a': 1, "b": 2}))
    print(lite_queue.qsize())
    # print(lite_queue.get())
    # print(lite_queue.qsize())
    # lite_queue.clear()
    # print(lite_queue.qsize())
