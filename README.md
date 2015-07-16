
TinyBER
=======

![tinyber logo](http://www.rps.org/~/media/Exhibitions/2013/June/25/Images%20for%20Science/019_Tardigr_Pm_Craterl_400x2_2010_Nicole_Ottawa.ashx?bc=White&mw=400 "tardigrade")

TinyBER is a very small, limited ASN.1 BER codec and code generator
meant for use on embedded devices (or anywhere code size is
restricted).  The generated code uses fixed-size structures and makes
no calls to malloc or free.

Install
-------

```shell
$ sudo python setup.py install
```

Usage
-----

TinyBER can be used for ad-hoc encoding and decoding of data, but it
also comes with a limited code generator.

Buffers
-------

A simple ``buf_t`` structure is used for both input and output::

```c
    typedef struct {
      uint8_t * buffer;
      unsigned int pos;
      unsigned int size;
    } buf_t;
```

Encoding
--------

Encoding is a little unusual.  In the interest of efficiency, data can
be encoded directly into an output buffer - backwards.  Because asn.1
structures tend to accumulate in reverse (the Type and Length precede
the Value in the stream), the most efficient way to *encode* them is to
do so in reverse.

For example, to encode a SEQUENCE of objects there are three steps::

```c
    int mark0 = obuf.pos;
    CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "ghi", 3));
    CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "def", 3));
    CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "abc", 3));
    CHECK (encode_TLV (&obuf, mark0, TAG_SEQUENCE));
```

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

```c
    buf_t src;
    init_ibuf (&src, data, length);
    asn1raw dst;
    int r = decode_TLV (&dst, &src);
```

Now examine the type tag - if it is the expected type, then you may
further decode the value.  If the value itself makes up a more complex
structure, continue the procedure recursively.

A simple utility structure, ``asn1raw`` is used to represent a TLV::

```c
    typedef struct {
      uint8_t type;
      int length;
      uint8_t * value;
      } asn1raw;
```

To decode a 'structured' element (i.e., a SEQUENCE or SET), create an
array of ``asn1raw`` objects, and pass it to ``decode_structured()``::

```c
    asn1raw subs[50];
    int n = 50;
    int i;
    CHECK (decode_structured (ob, &subs[0], &n));
```

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
OIDs, etc... though if you are familiar with BER they can be
implemented with relative ease.

Because tinyber requires fixed-sized elements for all structures (to
avoid malloc & free), using recursive (or mutually recursive) types is
impossible::

```asn1
    List ::= SEQUENCE {
        car INTEGER,
	    cdr List OPTIONAL
    }
```

Tinyber can't make a fixed-sized structure that might hold a
potentially infinite list, so it cannot handle this kind of
construction.

Code Generation
---------------

Included is a code generator, ``tinyber_gen.py``, which can generate
type definitions and BER encoders/decoders for a limited subset of the
ASN.1 specification language (X.680) in C and Python.

```text
usage: tinyber_gen [-h] [-o OUTDIR] [-l LANG] [-ns] FILE

tinyber ASN.1 BER/DER code generator.

positional arguments:
  FILE                  asn.1 spec

optional arguments:
  -h, --help            show this help message and exit
  -o OUTDIR, --outdir OUTDIR
                        output directory (defaults to location of input file)
  -l LANG, --lang LANG  output language ('c' or 'python')
  -ns, --no-standalone  [python only] do not insert codec.py into output file.
```

For example::

```bash
    beast:tinyber rushing$ python tinyber_gen.py -l c thing.asn1
    beast:tinyber rushing$ ls -l thing.[ch]
    -rw-r--r--  1 rushing  staff  20240 Jan 20 13:08 thing.c
    -rw-r--r--  1 rushing  staff   4939 Jan 20 13:08 thing.h
    beast:tinyber rushing$
```


The code generator requires the
[asn1ate package](https://github.com/kimgr/asn1ate) to be installed.
``asn1ate`` is a parser for X.680 designed for use by code generators.


Module Design
-------------

If your goal is to keep your codec as small as possible, a good approach is
to segregate your packet types into 'server' and 'client' groups.  Otherwise
the outermost CHOICE PDU will force the inclusion of both server and client
encoders and decoders on both sides.  If you use two different PDU's, you will
get only the encoders and decoders needed for each side.  For example::

```asn1
    ThingModule DEFINITIONS ::= BEGIN

      ThingClientMessage ::= CHOICE {
        login-request  [0] LoginRequest,
        status-request [1] StatusRequest,
	  }

      ThingServerMessage ::= CHOICE {
          login-reply  [0] LoginReply,
          status-reply [1] StatusReply
      }
```

Licensing
---------
This software is licensed under the Apache 2 license. However, the output,
which is included into other projects, is not encumbered with any license
restrictions. See the LICENSE.txt for more details.
