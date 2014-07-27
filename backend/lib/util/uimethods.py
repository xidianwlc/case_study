#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime

def strftime(handler, dtime, fmt='%Y-%m-%d'):
    return dtime.strftime(fmt)
    
def jsondump(handler, obj):
	import json
	return json.dumps(obj)

def base64_url(handler, url):
	import base64
	return base64.b64encode(url)

def extract_url(handler, url):
	return url.split("http://")[1].split("/")[0]

def formatdate(handler, obj=None, format="%Y-%m-%d %H:%M:%S"):
	from datetime import datetime
	res = datetime.now() if not obj else obj
	return res.strftime(format)

def number_parity(handler, number):
	# check a number is an odd number or an even number
	if number % 2 == 0:
		return 'odd'
	else:
		return 'even'

def stc_url(handler, uri):
	return 'stc/%s'%uri

def touch_resource(handler, args):
    if handler.current_user:
        return handler.current_user.touch_resource(args)
    return False

def has_perm(handler, oper, resource, **attr):
    if handler.current_user:
        return handler.current_user.has_perm(oper,resource,**attr)
    return False

def wrap_url(handler, url, escape=False):
    return handler.wrap_url(url,escape)

def wrap_static_url(handler, uri):
    uri = '/static/%s' % uri
    return handler.wrap_url(uri,need_target=False)

def parse_widget_ranges(handler, ranges):
    return [i.split(':') for i in ranges.split(',') if len(i.split(':'))==2]

def truncate(handler, content, length=10):
    suffix = ''
    if not isinstance(content,unicode):
        content = content.decode('utf-8')
        suffix = '...' if len(content)>length else ''
    return content[:length].encode('utf-8') + suffix

def extract_ad_image_size(handler, path):
    arr = path.split(os.path.sep)
    return arr[-2] if len(arr)>=2 else ''

