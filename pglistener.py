import sys, psycopg

import select, time, os, signal, errno, stat

class PgListener:
  def __init__(self):
    self.name=""
    self.notifications=[]
    self.query=""
    self.format=""
    self.format_code=""
    self.destination=""
    self.posthooks=[]
    self.cursor=""

  def log(self,msg):
    print "%s: %s" % (self.name, msg)

  def do_query(self):
    self.cursor.execute(self.query)
    return self.cursor.fetchall()

  def do_format(self,row):
    return self.format % row

  def do_write(self,result,target):
    f = open(target,"w+")
    for row in result:
      f.write(self.do_format(row))
    f.close

  def do_perms(self, target):
    orig = os.stat(self.destination)
    os.chmod(target, orig[stat.ST_MODE])
    try:
      os.chown(target, orig[stat.ST_UID], orig[stat.ST_GID])
    except select.error, (errno, strerror):
      self.log("Failed to chmod new file: %s" % strerror)

  def do_update(self):
    target = self.destination+"~"
    result = self.do_query()

    self.do_write(result, target)
    self.do_perms(target)

    self.log("Updating: %s" % self.destination)
    os.rename(target, self.destination)

  def do_posthooks(self):
    for hook in self.posthooks:
      self.log("Executing: %s" % hook)
      os.system(hook)

  def get_notifies (self):
    cursor = self.cursor

    time.sleep(0.1)
    cursor.execute("select 1")
    return cursor.notifies()

  def monitor (self):
    cursor = self.cursor
    self.log("Starting monitor for %s" % self.destination)

    self.force_update = False
    def handle_usr1(signo, frame): self.force_update = True
    signal.signal(signal.SIGUSR1, handle_usr1)

    for n in self.notifications:
      self.log("Listening for: %s" % n)
      cursor.execute("listen %s" % n)

    self.do_update()
    notifications = []
    while 1:
      while notifications or self.force_update:
        if self.force_update:
          self.log("Got SIGUSR1, forcing update.")
          self.force_update = False
        else:
          self.log("Got: %s" % notifications)
        self.do_update()
        notifications = self.get_notifies();

      self.do_posthooks()

      try:
        select.select([cursor],[],[])
      except select.error, (err, strerror):
        if err == errno.EINTR:
          pass
        else:
          raise
      else:
        notifications = self.get_notifies()
