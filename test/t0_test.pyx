# -*- Mode: Cython -*-

from libc.stdint cimport uint8_t

cdef extern from "t0.h":

    ctypedef struct ThingMsg_t:
        pass
    cdef int decode_ThingMsg (ThingMsg_t * dst, buf_t * src)
    cdef int encode_ThingMsg (buf_t * dst, const ThingMsg_t * src)

    ctypedef struct buf_t:
        uint8_t * buffer
        unsigned int pos
        unsigned int size

def try_decode (bytes pkt):
    cdef buf_t o
    cdef buf_t b
    cdef ThingMsg_t msg
    cdef uint8_t buffer[1024]
    b.buffer = <uint8_t *> <char *> pkt
    b.size = len(pkt)
    b.pos = 0
    cdef int r = decode_ThingMsg (&msg, &b)
    if r == 0:
        # good decode, now let's encode it.
        o.buffer = &buffer[0]
        o.size = sizeof(buffer)
        o.pos = o.size
        r = encode_ThingMsg (&o, &msg)
        if r == 0:
            return o.buffer[o.pos:o.size]
        else:
            return r
    else:
        return r
    
