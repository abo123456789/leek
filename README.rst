**包安装**::

    pip install redis-queue-tool

**使用例子**::

    ##### 1.发布消费字符串类型任务
        from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer, init_redis_config


        # redis连接配置
        init_redis_config(host='127.0.0.1', password='', port=6379, db=8)

        for zz in range(1, 501):
            # 发布字符串任务 queue_name发布队列名称 fliter_rep=True任务自动去重(默认False)
            RedisPublish(queue_name='test1', fliter_rep=False).publish_redispy_str(str(zz))


        def print_msg_str(msg):
            print(f"msg_str:{msg}")


        # 消费字符串任务 queue_name消费队列名称 max_retry_times错误最大重试次数
        RedisCustomer(queue_name='test1', consuming_function=print_msg_str, process_num=2, threads_num=100,
                      max_retry_times=5).start_consuming_message()


    ##### 2.发布消费多参数类型任务
        from redis_queue_tool.RedisQueue import RedisPublish, RedisCustomer, init_redis_config

        # redis连接配置
        init_redis_config(host='127.0.0.1', password='', port=6379, db=8)

        for zz in range(1, 501):
             # 发布多参数任务
             RedisPublish(queue_name='test2').publish_redispy(c=str(zz), b=str(zz), a=str(zz))


        def print_msg_dict(a, b, c):
            print(f"msg_dict:{a},{b},{c}")


        # 消费多参数类型任务 queue_name消费队列名称 is_support_mutil_param=True消费函数支持多参数(默认False) qps每秒消费任务数
        RedisCustomer(queue_name='test2', consuming_function=print_msg_dict, process_num=2, threads_num=100,
                      max_retry_times=5, is_support_mutil_param=True, qps=50).start_consuming_message()

    ##### 3.批量提交任务
        from redis_queue_tool.RedisQueue import RedisPublish, init_redis_config

        # redis连接配置
        init_redis_config(host='127.0.0.1', password='', port=6379, db=8)

        result = [str(i) for i in range(1, 501)]
        # 批量提交任务 queue_name提交任务队列名称 max_push_size每次批量提交记录数(默认值50)
        RedisPublish(queue_name='test3', max_push_size=100).publish_redispy_list(result)