# -*- Mode: Python -*-

# exhaustive test of the encoder, using t0.asn

# Note: the encoder does not [yet] check constraints, only the decoder.
#  this test suite will need slight tweaking once that is added.

import unittest
from t0_ber import *

class NoError (Exception):
    pass

def union_error (*errors):
    r = NoError
    # return the most specific error when possible
    for e in errors:
        if e is not NoError:
            if r is NoError:
                r = e
            else:
                # more than one specific error, use the base class
                return DecodingError
    return r

def gen_pair():
    return [
        # good
        (NoError, Pair (a=10, b=101)),
        # out of range integer
        (ConstraintViolation, Pair (a=10, b=10)),
        (ConstraintViolation, Pair (a=1001, b=10)),
        # unwanted negative integer
        (ConstraintViolation, Pair (a=-5, b=-6)),
    ]

def gen_color():
    return [
        (NoError, Color ('red')),
        (NoError, Color ('blue')),
        (NoError, Color ('green')),
        (BadEnum, Color ('orange')),
    ]

def gen_msgc():
    return [
        (NoError,             MsgC (lstr = b'testing', tbool=False)),
        (NoError,             MsgC (lstr = b'x' * 499, tbool=False)),
        (ConstraintViolation, MsgC (lstr = b'x' * 501, tbool=False)),
    ]

def gen_msgb():
    return [
        (NoError, MsgB (a=1001, b=True, x=[], y=[1])),
        (NoError, MsgB (a=1<<30, b=True, x=[], y=[1])),
        (NoError, MsgB (a=1001, b=False, x=[], y=[1])),
        (NoError, MsgB (a=1001, b=False, x=[], y=[1, 2])),
        # exactly one x
        (NoError, MsgB (a=1001, b=False, x=[True], y=[1, 2])),
        # exactly two x
        (NoError, MsgB (a=1001, b=False, x=[True, False], y=[1, 2])),
        # too many x
        (ConstraintViolation, MsgB (a=1001, b=False, x=[True, False, True], y=[1, 2])),
        # < 1 y
        (ConstraintViolation, MsgB (a=1001, b=False, x=[], y=[])),
        # out of range y
        (ConstraintViolation, MsgB (a=1001, b=False, x=[], y=[1, 1001])),
    ]

def gen_msga():
    for error0, pair in gen_pair():
        for error1, color in gen_color():
            r0 = [
                # potentially good data
                (NoError,             MsgA (toctet=b'abc', t8int=50, t16int=10001, t32int=398234234, tarray=[pair, pair, pair, pair], tbool=False, tenum=color)),
                (NoError,             MsgA (toctet=b'abc', t8int=51, t16int=10001, t32int=398234234, tarray=[pair, pair, pair, pair], tbool=False, tenum=color)),
                (NoError,             MsgA (toctet=b'abc', t8int=52, t16int=10001, t32int=398234234, tarray=[pair, pair, pair, pair], tbool=False, tenum=color)),
                (NoError,             MsgA (toctet=b'abc', t8int=255, t16int=10001, t32int=398234234, tarray=[pair, pair, pair, pair], tbool=False, tenum=color)),
                (ConstraintViolation, MsgA (toctet=b'abc', t8int=256, t16int=10001, t32int=398234234, tarray=[pair, pair, pair, pair], tbool=False, tenum=color)),
                (ConstraintViolation, MsgA (toctet=b'abc', t8int=-1, t16int=10001, t32int=398234234, tarray=[pair, pair, pair, pair], tbool=False, tenum=color)),
                # not enough entries
                (ConstraintViolation, MsgA (toctet=b'abc', t8int=52, t16int=10001, t32int=398234234, tarray=[pair, pair, pair], tbool=False, tenum=color)),
                # bad first type
                (ConstraintViolation, MsgA (toctet=99, t8int=52, t16int=10001, t32int=398234234, tarray=[pair, pair, pair], tbool=False, tenum=color)),
            ]
            for error2, msg in r0:
                yield union_error (error0, error1, error2), msg

def gen_thingmsg():
    for error, msga in gen_msga():
        yield (error, ThingMsg (msga))
    for error, msgb in gen_msgb():
        yield (error, ThingMsg (msgb))
    for error, msgc in gen_msgc():
        yield (error, ThingMsg (msgc))

class TestEncoder(unittest.TestCase):

    # the codec does not currently check constraints in the *encoder*,
    #   so to verify contraint checking we do a round trip.
    def round_trip (self, ob):
        ob0 = ob.__class__()
        encoded = ob.encode()
        ob0.decode (encoded)
        self.assertEqual (ob0, ob)
        raise NoError

    def test_round_trip (self):
        # all generators, simplest to the most complex
        gens = [gen_pair, gen_color, gen_msgc, gen_msgb, gen_msga, gen_thingmsg]
        n = 0
        for gen in gens:
            for expected, ob in gen():
               with self.assertRaises (expected):
                   self.round_trip (ob)
                   n += 1
        # XXX would be nice if there was some way to report the total number of tests here.

if __name__ == '__main__':
    unittest.main()
