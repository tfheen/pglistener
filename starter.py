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

import os
import sys

from pglistener import config, daemon

def main(argv):
    configfile = argv[1]
    listeners = list(config.read_config(configfile))

    for listener in listeners:
        listener.try_connect()
        listener.listen()
        listener.do_update()
        listener.do_posthooks()

    daemon.daemonize()
    daemon.loop(listeners)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

