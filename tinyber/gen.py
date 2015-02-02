#!/usr/bin/env python
# -*- Mode: Python -*-

import os
import sys

from asn1ate import parser
from asn1ate.sema import *
from tinyber.walker import Walker

def main():
    import argparse
    p = argparse.ArgumentParser (description='tinyber code generator.')
    p.add_argument ('-o', '--outdir', help="output directory (defaults to location of input file)", default='')
    p.add_argument ('-l', '--lang', help="output language ('c' or 'python')", default='c')
    p.add_argument ('file', help="asn.1 spec", metavar="FILE")
    args = p.parse_args()

    with open (args.file) as f:
        asn1def = f.read()

    parse_tree = parser.parse_asn1(asn1def)
    modules = build_semantic_model(parse_tree)
    assert (len(modules) == 1)
    base, ext = os.path.splitext (args.file)
    parts = os.path.split (base)
    module_name = parts[-1]
    if args.outdir:
        path = os.path.join (args.outdir, module_name)
    else:
        path = base

    if args.lang == 'python':
        from tinyber.py_nodes import PythonBackend as Backend
        from tinyber import py_nodes as nodes
    elif args.lang == 'c':
        from tinyber.c_nodes import CBackend as Backend
        from tinyber import c_nodes as nodes

    # pull in the python-specific node implementations
    walker = Walker (modules[0], nodes)
    walker.walk()

    backend = Backend (walker, module_name, path)
    backend.generate_code()
