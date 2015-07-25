
# build t0_wrap.pyx before doing any of the other tests.

from tests.utils import generate_c, generate_py, test_reload

print 'building from __init__ script...'
generate_c ('tests/coverage/t0.asn', 't0', 'tests/coverage')
from distutils.core import run_setup
run_setup ('tests/coverage/setup.py', ['build_ext', '--inplace'])

generate_py ('tests/coverage/t0.asn', 't0', 'tests/coverage')
