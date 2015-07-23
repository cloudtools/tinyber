# -*- Mode: Python -*-

# base for python codecs.

# NOTE: the encoder accumulates in *reverse*.


class DecodingError(Exception):
    pass


class IndefiniteLength(DecodingError):
    pass


class ElementTooLarge(DecodingError):
    pass


class Underflow(DecodingError):
    pass


class UnexpectedType(DecodingError):
    pass


class UnexpectedFlags(DecodingError):
    pass


class ConstraintViolation(DecodingError):
    pass


class BadChoice(DecodingError):
    pass


class ExtraData(DecodingError):
    pass


class FLAG:
    UNIVERSAL = 0x00
    STRUCTURED = 0x20
    APPLICATION = 0x40
    CONTEXT = 0x80


class TAG:
    BOOLEAN = 0x01
    INTEGER = 0x02
    BITSTRING = 0x03
    OCTETSTRING = 0x04
    NULLTAG = 0x05
    OID = 0x06
    ENUMERATED = 0x0A
    UTF8STRING = 0x0C
    SEQUENCE = 0x10
    SET = 0x11


class Decoder:

    def __init__(self, data, pos=0, end=None):
        self.data = data
        self.pos = pos
        if end is None:
            end = len(data)
        self.end = end

    def pop_byte(self):
        if self.pos + 1 > self.end:
            raise Underflow(self)
        else:
            try:
                val = ord(self.data[self.pos])
            except TypeError:
                val = self.data[self.pos]
            self.pos += 1
            return val

    def pop(self, nbytes):
        if self.pos + nbytes > self.end:
            raise Underflow(self)
        else:
            r = Decoder(self.data, self.pos, self.pos + nbytes)
            self.pos += nbytes
            return r

    def pop_bytes(self, nbytes):
        if self.pos + nbytes > self.end:
            raise Underflow(self)
        else:
            result = self.data[self.pos:self.pos+nbytes]
            self.pos += nbytes
            return result

    def done(self):
        return self.pos == self.end

    def assert_done(self):
        if self.pos != self.end:
            raise ExtraData(self)

    def get_length(self):
        val = self.pop_byte()
        if val < 0x80:
            # one-byte length
            return val
        elif val == 0x80:
            raise IndefiniteLength(self)
        else:
            # get length of length
            lol = val & 0x7f
            if lol > 4:
                raise ElementTooLarge(self)
            else:
                n = 0
                while lol:
                    n = (n << 8) | self.pop_byte()
                    lol -= 1
                return n

    def get_multibyte_tag(self):
        r = 0
        while 1:
            val = self.pop_byte()
            r <<= 7
            r |= val & 0x7f
            if not val & 0x80:
                break
        return r

    def get_tag(self):
        b = self.pop_byte()
        tag = b & 0b11111
        flags = b & 0b1100000
        if tag == 0b11111:
            tag = self.get_multibyte_tag()
        return tag, flags

    def check(self, expected_tag, expected_flags=0):
        tag, flags = self.get_tag()
        if tag != expected_tag:
            raise UnexpectedType(tag, expected_tag)
        if flags != expected_flags:
            raise UnexpectedFlags(flags, expected_flags)

    def next(self, expected, flags=0):
        self.check(expected, flags)
        length = self.get_length()
        return self.pop(length)

    def get_integer(self, length):
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

    def next_INTEGER(self, min_val, max_val):
        self.check(TAG.INTEGER)
        r = self.get_integer(self.get_length())
        if min_val is not None and r < min_val:
            raise ConstraintViolation(r, min_val)
        if max_val is not None and r > max_val:
            raise ConstraintViolation(r, max_val)
        return r

    def next_OCTET_STRING(self, min_size, max_size):
        self.check(TAG.OCTETSTRING)
        r = self.pop_bytes(self.get_length())
        if min_size is not None and len(r) < min_size:
            raise ConstraintViolation(r, min_size)
        if max_size is not None and len(r) > max_size:
            raise ConstraintViolation(r, max_size)
        return r

    def next_BOOLEAN(self):
        self.check(TAG.BOOLEAN)
        assert(self.pop_byte() == 1)
        return self.pop_byte() != 0

    def next_ENUMERATED(self):
        self.check(TAG.ENUMERATED)
        return self.get_integer(self.get_length())

    def next_APPLICATION(self):
        tag, flags = self.get_tag()
        if not flags & FLAG.APPLICATION:
            raise UnexpectedFlags(self, flags, FLAG.APPLICATION)
        else:
            return tag, self.pop(self.get_length())


