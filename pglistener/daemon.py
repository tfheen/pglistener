
import errno
import os
import select

def daemonize():
    pid = os.fork()

    if pid != 0:
        os._exit(0)

    os.setsid()
    pid = os.fork()

    if pid != 0:
        os._exit(0)

    fh = file(os.devnull, 'r')
    os.dup2(fh.fileno(), 0)
    fh.close()

    fh = file(os.devnull, 'w')
    os.dup2(fh.fileno(), 1)
    os.dup2(fh.fileno(), 2)
    fh.close()

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

