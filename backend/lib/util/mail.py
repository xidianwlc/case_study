#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# Abstract: send mail

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

class Mail(object):
	def __init__(self, smtp, user, pwd):
		self.smtp = smtp
		self.user = user 
		self.pwd  = pwd
		self.isauth= True

	def parse_send(self, subject, content, plugin):
		return subject, content, plugin  

	def send(self, subject, content, tolist, cclist=[], plugins =[]):
		msg = MIMEMultipart()
		msg.set_charset('utf-8')
		msg['from'] = self.user
		msg['to'] = ','.join(tolist)
		if cclist:
			msg['cc'] = ','.join(cclist)
		msg['subject'] = subject 
		msg.attach( MIMEText(content,'html','utf-8'))
		for plugin in plugins:
			f = MIMEApplication(plugin['content'])
			f.add_header('content-disposition','attachment',filename=plugin['subject'])
			msg.attach(f)
		
		s = smtplib.SMTP(self.smtp)
		s.set_debuglevel(smtplib.SMTP.debuglevel)
		if self.isauth:
			s.docmd("EHLO %s"%self.smtp)
		try:
			s.starttls()
		except smtplib.SMTPException,e:
			pass
		s.login(self.user,self.pwd)
		r = s.sendmail(self.user,tolist,msg.as_string())
		s.close()
		return r

if __name__=="__main__" :
	subject = '发送邮件测试'
	content = '<font color="#0000FF">热门</color>'
	plugins = [{'subject':'附件1.txt','content':'内容1'},{'subject':'附件2.txt','content':'内容2'}]
	mail = Mail('smtp.exmail.qq.com','liangnaichen@duokan.com','xxxxxx' )
	tolist = ['laogouliang@163.com']
	cclist = []
	mail.send(subject,content,tolist,cclist,plugins)
	print 'duokan mail send' 

