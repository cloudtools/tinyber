
NOTE
----

This test suite is in the middle of being modified so that it can run under the
standard unittest suite and moved to ``../tests``.

The Tests
---------

The file ``t0.asn`` is meant to cover all the supported features of tinyber.
The file ``t0_gen_test.py`` auto-generates over 3000 tests in an attempt to
cover every possible error case.

Note: t0_c_test.py requires [shrapnel](https://github.com/ironport/shrapnel) for its BER codec.

Usage
-----

1. generate t0.[ch] from t0.asn.

    ``tinyber_gen -l c t0.asn``

2. build the cython extension.

    ``python setup.py build_ext --inplace``

3. run the test.

    ``python t0_c_test.py``



Demo
----

The file 'handwritten.c' is a sample of a hand-written encoding & decoding.
To build it:

```bash
$ gcc -O3 -I ../tinyber/data/ handwritten.c ../tinyber/data/tinyber.c -o handwritten
```

or just ``make test``.
