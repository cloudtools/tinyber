# -*- Mode: Python -*-

# run the auto-generated tests on the C codec.

import unittest

from tests.coverage.t0_gen_cases import gen_thingmsg
from tests.utils import test_reload, generate_c

class ExpectedGood (Exception):
    pass
class ExpectedBad (Exception):
    pass
class BadEncoding (Exception):
    pass

class TestBasic(unittest.TestCase):

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
                self.assertNotEqual (r, -1, msg=tval)
                self.assertEqual (r, tval)

if __name__ == '__main__':
    unittest.main()


