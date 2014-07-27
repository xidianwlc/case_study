#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# Abstract: MySQLdb & Model

import time
import json
import MySQLdb
import logging
from conf.settings import DB_CNF,options

class Mysql(object):
    """
    MySQLdb Wrapper
    """
    min_cycle,max_cycle,total_time,counter,succ,fail,ext = 0xffffL,0L,0L,0L,0L,0L,''
    def __init__(self, dba, ismaster=False):
        self.dba = dba
        self.ismaster = ismaster 
        self.conn = None
        self.cursor = None
        self.curdb = ""  
        self.connect(dba)
        self.reset_stat()
    
    def __del__(self):
        self.close()

    def __repr__(self):
        return "Mysql(%s)"%(str(self.dba),)

    def __str__(self):
        return "Mysql(%s)"%(str(self.dba),)
   
    def close(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def connect(self, dba):
        """
        connect to mysql server
        """
        self.dba = dba
        self.conn = MySQLdb.connect(host=str(dba['host']),user=str(dba['user']),passwd=str(dba['passwd']),db=str(dba['db']),unix_socket=str(dba['sock']),port=dba['port'])
        self.cursor = self.conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        self.execute("set names 'utf8'")
        self.execute("set autocommit=1")
        self.curdb = dba['db']
        return True
    
    def auto_reconnect(self):
        """
        ping mysql server
        """
        try:
            self.conn.ping()
        except Exception,e:
            try:
                self.cursor.close()
                self.conn.close()
            except:
                pass
            self.connect(self.dba)
        return True
    
    def execute(self, sql, values=()):
        """
        execute sql
        """
        if not self.ismaster and self.isupdate(sql):
            raise Exception("cannot execute[%s] on slave"%(sql,))
        start = time.time()
        self.auto_reconnect()
        if options.debug:
            logging.info('%s,%s',sql,values)
        if sql.upper().startswith("SELECT"):
            result = self.cursor.execute(sql,values)
        else:
            result = self.cursor.execute(sql)
        self.update_stat((time.time()-start)*1000,sql,values)
        return True

    def update_stat(self, t, sql, values):
        self.__class__.min_cycle = min(self.min_cycle,t)
        if t > self.__class__.max_cycle:
            self.__class__.max_cycle = t
            self.__class__.ext = '%s%%%s'%(sql,str(values))
        self.__class__.total_time += t
        self.__class__.counter += 1
        self.__class__.succ += 1

    @classmethod 
    def reset_stat(cls):
        cls.min_cycle,cls.max_cycle,cls.total_time,cls.counter,cls.succ,cls.fail,cls.ext = 0xffffL,0L,0L,0L,0L,0L,''

    @classmethod 
    def stat(cls):
        return cls.min_cycle,cls.max_cycle,cls.total_time,cls.counter,cls.succ,cls.fail,cls.ext

    def isupdate(self, sql):
        """
        """
        opers = ("INSERT","DELETE","UPDATE","CREATE","RENAME","DROP","ALTER","REPLACE","TRUNCATE")
        return sql.strip().upper().startswith(opers)

    def use_dbase(self, db):
        if self.curdb != db:
            self.execute("use %s"%(db,))
            self.curdb = db
        return True
     
    @classmethod
    def create_sql(cls, sql, params, noescape=""):
        """
        create sql acorrding to sql and params
        """
        result = sql;
        for each in params:
            val = params[each]
            if noescape=="" or  noescape.find(each)<0:
                val = MySQLdb.escape_string(str(val))
            result = result.replace(each,val)
        return result;

    @classmethod
    def merge_sql(cls, where, cond):
        """
        merge subsqls
        """
        return "%s AND %s"%(where,cond) if where and cond else (where or cond)
       
    def rows( self ):
        return self.cursor.fetchall()
    
    @property
    def lastrowid(self):
        return self.cursor.lastrowid
    
    def affected_rows(self):
        return self.conn.affected_rows()

    def connection( self ):
        return self.conn

class MysqlPool(object):
    """
    MySQLPool
    """
    def __init__(self, dbcnf):
        self.mcnf,self.scnf = {},{}
        for i in dbcnf['m']:
            for j in dbcnf['m'][i]:
                self.mcnf[j] = json.loads(i)
        for i in dbcnf['s']:
            for j in dbcnf['s'][i]:
                self.scnf[j] = json.loads(i)
        self.mpool,self.spool = {},{}
    
    def get_server(self, db, dbgroup, ismaster=False):
        cnf = (self.mcnf if ismaster else self.scnf)[dbgroup]
        cnf['db'] = db
        dbastr = '%s:%s:%s'%(cnf['host'],cnf['port'],cnf['db'])
        pool = self.mpool if ismaster else self.spool
        if dbastr not in pool:
            logging.info('--->get_server:%s,%s,%s,%s',db,dbgroup,dbastr,len(pool))
            pool[dbastr] = Mysql(cnf,ismaster=ismaster)
        return pool[dbastr]

    def disconnect_all(self):
        for i in self.mpool:
            self.mpool[i].close()
        for i in self.spool:
            self.spool[i].close()
 
class Model(dict):
    """
    Model
    """
    _db = ""
    _table = ""
    _fields = set()
    _extfds = set()
    _pk = ""
    _scheme = ()
    _engine = "InnoDB"
    _charset = "utf8"
    def __init__(self, obj={}, db=None, ismaster=False, **kargs):
        self.ismaster = ismaster 
        self.db = db or self.dbserver(**kargs)
        super(Model,self).__init__(obj)
        self._changed = set()

    def dbserver(self, **kargs):
        db,group = self.get_dbase(**kargs),self.get_db_group(**kargs)
        return self.dpool.get_server(db,group,self.ismaster)

    def property_copy(self,source):
        if source:
            source = dict(source)
            dist = dict(self)
            dist.update(source)
            return dist
        return {}
    @property
    def dpool(self):
        if not hasattr(Model,'_dpool'):
            Model._dpool = MysqlPool(DB_CNF)
        return Model._dpool
        
    def __getattr__(self, name):
        if name in self._fields or name in self._extfds:
            return self.__getitem__(name)
    
    def __setattr__(self, name, value):
        flag = name in self._fields or name in self._extfds
        if name != '_changed' and flag and hasattr(self, '_changed'):
            if name in self._fields:
                self._changed.add(name)
            super(Model,self).__setitem__(name,value)
        else:
            self.__dict__[name] = value

    def __setitem__(self, name, value):
        if name != '_changed' and name in self._fields and hasattr(self, '_changed'):
            self._changed.add(name)
        super(Model,self).__setitem__(name,value)

    def __delattr__(self, name):
        self.__delitem__(name)

    def init_table(self, **kargs):
        dbase = self.get_dbase(**kargs)
        if not self.is_dbase_exist(**kargs):
            self.db.execute("CREATE DATABASE %s"%(dbase,))
        if not self.is_table_exist(**kargs):
            self.db.use_dbase(dbase)
            scheme = ",".join(self._scheme)
            sql = "CREATE TABLE `%s` (%s)ENGINE=%s DEFAULT CHARSET=%s"
            self.db.execute(sql%(self.get_table(**kargs),scheme,self._engine,self._charset))
        return True

    def drop_table(self, **kargs):
        dbase = self.get_dbase(**kargs)
        if not self.is_dbase_exist(**kargs):
            raise Exception('%s not exist'%dbase)
        if self.is_table_exist(**kargs):
            self.db.use_dbase(dbase)
            sql = "DROP TABLE `%s`"%self.get_table(**kargs)
            self.db.execute(sql)
        return True

    def replace(self):
        self.db.use_dbase(self.get_dbase(**self))
        sql = self.replace_sql()
        self.db.execute(sql)
        if self._pk and self._pk not in self:
            self[self._pk] = self.db.lastrowid
        return self 
        
    def before_add(self):
        pass

    def add(self):
        self.before_add()
        self.db.use_dbase(self.get_dbase(**self))
        sql = self.insert_sql()
        self.db.execute(sql)
        if self._pk and self._pk not in self:
            self[self._pk] = self.db.lastrowid
        return self 
     
    def before_update(self):
        pass

    def update(self, unikey=None):
        if self._changed:
            self.before_update()
            self.db.use_dbase(self.get_dbase(**self))
            sql = self.update_sql(unikey)
            self.db.execute(sql)
        return True
 
    def save(self):
        if self.get(self._pk,""):
            self.update()
        else:
            self.add()
        return self
   
    def before_delete(self):
        pass

    def delete(self, unikey=None):
        self.before_delete()
        self.db.use_dbase(self.get_dbase(**self))
        sql = self.delete_sql(unikey)
        self.db.execute(sql)
        return True
    def delete_sql_batch(self,**kargs):
        '''
        批量删除sql：
        kargs：删除条件.格式：{"parent_id":[14,13,15],"type":5}
        '''
        obj = self
        table = self.get_table(**obj)
        if type(kargs) != dict:
            raise Exception(" parameter must be dict ,found %s"%(type(kargs)))
        condition = ""
        if kargs:
            for key in kargs:
                if condition:
                    condition += " AND "
                if type(kargs[key])==list:
                    condition += "`%s` in (%s)" %(key,','.join(value for value in kargs[key]))
                else:
                    condition += "`%s`='%s'" %(key,kargs[key])
        if 'disable' in self._fields:
            sql = "update %s set disable = 1 WHERE %s " % (table, condition)
        else:
            sql = "DELETE FROM %s WHERE %s" % (table, condition)
        return sql
        
    def delete_batch(self,if_del_bef=True,**kargs):
        '''
        if_del_bef 是否执行before_delete方法：默认执行
        kargs：删除条件.格式：{"parent_id":[14,13,15],"type":5}
        '''
        if if_del_bef:
            self.before_delete()
        self.db.use_dbase(self.get_dbase(**self))
        sql = self.delete_sql_batch(**kargs)
        self.db.execute(sql)
        return True

    @classmethod
    def mgr(cls, ismaster=False, **kargs):
        return cls(ismaster=ismaster,**kargs)

    @classmethod
    def new(cls, ismaster=True, **kargs):
        return cls(ismaster=ismaster,**kargs)

    def one(self, pk):
        return self.Q().filter(id=pk)[0]

    def Q(self, **kargs):
        """
        Query
        """
        return Query(self,**kargs)
        
    def select(self, where, **kargs):
        table = self.get_table(**kargs)
        sql = self.select_sql(table,where)
        self.db.use_dbase(self.get_dbase(**kargs))
        self.db.execute(sql)
        return self.db.rows()
  
    def raw(self, sql, values=(), **kargs):
        """
        execute raw sql
        """
        self.db.use_dbase(self.get_dbase(**kargs))
        self.db.execute(sql,values)
        return self.db.rows()
        
    @property
    def lastrowid(self):
        return self.db.lastrowid

    def get_db_group(self, **kargs):
        """
        get db group
        """
        return self._db

    def get_dbase(self, **kargs):
        """
        get db name
        """
        return self._db
        
    def get_table(self, **kargs):
        """
        get table name
        """
        return self._table
        
    def is_dbase_exist(self, **kargs):
        dbase = self.get_dbase(**kargs)
        sql = "select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = '%s'"
        self.db.execute(sql%(dbase,))
        rows = self.db.rows()
        return True if rows else False

    def is_table_exist(self, **kargs):
        """
        判断表是否已经存在
        """
        dbname = self.get_dbase(**kargs)
        tablename = self.get_table(**kargs)
        values = (tablename,dbname)
        sql = "select TABLE_NAME from information_schema.TABLES where TABLE_NAME='%s' AND TABLE_SCHEMA='%s'"
        self.db.execute(sql%values)
        rows = self.db.rows()
        return True if rows else False

    def insert_sql(self):
        obj = self
        table = self.get_table(**obj)
        domains = ','.join(["`%s`"%(e,) for e in obj if e in self._fields])
        values  = ','.join(["'%s'"%(MySQLdb.escape_string(str(obj[e])),) for e in obj if e in self._fields])
        return "INSERT INTO %s (%s) VALUES (%s)" % (table, domains, values)
    
    def insert_batch(self, sql=None, values=None, **kargs):
        '''
        批量导入操作
        sql = "insert into bk_comment(title) values(%s)"
        values = [('ninini'), ('koko')]
        kargs:如果有多组sql和values的组合，[{"sql":sql,"values":values},{"sql":sql,"values":values}]方式保存为kargs
        优先支持第一种方式
        '''
        cursor = None
        try:
            self.db.auto_reconnect()
            cursor=self.db.conn.cursor()
            #self.db.execute("set autocommit=0")
            sum = 0
            count = 0
            circle = 1000
            
            if sql and values:
                while sum < len(values):
                    temp_values = values[count*circle:(count+1)*circle-1]
                    sum = (count+1)*circle-1
                    count += 1
                    cursor.executemany(sql,temp_values)
            else:
                for lst in kargs['kargs']:
                    #每次循环开始，sum,count重新初始化
                    sum,count =0,0            
                    sql = lst['sql']
                    values = lst['values']
                    while sum < len(values):
                        temp_values = values[count*circle:(count+1)*circle-1]
                        sum = (count+1)*circle-1
                        count +=1
                        cursor.executemany(sql,temp_values)
        except Exception,e:
            logging.error("------%s" %str(e), exc_info=True)

    def replace_sql(self):
        obj = self
        table = self.get_table(**obj)
        domains = ','.join(["`%s`"%(e,) for e in obj if e in self._fields ])
        values  = ','.join(["'%s'"%(MySQLdb.escape_string(str(obj[e])),) for e in obj if e in self._fields])
        return "REPLACE INTO %s (%s) VALUES (%s)" % (table, domains, values)
        
    def update_sql(self, unikey=None):
        obj = self
        table = self.get_table(**obj)
        uni = unikey or self._pk
        values_up  = ','.join(["`%s`='%s'"%(e,MySQLdb.escape_string(str(obj[e])),) for e in obj if e!=uni and e in self._changed])
        return "UPDATE %s SET %s WHERE `%s`='%s'" % (table, values_up, uni, str(obj[uni]))
    
    def delete_sql(self, unikey=None):
        obj = self
        table = self.get_table(**obj)
        uni = unikey or self._pk
        if obj.has_key('disable'):
            sql = "update %s set disable = 1 WHERE `%s`='%s'" % (table, uni, obj[uni])
        else:
            sql = "DELETE FROM %s WHERE `%s`='%s'" % (table, uni, obj[uni])
        return sql
        
    def select_sql(self, table, where):
        return "SELECT * FROM %s %s %s" % (table, where and "WHERE" or "", where)

class Query(object):
    """
    """
    def __init__(self, model=None, qtype="SELECT *", **kargs):
        self.model = model 
        self.cache = None
        self.qtype = qtype
        self.conditions = {}
        self.limit = ()
        self.extras = []
        self.order = ""
        self.group = ""
        self.placeholder = "%s"
        self.kargs = kargs  # used to choose table & dbase
    def __getitem__(self, k):
        if self.cache:
            return self.cache[k]
        if isinstance(k, (int, long)):
            self.limit = (k,1)
            lst = self.data()
            if not lst:
                return None
            return lst[0]
        elif isinstance(k, slice):
            if k.start is not None:
                assert k.stop is not None, "Limit must be set when an offset is present"
                assert k.stop >= k.start, "Limit must be greater than or equal to offset"
                self.limit = k.start, (k.stop - k.start)
            elif k.stop is not None:
                self.limit = 0, k.stop
        return self.data()

    def __len__(self):
        return len(self.data())

    def __iter__(self):
        return iter(self.data())
                                    
    def __repr__(self):
        return repr(self.data())

    def filter(self, **kwargs):
        self.cache = None
        self.conditions.update(kwargs)
        return self
 
    def extra(self, *args):
        self.cache = None
        self.extras.extend([e for e in args if e])
        return self

    def orderby(self, field, direction='ASC'):
        self.cache = None
        self.order = 'ORDER BY `%s` %s' % (field, direction)
        return self
    
    def orderbys(self,fields):
        self.cache = None
        self.order = 'ORDER BY %s ' % (fields)
        return self
    
    def groupby(self, field):
        self.cache = None
        self.group = 'GROUP BY `%s`' % (field,)
        return self

    def set_limit(self, start, size):
        self.limit = start, size
        return self

    def get_condition_keys(self):
        where = ""
        if self.conditions:
            where = ' AND '.join("`%s`=%s" % (k, self.placeholder) for k in self.conditions)
        if self.extras:
            where = Mysql.merge_sql(where,' AND '.join([i.replace('%','%%') for i in self.extras]))
        if 'disable' in self.model._fields:
            if where:
                where += ' AND disable=0'
            else:
                where += ' disable=0'
        return "WHERE %s"%(where,) if where else ""

    def get_condition_values(self):
        return list(self.conditions.itervalues())

    def query_template(self):
        return '%s FROM %s %s %s %s %s' % (
                self.qtype,
                self.model.get_table(**self.kargs),
                self.get_condition_keys(),
                self.group,
                self.order,
                self.get_limit(),
                )

    def get_limit(self):
        return "LIMIT %s"%', '.join(str(i) for i in self.limit) if self.limit else ""

    def count(self):
        if self.cache is None:
            _qtype = self.qtype
            self.qtype = 'SELECT COUNT(1) AS CNT'
            rows = self.query()
            self.qtype = _qtype
            return rows[0]["CNT"] if rows else 0
        else:
            return len(self.cache)

    def data(self):
        if self.cache is None:
            self.cache = list(self.iterator())
        return self.cache

    def iterator(self):     
        for row in self.query():
            obj = self.model.__class__(row,db=self.model.db,ismaster=self.model.ismaster)
            yield obj

    def query(self):
        values = self.get_condition_values()
        return self.model.raw(self.query_template(),values,**self.kargs)

