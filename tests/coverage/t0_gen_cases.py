
#from coro.asn1.ber import *
from cyber.ber import *

# this will auto-generate test cases - both good and bad ones - to exhaustively
#  cover the tinyber codec generated for t0.asn.
# currently generates 3000+ tests.

def gen_pair():
    return [
        (SEQUENCE (INTEGER (10), INTEGER (101)), True),
        # out of range integer
        (SEQUENCE (INTEGER (10), INTEGER (10)), False),
        (SEQUENCE (INTEGER (1001), INTEGER (10)), False),
        # unwanted negative integer
        (SEQUENCE (INTEGER (-5), INTEGER (-6)), False),
        # junk
        (b'asdfasdfasdf', False),
        (b'\xDE\xAD\xBE\xEF', False),
        (b'x', False),
        # trailing junk
        (SEQUENCE (INTEGER (10), INTEGER (101), b'asdfasdf'), False),
        (SEQUENCE (INTEGER (10), INTEGER (101), BOOLEAN(True)), False),
    ]

def gen_color():
    return [
        (ENUMERATED (0), True),
        (ENUMERATED (1), True),
        (ENUMERATED (2), True),
        (ENUMERATED (3), False),
        (ENUMERATED (4), False),
        # bad type
        (INTEGER (99), False),
        # junk
        (b'wieuriuwiusdf', False),
        (b'x', False),
        ]

def gen_msgb():
    gx = SEQUENCE()
    gy = SEQUENCE (INTEGER (1))
    return [
        (SEQUENCE (INTEGER (1001), BOOLEAN(True), gx, gy), True),
        (SEQUENCE (INTEGER (1<<30), BOOLEAN(True), gx, gy), True),
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), gx, gy), True),
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(), SEQUENCE (INTEGER (1), INTEGER (2))), True),
        # exactly one x
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(BOOLEAN(True)), gy), True),
        # exactly two x
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(BOOLEAN(True), BOOLEAN(False)), gy), True),
        # too many x
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(BOOLEAN(True), BOOLEAN(False), BOOLEAN(True)), gy), False),
        # < 1 y
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(), SEQUENCE()), False),
        # out of range in y
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(), SEQUENCE (INTEGER (1), INTEGER (1001))), False),
        # extra data
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(), BOOLEAN(True), OCTET_STRING (b"asdfasdfasdfasdfasdfasdfasdfasdfasdf")), False),
        # not enough data
        (SEQUENCE (BOOLEAN(False), BOOLEAN(True)), False),
        (INTEGER (99), False),
        (b'ksdjfkjwekrjasdf', False),
        (b'x', False),
        ]

def gen_msga():
    result = []
    for pair, good_pair in gen_pair():
        for color, good_color in gen_color():
            result.extend ([
                # -- potentially good data ---
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (50), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), good_pair and good_color),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (51), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), good_pair and good_color),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (52), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(True), color), good_pair and good_color),
                # --- known to be bad data ---
                # not enough entries
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (52), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
                # bad first type
                (SEQUENCE (INTEGER (99), INTEGER (50), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                # out of range integers...
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (410), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (53), INTEGER (16555), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (54), INTEGER (10001), INTEGER (1<<33), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                # bad type in SEQUENCE OF
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (55), INTEGER (16555), INTEGER (99), SEQUENCE (INTEGER(99)), BOOLEAN(False), color), False),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (56), INTEGER (16555), INTEGER (99), INTEGER (99), BOOLEAN(False), color), False),
                # bad type in place of BOOLEAN
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (57), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), INTEGER(-9), color), False),
                # negative integers in unexpected places
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (58), INTEGER (10001), INTEGER (-1000), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (59), INTEGER (-100), INTEGER (-1000), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
                (SEQUENCE (OCTET_STRING (b'abc'), INTEGER (-20), INTEGER (-100), INTEGER (-1000), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
            ])

    return result

def gen_msgc():
    return [
        (SEQUENCE (OCTET_STRING (b''), BOOLEAN (True)), True),
        (SEQUENCE (OCTET_STRING (b'x' * 499), BOOLEAN (True)), True),
        (SEQUENCE (OCTET_STRING (b'x' * 501), BOOLEAN (True)), False),
    ]

def gen_msgd():
    # x INTEGER (-10..10),
    # y INTEGER (-10..-5)
    # exhaustive test around the range
    for i in range (-20, 20):
        for j in range (-20, 20):
            good = (-10 <= i <= 10) and (-10 <= j <= -5)
            yield (SEQUENCE (INTEGER (i), INTEGER (j)), good)

def gen_thingmsg():
    result = []
    for msgb, good in gen_msgb():
        result.append ((APPLICATION (1, True, msgb), good),)
        # wrong tag
        result.append ((APPLICATION (0, True, msgb), False),)
    for msga, good in gen_msga():
        result.append ((APPLICATION (0, True, msga), good),)
        # bad tag
        result.append ((APPLICATION (9, True, msga), False),)
        # wrong tag
        result.append ((APPLICATION (1, True, msga), False),)
    for msgc, good in gen_msgc():
        result.append ((APPLICATION (50, True, msgc), good))
    for msgd, good in gen_msgd():
        result.append ((APPLICATION (2, True, msgd), good))
    return result
