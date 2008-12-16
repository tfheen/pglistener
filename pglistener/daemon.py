
import errno
import os
import pwd
import re
import select
import sys
import syslog
import time

import psycopg2

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

    def make_connection(self, dsn):
        sleeptime = 1

        while True:
            self.info("connecting to: %s" % format_dsn(dsn))

            try:
                return psycopg2.connect(dsn)
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

    def get_notifications(self, conn, cursor):
        if not cursor.isready():
            return []

        notifications = [name for pid, name in conn.notifies]
        conn.notifies[:] = []
        return notifications

    def wait_for_notifications(self):
        connections = {}

        for conn in self.connections.values():
            connections[conn.cursor()] = conn

        try:
            readables, _, _ = select.select(connections.keys(), [], [], None)
        except select.error, (err, strerror):
            if err == errno.EINTR:
                return []
            else:
                raise

        notifications = set()

        for cursor in readables:
            try:
                notifications.update(
                    self.get_notifications(connections[cursor], cursor))
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
                    for notification in listener.notifications:
                        self.info("%s: listening for notification: %s" %
                            (listener.name, notification))
                        listens.append(notification)

            for listen in listens:
                cursor.execute('listen \"%s\"' % listen)

    def run(self):
        syslog.openlog('pglistener', syslog.LOG_PID, syslog.LOG_DAEMON)

        for listener in self.listeners:
            if listener.dsn not in self.connections:
                conn = self.make_connection(listener.dsn)
                conn.set_isolation_level(0)
                self.connections[listener.dsn] = conn

        for listener in self.listeners:
            self.update(listener)

        self.listen()
        self.loop()

def run(listeners):
    daemon = Daemon(listeners)
    daemon.run()


