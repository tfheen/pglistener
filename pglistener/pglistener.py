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

import errno
import os
import select
import stat
import syslog
import time

import psycopg2

class PgListener:
    def __init__(self, options):
        """Creates object and make connection to server and setup a cursor for
        the connection."""
        self.sleeptime = 0
        self.options = options
        self.name = options['name']
        self.dsn = options['dsn']
        self.query = options['query']
        self.notifications = options['notifications']
        self.destination = options['destination']
        self.conn = None

    def try_connect(self):
        if self.conn:
            self.conn.close()

        self.conn = psycopg2.connect(self.dsn)
        self.conn.set_isolation_level(0)
        self.cursor = self.conn.cursor()

    def connect(self):
        try:
            self.try_connect()
        except psycopg2.DatabaseError, e:
            self.log(syslog.LOG_ERR,
                "Exception: %s. Reconnecting and retrying." % e)

            # Exponential backoff foo
            if self.sleeptime == 0:
                self.sleeptime = 1
            else:
                time.sleep(self.sleeptime)
                self.sleeptime = self.sleeptime * 2

            self.connect()
            self.sleeptime = 0

    def log(self, priority, msg):
        syslog.syslog(priority, "%s: %s" % (self.name, msg))

    def do_query(self):
        """Execute the query supplied returning all the rows."""
        try:
            self.cursor.execute(self.query)
            return self.cursor.fetchall()
        except psycopg2.DatabaseError, e:
            self.log(syslog.LOG_ERR,
                "Exception: %s. Reconnecting and retrying." % e)
            self.connect()
            self.do_query()

    def do_format(self, row):
        """Apply the format string against a row."""
        return self.options['format'].replace('\\n', '\n') % row

    def write_file(self, path, f):
        tmp = path + "~"
        fh = open(tmp, "w+")

        try:
            f(fh)
        finally:
            fh.close()

        self.do_perms(path, tmp)
        os.rename(tmp, path)

    def do_write(self, result, target):
        """For each row in the result set apply the format and write it out to
        the target file."""

        def write_results(fh):
            for row in result:
                fh.write(self.do_format(row))

        self.write_file(target, write_results)

    def do_perms(self, source, target):
        """Apply the same file permissions from the original destination
        version of the file to the target."""

        if os.path.exists(source):
            orig = os.stat(source)

            try:
                os.chmod(target, orig[stat.ST_MODE])
            except select.error, (errno, strerror):
                self.log(syslog.LOG_ERR,
                    "Failed to chmod new file: %s" % strerror)

    def do_update(self):
        """Update the destination file with data from the database."""

        result = self.do_query()
        self.log(syslog.LOG_NOTICE, "Updating: %s" % self.destination)
        self.do_write(result, self.destination)

    def do_posthooks(self):
        """Execute all the provided hooks."""

        for hook in self.options.get('posthooks', '').strip().splitlines():
            self.log(syslog.LOG_INFO, "Executing: %s" % hook)
            os.system(hook)

    def get_notifies(self):
        """Get any pending notifications."""

        try:
            if not self.cursor.isready():
                return []

            notifies = self.conn.notifies[:]
            self.conn.notifies[:] = []
            return [name for pid, name in notifies]
        except psycopg2.DatabaseError, e:
            self.log(syslog.LOG_ERR,
                "Exception: %s. Reconnecting and retrying." % e)
            self.connect()
            self.get_notifies()

    def listen(self):
        # Set up the appropriate notifications

        for n in self.notifications:
            self.log(syslog.LOG_INFO, "Listening for: %s" % n)
            self.cursor.execute("listen \"%s\"" % n)

