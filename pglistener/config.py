
import sys

from ConfigParser import RawConfigParser

def read_config(path):
    cf = RawConfigParser()
    cf.read(path)

    for section in cf.sections():
        classname = cf.get(section, 'class')
        modname = 'pglistener.%s' % classname.lower()
        __import__(modname)
        cls = getattr(sys.modules[modname], classname)

        options = dict(cf.items(section))
        options['name'] = section
        options['notifications'] = [
            n.strip() for n in options['notifications'].split(',')]

        yield cls(options)
