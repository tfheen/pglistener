# Postgres Listener, writes out flatfiles when SQL NOTIFYs are triggered
# Copyright (C) 2008 Collabora Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import syslog

from pglistener import PgListener

class SshKeys(PgListener):
    def do_format(self, row):
        return ' '.join(row) + '\n'

    def do_write(self, result, target):
        if not os.path.exists(target):
            os.mkdir(target)

        keys = {}

        for username, key_type, key_base64, comment in result:
            if username not in keys:
                keys[username] = []

            keys[username].append((key_type, key_base64, comment))

        for username, values in keys.iteritems():
            PgListener.do_write(self, values,
                os.path.join(target, username))

        # Remove old files.

        for name in os.listdir(target):
            if name in ('.', '..'):
                continue

            if name not in keys:
                path = os.path.join(target, name)

                try:
                    os.unlink(path)
                except OSError:
                    self.log(syslog.LOG_WARNING, "failed to unlink %s" % path)

