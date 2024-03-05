import unittest
from tests import eva_tc
from parser.EvaParser import to_eva_lst
import Type


class TestBlock(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_block(self):
        self.assertEqual(eva_tc.tc(
            ['begin',
             ['var', 'x', 10],
             ['var', 'y', 10],
             ['+', ['*', 'x', 10], 'y'],
             ]
        ), Type.number)

    def test_nested_block(self):
        self.assertEqual(eva_tc.tc(
            ['begin',
             ['var', 'x', 10],
             ['begin',
              ['var', 'x', '"hello"'],
              ['var', 'y', '"world"'],
              ],
             ['-', 'x', 5],
             ]
        ), Type.number)

    def test_access_parent_block(self):
        self.assertEqual(eva_tc.tc(
            ['begin',
             ['var', 'x', 10],
             ['begin',
              ['var', 'y', 10],
              ['+', 'y', 'x']
              ],
             ]
        ), Type.number)

    def test_variable_update(self):
        self.assertEqual(eva_tc.tc(
            ['begin',
             ['var', 'x', 10],
             ['begin',
              ['var', 'y', 10],
              ['set', 'x', ['+', 'y', 'x']]
              ],
             ]
        ), Type.number)

    def test_variable_block_raw(self):
        eva_tc.tc(to_eva_lst('(var x 10)'))

        self.assertEqual(eva_tc.tc(to_eva_lst('''
                (begin 
                    (begin 
                    (var y 10)
                    (set x (+ y x))
                ))
            ''')), Type.number)
