# -*- Mode: Python -*-

# cython version of codec.py

# NOTE: the encoder writes into its buffer in *reverse*, with predecrement.
#  this makes things much simpler.

from libc.stdint cimport uint32_t, uint8_t
from cpython cimport PyBytes_FromStringAndSize
from libc.string cimport memcpy

class DecodingError (Exception):
    pass

class IndefiniteLength (DecodingError):
    pass

class ElementTooLarge (DecodingError):
    pass

class Underflow (DecodingError):
    pass

class UnexpectedType (DecodingError):
    pass

class UnexpectedFlags (DecodingError):
    pass

class ConstraintViolation (DecodingError):
    pass

class BadChoice (DecodingError):
    pass

class ExtraData (DecodingError):
    pass

class BadEnum (DecodingError):
    pass

# flags for BER tags
cdef enum FLAGS:
    FLAGS_UNIVERSAL       = 0x00
    FLAGS_STRUCTURED      = 0x20
    FLAGS_APPLICATION     = 0x40
    FLAGS_CONTEXT         = 0x80

# universal BER tags
cdef enum TAGS:
    TAGS_BOOLEAN          = 0x01
    TAGS_INTEGER          = 0x02
    TAGS_BITSTRING        = 0x03
    TAGS_OCTET_STRING     = 0x04
    TAGS_NULL             = 0x05
    TAGS_OBJID            = 0x06
    TAGS_OBJDESCRIPTOR    = 0x07
    TAGS_EXTERNAL         = 0x08
    TAGS_REAL             = 0x09
    TAGS_ENUMERATED       = 0x0a
    TAGS_EMBEDDED_PDV     = 0x0b
    TAGS_UTF8STRING       = 0x0c
    TAGS_SEQUENCE         = 0x10
    TAGS_SET              = 0x11

cdef class Decoder:
    cdef readonly bytes data
    cdef uint8_t * pdata
    cdef uint32_t pos
    cdef uint32_t end

    def __init__ (self, bytes data, uint32_t pos=0, uint32_t end=0):
        self.data = data
        self.pdata = data
        self.pos = pos
        if end == 0:
            end = len(data)
        self.end = end

    cdef uint8_t pop_byte (self) except? 255:
        cdef uint8_t val
        if self.pos + 1 > self.end:
            raise Underflow (self)
        else:
            val = self.pdata[self.pos]
            self.pos += 1
            return val

    cdef Decoder pop (self, uint32_t nbytes):
        cdef Decoder r
        if self.pos + nbytes > self.end:
            raise Underflow (self)
        else:
            r = Decoder (self.data, self.pos, self.pos + nbytes)
            self.pos += nbytes
            return r

    cdef bytes pop_bytes (self, uint32_t nbytes):
        if self.pos + nbytes > self.end:
            raise Underflow (self)
        else:
            result = self.data[self.pos:self.pos+nbytes]
            self.pos += nbytes
            return result

    cpdef done (self):
        return self.pos == self.end

    def assert_done (self):
        if self.pos != self.end:
            raise ExtraData (self)

    cdef uint32_t get_length (self) except? 4294967295:
        cdef uint8_t val, lol
        cdef uint32_t n
        val = self.pop_byte()
        if val < 0x80:
            # one-byte length
            return val
        elif val == 0x80:
            raise IndefiniteLength (self)
        else:
            # get length of length
            lol = val & 0x7f
            if lol > 4:
                raise ElementTooLarge (self)
            else:
                n = 0
                while lol:
                    n = (n << 8) | self.pop_byte()
                    lol -= 1
                return n

    cdef uint32_t get_multibyte_tag (self) except? 4294967295:
        cdef uint32_t r = 0
        cdef uint8_t val
        while 1:
            val = self.pop_byte()
            r <<= 7
            r |= val & 0x7f
            if not val & 0x80:
                break
        return r

    cpdef get_tag (self):
        cdef uint8_t b = self.pop_byte()
        cdef uint32_t tag  = b & 0b00011111
        cdef uint8_t flags = b & 0b11100000
        if tag == 0b11111:
            tag = self.get_multibyte_tag()
        return tag, flags

    cdef check (self, uint8_t expected_tag, uint8_t expected_flags=0):
        tag, flags = self.get_tag()
        if tag != expected_tag:
            raise UnexpectedType (tag, expected_tag)
        if flags != expected_flags:
            raise UnexpectedFlags (flags, expected_flags)

    cpdef next (self, uint8_t expected, uint8_t expected_flags=0):
        cdef uint32_t length
        self.check (expected, expected_flags)
        length = self.get_length()
        return self.pop (length)

    cdef get_integer (self, uint32_t length):
        # XXX do not declare result as uintXX_t,
        #   we want to support bignums here.
        if length == 0:
            return 0
        else:
            n = self.pop_byte()
            length -= 1
            if n & 0x80:
                # negative
                n -= 0x100
            else:
                while length:
                    n = n << 8 | self.pop_byte()
                    length -= 1
                return n

    def next_INTEGER (self, min_val, max_val):
        self.check (TAGS_INTEGER)
        r = self.get_integer (self.get_length())
        if min_val is not None and r < min_val:
            raise ConstraintViolation (r, min_val)
        if max_val is not None and r > max_val:
            raise ConstraintViolation (r, max_val)
        return r

    def next_OCTET_STRING (self, min_size, max_size):
        self.check (TAGS_OCTET_STRING)
        r = self.pop_bytes (self.get_length())
        if min_size is not None and len(r) < min_size:
            raise ConstraintViolation (r, min_size)
        if max_size is not None and len(r) > max_size:
            raise ConstraintViolation (r, max_size)
        return r

    def next_BOOLEAN (self):
        self.check (TAGS_BOOLEAN)
        assert (self.pop_byte() == 1)
        return self.pop_byte() != 0

    def next_ENUMERATED (self):
        self.check (TAGS_ENUMERATED)
        return self.get_integer (self.get_length())

    def next_APPLICATION (self):
        cdef uint32_t tag
        cdef uint8_t flags
        tag, flags = self.get_tag()
        if not flags & FLAGS_APPLICATION:
            raise UnexpectedFlags (self, flags, FLAGS_APPLICATION)
        else:
            return tag, self.pop (self.get_length())

