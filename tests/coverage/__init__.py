
# build t0_wrap.pyx before doing any of the other tests.

from tests.utils import generate_c

print 'building from __init__ script...'
generate_c ('tests/coverage/t0.asn', 't0', 'tests/coverage')
from distutils.core import run_setup
run_setup ('tests/coverage/setup.py', ['build_ext', '--inplace'])

import t0_test_encoder
import t0_c_driver
