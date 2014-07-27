#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# Abstract: session

import os
import time
import hashlib
import logging
import datetime 
import uuid
import cPickle as pickle

class SessionManager(object):  
	'''
	session manager
	''' 
	def __init__(self, cookie_name, secret, backend):
		self.cookie_name = cookie_name
		self.secret = secret
		self.backend = backend
	
	def save_session(self, session, expires=0):  
		data = pickle.dumps(dict(session.items()))
		if len(data) >= 16000:
			logging.warning('hi, man, attention! session(id=%s) data size is now so big:%d'%(session.id,len(data),))
		self.backend.set(session.id,data,expires)
	
	def load_session(self, session_id=None):  
		if not session_id:
			session_id = self.gen_session_id()
			session = Session(session_id,self)
		else:
			try:
				data = self.backend.get(session_id)
				if data:
					data = pickle.loads(data)
					assert type(data) == dict
				else:
					data = {}
			except:
				data = {}	
			session = Session(session_id,self,data)
		return session

	def gen_session_id(self):
		return hashlib.sha1("%s%s%s" %(uuid.uuid4(),time.time(),self.secret)).hexdigest()  

class Session(dict):  
	'''
	Base Session
	'''
	def __init__(self, session_id='', mgr=None, data={}):  
		self.id = session_id  
		self._mgr = mgr  
		self.update(data)  
		self._change = False

	def save(self, expires=0):  
		self._mgr.save_session(self,expires)  
	
	def __missing__(self, key):  
		return None  

	def __delitem__(self, key):  
		if key in self:  
			super(Session,self).__delitem__(key)  
	
	def __setitem__(self, key, val):  
		super(Session, self).__setitem__(key, val)  

	def set(self, key, value, expires=0):
		self[key] = value
		self.save(expires)

class TornadoSessionManager(SessionManager):
	'''
	session for tornado
	'''
	def load_session(self, reqHandler=None):
		self.reqHandler = reqHandler
		if self.reqHandler:
			session_id = reqHandler.get_cookie(self.cookie_name) 
		else:
			session_id = ''
		return super(TornadoSessionManager,self).load_session(session_id)

	def save_session(self, session, expires=0):
		if hasattr(self,'reqHandler') and self.reqHandler:
			_expires = None
			if expires:
				_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires)
			self.reqHandler.set_cookie(self.cookie_name, session.id, expires=_expires)
		return super(TornadoSessionManager, self).save_session(session,expires)