cdef class EncoderContext:
    cdef Encoder enc
    cdef uint32_t tag
    cdef uint8_t flags
    cdef uint32_t pos

    def __init__ (self, Encoder enc, uint32_t tag, uint8_t flags):
        self.enc = enc
        self.tag = tag
        self.flags = flags
        self.pos = enc.pos

    def __enter__ (self):
        pass

    def __exit__ (self, t, v, tb):
        self.enc.emit_length (self.enc.pos - self.pos)
        self.enc.emit_tag (self.tag, self.flags)

cdef class Encoder:

    cdef bytes buffer
    cdef unsigned int size
    cdef unsigned int pos

    def __init__ (self, unsigned int size=1024):
        self.buffer = PyBytes_FromStringAndSize (NULL, size)
        self.size = size
        self.pos = 0

    cdef grow (self):
        cdef unsigned int data_size = self.pos
        cdef unsigned int new_size = (self.size * 3) / 2 # grow by 50%
        cdef bytes new_buffer = PyBytes_FromStringAndSize (NULL, new_size)
        cdef unsigned char * pnew = new_buffer
        cdef unsigned char * pold = self.buffer
        # copy old string into place
        memcpy (&(pnew[new_size - data_size]), &(pold[self.size - data_size]), data_size)
        self.buffer = new_buffer
        self.size = new_size

    cdef ensure (self, unsigned int n):
        while (self.pos + n) > self.size:
            self.grow()

    cdef emit (self, bytearray s):
        cdef unsigned int slen = len(s)
        cdef unsigned char * pbuf = self.buffer
        cdef unsigned char * ps = s
        self.ensure (slen)
        self.pos += slen
        memcpy (&(pbuf[self.size - self.pos]), ps, slen)

    cdef emit_byte (self, uint8_t b):
        cdef unsigned char * pbuf = self.buffer
        self.ensure (1)
        self.pos += 1
        pbuf[self.size - self.pos] = b

    def emit_tag (self, uint32_t tag, uint8_t flags):
        if tag < 0b11111:
            self.emit_byte (tag | flags)
        else:
            while tag:
                if tag < 0x80:
                    self.emit_byte (tag)
                else:
                    self.emit_byte ((tag & 0x7f) | 0x80)
                tag >>= 7
            self.emit_byte (0b11111 | flags)

    cdef emit_length (self, unsigned int n):
        cdef int c = 0
        if n < 0x80:
            self.emit_byte (n)
        else:
            while n:
                self.emit_byte (n & 0xff)
                n >>= 8
                c += 1
            self.emit_byte (0x80 | c)

    def TLV (self, tag, flags=0):
        return EncoderContext (self, tag, flags)

    def done (self):
        return self.buffer[self.size - self.pos : self.size]

    # base types

    # encode an integer, ASN1 style.
    # two's complement with the minimum number of bytes.
    cdef emit_integer (self, n):
        cdef uint8_t byte = 0x80
        cdef bint first = 1
        n0 = n
        n1 = n
        while 1:
            n1 >>= 8
            if n0 == n1:
                if n1 == -1 and ((not byte & 0x80) or first):
                    # negative, but high bit clear
                    self.emit_byte (0xff)
                elif n1 == 0 and byte & 0x80:
                    # positive, but high bit set
                    self.emit_byte (0x00)
                break
            else:
                byte = n0 & 0xff
                self.emit_byte (byte)
                n0 = n1
            first = 0

    cpdef emit_INTEGER (self, n):
        with self.TLV (TAGS_INTEGER):
            self.emit_integer (n)

    cpdef emit_OCTET_STRING (self, s):
        with self.TLV (TAGS_OCTET_STRING):
            self.emit (bytearray(s))

    cpdef emit_BOOLEAN (self, v):
        with self.TLV (TAGS_BOOLEAN):
            if v:
                self.emit_byte (b'\xff')
            else:
                self.emit_byte (b'\x00')

