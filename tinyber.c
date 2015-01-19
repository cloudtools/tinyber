// -*- Mode: C -*-

#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include "tinyber.h"

#define CHECK(x) if ((x) == -1) { return -1; }

// --------------------------------------------------------------------------------
//  buffer interface
// --------------------------------------------------------------------------------

// output buffers are written in reverse, using predecrement.
// [this is the most efficient way to render BER - you write
//  a sub-object first, then prepend its length and type byte].

void
init_obuf (buf_t * self, uint8_t * buffer, unsigned int size)
{
  self->buffer = buffer;
  self->pos = size;
  self->size = size;
}

void
init_ibuf (buf_t * self, uint8_t * buffer, unsigned int size)
{
  self->buffer = buffer;
  self->pos = 0;
  self->size = size;
}

// emit data <src> (of length <n>) into output buffer <dst>.
static
int
emit (buf_t * dst, const uint8_t * src, int n)
{
  if (dst->pos < n) {
    return -1;
  } else {
    dst->pos -= n;
    memcpy (dst->buffer + dst->pos, src, n);
    return 0;
  }
}

// emit a single byte into an output stream.
static
int
emit_byte (buf_t * self, uint8_t b)
{
  if (self->pos < 1) {
    return -1;
  } else {
    self->buffer[--self->pos] = b;
    return 0;
  }
}

// ensure there are at least <n> bytes of input available.
int
ensure_input (buf_t * self, unsigned int n)
{
  if ((self->pos + n) <= self->size) {
    return 0;
  } else {
    return -1;
  }
}

// ensure there are at least <n> bytes of output available.
int
ensure_output (buf_t * self, unsigned int n)
{
  if (self->pos >= n) {
    return 0;
  } else {
    return -1;
  }
}

// --------------------------------------------------------------------------------
//  encoder
// --------------------------------------------------------------------------------

// how many bytes to represent length <n> (the 'L' in TLV).
static
int
length_of_length (asn1int_t n)
{
  if (n < 0x80) {
    return 1;
  } else {
    int r = 1;
    while (n) {
      n >>= 8;
      r += 1;
    }
    return r;
  }
}

// encode leng into a byte buffer.
static
void
encode_length (asn1int_t len, int n, uint8_t * buffer)
{
  // caller must ensure room.  see length_of_length above.
  if (len < 0x80) {
    buffer[0] = (uint8_t) len;
  } else {
    int i;
    buffer[0] = 0x80 | ((n-1) & 0x7f);
    for (i=1; i < n; i++) {
      buffer[n-i] = len & 0xff;
      len >>= 8;
    }
  }
}

// encode an integer, ASN1 style.
// two's complement with the minimum number of bytes.
int
encode_INTEGER (buf_t * o, asn1int_t n)
{
  asn1int_t n0 = n;
  asn1int_t i = 0;
  uint8_t byte = 0x80; // for n==0
  uint8_t result[16]; // plenty of room up to uint128_t
  while (1) {
    n >>= 8;
    if (n0 == n) {
      if ((n == -1) && (!(byte & 0x80) || (i == 0))) {
	// negative, but high bit clear
	result[15-i] = 0xff;
	i += 1;
      } else if ((n == 0) && (byte & 0x80)) {
	// positive, but high bit set
	result[15-i] = 0x00;
	i += 1;
      }
      break;
    } else {
      byte = n0 & 0xff;
      result[15-i] = byte;
      i += 1;
      n0 = n;
    }
  }
  // for machine-sized ints, lol is one byte, tag is one byte.
  // Note: emit() works in reverse.
  CHECK (emit (o, result + (16 - i), i));  // V
  CHECK (emit_byte (o, (uint8_t) i));      // L
  CHECK (emit_byte (o, TAG_INTEGER));      // T
  return 0;
}

