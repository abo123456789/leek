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
    redis_pub = RedisPublish(queue_name=quenen_name, fliter_rep=True)

    result = [str(i) for i in range(1, 101)]

    for zz in result:
        redis_pub.publish_redispy(a=zz, b=zz, c=zz)  # 多线程单条记录写入

    redis_pub.publish_redispy_list(result)  # 单线程批量写入1

    for zz in result:
        redis_pub.publish_redispy_mutil(zz)  # 单线程批量写入2


    def print_msg(msg):
        print(json.loads(msg))


    # 多线程消费
    redis_customer = RedisCustomer(quenen_name, consuming_function=print_msg, threads_num=100)
    print(redis_customer.threads_num)
    redis_customer.start_consuming_message()