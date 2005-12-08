from ConfigParser import SafeConfigParser

import sys,os


cf = SafeConfigParser()

configfile=sys.argv[1]
section=sys.argv[2]

if (not os.path.exists(configfile)):
  print "ERROR: File not found: %s" % configfile
cf.read(configfile)

if section:
  
  # Import the appropriate class
  # Module name = lower of class name
  classname = cf.get(section,"class")

  if (not os.path.exists(classname.lower() + ".py")):
    print "ERROR: Module not found: %s" % classname
  exec("from %s import %s" % (classname.lower(),classname))
  options=dict(cf.items(section))
  print options
  options['notifications']=eval(options['notifications'])
  options['posthooks']=eval(options['posthooks'])
  options['name']=section
  listener = eval("%s(%s)" % (classname,options))


