# -*- Mode: Python -*-

from distutils.core import setup

setup (
    name             = 'tinyber_gen',
    packages         = ['tinyber'],
    description      = 'code generator for tinyber',
    scripts          = ['scripts/tinyber_gen_c', 'scripts/tinyber_gen_py'],
    )
