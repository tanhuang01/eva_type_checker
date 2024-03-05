import unittest
from tests import eva_tc
from parser.EvaParser import to_eva_lst
import Type


class TestPrimitive(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_number(self):
        self.assertEqual(eva_tc.tc(1), Type.number)
        self.assertEqual(eva_tc.tc(42), Type.number)

    def test_string(self):
        self.assertEqual(eva_tc.tc('"a"'), Type.string)
        self.assertEqual(eva_tc.tc('"to_be_continue"'), Type.string)

    def test_boolean(self):
        self.assertEqual(eva_tc.tc(to_eva_lst('False')), Type.boolean)
        self.assertEqual(eva_tc.tc('True'), Type.boolean)
        self.assertEqual(eva_tc.tc('"False"'), Type.boolean)
        self.assertEqual(eva_tc.tc('"True"'), Type.boolean)
