# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/10 00:26
import abc
import os

from redis_queue_tool.utils import get_host_ip, get_day_str


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
        self.key_sets = self.queue_name + ':filter'

        self.heartbeat_field = f"{self.queue_name}:heartbeat_{os.getpid()}_{get_host_ip()}_{get_day_str()}"
        self.un_ack_sets = f"{self.heartbeat_field}:unack_message"
        self.heartbeat_key = f"tasks:heartbeat:check"
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

    def ack(self, value):
        pass

    def un_ack(self, value):
        pass

    def dlq_re_consume(self):
        pass
