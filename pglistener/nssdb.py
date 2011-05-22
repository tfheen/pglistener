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

from pglistener import PgListener

import bsddb, os

class NssDb(PgListener):
  def do_write(self,result,target):
    db_keys = self.options['db-keys']
    db = bsddb.btopen("%s.tmp" % (target, ), "n")
    index = 0

    for row in result:
      entry = self.do_format(row) + '\0'

      for field in db_keys.keys():
        db[db_keys[field] % row[field]] = entry

      db["0%d" % index] = entry

      index += 1

    db.sync()
    db.close()
    os.rename("%s.tmp" % (target, ), target)
