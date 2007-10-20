import sys, psycopg
from pglistener import PgListener
import select, time, os, signal, errno, stat
from syslog import *

import dbhash

class SimpleDBM(PgListener):
  def do_write(self,result,target):
    
    db=dbhash.open(target,"n")
    for row in result:
      db[row[0]]=row[1]
    db.sync()

