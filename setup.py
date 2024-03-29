# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2019/5/25 23:26
import sys

from setuptools import setup, find_packages

PY_VER = sys.version_info
if PY_VER < (3, 0):
    raise RuntimeError("leek doesn't support Python version prior 3.6")
setup(
    name='leek',
    version='1.7.1',
    description=(
        'Task publishing and consumption Middleware'
    ),
    keywords=(
        "redisqueue", "queue-tasks", "redis", "distributed-scraper", "producer-consumer",
        "distribute-crawler", "leek"),
    long_description_content_type="text/markdown",
    long_description=open('README.md', encoding='utf-8').read(),
    author='cc',
    author_email='abcdef123456chen@sohu.com',
    maintainer='cc',
    maintainer_email='abcdef123456chen@sohu.com',
    license='MIT License',
    install_requires=[
        "redis>=2.10.6",
        "tomorrow3>=1.1.0",
        "retrying>=1.3.3",
        "py-log>=1.9",
        "persist-queue>=0.5.0",
        "gevent>=1.5.0",
        "kafka-python",
        "pypattyrn"
    ],
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/abo123456789/redisqueue/tree/leek',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries'
    ])
