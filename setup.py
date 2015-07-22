# -*- Mode: Python -*-

from setuptools import setup, find_packages
from distutils.extension import Extension

try:
    from Cython.Build import cythonize
    exts = cythonize ([Extension ("tinyber._codec", ['tinyber/_codec.pyx'])])
except ImportError:
    exts = []

setup (
    name             = 'tinyber',
    version          = '0.0.1',
    url              = "https://github.com/cloudtools/tinyber",
    packages         = find_packages(),
    description      = 'ASN.1 code generator for Python and C',
    scripts          = ['scripts/tinyber_gen', 'scripts/dax'],
    package_data     = {
        'tinyber': ['data/*.[ch]', 'tinyber/codec.py'],
        'tests': ['*.asn1'],
    },
    ext_modules      = exts,
    test_suite       = "tests",
    use_2to3         = True,
    install_requires = ['asn1ate>=0.5', 'pyparsing>=2.0.0'],
    )
