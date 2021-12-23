# -*- coding: utf-8 -*-
# @Time    : 2020/7/17 19:30
# @Author  : CC
# @Desc    : t_queue.py
import time

from leek import get_consumer


def t_demo1():
    from leek import TaskPublisher, TaskConsumer

    # for zz in range(1, 11):
    #     TaskPublisher(queue_name='test1').pub({'a': zz, 'b': zz})
    #
    # def print_msg_dict2(a):
    #     print(f"t_demo1:{a}")

    # for zz in range(1, 11):
    #     TaskPublisher(queue_name='test1', fliter_rep=True).pub(a=zz, b=zz)
    #
    # def print_msg_dict1(a, b):
    #     print(f"t_demo1:{a},{b}")
    #     print(print_msg_dict1.meta)

    # for zz in range(1, 11):
    #     TaskPublisher(queue_name='test1', fliter_rep=True).pub(zz)
    #
    # def print_msg_dict3(a):
    #     print(f"t_demo1:{a}")
    #     print(print_msg_dict3.meta)

    def print_msg_dict4(a: dict):
        print(f"t_demo1:{a}")
        print(print_msg_dict4.meta)

    tasks = [dict(a=zz, b=zz) for zz in range(1, 11)]
    TaskPublisher(queue_name='test1', fliter_rep=True).pub_list(tasks, param_type='only')

    TaskConsumer(queue_name='test1', consuming_function=print_msg_dict4, fliter_rep=True).start()


def t_demo2():
    def execute_data_import(batch_id):
        time.sleep(30)
        print('导入', batch_id)
        cal_consumer.task_publisher.pub(batch_id=batch_id)

    def execute_all_cal(batch_id):
        time.sleep(30)
        print('计算', batch_id)
        export_consumer.task_publisher.pub(batch_id=batch_id)

    def execute_all_export(batch_id):
        time.sleep(30)
        print('导出', batch_id)

    # db_config = dict(redis_host='127.0.0.1', redis_port=6379, redis_db=1,
    #                  redis_password='', redis_ssl=False)
    db_config = dict(redis_host='127.0.0.1', redis_port=6379, redis_db=1,
                     redis_password='', redis_ssl=False)
    import_consumer = get_consumer(queue_name='test:import_queue', consuming_function=execute_data_import, ack=True,
                                   max_retry_times=1, db_config=db_config)
    cal_consumer = get_consumer(queue_name='test:cal_queue', consuming_function=execute_all_cal, ack=True,
                                process_num=2,
                                max_retry_times=1,
                                db_config=db_config)
    export_consumer = get_consumer(queue_name='test:export_queue', consuming_function=execute_all_export, ack=True,
                                   process_num=2, max_retry_times=1,
                                   db_config=db_config)
    import_consumer.task_publisher.pub(batch_id='batch_test_v20211223_1.0')
    import_consumer.start()
    cal_consumer.start()
    export_consumer.start()


if __name__ == '__main__':
    t_demo2()
