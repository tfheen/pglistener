from ConfigParser import SafeConfigParser

import sys,os

cf = SafeConfigParser()

if (not os.path.exists(sys.argv[1])):
  print "ERROR: File not found: %s" % sys.argv[1]
cf.read(sys.argv[1])

for section in cf.sections():
 
  # Import the appropriate class
  # Module name = lower of class name
  classname = cf.get(section,"class")

  if (not os.path.exists(classname.lower() + ".py")):
    print "ERROR: Module not found: %s" % classname
  exec("from %s import %s" % (classname.lower(),classname))
  listener = eval("%s(%s)" % (classname,cf.get(section,"DSN")))
  listener.monitor()


