
import os
import sys
import shutil
import tempfile
import unittest

from pglistener import pglistener

class FakeCursor(object):
    def execute(self, query):
        pass

    def fetchall(self):
        return [('a', '1'), ('b', '2')]

class TestListener(pglistener.PgListener):
    def __init__(self, options):
        pglistener.PgListener.__init__(self, options)
        self.cursor = FakeCursor()

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
        listener.do_update()
        self.assertEquals('a:1\nb:2\n', file(destination).read())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

def main():
    unittest.main()

if __name__ == '__main__':
    main()

