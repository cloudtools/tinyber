# -*- Mode: Python -*-

# run the auto-generated tests on the C codec.

import unittest

from coro.asn1.ber import *
from tests.coverage.t0_gen_cases import gen_thingmsg
from tests.utils import test_reload, generate_c

class ExpectedGood (Exception):
    pass
class ExpectedBad (Exception):
    pass
class BadEncoding (Exception):
    pass

class TestBasic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import os
        generate_c ('tests/coverage/t0.asn', 't0', 'tests/coverage')
        from distutils.core import run_setup
        run_setup ('tests/coverage/setup.py', ['build_ext', '--inplace'])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_build (self):
        pass

if __name__ == '__main__':
    unittest.main()


