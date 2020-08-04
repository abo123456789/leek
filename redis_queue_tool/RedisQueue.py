# -*- coding: utf-8 -*-
# @Time    : 2020/8/3 16:51
# @Author  : CC
# @Desc    : RedisQueue.py 用来兼容旧版本,请勿使用这个文件导入相应的包
import warnings

warnings.warn("RedisQueue is deprecated", DeprecationWarning)
from redis_queue_tool import task_deco, RedisPublish, RedisCustomer, init_redis_config