class ASN1:
    value = None
    def __init__ (self, value=None):
        self.value = value
    def encode (self):
        cdef Encoder e = Encoder()
        self._encode (e)
        return e.done()
    def decode (self, data):
        b = Decoder (data)
        self._decode (b)
    def __eq__ (self, other):
        return isinstance (other, self.__class__) and self.value == other.value
    def __ne__ (self, other):
        return not self.__eq__ (other)
    def __repr__ (self):
        return '<%s %r>' % (self.__class__.__name__, self.value)

class SEQUENCE (ASN1):
    __slots__ = ()
    def __init__ (self, **args):
        for k, v in args.iteritems():
            setattr (self, k, v)
    def __eq__ (self, other):
        if not isinstance (other, self.__class__):
            return False
        else:
            for name in self.__slots__:
                if getattr (self, name) != getattr (other, name):
                    print 'slot __eq__ issue', name, getattr (self, name), getattr (other, name)
                    return False
            return True
    def __repr__ (self):
        r = []
        for name in self.__slots__:
            r.append ('%s=%r' % (name, getattr (self, name)))
        return '<%s %s>' % (self.__class__.__name__, ' '.join (r))

class CHOICE (ASN1):
    tags_f = {}
    tags_r = {}
    def _decode (self, Decoder src):
        cdef uint8_t tag
        cdef Decoder src0
        tag, src0 = src.next_APPLICATION()
        self.value = self.tags_r[tag]()
        self.value._decode (src0)
    def _encode (self, Encoder dst):
        for klass, tag in self.tags_f.iteritems():
            if isinstance (self.value, klass):
                with dst.TLV (tag, FLAGS_APPLICATION | FLAGS_STRUCTURED):
                    self.value._encode (dst)
                    return
        raise BadChoice (self.value)

class ENUMERATED (ASN1):
    tags_f = {}
    tags_r = {}
    value = 'NoValueDefined'
    def _decode (self, Decoder src):
        v = src.next_ENUMERATED()
        try:
            self.value = self.tags_r[v]
        except KeyError:
            raise BadEnum (v)
    def _encode (self, Encoder dst):
        with dst.TLV (TAGS_ENUMERATED):
            try:
                dst.emit_integer(self.tags_f[self.value])
            except KeyError:
                raise BadEnum (self.value)
    def __repr__ (self):
        return '<%s %s>' % (self.__class__.__name__, self.value)
