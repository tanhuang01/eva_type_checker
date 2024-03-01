import unittest
from tests import eva_tc
from parser import to_eva_lst
import Type


class TestBlock(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_basic_if(self):
        self.assertEqual(eva_tc.tc(to_eva_lst('''
                (begin 
                    (var y 10)
                    (var x 10)
                    (set x (+ y x))
                    
                    (while (<= x 10) 
                        (set x (- x 1))
                    )
                    x
                )
            ''')), Type.number)
