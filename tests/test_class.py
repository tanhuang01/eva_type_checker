import unittest
from tests import eva_tc
from parser import to_eva_lst, to_eva_block
import Type


class TestClass(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_a_class_define(self):
        self.assertEqual(eva_tc.tc(to_eva_block('''
            (class Point null
                (begin 
                    (var (x number) 0)
                    (var (y number) 0)
                    
                    (def constructor((self Point)(x number)(y number)) -> Point 
                        (begin 
                            self    
                    ))
                    
                    (def calc ((self Point)) -> number
                        1
                    )
                        
            ))
            
            1
        
        ''')), Type.number)


