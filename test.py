
import bsddb
import os
import sys
import shutil
import tempfile
import unittest

import coverage

from pglistener import pglistener
from pglistener.config import read_config
from pglistener.nsspasswddb import NssPasswdDb

class TestListener(pglistener.PgListener):
    def __init__(self, options):
        pglistener.PgListener.__init__(self, options)

    def log(self, priority, message):
        pass

class PgListenerTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def runTest(self):
        destination = os.path.join(self.tmpdir, 'destination')
        listener = TestListener({
            'name': 'fake',
            'dsn': 'fake',
            'notifications': [],
            'destination': destination,
            'format': '%s:%s\\n',
            'query': 'fake query'
            })
        listener.do_write([('a', '1'), ('b', '2')], listener.destination)
        self.assertEquals('a:1\nb:2\n', file(destination).read())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

class NssPasswdDbTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def runTest(self):
        destination = os.path.join(self.tmpdir, 'destination')
        listener = NssPasswdDb({
            'name': 'fake',
            'dsn': 'fake',
            'notifications': [],
            'destination': destination,
            'format': '%s:%s\\n',
            'query': 'fake query'
            })
        listener.do_write([
            ('amy', 'x', 1000, 1000, 'amy', '/home/amy', '/bin/bash'),
            ('beth', 'x', 1001, 1001, 'beth', '/home/beth', '/bin/zsh')],
            listener.destination)
        db = bsddb.btopen(listener.destination, "r")
        self.assertEquals(
            'amy:x:1000:1000:amy:/home/amy:/bin/bash\x00', db['.amy'])
        self.assertEquals(
            'beth:x:1001:1001:beth:/home/beth:/bin/zsh\x00', db['=1001'])
        db.close()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def runTest(self):
        config_file = os.path.join(self.tmpdir, 'pglistener.cfg')

        def write_file(path, s):
            fh = file(path, 'w')
            fh.write(s)
            fh.close()

        config_str = (
            '[%s]\n' +
            'class = NssDb\n' +
            'notifications = foo\n' +
            'dsn = fake\n' +
            'query = fake\n' +
            'destination = fake\n')
        write_file(config_file, config_str % 'foo')
        (foo,) = list(read_config(config_file))
        self.assertEquals('foo', foo.name)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

def run_coverage(*args):
    os.spawnlp(os.P_WAIT, 'python', 'python', coverage.__file__, *args)

def find_python_files(path):
    for dirpath, dirnames, filenames in os.walk(path):
        # Filter out non-packages.
        dirnames[:] = [d for d in dirnames
            if os.path.exists(os.path.join(dirpath, d, '__init__.py'))]

        for filename in filenames:
            if filename.endswith('.py'):
                yield os.path.join(dirpath, filename)

def main():
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-c':
            del sys.argv[i]
            run_coverage('-e')
            run_coverage('-x', __file__, *sys.argv[1:])
            files = list(find_python_files('.'))
            run_coverage('-r', *files)
            run_coverage('-a', *files)
            raise SystemExit(0)

    unittest.main()

if __name__ == '__main__':
    main()

