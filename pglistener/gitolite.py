# Postgres Listener, writes out flatfiles when SQL NOTIFYs are triggered                                  
# Copyright (C) 2008 Collabora Ltd.
# Copyright (C) 2013 Varnish Software AS
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
import hashlib

from sshkeys import SshKeys

class Gitolite(SshKeys):
    def do_write(self, result, target):
        if not os.path.exists(target):
            os.mkdir(target)

        fnames = []

        for username, key_type, key_base64, comment in result:
            fname = "{0}.{1}.pub".format(username,
                                         hashlib.md5(key_base64).hexdigest())
            fnames.append(fname)
            self.write_file(os.path.join(target, fname),
                            lambda fh: fh.write(self.do_format([key_type, key_base64, comment])))

        # Remove old files.                                                                               

        for name in os.listdir(target):
            if name in ('.', '..'):
                continue

            if name not in fnames:
                path = os.path.join(target, name)
                try:
                    os.unlink(path)
                except OSError:
                    self.err("failed to unlink %s" % path)
