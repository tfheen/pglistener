#!/usr/bin/env python

from ConfigParser import SafeConfigParser

import sys,os
import thread

sys.path.append("src")

cf = SafeConfigParser()

configfile=sys.argv[1]

if (not os.path.exists(configfile)):
  print "ERROR: File not found: %s" % configfile
cf.read(configfile)

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
    pid = os.fork()
    if pid == 0:
      listener = eval("%s(%s)" % (classname,options))

