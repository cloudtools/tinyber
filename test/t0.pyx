# -*- Mode: Cython -*-

from libc.stdint cimport uint8_t

cdef extern from "t0.h":

    ctypedef struct ThingMsg_t:
        pass
    cdef int decode_ThingMsg (ThingMsg_t * dst, buf_t * src)

    ctypedef struct buf_t:
        uint8_t * buffer
        unsigned int pos
        unsigned int size

def try_decode (bytes pkt):
    cdef buf_t b
    cdef ThingMsg_t msg
    b.buffer = <uint8_t *> <char *> pkt
    b.size = len(pkt)
    b.pos = 0
    cdef int r = decode_ThingMsg (&msg, &b)
    
