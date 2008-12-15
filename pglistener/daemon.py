
import errno
import os
import pwd
import select
import sys
import syslog

def setuid(username):
    uid = pwd.getpwnam(username).pw_uid
    os.setuid(uid)

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

def daemonize(username, pidfile):
    # Open the PID file before we drop privileges, but write it after we're
    # done forking.
    fd = os.open(pidfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    fh = os.fdopen(fd, 'w')
    setuid(username)
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

class Daemon:
    def __init__(self, listeners):
        self.listeners = listeners

    def err(self, message):
        syslog.syslog(syslog.LOG_ERR, message)

    def info(self, message):
        syslog.syslog(syslog.LOG_INFO, message)

    def wait_for_notifications(self, cursors):
        try:
            readables, _, _ = select.select(cursors.keys(), [], [], None)
        except select.error, (err, strerror):
            if err == errno.EINTR:
                return []
            else:
                raise

        notifications = set()

        for cursor in readables:
            listener = cursors[cursor]
            notifications.update(listener.get_notifies())

        return notifications

    def do_iteration(self, cursors):
        notifications = self.wait_for_notifications(cursors)

        for listener in cursors.values():
            if notifications & set(listener.notifications):
                listener.do_update()
                listener.do_posthooks()

    def loop(self):
        cursors = {}

        for listener in self.listeners:
            cursors[listener.cursor] = listener

        while True:
            self.do_iteration(cursors)

    def run(self):
        syslog.openlog('pglistener', syslog.LOG_PID, syslog.LOG_DAEMON)

        for listener in self.listeners:
            listener.try_connect()
            listener.do_update()
            listener.do_posthooks()

        for listener in self.listeners:
            listener.listen()

        self.loop()

def run(listeners):
    daemon = Daemon(listeners)
    daemon.run()


