# -*- coding: utf-8 -*-
# @Author  : cc
# @Time    : 2020/6/11 0011 0:56
"""

使用覆盖的方式，做配置。
"""
import sys
import time
import importlib
from pathlib import Path

config_file_content = '''# -*- coding: utf-8 -*-
"""
此文件redis_queue_tool_config.py是自动生成的redis-queue-tool框架的数据库配置文件。
"""
# redis连接配置
#redis_host = '127.0.0.1'
#redis_password = ''
#redis_port = 6379
#redis_db = 0

# kafka配置连接信息
#kafka_port = 9092
#kafka_host = '127.0.0.1'
#kafka_username = ''
#kafka_password = ''
'''


def use_config_form_distributed_frame_config_module():
    """
    自动读取配置,没有则读取项目根目录下的redis_queue_tool_config.py
    :return:
    """
    line = sys._getframe().f_back.f_lineno
    file_name = sys._getframe(1).f_code.co_filename
    try:
        m = importlib.import_module('redis_queue_tool_config')
        msg = f'读取到\n "{m.__file__}:1" 配置文件了\n'
        sys.stdout.write(f'{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {msg} \n \033[0m')
    except ModuleNotFoundError:
        msg = '在你的项目根目录下生成了 redis_queue_tool_config.py配置文件，快去看看并修改一些自定义配置吧'
        sys.stdout.write(f'{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {msg} \n \033[0m')
        auto_creat_config_file_to_project_root_path()


def auto_creat_config_file_to_project_root_path():
    if Path(sys.path[1]).as_posix() in Path(__file__).parent.parent.absolute().as_posix():
        pass
    with (Path(sys.path[1]) / Path('redis_queue_tool_config.py')).open(mode='w', encoding='utf8') as f:
        f.write(config_file_content)


if __name__ == '__main__':
    auto_creat_config_file_to_project_root_path()
