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

    def test_c_coverage (self):
        # this is disgusting, but "from tests.coverage.t0_wrap" does not work here.
        test_reload()
        import sys
        sys.path.append ('tests/coverage')
        from t0_wrap import try_decode
        for tval, good in gen_thingmsg():
            #print tval.encode ('hex'), good
            r = try_decode (tval)
            if not good:
                # it should have been bad, but wasn't.
                self.assertEqual (r, -1)
            else:
                self.assertNotEqual (r, -1)
                self.assertEqual (r, tval)

if __name__ == '__main__':
    unittest.main()