class EncoderContext:

    def __init__(self, enc, tag, flags):
        self.enc = enc
        self.tag = tag
        self.flags = flags
        self.pos = enc.length

    def __enter__(self):
        pass

    def __exit__(self, t, v, tb):
        self.enc.emit_length(self.enc.length - self.pos)
        self.enc.emit_tag(self.tag, self.flags)


class Encoder:

    def __init__(self):
        self.r = []
        self.length = 0

    def _chr(self, x):
        return bytearray((x,))

    def emit(self, data):
        self.r.insert(0, data)
        self.length += len(data)

    def emit_length(self, n):
        if n < 0x80:
            self.emit(self._chr(n))
        else:
            r = []
            while n:
                r.insert(0, self._chr(n & 0xff))
                n >>= 8
            r.insert(0, self._chr(0x80 | len(r)))
            self.emit(bytearray().join(r))

    def emit_tag(self, tag, flags=0):
        if tag < 0x1f:
            self.emit(self._chr(tag | flags))
        else:
            while tag:
                if tag < 0x80:
                    self.emit(self._chr(tag))
                else:
                    self.emit(self._chr((tag & 0x7f) | 0x80))
                tag >>= 7
            self.emit(self._chr(0x1f | flags))

    def TLV(self, tag, flags=0):
        return EncoderContext(self, tag, flags)

    def done(self):
        return bytearray().join(self.r)

    # base types

    # encode an integer, ASN1 style.
    # two's complement with the minimum number of bytes.
    def emit_integer(self, n):
        i = 0
        n0 = n
        byte = 0x80
        r = []
        while 1:
            n >>= 8
            if n0 == n:
                if n == -1 and ((not byte & 0x80) or i == 0):
                    # negative, but high bit clear
                    r.insert(0, self._chr(0xff))
                    i = i + 1
                elif n == 0 and (byte & 0x80):
                    # positive, but high bit set
                    r.insert(0, self._chr(0x00))
                    i = i + 1
                break
            else:
                byte = n0 & 0xff
                r.insert(0, self._chr(byte))
                i += 1
                n0 = n
        self.emit(bytearray().join(r))

    def emit_INTEGER(self, n):
        with self.TLV(TAG.INTEGER):
            self.emit_integer(n)

    def emit_OCTET_STRING(self, s):
        with self.TLV(TAG.OCTETSTRING):
            self.emit(s)

    def emit_BOOLEAN(self, v):
        with self.TLV(TAG.BOOLEAN):
            if v:
                self.emit(b'\xff')
            else:
                self.emit(b'\x00')


class ASN1:
    value = None

    def __init__(self, value=None):
        self.value = value

    def encode(self):
        e = Encoder()
        self._encode(e)
        return e.done()

    def decode(self, data):
        b = Decoder(data)
        self._decode(b)

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.value)


class SEQUENCE(ASN1):
    __slots__ = ()

    def __init__(self, **args):
        for k, v in args.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        r = []
        for name in self.__slots__:
            r.append('%s=%r' % (name, getattr(self, name)))
        return '<%s %s>' % (self.__class__.__name__, ' '.join(r))


class CHOICE(ASN1):
    tags_f = {}
    tags_r = {}

    def _decode(self, src):
        tag, src = src.next_APPLICATION()
        self.value = self.tags_r[tag]()
        self.value._decode(src)

    def _encode(self, dst):
        for klass, tag in self.tags_f.iteritems():
            if isinstance(self.value, klass):
                with dst.TLV(tag, FLAG.APPLICATION | FLAG.STRUCTURED):
                    self.value._encode(dst)
                    return
        raise BadChoice(self.value)


class ENUMERATED(ASN1):
    tags_f = {}
    tags_r = {}
    value = 'NoValueDefined'

    def _decode(self, src):
        v = src.next_ENUMERATED()
        self.value = self.tags_r[v]

    def _encode(self, dst):
        with dst.TLV(TAG.ENUMERATED):
            dst.emit_integer(self.tags_f[self.value])

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.value)


# try to pull in cython version if available.
try:
    from tinyber._codec import *
except ImportError:
    pass
