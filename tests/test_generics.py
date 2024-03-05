import unittest

import Type
from parser import to_eva_block
from tests import eva_tc


class TestBlock(unittest.TestCase):
    def setUp(self) -> None:
        eva_tc.tc_global(to_eva_block('''
                       (def combine <K> ((x K)(y K)) -> K (+ x y))
                    '''))

    def test_a_basic_generics(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (combine <number> 2 3)
            ''')), Type.number)
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (combine <string> \\"x\\" \\"y\\")
            ''')), Type.string)

    def test_lambda_generics(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                ((lambda <K> ((x K)) -> K (+ x x)) <number> 2)
            ''')), Type.number)
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                ((lambda <K> ((x K)) -> K (+ x x)) <string> \\"x\\")
            ''')), Type.string)
