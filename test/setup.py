from setuptools import setup, find_packages
from distutils.extension import Extension
from Cython.Build import cythonize

ext = [
    Extension ("t0_test", ['t0_test.pyx', 't0.c', '../tinyber/data/tinyber.c'], include_dirs=['../tinyber/data/'])
    ]

setup (
    name             = 'tinyber_test',
    version          = '0.1',
    packages         = find_packages(),
    ext_modules      = cythonize (ext)
    )
