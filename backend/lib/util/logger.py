#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2013,掌阅科技
All rights reserved.

File Name: logger.py
Author: WangLichao
Created on: 2014-03-28
'''
import os
import os.path
import logging
import logging.handlers

def init_logger(log_conf_items):
    """
    初始化logger.
    Args:
      log_conf_items: 配置项list.
    """
    LOGGER_LEVEL = {
            'DEBUG': logging.DEBUG,
            'INFO' : logging.INFO,
            'WARNING' : logging.WARNING,
            'ERROR' : logging.ERROR,
            'CRITICAL':logging.CRITICAL
            }
    for log_item in log_conf_items:
        logger = logging.getLogger(log_item['name'])
        path = os.path.expanduser(log_item['file'])
        dir = os.path.dirname(path)
        if dir and not os.path.exists(dir):
            os.makedirs(dir)
        handler = logging.FileHandler(path)
        #在单进程服务中可以使用，多进程中需要用cronnolog
        handler.suffix='%Y%m%d%H'
        formatter = logging.Formatter(log_item['format'])
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LOGGER_LEVEL[log_item['level']])

if __name__ == '__main__':
    log_items = [
            { 'name':'operation', 'file':'log/operation.log', 'level':'DEBUG', 'format':'%(asctime)s %(levelname)s %(message)s'},
            ]
    init_logger(log_items)
    logger = logging.getLogger('operation')
    logger.info('just for test')
