
import errno
import os
import pwd
import select
import sys

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
        for line in s.strip().splitlines():
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

def do_iteration(cursors):
    try:
        readables, _, _ = select.select(cursors.keys(), [], [], None)
    except select.error, (err, strerror):
        if err == errno.EINTR:
            return
        else:
            raise

    for cursor in readables:
        listener = cursors[cursor]
        notifications = listener.get_notifies()

        while notifications:
            listener.do_update()
            notifications = listener.get_notifies()

        listener.do_posthooks()

def loop(listeners):
    cursors = {}

    for listener in listeners:
        cursors[listener.cursor] = listener

    while True:
        do_iteration(cursors)

def run(listeners):
    for listener in listeners:
        listener.try_connect()
        listener.do_update()
        listener.do_posthooks()

    for listener in listeners:
        listener.listen()

    loop(listeners)

