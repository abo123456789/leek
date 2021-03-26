# -*- coding: utf-8 -*-
# @Time    : 19/10/12 下午12:13
# @Author  : cc
# @FileName: __init__.py.py
from .middleware_eum import *
from .producter_consumer import *
from .init_config_file import use_config_form_distributed_frame_config_module
from multiprocessing import set_start_method
import platform
if platform.system() == 'Darwin' or platform.system() == 'Linux':
    set_start_method("fork")

use_config_form_distributed_frame_config_module()
