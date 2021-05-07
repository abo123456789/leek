# -*- coding: utf-8 -*-
# @Time    : 2020/7/17 19:30
# @Author  : CC
# @Desc    : t_queue.py


def t_demo1():
    from leek import TaskPublisher, TaskConsumer

    # for zz in range(1, 11):
    #     TaskPublisher(queue_name='test1').pub({'a': zz, 'b': zz})
    # def print_msg_dict2(a):
    #     print(f"t_demo1:{a['a']}")
    #
    # for zz in range(1, 11):
    #     TaskPublisher(queue_name='test1').pub(a=zz, b=zz)
    # def print_msg_dict1(a, b):
    #     print(f"t_demo1:{a},{b}")
    #     # print(print_msg_dict.meta)

    for zz in range(1, 11):
        TaskPublisher(queue_name='test1').pub(zz)

    def print_msg_dict3(a):
        print(f"t_demo1:{a}")
        print(print_msg_dict3.meta)

    TaskConsumer(queue_name='test1', consuming_function=print_msg_dict3).start()


if __name__ == '__main__':
    t_demo1()
