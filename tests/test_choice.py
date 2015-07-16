import unittest

from asn1ate import parser
from asn1ate.sema import *
from tinyber.walker import Walker

from tinyber.py_nodes import PythonBackend as Backend
from tinyber import py_nodes as nodes

def generate(infilename, outfilename):
    class FakeArgs(object):
        no_standalone = False

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


class TestBasic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generate("tests/test_choice.asn1", "gen_choice")

    @classmethod
    def tearDownClass(cls):
        pass

    def test_choice1(self):
        import gen_choice_ber
        choice1 = gen_choice_ber.Choice1()


if __name__ == '__main__':
    unittest.main()
