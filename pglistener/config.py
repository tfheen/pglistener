
import glob
import os
import sys

from ConfigParser import RawConfigParser

def expand_dirs(paths):
    file_paths = []

    for path in paths:
        if os.path.isdir(path):
            file_paths.extend([
                p for p in glob.glob('%s/*.cfg' % path)
                if os.path.isfile(p)])
        else:
            file_paths.append(path)

    return file_paths

def read_configs(paths):
    file_paths = expand_dirs(paths)
    cf = RawConfigParser()

    if cf.read(file_paths) != file_paths:
        raise RuntimeError("couldn't read config file")

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