int
encode_BOOLEAN (buf_t * o, int value)
{
  static const uint8_t encoded_bool_true[3]  = {0x01, 0x01, 0xff};
  static const uint8_t encoded_bool_false[3] = {0x01, 0x01, 0x00};
  if (value) {
    CHECK (emit (o, encoded_bool_true, sizeof(encoded_bool_true)));
  } else {
    CHECK (emit (o, encoded_bool_false, sizeof(encoded_bool_false)));
  }
  return 0;
}

int
encode_OCTET_STRING (buf_t * o, uint8_t * src, int src_len)
{
  int mark = o->pos;
  CHECK (emit (o, src, src_len));
  CHECK (encode_TLV (o, mark, TAG_OCTETSTRING));
  return 0;
}

// assuming the encoded value has already been emitted (starting at position <mark>),
//  emit the length and tag for that value.
int
encode_TLV (buf_t * o, unsigned int mark, uint8_t tag)
{
  int length = mark - o->pos;
  uint8_t encoded_length[6];
  uint8_t lol;
  // compute length of length
  lol = length_of_length (length);
  // ensure room for length
  CHECK (ensure_output (o, lol));
  // encode & emit the length
  encode_length (length, lol, encoded_length);
  CHECK (emit (o, encoded_length, lol));
  // emit tag
  CHECK (emit_byte (o, tag));
  return 0;
}

// --------------------------------------------------------------------------------
//  decoder
// --------------------------------------------------------------------------------

int
decode_length (buf_t * src, uint32_t * length)
{
  uint8_t lol;
  // assure at least one byte [valid for length == 0]
  CHECK (ensure_input (src, 1));
  // 2) get length
  if (src->buffer[src->pos] < 0x80) {
    // one-byte length
    *length = src->buffer[src->pos++];
    return 0;
  } else if (src->buffer[src->pos] == 0x80) {
    // indefinite length
    return -1;
  } else {
    // long definite length from, lower 7 bits
    // give us the number of bytes of length.
    lol = src->buffer[src->pos++] & 0x7f;
    if (lol > 4) {
      // we don't support lengths > 32 bits
      return -1;
    } else {
      CHECK (ensure_input (src, lol));
      uint8_t i;
      uint32_t n=0;
      for (i=0; i < lol; i++) {
	n = (n << 8) | src->buffer[src->pos++];
      }
      *length = n;
      return 0;
    }
  }
}


int
decode_TLV (asn1raw_t * dst, buf_t * src)
{
  uint8_t tag;
  uint32_t length;
  // 1) get tag
  tag = src->buffer[src->pos++];
  if ((tag & 0x1f) == 0x1f) {
    return -1; // multi-byte tag
  } else {
    // read the length
    CHECK (decode_length (src, &length));
    CHECK (ensure_input (src, length));
    dst->type = tag;
    dst->length = length;
    dst->value = src->buffer + src->pos;
    src->pos += length;
    return 0;
  }
}

asn1int_t
decode_INTEGER (asn1raw_t * src)
{
  uint8_t length = src->length;
  if (length == 0) {
    return 0;
  } else {
    asn1int_t n;
    uint8_t pos = 0;
    n = src->value[pos];
    if (n & 0x80) {
      // negative
      n = n - 0x100;
    }
    length -= 1;
    while (length) {
      pos += 1;
      n = (n << 8) | src->value[pos];
      length -= 1;
    }
    return n;
  }
}

int
decode_BOOLEAN (asn1raw_t * src)
{
  return (src->value[0] == 0xff);
}

int
decode_structured (asn1raw_t * src, asn1raw_t * dst, int * n)
{
  // create a buffer to iterate through the encoded data
  buf_t src0;
  init_ibuf (&src0, src->value, src->length);
  int i = 0;
  while (1) {
    if (i > *n) {
      // too many elements.
      return -1;
    } else if (src0.pos == src0.size) {
      break;
    }
    // unwrap TLV for each element.
    CHECK (decode_TLV (&dst[i], &src0));
    i++;
  }
  // tell the caller how many entries were present.
  *n = i;
  return 0;
}