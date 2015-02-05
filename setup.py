# -*- Mode: Python -*-

from setuptools import setup, find_packages
from distutils.extension import Extension

try:
    from Cython.Build import cythonize
    exts = cythonize ([Extension ("tinyber._codec", ['tinyber/_codec.pyx'])])
except ImportError:
    exts = []

setup (
    name             = 'tinyber_gen',
    packages         = find_packages(),
    description      = 'code generator for tinyber',
    scripts          = ['scripts/tinyber_gen'],
    package_data     = {'tinyber': ['data/*.[ch]', 'tinyber/codec.py']},
    ext_modules      = exts
    )
