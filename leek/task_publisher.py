# -*- coding:utf-8 -*-
# @Author cc
import json
import traceback
from collections.abc import Callable

from py_log import get_logger
from leek.utils import sort_dict, str_sha256, gen_uuid, get_now_seconds
from leek import default_config
from leek.memery_queue import MemoryQueue
from leek.middleware_eum import MiddlewareEum
from leek.sqllite_queue import SqlliteQueue


class TaskPublisher(object):
    """任务发布类"""
    logger = get_logger(__name__, formatter_template=5)

    def __init__(self, queue_name, fliter_rep=False, filter_field=None, priority: int = None, max_push_size=50,
                 middleware=MiddlewareEum.REDIS, task_expires=None, batch_id=None,
                 max_retry_times=3, consuming_function: Callable = None,
                 db_config: dict = dict()):
        """
        初始化消息发布队列
        :param queue_name: 队列名称
        :param fliter_rep: 队列任务是否去重 True:去重  False:不去重
        :filter_field : 队列任务根据该字段去重
        :param priority: 队列优先级
        :param max_push_size: 使用批量提交时,每次批量提交数量
        :param task_expires: 任务过期时间
        :param batch_id: 批次ID
        :param middleware: 中间件,默认redis
        :param consuming_function: 消费函数名称
        """
        if priority and priority > 4:
            raise Exception('max priority support is 4')
        if middleware == MiddlewareEum.SQLITE:
            self._quenen = SqlliteQueue(queue_name=queue_name)
        elif middleware == MiddlewareEum.KAFKA:
            from leek.kafka_queue import KafkaQueue
            self._quenen = KafkaQueue(queue_name=queue_name, host=default_config.kafka_host,
                                      port=default_config.kafka_port)
        elif middleware == MiddlewareEum.MEMORY:
            self._quenen = MemoryQueue(queue_name=queue_name)
        else:
            from leek.redis_queue import RedisQueue
            _redis_db = default_config.redis_db if db_config.get('redis_db') is None or db_config.get(
                'redis_db') == '' else db_config.get('redis_db')
            _redis_ssl = default_config.redis_ssl if db_config.get('redis_ssl') is None or db_config.get(
                'redis_ssl') == '' else db_config.get('redis_ssl')
            self._quenen = RedisQueue(queue_name, priority=priority, namespace='',
                                      host=db_config.get('redis_host') or default_config.redis_host,
                                      port=db_config.get('redis_port') or default_config.redis_port,
                                      db=_redis_db,
                                      password=db_config.get('redis_password') or default_config.redis_password,
                                      ssl=_redis_ssl)
        self.quenen = self._quenen
        self.queue_name = queue_name
        self.max_push_size = max_push_size
        self._pipe = None
        self.middleware = middleware
        self.consuming_function = consuming_function
        self.fliter_rep = fliter_rep
        self.filter_field = filter_field
        self.task_expires = task_expires
        self.batch_id = batch_id
        self.max_retry_times = max_retry_times
        self.db_config = db_config
        self.meta = dict(queue_name=queue_name, fliter_rep=fliter_rep,
                         max_retry_times=max_retry_times,
                         batch_id=batch_id, priority=priority)

    # noinspection PyBroadException
    def pub(self, *args, **kwargs):
        """
        将多参数写入消息队列
        :param kwargs: 待写入参数 (a=3,b=4)
        :return: None
        """
        if self.task_expires:
            self.meta['task_expires'] = self.task_expires + get_now_seconds()
        task = dict(meta=self.meta)
        if kwargs:
            dict_msg = sort_dict(kwargs)
            task['meta']['msg_type'] = 'params'
        elif args:
            dict_msg = args[0]
            if type(dict_msg) == dict:
                task['meta']['msg_type'] = 'dict'
            else:
                task['meta']['msg_type'] = 'only'
        else:
            raise Exception('^^^^^^^^参数非法^^^^^^^^')
        task['body'] = dict_msg
        if not task['body']:
            return False
        task['meta']['task_id'] = gen_uuid()
        if self.fliter_rep:
            if self.filter_field:
                hash_value = str(task['body'].get(self.filter_field, ''))
            else:
                hash_value = str_sha256(json.dumps(task['body']))
            if self._quenen.check_has_customer(hash_value):
                self.logger.warning(f'{task} is repeat task!!')
                return False
        self._quenen.put(json.dumps(task))
        return True

    def pub_list(self, tasks: list, param_type: str = 'params'):
        """
        批量写入redis队列(批量提交暂时不支持去重)
        :param tasks: 待写入任务列表数据
        :param param_type: 待写入任务列表数据类型 params(多参数) only(单参数)
        :return:
        """
        if self.task_expires:
            self.meta['task_expires'] = self.task_expires + get_now_seconds()
        if self.middleware == MiddlewareEum.REDIS:
            pipe = self._quenen.getdb().pipeline()
            for msg in tasks:
                try:
                    message = json.loads(msg) if isinstance(msg, str) and '{' in msg and '}' in msg else msg
                    task_body = sort_dict(message)
                except (Exception,):
                    self.logger.error(traceback.format_exc())
                    return False
                task = dict(meta=self.meta, body=task_body)
                task['meta']['task_id'] = gen_uuid()
                task['meta']['msg_type'] = 'params' if isinstance(msg, dict) and param_type == 'params' else 'only'
                pipe.lpush(self._quenen.queue_name, json.dumps(task))
                if len(pipe) == self.max_push_size:
                    pipe.execute()
                    self.logger.info(str(self.max_push_size).center(20, '*') + 'commit')
            if len(pipe) > 0:
                pipe.execute()
        else:
            raise Exception('不支持批量提交的中间件,请使用单个提交方法')
        return True

    def clear(self):
        """
        清空当前队列
        :return:
        """
        self._quenen.clear()

    def qsize(self):
        """
        获取当前队列任务数量
        :return: int 队列中任务数量
        """
        return self._quenen.qsize()

    def dlq_re_queue(self):
        if self.middleware == MiddlewareEum.REDIS:
            self._quenen.dlq_re_consume()
        else:
            pass


if __name__ == '__main__':
    db_config = dict(redis_host='127.0.0.1', redis_port='6379', redis_db='1', redis_password='', redis_ssl=False)
    task_publisher = TaskPublisher('test123', middleware=MiddlewareEum.REDIS, db_config=db_config)
    # result = task_publisher.pub(a=1, b=2)
    # print(task_publisher.meta)
    # print(result)

    results = [json.dumps(dict(a=i, c=i, b=i)) for i in range(1, 51)]
    result = task_publisher.pub_list(results)
    # print(result)

    # task_publisher.clear()
