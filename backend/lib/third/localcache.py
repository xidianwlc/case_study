# -*- coding: utf-8 -*-
#
# Copyright(c) 2010 poweredsites.org
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import hashlib
from time import time

_mem_caches = {}

def mem_cache(expire=7200, key="", maxlen=100000,start=0):
	"""Mem cache to python dict by key"""
	def wrapper(func):
		def mem_wrapped_func(*args, **kwargs):
			now = time()
			if key:
				c = key
			else:
				c = repr(func)
			k = key_gen(c, *args[start:], **kwargs)

			value = _mem_caches.get(k, None)
			if _valid_cache(value, now):
				return value["value"]
			else:
				val = func(*args, **kwargs)
				assert len(str(val))<=maxlen
				_mem_caches[k] = {"value":val, "expire":now+expire}

				return val

		return mem_wrapped_func
	return wrapper

def purge_mem():
	global _mem_caches
	count = len(_mem_caches)
	_mem_caches = {}
	return count

def key_gen(key, *args, **kwargs):
	code = hashlib.md5()

	code.update(str(key))
	code.update("".join(sorted(map(str, args))))
	code.update("".join(sorted(map(str, kwargs.iteritems()))))

	return code.hexdigest()

def _valid_cache(value, now):
	if value:
		if value["expire"] > now:
			return True
		else:
			return False
	else:
		return False

