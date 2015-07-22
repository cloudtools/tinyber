# -*- Mode: Python -*-

# how many bytes to represent length <n> (the 'L' in TLV).

def length_of_length (n):
    if n < 0x80:
        return 1
    else:
        r = 1
        while n:
            n >>= 8
            r += 1
        return r

def length_of_integer (n):
    i = 0
    n0 = n
    byte = 0x80
    r = 0
    while 1:
        n >>= 8
        if n0 == n:
            if n == -1 and ((not byte & 0x80) or (i == 0)):
                # negative, but high bit clear
                r += 1
                i += 1
            elif n == 0 and (byte & 0x80):
                # positive, but high bit set
                r += 1
                i += 1
            break
        else:
            byte = n0 & 0xff
            r += 1
            i += 1
            n0 = n
    return r
