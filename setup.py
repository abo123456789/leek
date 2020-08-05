# -*- coding:utf-8 -*-
# @Author cc
# @TIME 2019/5/25 23:26

from setuptools import setup, find_packages

setup(
    name='redis-queue-tool',
    version='4.5.6',
    description=(

        '高并发reids队列,分布式爬虫利器(High concurrency RedisQueue,Distributed crawler weapon)'
    ),
    keywords=(
        "redisqueue", "queue-tasks", "redis", "distributed-scraper", "producer-consumer",
        "distribute-crawler", "web-crawler"),
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
        "gevent>=1.4.0",
        "pypattyrn"
    ],
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/abo123456789/redis-queue-tool',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ])
