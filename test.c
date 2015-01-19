
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include <ctype.h>

#include "tinyber.h"

#define CHECK(x) if ((x) == -1) { return -1; }

static
void
dump_hex (uint8_t * values, int n)
{
  int i;
  for (i=0; i < n; i++) {
    fprintf (stderr, "%02x", values[i]);
  }
}

static
void
indent (int n)
{
  for (int i=0; i < n; i++) {
    fprintf (stderr, "  ");
  }
}

static
void
dump_tlv (asn1raw_t * ob)
{
  fprintf (stderr, "{%d %d ", ob->type, ob->length);
  dump_hex (ob->value, ob->length);
  fprintf (stderr, "}\n");
}

static
void
dump_octet_string (uint8_t * s, unsigned int len)
{
  int i;
  for (i=0; i < len; i++) {
    if (isprint (s[i])) {
      fputc (s[i], stderr);
    } else {
      fprintf (stderr, "\\x");
      dump_hex (s + i, 1);
    }
  }
}

int
dump (asn1raw_t * ob, int depth)
{
  indent (depth);
  //dump_tlv (ob);
  indent (depth);
  switch (ob->type) {
  case TAG_INTEGER:
    fprintf (stderr, "%lld\n", decode_INTEGER (ob));
    break;
  case TAG_BOOLEAN:
    fprintf (stderr, decode_BOOLEAN (ob) ? "TRUE\n" : "FALSE\n");
    break;
  case TAG_OCTETSTRING:
    fputc ('\'', stderr);
    dump_octet_string (ob->value, ob->length);
    fprintf (stderr, "\'\n");
    break;
  case TAG_SEQUENCE: {
    asn1raw_t subs[50];
    int n = 50;
    int i;
    CHECK (decode_structured (ob, &subs[0], &n));
    indent (depth);
    fprintf (stderr, "SEQUENCE {\n");
    for (i=0; i < n; i++) {
      CHECK (dump (&subs[i], depth + 1));
    }
    indent (depth);
    fprintf (stderr, "}\n");
  }
    break;
  default:
    fprintf (stderr, "unhandled tag %d\n", ob->type);
  }
  return 0;
}

int
decode_bytes (uint8_t * data, int length)
{
  buf_t src;
  init_ibuf (&src, data, length);
  asn1raw_t dst;
  fprintf (stderr, "decode ");
  dump_hex (data, length);
  fprintf (stderr, "\n");  
  int r = decode_TLV (&dst, &src);
  if (r) {
    fprintf (stderr, "\n *** error decoding at position %d ***\n\n", src.pos);
    return -1;
  } else {
    dump (&dst, 0);
    return 0;
  }
}


int
test_decoder (void)
{
  fprintf (stderr, "\n--- testing decoder ---\n");
  uint8_t data0[6] = "\x02\x04@\x00\x00\x00";
  decode_bytes (data0, sizeof(data0));
  uint8_t data1[] = "0\t\x02\x01\x00\x02\x01\x01\x02\x01\x02";
  decode_bytes (data1, sizeof(data1));
  uint8_t data2[] = "\x30\x11\x02\x04\xff\x61\x63\x39\x30\x09\x02\x01\x00\x01\x01\x00\x02\x01\x02";
  decode_bytes (data2, sizeof(data2));
  return 0;
}

int
test_encoder (void)
{
  fprintf (stderr, "\n--- testing encoder ---\n");
  uint8_t buffer[512];
  buf_t obuf;
  init_obuf (&obuf, buffer, sizeof(buffer));

  memset (buffer, 0, sizeof(buffer));
  
  // [-3141, False, ['abc', 'def', 'ghi'], 3735928559, 'Mary had a little lamb. I ate it with a mint sauce.']

  int mark = obuf.pos;
  uint8_t msg[] = "Mary had a little lamb. I ate it with a mint sauce.";
  CHECK (encode_OCTET_STRING (&obuf, msg, sizeof(msg) - 1)); // elide NUL
  CHECK (encode_INTEGER (&obuf, 0xdeadbeef));

  int mark0 = obuf.pos;
  CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "ghi", 3));
  CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "def", 3));
  CHECK (encode_OCTET_STRING (&obuf, (uint8_t *) "abc", 3));
  CHECK (encode_TLV (&obuf, mark0, TAG_SEQUENCE));

  CHECK (encode_BOOLEAN (&obuf, 0));
  CHECK (encode_INTEGER (&obuf, -3141));
  CHECK (encode_TLV (&obuf, mark, TAG_SEQUENCE));

  int length = mark - obuf.pos;
  fprintf (stderr, "length=%d\n", length);
  dump_hex ((buffer + sizeof(buffer)) - length, length);
  fprintf (stderr, "\n");
  decode_bytes ((buffer + sizeof(buffer)) - length, length);
  return 0;
}

int
main (int argc, char * argv[])
{
  test_decoder();
  test_encoder();
}