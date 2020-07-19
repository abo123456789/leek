# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:26
import abc


class BaseQueue(metaclass=abc.ABCMeta):
    def __init__(self, queue_name, fliter_rep=False, namespace='', **kwargs):
        """

        :param name: 队列名称
        :param fliter_rep: 是否开始重复任务过滤
        :param namespace: 队列名命名空间
        :param kwargs: db连接动态参数
        """
        if namespace:
            self.queue_name = '%s:%s' % (namespace, queue_name)
        else:
            self.queue_name = queue_name
        self.fliter_rep = fliter_rep
        self.key_sets = queue_name + ':sets'
        self._db = self._getconn(**kwargs)

    @abc.abstractmethod
    def _getconn(self, **kwargs):
        pass

    @abc.abstractmethod
    def getdb(self):
        pass

    @abc.abstractmethod
    def qsize(self):
        pass

    @abc.abstractmethod
    def isempty(self):
        pass

    @abc.abstractmethod
    def put(self, item):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

    @abc.abstractmethod
    def get(self, block=False, timeout=None):
        pass

    def check_has_customer(self, hash_value):
        return False

    def add_customer_task(self, hash_value):
        pass
