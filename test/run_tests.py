
# this is a first step toward moving this test suite into the 'tests'
#  directory where it can be run with unittest.

# 1) generate t0.[ch]

# this is based on ../tests/utils.py

from asn1ate import parser
from asn1ate.sema import *
from tinyber.walker import Walker

from tinyber.c_nodes import CBackend
from tinyber import c_nodes as nodes

def generate(infilename, outfilename):
    class FakeArgs(object):
        no_standalone = False

    import os
    with open(infilename) as f:
        asn1def = f.read()

    parse_tree = parser.parse_asn1(asn1def)
    modules = build_semantic_model(parse_tree)
    assert (len(modules) == 1)

    module_name = outfilename
    path = "."
    args = FakeArgs()

    # pull in the python-specific node implementations
    walker = Walker(modules[0], nodes)
    walker.walk()

    backend = CBackend(args, walker, module_name, path)
    backend.generate_code()


generate ('t0.asn', 't0')

# 2) build the cython extension in place.
from distutils.core import run_setup
run_setup ('setup.py', ['build_ext', '--inplace'])

# 3) run the test
execfile ("t0_c_test.py")
