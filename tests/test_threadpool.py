import unittest

from irctk.threadpool import ThreadPool, Worker

import Queue
import time


class WorkerTestCase(unittest.TestCase):
    '''This test case tests the Worker class methods.'''
    
    def setUp(self):
        self.tasks = Queue.Queue()
        for x in range(3):
            self.tasks.put((_worker_test_funct,
                    (self, 'testString'), {'c': False}))
        self.logger = None
        self.worker = Worker(self.tasks, self.logger)
        
        self.assertEquals(self.worker.logger, None)
        self.assertTrue(self.worker.daemon)
    
    def test_run(self):
        pass


def _worker_test_funct(a, b, c=None, d=True):
    a.assertEquals(b, 'testString')
    a.assertEquals(c, False)
    a.assertEquals(d, True)

class ThreadPoolTestCase(unittest.TestCase):
    '''This test case tests the ThreadPool class methods.'''
    
    def setUp(self):
        self.workers = 3
        self.logger = None
        self.tp = ThreadPool(self.workers, self.logger)
        # Give the htread pool time to get up to speed.
        time.sleep(0.3)
        
        self.assertEquals(self.tp.workers, 3)
        self.assertEquals(self.tp.logger, None)
        self.assertEquals(self.tp.wait, 0.01)
        self.assertTrue(self.tp.daemon)
    
    def test_enqueue_task(self):
        self.tp.enqueue_task('foo', 'bar')
        task = self.tp.tasks.get()
        self.assertEquals(('foo', ('bar',), {}), task)
        
        self.tp.enqueue_task('foo', 'bar', test=True)
        task = self.tp.tasks.get()
        self.assertEquals(('foo', ('bar',), {'test': True}), task)
    
    def test_worker(self):
        pass
    
    def test_run(self):
        pass

if __name__ == '__main__':
    unittest.main()

