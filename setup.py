# -*- Mode: Python -*-

from distutils.core import setup

setup (
    name             = 'tinyber_gen',
    packages         = ['tinyber'],
    description      = 'code generator for tinyber',
    scripts          = ['scripts/tinyber_gen'],
    package_data     = {'tinyber': ['data/*.[ch]', 'tinyber/codec.py']},
    )
