import unittest
from tests import eva_tc
import Type


class TestMath(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_binary(self):
        # numbers
        self.assertEqual(eva_tc.tc(['+', 3, 5]), Type.number)
        self.assertEqual(eva_tc.tc(['-', 3, 5]), Type.number)
        self.assertEqual(eva_tc.tc(['*', 3, 5]), Type.number)
        self.assertEqual(eva_tc.tc(['/', 3, 5]), Type.number)

        # string concat
        self.assertEqual(eva_tc.tc(['+', '"hello"', '"world"']), Type.string)
        # string should not support `-` operation
        with self.assertRaises(RuntimeError):
            eva_tc.tc(['-', '"hello"', '"world"'])
