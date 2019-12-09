**包安装**::

    pip install redis-queue-tool

**使用例子**::

    from redis_queue_tool import RedisQueue
    from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer


    # redis连接配置
    RedisQueue.redis_host = '127.0.0.1'
    RedisQueue.redis_password = ''
    RedisQueue.redis_port = 6379
    RedisQueue.redis_db = 0

    quenen_name = 'test1'
    # 初始化发布队列 fliter_rep=True任务自动去重
    redis_pub = RedisPublish(queue_name=quenen_name, fliter_rep=False)

    result = [str(i) for i in range(1, 101)]

    redis_pub.publish_redispy({"a":1,"b":1,"c":1})

    for zz in result:
        redis_pub.publish_redispy(c=zz, b=zz, a=zz)  # 写入字典任务 {"c":zz,"b":zz,"a":zz}

    for zz in result:
        redis_pub.publish_redispy_str(zz)  # 写入字符串任务

    redis_pub.publish_redispy_list(result)  # 批量提交任务1

    for zz in result:
        redis_pub.publish_redispy_mutil(zz)  # 批量提交任务2

    def print_msg(msg):
        print(msg)


    # 多进程和线程消费 (默认启动进程数:1,默认每个进程启动线程数:50)
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg,process_num=10, threads_num=100,max_retry_times=5)
    print(redis_customer.threads_num)
    redis_customer.start_consuming_message()