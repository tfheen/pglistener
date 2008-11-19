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
import signal
import stat
import sys
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
        self.syslog = options.get('syslog', 'no').lower() == 'yes'

        # Setup a handler for SIGUSR1 which will force and update when the
        # signal # is received.

        def handle_usr1(signo, frame):
            self.force_update = True

        signal.signal(signal.SIGUSR1, handle_usr1)

        if self.syslog:
            # Set the appropriate syslog settings if we are using syslog
            syslog.openlog('pglistener', syslog.LOG_PID, syslog.LOG_DAEMON)

    def connect(self):
        if getattr(self, 'conn', None):
            self.conn.close()

        try:
            conn = psycopg2.connect(self.dsn)
            self.conn = conn
            self.cursor = conn.cursor()
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
        """Record appropriate logging information. The message that is logged
        includes the name of the configuration. The priority are those
        specified in the syslog module."""

        if self.syslog:
            # Output to syslog if syslog support is enabled
            syslog.syslog(priority, "%s: %s" % (self.name, msg))

        print "%s: %s" % (self.name, msg)

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

    def do_write(self, result, target):
        """For each row in the result set apply the format and write it out to
        the target file."""

        f = open(target, "w+")

        for row in result:
            f.write(self.do_format(row))

        f.close()

    def do_perms(self, target):
        """Apply the same file permissions from the original destination
        version of the file to the target."""

        if os.path.exists(self.destination):
            orig = os.stat(self.destination)
            try:
                os.chmod(target, orig[stat.ST_MODE])
                os.chown(target, orig[stat.ST_UID], orig[stat.ST_GID])
            except select.error, (errno, strerror):
                self.log(syslog.LOG_ERR,
                    "Failed to chmod new file: %s" % strerror)

    def do_update(self):
        """Update the destination file with data from the database."""

        target = self.destination + "~"
        result = self.do_query()

        self.do_write(result, target)
        self.do_perms(target)

        self.log(syslog.LOG_NOTICE, "Updating: %s" % self.destination)

        os.rename(target, self.destination)

    def do_posthooks(self):
        """Execute all the provided hooks."""

        for hook in self.options.get('posthooks', []):
            self.log(syslog.LOG_INFO, "Executing: %s" % hook)
            os.system(hook)

    def get_notifies(self):
        """Get any pending notifications."""

        try:
            cursor = self.cursor
            time.sleep(0.1)
            cursor.execute("select 1")
            return cursor.notifies()
        except psycopg2.DatabaseError, e:
            self.log(syslog.LOG_ERR,
                "Exception: %s. Reconnecting and retrying." % e)
            self.connect()
            self.get_notifies()

    def monitor(self):
        """Start the main monitor loop."""

        # Save a bit of typing ;-)
        cursor = self.cursor

        self.log(syslog.LOG_NOTICE,
            "Starting monitor for %s" % self.destination)

        self.force_update = False

        # Setup the appropriate notifications
        for n in self.notifications:
            self.log(syslog.LOG_INFO, "Listening for: %s" % n)
            cursor.execute("listen \"%s\"" % n)

        self.do_update()
        notifications = []

        while True:
            while notifications or self.force_update:
                if self.force_update:
                    self.log(syslog.LOG_NOTICE, "Got SIGUSR1, forcing update.")
                    self.force_update = False
                else:
                    self.log(syslog.LOG_DEBUG, "Got: %s" % notifications)

                self.do_update()
                notifications = self.get_notifies()

            # We've run out of notifications so now we can safely do the
            # posthooks
            self.do_posthooks()

            # This blocks, the above is only executed when we do get a
            # notification

            try:
                select.select([cursor], [], [])
            except select.error, (err, strerror):
                if err != errno.EINTR:
                    raise
            else:
                notifications = self.get_notifies()

