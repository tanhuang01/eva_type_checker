import unittest
from tests import eva_tc
from parser import to_eva_lst, to_eva_block
import Type


class TestBlock(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_basic_boolean(self):
        self.assertEqual(eva_tc.tc(to_eva_lst('(>= 10 1)')), Type.boolean)
        self.assertEqual(eva_tc.tc(['>=', '"10"', '"1"']), Type.boolean)
        with self.assertRaises(RuntimeError):
            eva_tc.tc('(>= \\"10\\" 1)')

    def test_basic_if(self):
        eva_tc.tc(to_eva_lst('(var x 10)'))
        self.assertEqual(eva_tc.tc(to_eva_lst('''
                (begin 
                    (var y 10)
                    (set x (+ y x))
                    
                    (if (<= x 10) 
                        (set x 1)
                        (set x 2)
                    )
                    y
                )
            ''')), Type.number)

    def test_basic_if_without_begin(self):
        eva_tc.tc(to_eva_lst('(var x 10)'))
        self.assertEqual(eva_tc.tc(to_eva_block('''
                (var y 10)
                (set x (+ y x))
                
                (if (<= x 10) 
                    (set x 1)
                    (set x 2)
                )
                y
            ''')), Type.number)
