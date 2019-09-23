from atf import Device
import unittest


class TestDeviceMethods(unittest.TestCase):
    def test_serialno(self):
        self.assertIsNotNone(Device().serial_no)


if __name__ == '__main__':
    unittest.main(verbosity=2)