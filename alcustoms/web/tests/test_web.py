""" alcustoms.web.tests.test_web.py

    TestCases for utilities in alcustoms.web.__init__.py
"""
## Test framework
import unittest
## Test target
from alcustoms.web import RequestLock

## builtin
import time

class RequestLockTestCase(unittest.TestCase):
    """ TestCase for alcustoms.web.RequestLock """

    def test_basic(self):
        """ Iterates through a loop a few times, asserting that there is a delay each time (predicated on the loop taking less than 1 second to execute). """

        ## For this test to be accurate, timeout must be longer than the time 
        ## it takes to execute the below for-loop
        timeout = 1
        lock = RequestLock(timeout = timeout)
        ## Establishing an initial lasttime value
        with lock: pass
        for i in range(5):
            with lock:
                last = lock.lasttime
                self.assertGreaterEqual(time.time(), last + timeout)