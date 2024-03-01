import unittest
from tests import eva_tc
import Type


class TestVariable(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_variable(self):
        self.assertEqual(eva_tc.tc(['var', 'x', 10]), Type.number)
        self.assertEqual(eva_tc.tc(['var', 'z', '"hello"']), Type.string)
        self.assertEqual(eva_tc.tc(['var', ['x2', 'string'], '"hello"']), Type.string)
        self.assertEqual(eva_tc.tc(['var', ['y', 'number'], 'x']), Type.number)
        self.assertEqual(eva_tc.tc('x'), Type.number)
        self.assertEqual(eva_tc.tc('VERSION'), Type.string)
