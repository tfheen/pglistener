#!/usr/bin/env python

from ConfigParser import SafeConfigParser

import sys,os
import thread

def createDaemon():
  pid = os.fork()

  # exit parent
  if pid != 0:
    os._exit(0)

  # become session leader
  os.setsid()

  pid = os.fork()

  # exit first child
  if pid != 0:
    os._exit(0)

  return

if 0:
  # find max number of FDs
  if (os.sysconf_names.has_key("SC_OPEN_MAX")):
    maxfd = os.sysconf("SC_OPEN_MAX")
  else:
    maxfd = 1024

  # close all FDs
  for fd in range(0, maxfd):
    try:
      os.close(fd)
    except OSError:
      pass

  if (hasattr(os, "devnull")):
    redirect_to = os.devnull
  else:
    redirect_to = "/dev/null"

  os.open(redirect_do, os.O_RDWR)
  os.dup2(0, 1)
  os.dup2(0, 2)

sys.path.append("src")

cf = SafeConfigParser()

configfile=sys.argv[1]

if (not os.path.exists(configfile)):
  os.exit("ERROR: File not found: %s" % configfile)

cf.read(configfile)

createDaemon()

for section in cf.sections():

  print section

  # Import the appropriate class
  # Module name = lower of class name
  classname = cf.get(section,"class")

  exec("from %s import %s" % (classname.lower(),classname))
  options=dict(cf.items(section))
  print options
  options['notifications']=eval(options['notifications'])
  options['posthooks']=eval(options['posthooks'])
  options['name']=section

  pid = os.fork()
  if pid == 0:
    listener = eval("%s(%s)" % (classname,options))
    break

