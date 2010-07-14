
import errno
import os
import pwd
import re
import select
import sys
import syslog
import time
import socket

import psycopg2
import psycopg2.extensions

def close_stdio():
    fh = file(os.devnull, 'r')
    os.dup2(fh.fileno(), 0)
    fh.close()

    fh = file(os.devnull, 'w')
    os.dup2(fh.fileno(), 1)
    os.dup2(fh.fileno(), 2)
    fh.close()

class FakeStderr:
    def write(self, s):
        for line in s.rstrip().splitlines():
            syslog.syslog(syslog.LOG_ERR, line)

def daemonize(pidfile):
    # Open the PID file before we fork, so that our parent will see an error
    # if we fail.
    fd = os.open(pidfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0644)
    fh = os.fdopen(fd, 'w')
    pid = os.fork()

    if pid != 0:
        os._exit(0)

    os.setsid()
    pid = os.fork()

    if pid != 0:
        fh.write('%d\n' % pid)
        fh.close()
        os._exit(0)

    close_stdio()
    sys.stderr = FakeStderr()

def format_dsn(dsn):
    matches = re.findall('([^\s=]+)=(\S+)', dsn)
    acc = []

    for k, v in matches:
        if k != 'password':
            acc.append('%s=%s' % (k, v))

    return ' '.join(acc)

class Daemon:
    def __init__(self, listeners):
        self.connections = {}
        self.listeners = listeners

    def err(self, message):
        syslog.syslog(syslog.LOG_ERR, message)

    def info(self, message):
        syslog.syslog(syslog.LOG_INFO, message)

    def _make_connection(self, dsn):
        return psycopg2.connect(dsn)

    def make_connection(self, dsn):
        sleeptime = 1

        while True:
            self.info("connecting to: %s" % format_dsn(dsn))

            try:
                return self._make_connection(dsn)
            except psycopg2.DatabaseError, e:
                self.err("error: %s" % e)
                time.sleep(sleeptime)

                if sleeptime < 128:
                    sleeptime *= 2

    def query(self, listener):
        sleeptime = 1

        while True:
            connection = self.connections[listener.dsn]
            cursor = connection.cursor()
            if hasattr(socket, 'SO_KEEPALIVE'):
                fd = None
                try:
                    fd = cursor.fileno()
                except AttributeError:
                    fd = cursor.connection.fileno()
                except AttributeError:
                    pass
                else:
                    s = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
                    # avoid unix sockets
                    if type(s.getsockname()) == type(()):
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            try:
                cursor.execute(listener.query)
                return cursor.fetchall()
            except psycopg2.DatabaseError, e:
                self.err("error: %s" % e)
                self.err("reconnecting and retrying")
                self.connections[listener.dsn] = \
                    self.make_connection(listener.dsn)

                if sleeptime < 128:
                    sleeptime *= 2

    def get_notifications(self, conn, cursor = None):
        # Newer psycopg needs poll, but older doesn't have it.
        try:
            conn.poll()
        except AttributeError:
            conn.cursor().isready()
        notifications = [name for pid, name in conn.notifies]
        conn.notifies[:] = []
        return notifications

    def wait_for_notifications(self):
        connections = self.connections.values()

        # Backwards compatibility
        if not hasattr(connections[0], 'fileno'):
            connections = [x.cursor() for x in connections]

        try:
            readables, _, _ = select.select(connections, [], [], None)
        except select.error, (err, strerror):
            if err == errno.EINTR:
                return []
            else:
                raise

        notifications = set()

        for obj in readables:
            conn = obj
            if hasattr(obj, 'connection'):
                # conn is a cursor, not a connection
                conn = conn.connection
            try:
                notifications.update(
                    self.get_notifications(conn))
            except psycopg2.DatabaseError, e:
                # Probably end of file due to losing the connection.
                # Reconnect.

                self.err(str(e))

                for dsn, c in self.connections.iteritems():
                    if c is conn:
                        self.connections[dsn] = self.make_connection(dsn)

        return notifications

    def update(self, listener):
        self.info("updating: %s (%s)" %
            (listener.name, listener.destination))
        results = self.query(listener)
        listener.do_write(results, listener.destination)
        listener.do_posthooks()

    def do_iteration(self):
        notifications = self.wait_for_notifications()

        for notification in notifications:
            self.info("got notification: %s" % notification)

        for listener in self.listeners:
            if notifications & set(listener.notifications):
                self.update(listener)

    def loop(self):
        while True:
            self.do_iteration()

    def listen(self):
        for dsn, conn in self.connections.iteritems():
            listens = []
            cursor = conn.cursor()

            for listener in self.listeners:
                if listener.dsn == dsn:
                    self.info("%s: listening for: %s" %
                        (listener.name, ' '.join(listener.notifications)))
                    listens.extend(listener.notifications)

            for listen in listens:
                cursor.execute('listen \"%s\"' % listen)

    def openlog(self):
        syslog.openlog('pglistener', syslog.LOG_PID, syslog.LOG_DAEMON)

    def run(self):
        self.info('starting up')

        for listener in self.listeners:
            if listener.dsn not in self.connections:
                conn = self.make_connection(listener.dsn)
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                self.connections[listener.dsn] = conn

        for listener in self.listeners:
            self.update(listener)

        self.listen()
        self.loop()

def run(listeners):
    daemon = Daemon(listeners)
    daemon.run()


