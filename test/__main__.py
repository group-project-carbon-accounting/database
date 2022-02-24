import tornado.test.runtests
import unittest
from .integration.test_integration import TestApp


def all():
    all_tests = unittest.TestLoader()
    suite = all_tests.loadTestsFromTestCase(TestApp)
    return suite

tornado.test.runtests.main()