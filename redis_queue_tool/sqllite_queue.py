# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:41
import json
import traceback

import persistqueue

from redis_queue_tool.base_queue import BaseQueue


class SqlliteQueue(BaseQueue):
    middleware_name = 'sqlite'

    def qsize(self):
        return self._db._count()

    def isempty(self):
        return True if self.qsize() == 0 else False

    def _getconn(self, **kwargs):
        return persistqueue.SQLiteAckQueue(path='/root/sqllite_queues', name=self.queue_name, auto_commit=True,
                                           multithreading=True, serializer=json)

    def clear(self):
        try:
            sql = f'{"DELETE"}  {"FROM"} ack_queue_{self.queue_name}'
            print(sql)
            self._db._getter.execute(sql)
            self._db._getter.commit()
            self._db.total = 0
        except:
            traceback.print_exc()

    def getdb(self):
        return self._db

    def put(self, item):
        self._db.put(item)

    def get(self, block=False, timeout=10):
        try:
            if self.qsize() > 0:
                item = self._db.get(block, timeout)
                self._db.ack(item)
                return item
        except:
            return None
        return None


if __name__ == '__main__':
    lite_queue = SqlliteQueue(queue_name='test')
    lite_queue.put('12345')
    lite_queue.put(json.dumps({'a': 1, "b": 2}))
    print(lite_queue.qsize())
    print(lite_queue.get())
    print(lite_queue.qsize())
    lite_queue.clear()
    print(lite_queue.qsize())
