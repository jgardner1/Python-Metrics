import unittest
import metrics
import threading

import logging
import StringIO
import json
from time import time

logger = logging.getLogger('metrics')
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(message)s")

class DummyApp(object):

    def __call__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

class TestAll(unittest.TestCase):
    
    def test_Context(self):
        log_data = StringIO.StringIO()
        handler = logging.StreamHandler(log_data)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        start = time()
        with metrics.Context(a=5) as c:
            self.assertEquals(c['a'], 5)
            c['b'] = 6
            self.assertEquals(c['b'], 6)
            with metrics.Timer('foo', d=7) as t:
                self.assertEquals(t['d'], 7)
                t['e'] = 8
                self.assertEquals(t['e'], 8)

            self.assertEquals(len(metrics.context.events), 1)

            metrics.event('bar', f=9)

            self.assertEquals(len(metrics.context.events), 2)
        duration = time()-start

        logger.removeHandler(handler)
        data = json.loads(log_data.getvalue())
        from pprint import pprint
        pprint(data)
        self.assertEquals(data['a'], 5)
        self.assertEquals(data['b'], 6)
        self.assertAlmostEquals(data['start'], start, 2)
        self.assertAlmostEquals(data['duration'], duration, 2)
        self.assertEquals(len(data['events']), 2)

        e0 = data['events'][0]
        self.assertAlmostEquals(e0['start'], start, 2)
        self.assertAlmostEquals(e0['duration'], duration, 2)
        self.assertEquals(e0['name'], 'foo')
        self.assertEquals(e0['d'], 7)
        self.assertEquals(e0['e'], 8)

        e1 = data['events'][1]
        self.assertAlmostEquals(e1['start'], start, 2)
        self.assertEquals(e1['name'], 'bar')
        self.assertEquals(e1['f'], 9)



    def test_no_context(self):
        """Without a context, we shouldn't see any exceptions, although the
        log will complain."""
        with metrics.Timer('foo') as t:
            pass
        metrics.event('bar')


    def test_WSGI(self):
        d = DummyApp()
        app = metrics.MetricsContextApp(d)
        app(dict(
            REMOTE_ADDR='remote_addr',
            PATH_INFO='path_info',
            QUERY_STRING='query_string',
        ), 17)
        self.assertEquals(d.start_response, 17)
        c = d.environ['metrics_context']
        self.assertEquals(c['REMOTE_ADDR'], 'remote_addr')
        self.assertEquals(c['PATH_INFO'], 'path_info')
        self.assertEquals(c['QUERY_STRING'], 'query_string')
        self.assertEquals(c['thread'], threading.current_thread().name)

if __name__ == '__main__':
    unittest.main()
