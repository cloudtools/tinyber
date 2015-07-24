
# this is a first step toward moving this test suite into the 'tests'
#  directory where it can be run with unittest.

# 1) generate t0.[ch]

# this is based on ../tests/utils.py

from asn1ate import parser
from asn1ate.sema import *
from tinyber.walker import Walker

from tinyber.c_nodes import CBackend
from tinyber import c_nodes as nodes

import unittest
import os

from tests.utils import generate_c

class TestCoverage (unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import os
        generate_c ('tests/coverage/t0.asn', 'tests/coverage/t0', '.')
        from distutils.core import run_setup
        run_setup ('tests/coverage/setup.py', ['build_ext', '--inplace'])
        # ARRGGGHGHGHHHHHHHHHH
        #import pdb; pdb.set_trace()
        #os.rename ('t0_wrap.so', 'test/coverage/t0_wrap.so')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_build_extension(self):
        # dummy
        pass

if __name__ == '__main__':
    unittest.main()
