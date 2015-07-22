from asn1ate import parser
from asn1ate.sema import *
from tinyber.walker import Walker

from tinyber.py_nodes import PythonBackend as Backend
from tinyber import py_nodes as nodes


def generate(infilename, outfilename):
    class FakeArgs(object):
        no_standalone = False

    import os
    print(os.path.realpath(infilename))
    print(os.path.realpath(outfilename))
    with open(infilename) as f:
        asn1def = f.read()

    parse_tree = parser.parse_asn1(asn1def)
    modules = build_semantic_model(parse_tree)
    assert (len(modules) == 1)

    module_name = outfilename
    path = "tests"
    args = FakeArgs()

    # pull in the python-specific node implementations
    walker = Walker(modules[0], nodes)
    walker.walk()

    backend = Backend(args, walker, module_name, path)
    backend.generate_code()

def test_reload():
    import sys
    sys.path[:0] = '.'

    # reload tests since we just created a new module
    import tests
    reload(tests)
