# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/13 11:30
import json

import time
import traceback

from kafka import KafkaConsumer, KafkaProducer
from leek import default_config

from leek.base_queue import BaseQueue

kafka_conn_instance = {}


class KafkaConsumerOwner(object):
    """
    使用Kafka—python的消费模块
    """

    def __init__(self, host, port, topic, groupid='default'):
        self.kafkatopic = topic
        self.groupid = groupid
        if ',' in host:
            self.bootstrap_servers = ','.join(
                [f'{host_pre}:{port}' if port and str(port) not in host_pre else host_pre for host_pre in
                 host.split(',')])
        else:
            self.bootstrap_servers = f'{host}:{port}' if port and str(port) not in host else host

        key = f"consumer_{self.kafkatopic}_{self.bootstrap_servers}"
        if kafka_conn_instance.get(key):
            self.consumer = kafka_conn_instance.get(key)
        else:
            if default_config.kafka_username and default_config.kafka_password:
                self.consumer = KafkaConsumer(self.kafkatopic,
                                              group_id=groupid,
                                              sasl_plain_username=default_config.kafka_username,
                                              sasl_plain_password=default_config.kafka_password,
                                              bootstrap_servers=self.bootstrap_servers, enable_auto_commit=True)
            else:
                self.consumer = KafkaConsumer(self.kafkatopic,
                                              group_id=groupid,
                                              bootstrap_servers=self.bootstrap_servers, enable_auto_commit=True)
            kafka_conn_instance[key] = self.consumer

    def get_msg(self):
        return self.consumer.poll(1000)


class KafkaProducerOwner(object):
    """
    使用kafka的生产模块
    """

    def __init__(self, host, port, topic):
        self.kafkatopic = topic
        if ',' in host:
            self.bootstrap_servers = ','.join(
                [f'{host_pre}:{port}' if port and str(port) not in host_pre else host_pre for host_pre in host.split(',')])
        else:
            self.bootstrap_servers = f'{host}:{port}' if port and str(port) not in host else host
        key = f"producer_{self.kafkatopic}_{self.bootstrap_servers}"
        if kafka_conn_instance.get(key):
            self.producer = kafka_conn_instance.get(key)
        else:
            if default_config.kafka_username and default_config.kafka_password:
                self.producer = KafkaProducer(sasl_plain_username=default_config.kafka_username,
                                              sasl_plain_password=default_config.kafka_password,
                                              bootstrap_servers=self.bootstrap_servers)
            else:
                self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)
            kafka_conn_instance[key] = self.producer

    def send_msg(self, params):
        parmas_message = json.dumps(params) if isinstance(params, dict) else params
        self.producer.send(self.kafkatopic, parmas_message.encode())


class KafkaQueue(BaseQueue):

    # noinspection PyBroadException
    def put(self, item):
        try:
            self.producer_k.send_msg(item)
        except Exception:
            traceback.print_exc()

    def getdb(self):
        super().getdb()

    def qsize(self):
        super().qsize()

    # noinspection PyBroadException
    def get(self, block=False, timeout=None):
        try:
            rs = self.consumer_k.consumer.poll(timeout_ms=1000)
            result = []
            for key in rs:
                for record in rs[key]:
                    result.append(json.loads(record.value.decode()))
        except Exception:
            traceback.print_exc()
            return None
        return result

    def _getconn(self, **kwargs):
        self.producer_k = KafkaProducerOwner(topic=self.queue_name, **kwargs)
        self.consumer_k = KafkaConsumerOwner(topic=self.queue_name, **kwargs)

    def isempty(self):
        super().isempty()

    def clear(self):
        self.producer_k.producer.flush()


if __name__ == '__main__':
    kafka_queue = KafkaQueue(queue_name='test_leek', host=default_config.kafka_host, port=default_config.kafka_port)
    while True:
        kafka_queue.put('123456789')
        time.sleep(3)
