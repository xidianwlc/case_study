#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# Abstract: excel operation

import os
import random
import string
import datetime
import xlrd
import xlwt

class Excel(object):
    '''
    excel processing
    '''
    def __init__(self, home='/tmp'):
        self.home = home 

    def load(self, file_name):
        '''
        assume the first line is title
        file_name: file name
        '''
        title,data = [],[]
        work_book = xlrd.open_workbook(file_name)
        sheet = work_book.sheet_by_index(0)
        for c in xrange(sheet.ncols):
            title.append(shell.cell(0,c).value)
        for r in xrange(1,sheet.nrows):
            unit = {}
            for c in xrange(sheet.ncols):
                unit[title[c]] = sheet.cell(r,c).value
            data.append(unit)
        return data
    
    def generate(self, title, data, sep=1, callback=None):
        '''
        generate excel content
        title: excel title
        data: data result，list
        sep: width ratio
        '''
        work_book =  xlwt.Workbook('UTF-8')
        sheet = work_book.add_sheet('sheet', True)       
        ncols = len(title)
        # write title
        title_style = self.get_title_style()
        for j in xrange(ncols):
            sheet.col(j).width = 3333*sep
            sheet.write(0,j,title[j][1],title_style)
        nrows = len(data)
        text_style = self.get_text_style()
        for i in xrange(nrows):
            for j in xrange(ncols):
                key = title[j][0]
                val = callback(data[i],key) if callback else data[i].get(key,'') 
                if isinstance(val,datetime.datetime):
                    val = val.strftime('%Y-%m-%d')
                sheet.write(i+1,j,val,text_style)
        filename = self.tmp_filename()
        work_book.save(filename)
        content = ''
        with open(filename,'rb') as f:
            content = f.read()
        os.remove(filename)
        return content
        
    def tmp_filename(self):
        return os.path.join(self.home,''.join(random.sample(string.lowercase,10)))
    
    def get_title_style(self):
        '''
        excel title style
        '''
        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True        
        style.font = font
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        style.alignment = alignment
        return style
    
    def get_text_style(self):
        '''
        excel text style
        '''
        style = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        style.alignment = alignment
        return style
    
if __name__ == '__main__': 
    title = [('name','姓名'),('age','年龄'),('gender','性别')]
    data = [{'name':'liangsix','age':10,'gender':'男'},{'name':'梁六','age':12,'gender':'男'}]
    f = open('test.xls','wb')
    f.write(Excel().generate(title,data))
    f.close()

