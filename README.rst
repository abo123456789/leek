**包安装**::

    pip install redis-queue-tool

**使用例子**::

    from redis_queue_tool import RedisQueue
    from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer


    # redis连接配置
    redis_host = '127.0.0.1'
    redis_password = ''
    redis_port = 6379
    redis_db = 8

    quenen_name = 'test1'
    # 初始化发布队列 fliter_rep=True任务自动去重
    redis_pub = RedisPublish(queue_name=quenen_name,fliter_rep=False, max_push_size=50)

    result = [str(i) for i in range(1, 501)]

    def print_msg_str(msg):
        print(f"msg_str:{msg}")

    for zz in result:
        redis_pub.publish_redispy_str(zz)  # 写入字符串任务

    # 多线程消费字符串任务
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg_str, process_num=5, threads_num=100,
                                   max_retry_times=5)
    redis_customer.start_consuming_message()

    for zz in result:
        redis_pub.publish_redispy(c=zz, b=zz, a=zz)  # 写入字典任务 {"c":zz,"b":zz,"a":zz}

    # redis_pub.publish_redispy_list(result)  # 批量提交任务1

    def print_msg_dict(a,b,c):
        print(f"msg_dict:{a},{b},{c}")

    # 多线程消费字典任务
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg_dict,process_num=5,threads_num=100,
                                   max_retry_times=5,is_support_mutil_param=True)
    redis_customer.start_consuming_message()