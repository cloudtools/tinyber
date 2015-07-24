from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

exts = [
    Extension ("t0_wrap", ['t0_wrap.pyx', 't0.c', 'tinyber.c'])
    ]

# this is a complete hack to try to get unittest to work with this
#  generated module.
import os
here = os.getcwd()
src, _ = os.path.split (__file__)
os.chdir (src)
try:
    setup (
        ext_modules = cythonize (exts),
    )
finally:
    os.chdir (here)

