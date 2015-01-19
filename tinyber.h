// -*- Mode: C -*-

#ifndef _TINYBER_H_
#define _TINYBER_H_

typedef int64_t asn1int_t;
//typedef int32_t asn1int_t;
typedef uint8_t asn1bool_t;

typedef enum {
  FLAG_UNIVERSAL   = 0x00,
  FLAG_STRUCTURED  = 0x20,
  FLAG_APPLICATION = 0x40,
  FLAG_CONTEXT     = 0x80,
} asn1flag;

typedef enum {
  TAG_BOOLEAN     = 0x01,
  TAG_INTEGER     = 0x02,
  TAG_BITSTRING   = 0x03,
  TAG_OCTETSTRING = 0x04,
  TAG_NULLTAG     = 0x05,
  TAG_OID         = 0x06,
  TAG_ENUMERATED  = 0x0A,
  TAG_UTF8STRING  = 0x0C,
  TAG_SEQUENCE    = 0x10 | FLAG_STRUCTURED,
  TAG_SET         = 0x11 | FLAG_STRUCTURED
} asn1type;

typedef struct {
  uint8_t type;
  int length;
  uint8_t * value;
} asn1raw_t;

typedef struct {
  uint8_t * buffer;
  unsigned int pos;
  unsigned int size;
} buf_t;

// buffer interface
void init_ibuf (buf_t * self, uint8_t * buffer, unsigned int size);
void init_obuf (buf_t * self, uint8_t * buffer, unsigned int size);

// decoder
int decode_BOOLEAN (asn1raw_t * src);
asn1int_t decode_INTEGER (asn1raw_t * src);
int decode_TLV (asn1raw_t * dst, buf_t * src);
int decode_length (buf_t * src, uint32_t * length);
int decode_structured (asn1raw_t * src, asn1raw_t * dst, int * n);

// encoder
int encode_TLV (buf_t * o, unsigned int mark, uint8_t tag);
int encode_INTEGER (buf_t * o, asn1int_t n);
int encode_BOOLEAN (buf_t * o, int value);
int encode_OCTET_STRING (buf_t * o, uint8_t * src, int src_len);

#endif // _TINYBER_H_
