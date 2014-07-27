#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# Abstract: pylibmc wrap

import time
import memcache
import logging

class MClient(object):
	min_cycle,max_cycle,total_time,counter,succ,fail,ext = 0xffffL,0L,0L,0L,0L,0L,''
	def __init__(self, servers, binary=True, behaviors={"tcp_nodelay":True,"ketama":True}):
		self.servers = servers
		self.mc = memcache.Client(self.servers)

	def __getattr__(self, attr):
		return getattr(self.mc,attr)
	
	def __del__(self):
		self.mc.disconnect_all()

	def __repr__(self):
		return '<MCStore(server=%s)>' % repr(self.servers)

	def __str__(self):
		return self.servers

	def set(self, key, data, _time=0):
		start = time.time()
		r = bool(self.mc.set(key, data, _time))
		self.update_stat((time.time()-start)*1000,key,cmd='set')
		return r

	def get(self, key):
		start = time.time()
		r = self.mc.get(key)
		self.update_stat((time.time()-start)*1000,key,cmd='get')
		return r

	def get_multi(self, keys, prefix=''):
		start = time.time()
		r = self.mc.get_multi(keys,prefix)
		self.update_stat((time.time()-start)*1000,keys,prefix=prefix,cmd='get_multi')
		return r

	def delete(self, key):
		start = time.time()
		r = bool(self.mc.delete(key))
		self.update_stat((time.time()-start)*1000,key,cmd='delete')
		return r

	def mutex(self, key):
		logging.info('mutex %s'%key)
		return self.mc.add(key,'',5)

	def unmutex(self, key):
		logging.info('unmutex %s'%key)
		return self.mc.delete(key)
	
	@classmethod 
	def reset_stat(cls):
		cls.min_cycle,cls.max_cycle,cls.total_time,cls.counter,cls.succ,cls.fail,cls.ext = 0xffffL,0L,0L,0L,0L,0L,''

	@classmethod 
	def stat(cls):
		return cls.min_cycle,cls.max_cycle,cls.total_time,cls.counter,cls.succ,cls.fail,cls.ext

	def update_stat(self, t, keys, prefix='', server='', cmd='get'):
		self.__class__.min_cycle = min(self.min_cycle,t)
		if t > self.__class__.max_cycle:
			self.__class__.max_cycle = t
			self.__class__.ext = '%s:(%s)%s+%s'%(cmd,str(server),prefix,str(keys))
		self.__class__.total_time += t
		self.__class__.counter += 1
		self.__class__.succ += 1

