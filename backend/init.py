#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
服务初始化
'''

# sys
import os
import sys
import logging

# tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

define('port', default=5566, help='run on this port', type=int)
define('debug', default=True, help='enable debug mode')
define('conf', default='conf/dev/conf.yml', help='specify conf path')
define('project_path', default=sys.path[0], help='deploy_path' )

tornado.options.parse_command_line()

if options.debug:
    import tornado.autoreload
    tornado.autoreload.watch(options.conf)
    tornado.autoreload.watch('conf/common.yml')

# my
from conf import CONFIG
from lib.util.session import TornadoSessionManager
from lib.util.mclient import MClient
from lib.util import uimodules, uimethods
from lib.util import logger
# handler
from handler.index import IndexHandler

class Application(tornado.web.Application):
    '''
    tornado应用
    '''
    def __init__(self):
        '''
        应用初始化
        '''
        logger.init_logger(CONFIG.LOG_CONF, suffix=options.port)
        settings = {
            'static_path': os.path.join(options.project_path, 'static'),
            'template_path': os.path.join(options.project_path, 'tpl'),
            'xsrf_cookies': False,
            'site_title': 'demo',
            'debug': options.debug,
            'ui_modules':uimodules,
            'ui_methods':uimethods,
            "session_mgr": TornadoSessionManager(CONFIG.COOKIE_NAME,
                                                 CONFIG.COOKIE_SECRET,
                                                 MClient(CONFIG.MC_SERVERS)),
        }
        handlers = [
            (r"/", IndexHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)

    def log_request(self, handler):
        status = handler.get_status()
        if status < 400:
            if handler.request.uri[0:7] == '/static':
                return
            log_method = logging.info
        elif status < 500:
            log_method = logging.warning
        else:
            log_method = logging.error
        request_time = 1000.0 * handler.request.request_time()
        if request_time > 30.0 or options.debug or status >= 400:
            summary = handler.request.method + ' ' + handler.request.uri + \
                      ' (' + handler.request.remote_ip + ')'
            log_method('%d %s %.2fms', status, summary, request_time)

if __name__ == '__main__':
    tornado.httpserver.HTTPServer(Application(), xheaders=True).listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
