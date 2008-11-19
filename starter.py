#!/usr/bin/env python

# Postgres Listener, writes out flatfiles when SQL NOTIFYs are triggered
# Copyright (C) 2005 Rob Bradford <rob@robster.org.uk>
# Copyright (C) 2007-8 Robert McQueen <robert.mcqueen@bluelinux.co.uk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from ConfigParser import RawConfigParser

import os
import sys

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
    if 'SC_OPEN_MAX' in os.sysconf_names:
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

def read_config(path):
    cf = RawConfigParser()
    cf.read(path)

    for section in cf.sections():
        classname = cf.get(section, 'class')
        cls = getattr(__import__(classname.lower()), classname)

        options = dict(cf.items(section))
        options['name'] = section
        options['notifications'] = eval(options['notifications'])

        yield (cls, options)

def main(argv):
    sys.path.append("src")

    configfile = sys.argv[1]

    if (not os.path.exists(configfile)):
        print "ERROR: File not found: %s" % configfile
        return 1

    config = list(read_config(configfile))
    createDaemon()

    for cls, options in config:
        pid = os.fork()

        if pid == 0:
            cls(options)
            break

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

