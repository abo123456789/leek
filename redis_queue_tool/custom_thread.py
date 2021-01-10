# -*- coding:utf-8 -*-
# @Time    : 2020/04/12 上午12:00
# @Author  : ydf
"""
可自动实时调节线程数量的线程池。
不仅能扩大，还可缩小
"""

import atexit
import queue
import threading
import weakref

import time

from py_log import get_logger

_shutdown = False
_threads_queues = weakref.WeakKeyDictionary()
logger = get_logger(__name__)


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


atexit.register(_python_exit)


class _WorkItem(object):
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            logger.error(f'函数 {self.fn.__name__} 中发生错误，错误原因是 {type(exc)} {exc} ')
            raise Exception(exc)

    def __str__(self):
        return f'{(self.fn.__name__, self.args, self.kwargs)}'


class CustomThreadPoolExecutor:
    def __init__(self, max_workers=None, thread_name_prefix=''):
        """
        最好需要兼容官方concurren.futures.ThreadPoolExecutor 和改版的BoundedThreadPoolExecutor，入参名字和个数保持了一致。
        :param max_workers:
        :param thread_name_prefix:
        """
        self._max_workers = max_workers or 4
        self._min_workers = 5
        self._thread_name_prefix = thread_name_prefix
        self.work_queue = queue.Queue(max_workers)
        # self._threads = set()
        self._threads = weakref.WeakSet()
        self._lock_compute_threads_free_count = threading.Lock()
        self.threads_free_count = 0
        self._shutdown = False
        self._shutdown_lock = threading.Lock()

    def set_min_workers(self, min_workers=10):
        self._min_workers = min_workers
        return self

    def change_threads_free_count(self, change_num):
        with self._lock_compute_threads_free_count:
            self.threads_free_count += change_num

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('不能添加新的任务到线程池')
        self.work_queue.put(_WorkItem(func, args, kwargs))
        self._adjust_thread_count()

    def _adjust_thread_count(self):
        # if len(self._threads) < self._threads_num:
        if self.threads_free_count < self._min_workers and len(self._threads) < self._max_workers:
            # t = threading.Thread(target=_work,
            #                      args=(self._work_queue,self))
            t = _CustomThread(self)
            t.setDaemon(True)
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self.work_queue

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self.work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False


class _CustomThread(threading.Thread, ):
    def __init__(self, executorx: CustomThreadPoolExecutor):
        super().__init__()
        self._executorx = executorx
        self._run_times = 0

    # noinspection PyProtectedMember
    def _remove_thread(self, stop_resson=''):
        # noinspection PyUnresolvedReferences
        logger.info(stop_resson)
        self._executorx.change_threads_free_count(-1)
        self._executorx._threads.remove(self)
        _threads_queues.pop(self)

    # noinspection PyProtectedMember
    def run(self):
        # noinspection PyUnresolvedReferences

        self._executorx.change_threads_free_count(1)
        while True:
            try:
                work_item = self._executorx.work_queue.get(block=True, timeout=60)
            except queue.Empty:
                if self._executorx.threads_free_count > self._executorx._min_workers:
                    self._remove_thread(
                        f'当前线程超过60秒没有任务，线程池中不在工作状态中的线程数量是 {self._executorx.threads_free_count}，'
                        f'超过了指定的数量 {self._executorx._min_workers}')
                    break
                else:
                    continue

            # print(work_item)
            if work_item is not None:
                self._executorx.change_threads_free_count(-1)
                work_item.run()
                del work_item
                self._executorx.change_threads_free_count(1)
                continue
            if _shutdown or self._executorx._shutdown:
                self._executorx.work_queue.put(None)
                break


if __name__ == '__main__':
    pool = CustomThreadPoolExecutor(200)

    # pool = BoundedThreadPoolExecutor(200)


    def consume(x):
        time.sleep(2)
        print(x)


    def show_count():
        while 1:
            time.sleep(1)
            print(f'线程数量 {threading.active_count()}')


    threading.Thread(target=show_count).start()

    for i in range(1000):
        time.sleep(0.1)
        pool.submit(consume, i)
