# -*- Mode: Python; indent-tabs-mode: nil -*-

from t0_ber import *

data = '300602016302016e'.decode ('hex')
b = Buf (data)
p = Pair()
p.decode (b)

e = Encoder()
p.encode (e)
print e.done().encode ("hex")

