# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2020/5/13 11:30
import json

import time
import traceback

from kafka import KafkaConsumer, KafkaProducer
from redis_queue_tool import default_config

from redis_queue_tool.base_queue import BaseQueue

kafka_conn_instance = {}


class Kafka_consumer(object):
    """
    使用Kafka—python的消费模块
    """

    def __init__(self, host, port, topic, groupid='default'):
        self.kafkatopic = topic
        self.groupid = groupid
        self.bootstrap_servers = f'{host}:{port}'
        key = f"consumer_{self.kafkatopic}_{self.bootstrap_servers}"
        if kafka_conn_instance.get(key):
            self.consumer = kafka_conn_instance.get(key)
        else:
            if default_config.kafka_username and default_config.kafka_password:
                self.consumer = KafkaConsumer(self.kafkatopic
                                              , group_id=groupid,
                                              sasl_mechanism='PLAIN',
                                              security_protocol='SASL_PLAINTEXT',
                                              sasl_plain_username=default_config.kafka_username,
                                              sasl_plain_password=default_config.kafka_password,
                                              bootstrap_servers=self.bootstrap_servers, enable_auto_commit=True)
            else:
                self.consumer = KafkaConsumer(self.kafkatopic
                                              , group_id=groupid,
                                              bootstrap_servers=self.bootstrap_servers, enable_auto_commit=True)
            kafka_conn_instance[key] = self.consumer

    def get_msg(self):
        return self.consumer.poll(1000)


class Kafka_producer(object):
    """
    使用kafka的生产模块
    """

    def __init__(self, host, port, topic):
        self.kafkatopic = topic
        self.bootstrap_servers = f'{host}:{port}'
        key = f"producer_{self.kafkatopic}_{self.bootstrap_servers}"
        if kafka_conn_instance.get(key):
            self.producer = kafka_conn_instance.get(key)
        else:
            if default_config.kafka_username and default_config.kafka_password:
                self.producer = KafkaProducer(sasl_mechanism='PLAIN',
                                              security_protocol='SASL_PLAINTEXT',
                                              sasl_plain_username=default_config.kafka_username,
                                              sasl_plain_password=default_config.kafka_password,
                                              bootstrap_servers=self.bootstrap_servers)
            else:
                self.producer = KafkaProducer(bootstrap_servers=self.bootstrap_servers)
            kafka_conn_instance[key] = self.producer

    def send_msg(self, params):
        parmas_message = json.dumps(params)
        self.producer.send(self.kafkatopic, parmas_message.encode())


class KafkaQueue(BaseQueue):

    def put(self, item):
        try:
            self.producer_k.send_msg(item)
        except:
            traceback.print_exc()

    def getdb(self):
        super().getdb()

    def qsize(self):
        super().qsize()

    def get(self, block=False, timeout=None):
        try:
            rs = self.consumer_k.consumer.poll(timeout_ms=1000)
            result = []
            for key in rs:
                for record in rs[key]:
                    result.append(json.loads(record.value.decode()))
        except:
            traceback.print_exc()
            return None
        return result

    def _getconn(self, **kwargs):
        self.producer_k = Kafka_producer(topic=self.queue_name, **kwargs)
        self.consumer_k = Kafka_consumer(topic=self.queue_name, **kwargs)

    def isempty(self):
        super().isempty()

    def clear(self):
        self.producer_k.producer.flush()


if __name__ == '__main__':
    kafka_queue = KafkaQueue(queue_name='test5', host='127.0.0.1', port=9092)
    while True:
        kafka_queue.put('123456789')
        time.sleep(3)
