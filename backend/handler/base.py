#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import tornado.web
from urlparse import urljoin
from conf import CONFIG
from lib.util.logger import OpLogger
from lib.util import url_add_params
from model.user import User
from service import Service

SESSION_USER = CONFIG.SESSION_USER

class BaseHandler(tornado.web.RequestHandler):
    '''重写部分request方法
    Attributes:
        ret_code: 表示http请求的返回值配置
        service: service实例
        logger: 日志配置
        NEED_LOGIN: 表示用户是否需要登录
    '''

    NEED_LOGIN = True
    def initialize(self):
        self.ret_code = CONFIG.RETUNT_CODE
        self.service = Service.inst()
        self.logger = OpLogger()
        self.current_user = None

    def get_argument(self, name,
                     default=tornado.web.RequestHandler._ARG_DEFAULT,
                     strip=True):
        '''重写tornado的方法，将所有的参数进行utf8编码
        Args:
            name: 参数名称
            default: 默认值
            strip: 是否需要过滤空格
        Retruns:
            返回参数的值
        '''
        value = super(BaseHandler,self).get_argument(name,default,strip)
        if not value and default != tornado.web.RequestHandler._ARG_DEFAULT:
            value = default
        if isinstance(value,unicode):
            value = value.encode('utf-8')
        return value

    def get_arguments(self, name, strip=True):
        rlist = super(BaseHandler,self).get_arguments(name,strip)
        for idx,val in enumerate(rlist):
            if isinstance(val,unicode):
                rlist[idx] = val.encode('utf-8')
        return rlist

    def prepare(self):
        '''called by tornado before every request handling
        '''
        self.target_tab = self.get_argument('target_tab', '')

    def wrap_url(self, url, escape=False, need_target=True):
        '''wrap the url to send req to authsys to proxy
        '''
        proxy_source = self.get_argument('x-proxy','')
        if proxy_source:
            if not url.startswith('http://'):
                url = urljoin('http://%s'%self.request.host,url)
            url = url_add_params(proxy_source, escape,**{'x-url':url})
        if need_target:
            url = url_add_params(url, escape,target_tab=self.target_tab)
        return url

    @property
    def session(self):
        if not hasattr(self,'_session'):
            self._session = self.application.settings['session_mgr'].load_session(self)
        return self._session

    def send_json(self, res=None, desc='E_OK',
                  callback=None):
        '''发送json数据
        Args:
            res: 返回的body内容
            desc: 返回码描述
            callback: 是否添加头信息
        '''
        r = self.ret_code[desc]
        r['body'] = res or ''
        r = json.dumps(r, default=BaseHandler._default)
        if callback:
            r = '%s(%s);' % (callback, r)
            self.set_header('Content-Type', 'application/json')
        self.write(r)

    def parse_module(self, module):
        mod, sub = "", ""
        if module:
            arr = module.split("/")
            if len(arr)>=3:
                mod, sub = arr[1], arr[2]
            elif len(arr) >= 2:
                mod = arr[1]
        return '%s__%s'%(mod, sub) if sub else mod

    def get(self, module):
        if self.NEED_LOGIN and not self.current_user and self.request.uri != '/user/login':
            self.redirect('/user/login')
            return
        module = self.parse_module(module)
        method = getattr(self, module or 'index', None)
        if method and module not in ('get','post'):
            try:
                method()
            except Exception,e:
                self.logger.error("act=get error=%s,module=%s" % (e, module),
                                  exc_info=True)
        else:
            raise tornado.web.HTTPError(404)

    def post(self, module):
        if self.NEED_LOGIN and not self.current_user and self.request.uri != '/user/login':
            self.redirect('/user/login')
            return
        module = self.parse_module(module)
        method = getattr(self, module or 'index', None)
        if method and module not in ('get','post'):
            try:
                method()
            except Exception,e:
                self.logger.error("act=post error=%s,module=%s" % (str(e), module),
                                  exc_info=True)
        else:
            raise tornado.web.HTTPError(404)

    def get_current_user(self):
        '''
        when request from authsys
        get user by auth api of authsys
        '''
        proxy_source = self.get_argument('x-proxy', '')
        if proxy_source:
            session_id = self.get_cookie('session_id')
            u = self.service.auth.check_login(session_id)
        else:
            uinfo, u = self.session[SESSION_USER], None
            if uinfo:
                u = User.mgr().Q().filter(id=uinfo['uid'])[0]
        if not u:
            self._logout()
        return u

    def _login(self, uid):
        self.session[SESSION_USER] = {'uid':uid}
        self.session.save()

    def _logout(self):
        self.session[SESSION_USER] = None
        self.session.save()
