import unittest

import Type
from parser import to_eva_block
from tests import eva_tc


class TestBlock(unittest.TestCase):
    def setUp(self) -> None:
        eva_tc.tc_global(to_eva_block('''
                        (type value (or number string))

                        (type ID (or string number))
                    '''))

    def test_a_basic_union(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (var (x value) 10) 
                
                x
            ''')), Type.number)

        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            x
        ''')), Type.string)

    def test_b_complex_union(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            (var (a value) 10)
            (var (b ID) \\"x\\")
            
            (def process((id ID)) -> number
                (+ a id))
                
            (process b)
            
            (+ a b)
            
        ''')), Type.number)

        with self.assertRaises(RuntimeError):
            eva_tc.tc_global(to_eva_block('''
                            (- a b) 
                        '''))

    def test_c_type_narrow(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (def accept ((x value)) -> value 
                    (begin 
                        (if (== (typeof x) \\"number\\")
                            (- 1 x)
                            (+ \\"y\\" x))
                    )
                )
                
                (accept 10)
            ''')), Type.number)

        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            (accept \\"x\\")
        ''')), Type.string)
