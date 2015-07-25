from asn1ate import parser
from asn1ate.sema import *
from tinyber.walker import Walker

from tinyber.py_nodes import PythonBackend as Backend
from tinyber import py_nodes as nodes


def generate_py(infilename, outfilename, path):
    class FakeArgs(object):
        no_standalone = False

    import os
    with open(infilename) as f:
        asn1def = f.read()

    parse_tree = parser.parse_asn1(asn1def)
    modules = build_semantic_model(parse_tree)
    assert (len(modules) == 1)

    module_name = outfilename
    args = FakeArgs()

    # pull in the python-specific node implementations
    walker = Walker(modules[0], nodes)
    walker.walk()

    backend = Backend(args, walker, module_name, path)
    backend.generate_code()

from tinyber.c_nodes import CBackend
from tinyber import c_nodes

def generate_c(infilename, outfilename, path):
    class FakeArgs(object):
        no_standalone = False

    import os
    with open(infilename) as f:
        asn1def = f.read()

    parse_tree = parser.parse_asn1(asn1def)
    modules = build_semantic_model(parse_tree)
    assert (len(modules) == 1)

    module_name = outfilename
    args = FakeArgs()

    # pull in the python-specific node implementations
    walker = Walker(modules[0], c_nodes)
    walker.walk()

    backend = CBackend(args, walker, module_name, path)
    backend.generate_code()


def test_reload():
    import sys
    sys.path[:0] = '.'

    # reload tests since we just created a new module
    import tests
    reload(tests)
