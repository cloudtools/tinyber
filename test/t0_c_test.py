# -*- Mode: Python -*-

# run the auto-generated tests on the C codec.

from coro.asn1.ber import *
from t0_test import try_decode
from t0_gen_test import gen_thingmsg

class ExpectedGood (Exception):
    pass
class ExpectedBad (Exception):
    pass
class BadEncoding (Exception):
    pass

# XXX use the unittest framework

def go():
    n = 0
    for tval, good in gen_thingmsg():
        print tval.encode ('hex'), good
        r = try_decode (tval)
        if not good:
            if r != -1:
                # it should have been bad, but wasn't.
                raise ExpectedBad
        elif r == -1:
            # it should have been good, but wasn't.
            raise ExpectedGood
        elif r != tval:
            # it was a good decode, but the encoding wasn't identical.
            raise BadEncoding
        else:
            # it's all good.
            pass
        n += 1
    print 'passed %d tests' % (n,)

go()

