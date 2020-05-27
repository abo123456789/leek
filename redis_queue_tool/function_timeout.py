# -*- coding: utf-8 -*-
# @Time    : 2020/5/27 11:33
# @Author  : CC
# @Desc    : function_timeout.py
import sys
import threading
import time


class __KThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
        self.__run_backup = None

    # noinspection PyAttributeOutsideInit
    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run  # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


# noinspection PyPep8Naming
class TIMEOUT_EXCEPTION(Exception):
    """function run timeout"""
    pass


def timeout(seconds):
    """超时装饰器，指定超时时间

    若被装饰的方法在指定的时间内未返回，则抛出Timeout异常"""

    def timeout_decorator(func):

        def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

        def _(*args, **kwargs):
            result = []
            new_kwargs = {
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = __KThread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(seconds)
            alive = thd.isAlive()
            thd.kill()  # kill the child thread

            if alive:
                # raise TIMEOUT_EXCEPTION('function run too long, timeout %d seconds.' % seconds)
                raise TIMEOUT_EXCEPTION(f'{func.__name__}运行时间超过{seconds}秒')
            else:
                if result:
                    return result[0]
                return result

        _.__name__ = func.__name__
        _.__doc__ = func.__doc__
        return _

    return timeout_decorator


if __name__ == '__main__':
    @timeout(5)
    def f():
        time.sleep(3)


    f()
