#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib
import datetime
import tornado.web
uibase = tornado.web.UIModule

class BasicQueryCond(uibase):
	def render(self, platform_id, run_id, plan_id, partner_id, version_name, product_name,
               run_list, plan_list, date=None, unique=None, start=None):
		return self.render_string("ui_mod/basic_query_cond.html",
			platform_id = platform_id,
			run_id = run_id,
			plan_id = plan_id,
			partner_id = partner_id,
			version_name = version_name,
			product_name = product_name,
			run_list = run_list,
			plan_list = plan_list,
			date = date,
			start = start,
			unique = unique,
		)

class FactoryQueryCond(uibase):
	def render(self, factory_list,factory_id, product_name, query_mode=None, start=None, date=None):
		return self.render_string("ui_mod/factory_query_cond.html",
			start = start,
			date = date,
			factory_list = factory_list,
			factory_id = factory_id,
			product_name = product_name,
			query_mode = query_mode,
		)

class MyHomeModule(uibase):
	def render(self):
		return self.render_string("ui_mod/myhome.html")

class Pagination(uibase):
	def render(self, count, page, psize, target_type='navTab'):
		return self.render_string("ui_mod/pagination.html",
			count = count,
			page = page,
			psize = psize,
			target_type = target_type
		)

class ProductConfData(uibase):
    def render(self, pconf_data,method):
        return self.render_string('product/conf_data.html',
                    pconf_data = pconf_data,method=method)

class ProductChannelData(uibase):
    def render(self, channel_data):
        return self.render_string('product/channel_data.html',
                 scheme_dict = channel_data['scheme_dict'],
                 cur_schemeid_list = channel_data['cur_schemeid_list'],
                 channel_dict = channel_data['channel_dict'])

class PriceChapterBvalue(uibase):
    def render(self, btype, bvalue=0):
        return self.render_string('price/chapter_bvalue.html',
                   btype = btype,
                   bvalue = bvalue)

class CampaignConfData(uibase):
    def render(self, pconf_data,method):
        return self.render_string('campaign/conf_data.html',
                    pconf_data = pconf_data,method=method)


