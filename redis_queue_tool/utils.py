# -*- coding: utf-8 -*-
# @Time    : 2020/7/19 13:15
# @Author  : CC
# @Desc    : utils.py
# @Notice  :Please do not use it for commercial use. All consequences are borne by users
import hashlib


def str_sha256(text: str) -> bytes:
    """
    获取字符串hash256值
    :param text: 待hash原始字符串
    :return: hash值
    """
    hash_obj = hashlib.sha256()
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


def str_sha512(text: str) -> bytes:
    """
    获取字符串hash512值
    :param text: 待hash原始字符串
    :return: hash值
    """
    hash_obj = hashlib.sha512()
    hash_obj.update(text.encode('utf-8'))
    return hash_obj.hexdigest()


if __name__ == '__main__':
    for st in ['我的地盘', '123', 'abcdefg', '中1abcd']:
        print(str_sha256(st))
