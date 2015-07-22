import unittest

from tinyber.c_nodes import int_max_size_type

class TestBasic(unittest.TestCase):

    def test_int8(self):
        size = "int8_t"
        self.assertEqual(int_max_size_type(-2**7, 0), size)
        self.assertEqual(int_max_size_type(-1, 0), size)
        self.assertEqual(int_max_size_type(-1, 2**7 - 1), size)
        self.assertEqual(int_max_size_type(-2**7, 2**7 - 1), size)
        self.assertNotEqual(int_max_size_type(0, 2**7), size)
        self.assertNotEqual(int_max_size_type(0, 2**7 - 1), size)

    def test_int16(self):
        size = "int16_t"
        self.assertEqual(int_max_size_type(-1, 256), size)
        self.assertEqual(int_max_size_type(-1, 2**15 - 1), size)
        self.assertEqual(int_max_size_type(-2**15, 2**15 - 1), size)
        self.assertNotEqual(int_max_size_type(0, 2**15), size)
        self.assertNotEqual(int_max_size_type(0, 2**15 - 1), size)

    def test_int32(self):
        size = "int32_t"
        self.assertEqual(int_max_size_type(-1, 2**16), size)
        self.assertEqual(int_max_size_type(-1, 2**31 - 1), size)
        self.assertEqual(int_max_size_type(-2**31, 2**31 - 1), size)
        self.assertNotEqual(int_max_size_type(-1, 2**31), size)
        self.assertNotEqual(int_max_size_type(0, 2**31), size)

    def test_int64(self):
        size = "int64_t"
        self.assertEqual(int_max_size_type(-1, 2**32), size)
        self.assertEqual(int_max_size_type(-1, 2**63 - 1), size)
        self.assertEqual(int_max_size_type(-2**63, 2**63 - 1), size)
        self.assertNotEqual(int_max_size_type(0, 2**63), size)
        with self.assertRaises(NotImplementedError):
            int_max_size_type(-1, 2**63)
        with self.assertRaises(NotImplementedError):
            int_max_size_type(-2**64, 0)

    def test_uint8(self):
        size = "uint8_t"
        self.assertEqual(int_max_size_type(0, 0), size)
        self.assertEqual(int_max_size_type(0, 2**8 - 1), size)
        # self.assertNotEqual(int_max_size_type(0, -1), size)
        self.assertNotEqual(int_max_size_type(0, 2**8), size)

    def test_uint16(self):
        size = "uint16_t"
        self.assertEqual(int_max_size_type(0, 256), size)
        self.assertEqual(int_max_size_type(0, 2**16 - 1), size)
        self.assertNotEqual(int_max_size_type(0, 2**16), size)

    def test_uint32(self):
        size = "uint32_t"
        self.assertEqual(int_max_size_type(0, 2**16), size)
        self.assertEqual(int_max_size_type(0, 2**32 - 1), size)
        self.assertNotEqual(int_max_size_type(0, 2**32), size)

    def test_uint64(self):
        size = "uint64_t"
        self.assertEqual(int_max_size_type(0, 2**32), size)
        self.assertEqual(int_max_size_type(0, 2**64 - 1), size)
        with self.assertRaises(NotImplementedError):
            int_max_size_type(0, 2**64)


if __name__ == '__main__':
    unittest.main()
