
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "tinyber.h"

#define FAILIF(x) do { if (x) { return -1; } } while(0)
#define CHECK(x) FAILIF(-1 == (x))

int
main (int argc, char * argv[])
{
  asn1int_t n = 0;
  buf_t obuf;
  buf_t ibuf;
  uint8_t buffer[1024];
  init_obuf (&obuf, buffer, sizeof(buffer));
  
  for (int64_t i=INT32_MIN; i <= INT32_MAX; i++) {

    if ((i % 1000000) == 0) {
      fprintf (stderr, ".");
    }

    init_obuf (&obuf, buffer, sizeof(buffer));
    n = i;
    encode_INTEGER (&obuf, &n);

    asn1raw_t tlv;
    asn1int_t m;
    init_ibuf (&ibuf, obuf.buffer + obuf.pos, obuf.size - obuf.pos);
    CHECK (decode_TLV (&tlv, &ibuf));
    FAILIF (tlv.type != TAG_INTEGER);
    m = decode_INTEGER (&tlv);
    if (m != i) {
      exit(1);
    }
  }
  fprintf (stderr, "success.\n");
  exit(0);
}
