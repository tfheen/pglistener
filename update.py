#!/usr/bin/env python

import sys

from pglistener import config

def main(argv):
    configfile = argv[1]
    sections = argv[2:]

    listeners = dict([(l.name, l) for l in
        config.read_config(configfile)])

    if not sections:
        sections = listeners.keys()

    for section in sections:
        listeners[section].connect()
        listeners[section].do_update()

if __name__ == '__main__':
    main(sys.argv)

