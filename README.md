
TinyBER
=======

TinyBER is a very small, limited ASN.1 BER codec meant for use on
embedded devices (or anywhere code size is restricted).

Usage
-----

TinyBER is designed for ad-hoc encoding and decoding of data, it does
not use code generation - though it could theoretically be paired with
a generator.

See the file test.c for examples of how to use the codec.

Buffers
-------

A simple ``buf_t`` structure is used for both input and output::

    typedef struct {
      uint8_t * buffer;
      unsigned int pos;
      unsigned int size;
    } buf_t;

Encoding
--------

Encoding is a little unusual.  In the interest of efficiency, data can
be encoded directly into an output buffer - backwards.  Because asn.1
structures tend to accumulate in reverse (the Type and Length precede
the Value in the stream), the most efficient way to *encode* them is to
do so in reverse.

For example, to encode a SEQUENCE of objects there are three steps::

    int mark0 = obuf.pos;
    CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "ghi", 3));
    CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "def", 3));
    CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "abc", 3));
    CHECK (encode_TLV (&obuf, mark0, TAG_SEQUENCE));

1. Remember the stream's position (record the value of obuf.pos).
2. Encode each item of the SEQUENCE in reverse.
3. Emit the type and length for the entire sequence.

Note that the ``buf_t`` object is used in a 'predecrement' mode. When
you initialize a buffer for output, its ``pos`` field points to the
*end* of the buffer.  As data is written, ``pos`` moves backward.


Decoding
--------

When decoding an object, first call ``decode_TLV()`` to get the type,
length, and value pointers to the object::

    buf_t src;
    init_ibuf (&src, data, length);
    asn1raw dst;
    int r = decode_TLV (&dst, &src);

Now examine the type tag - if it is the expected type, then you may
further decode the value.  If the value itself makes up a more complex
structure, continue the procedure recursively.

A simple utility structure, ``asn1raw`` is used to represent a TLV::

    typedef struct {
      uint8_t type;
      int length;
      uint8_t * value;
    } asn1raw;

To decode a 'structured' element (i.e., a SEQUENCE or SET), create an
array of ``asn1raw`` objects, and pass it to ``decode_structured()``::

    asn1raw subs[50];
    int n = 50;
    int i;
    CHECK (decode_structured (ob, &subs[0], &n));

In this example we allow up to 50 sub-elements.  If more are present
in the stream an error will be returned.  If there are less than 50
the actual number will be set in ``n`` (i.e., ``n`` is an in-out
param).

Now that you have the metadata for each sub-element, you may
recursively continue decoding each one in turn.  (This could be viewed
as a form of recursive-descent parser).

Limitations
-----------

This is not a full BER codec by any stretch: for example it supports
only definite-length (i.e., actual length is always prepended), and as
such it can be used for DER encoding as long as care is taken to
follow the rules.

It does not support INTEGERs larger than a machine int (int64_t by default).

Still missing are direct support for SET, APPLICATION, BITSTRING,
ENUMERATED, OIDs, etc... though if you are familiar with BER they can be
implemented with relative ease.

