
The Tests
---------

The file ``t0.asn`` is meant to cover all the supported features of tinyber.
The file ``t0_gen_test.py`` auto-generates over 3000 tests in an attempt to
cover every possible error case.

Usage
-----

1. generate t0.[ch] from t0.asn.

    ``python ../tinyber_gen.py t0.asn``

2. build the cython extension.

    ``python setup.py build_ext --inplace``

3. run the test.

    ``python t0_gen_test.py``

