# Postgres Listener, writes out flatfiles when SQL NOTIFYs are triggered
# Copyright (C) 2008 Dafydd Harries <dafydd.harries@collabora.co.uk>
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

class MailingList(PgListener):
    def do_format(self, row):
        return row + '\n'

    def do_write(self, result, target):
        if not os.path.exists(target):
            os.mkdir(target)

        lists = {}

        for list, emailaddress in result:
            if list not in lists:
                lists[list] = []

            lists[list].append((emailaddress))

        for list, values in lists.iteritems():
            PgListener.do_write(self, values,
                os.path.join(target, list))

        # Remove old files.

        for name in os.listdir(target):
            if name in ('.', '..'):
                continue

            if name not in lists:
                path = os.path.join(target, name)

                try:
                    os.unlink(path)
                except OSError:
                    self.log(syslog.LOG_WARNING, "failed to unlink %s" % path)

