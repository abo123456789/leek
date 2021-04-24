# -*- coding: utf-8 -*-
# @Time    : 2020/7/19 13:15
# @Author  : CC
# @Desc    : utils.py
# @Notice  :Please do not use it for commercial use. All consequences are borne by users
import getpass
import hashlib
import socket
import time


def str_sha256(text: str) -> str:
    """
    获取字符串hash256值
    :param text: 待hash原始字符串
    :return: hash值
    """
    hash_obj = hashlib.sha256()
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def str_sha512(text: str) -> str:
    """
    获取字符串hash512值
    :param text: 待hash原始字符串
    :return: hash值
    """
    hash_obj = hashlib.sha512()
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def get_day_str():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())


def sort_dict(dict_obj: dict) -> dict:
    rs = dict()
    if not dict_obj:
        return rs
    for k in sorted(dict_obj.keys()):
        rs[k] = dict_obj[k]
    return rs


def get_now_millseconds():
    return int(time.time() * 1000)


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    ip = '127.0.0.1'
    s = socket.socket(type=socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        pass
    finally:
        s.close()
    return ip


def get_host_name():
    return getpass.getuser()


def get_day_formate(millseconds: float):
    """
    将毫秒转换成日期
    :param millseconds: 毫秒
    :return: 220-04-08 12:34:56
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(millseconds / 1000))


if __name__ == '__main__':
    for st in ['我的地盘', '123', 'abcdefg', '中1abcd']:
        print(type(str_sha256(st)))
        print(str_sha256(st))
    print(get_day_str())
    print(get_host_ip())
    print(get_host_name())
    print(get_now_millseconds())
    print(get_day_formate(get_now_millseconds()))
    print(sort_dict(dict(a=12, b=32, d=1, c=9)))
