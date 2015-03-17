
from coro.asn1.ber import *
from t0_test import try_decode

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
        ('asdfasdfasdf', False),
        ('\xDE\xAD\xBE\xEF', False),
        ('x', False),
        # trailing junk
        (SEQUENCE (INTEGER (10), INTEGER (101), 'asdfasdf'), False),
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
        ('wieuriuwiusdf', False),
        ('x', False),
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
        (SEQUENCE (INTEGER (1001), BOOLEAN(False), SEQUENCE(), BOOLEAN(True), OCTET_STRING ("asdfasdfasdfasdfasdfasdfasdfasdfasdf")), False),
        # not enough data
        (SEQUENCE (BOOLEAN(False), BOOLEAN(True)), False),
        (INTEGER (99), False),
        ('ksdjfkjwekrjasdf', False),
        ('x', False),
        ]

def gen_msga():
    result = []
    for pair, good_pair in gen_pair():
        for color, good_color in gen_color():
            result.extend ([
                # -- potentially good data ---
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (50), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), good_pair and good_color),
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (51), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), good_pair and good_color),
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (52), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(True), color), good_pair and good_color),
                # --- known to be bad data ---
                # not enough entries
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (52), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
                # bad first type
                (SEQUENCE (INTEGER (99), INTEGER (50), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                # out of range integers...
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (410), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (53), INTEGER (16555), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (54), INTEGER (10001), INTEGER (1<<33), SEQUENCE (pair,pair,pair,pair), BOOLEAN(False), color), False),
                # bad type in SEQUENCE OF
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (55), INTEGER (16555), INTEGER (99), SEQUENCE (INTEGER(99)), BOOLEAN(False), color), False),
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (56), INTEGER (16555), INTEGER (99), INTEGER (99), BOOLEAN(False), color), False),
                # bad type in place of BOOLEAN
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (57), INTEGER (10001), INTEGER (398234234), SEQUENCE (pair,pair,pair,pair), INTEGER(-9), color), False),
                # negative integers in unexpected places
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (58), INTEGER (10001), INTEGER (-1000), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False), 
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (59), INTEGER (-100), INTEGER (-1000), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
                (SEQUENCE (OCTET_STRING ('abc'), INTEGER (-20), INTEGER (-100), INTEGER (-1000), SEQUENCE (pair,pair,pair), BOOLEAN(True), color), False),
            ])

    return result

def gen_msgc():
    return [
        (SEQUENCE (OCTET_STRING (''), BOOLEAN (True)), True),
        (SEQUENCE (OCTET_STRING ('x' * 499), BOOLEAN (True)), True),
        (SEQUENCE (OCTET_STRING ('x' * 501), BOOLEAN (True)), False),
    ]

def gen_thingmsg():
    result = []
    for msgb, good in gen_msgb():
        result.append ((TLV (APPLICATION (1), msgb), good),)
        # wrong tag
        result.append ((TLV (APPLICATION (0), msgb), False),)
    for msga, good in gen_msga():
        result.append ((TLV (APPLICATION (0), msga), good),)
        # bad tag
        result.append ((TLV (APPLICATION (9), msga), False),)
        # wrong tag
        result.append ((TLV (APPLICATION (1), msga), False),)
    for msgc, good in gen_msgc():
        result.append ((TLV (APPLICATION (2), msgc), good))
    return result
        
