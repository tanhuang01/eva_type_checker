import unittest
from tests import eva_tc
from parser.EvaParser import to_eva_lst
import Type


class TestMath(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_binary(self):
        # numbers
        self.assertEqual(eva_tc.tc(to_eva_lst('(sum 1 5)')), Type.number)
