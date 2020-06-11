# -*- coding: utf-8 -*-
# @Time    : 2020/6/11 00:12
# @Author  : CC
# @Desc    : custom_gevent.py
import atexit
import time

from gevent import pool as gevent_pool
from gevent import monkey


class CustomGeventPoolExecutor(gevent_pool.Pool):
    def __init__(self, size=None, greenlet_class=None):
        super().__init__(size, greenlet_class)
        if monkey.is_module_patched('socket') is False:
            raise Exception("""请先打猴子补丁,代码开头加入:
            from gevent import monkey 
            monkey.patch_all()""")
        atexit.register(self.shutdown)

    def submit(self, *args, **kwargs):
        self.spawn(*args, **kwargs)

    def shutdown(self):
        self.join()


if __name__ == '__main__':
    monkey.patch_all()


    def prt(x):
        time.sleep(5)
        print(x)


    pool = CustomGeventPoolExecutor(4)
    for i in range(20):
        pool.submit(prt, i)
