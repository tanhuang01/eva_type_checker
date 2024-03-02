import unittest
from tests import eva_tc
from parser import to_eva_lst, to_eva_block
import Type


class TestAlias(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_basic_alias(self):
        (eva_tc.tc(to_eva_block('''
            (type int number)
            
            (type ID int)
            
            (type Index ID)
        
        ''')))

        self.assertEqual(eva_tc.tc(to_eva_block('''
            (def _square ((x int)) -> int (* x x))
            
            (_square 2)
        
        ''')), Type.number)

        self.assertEqual(eva_tc.tc(to_eva_block('''
            (def promote ((user_id ID)) -> ID (+ 1 user_id))
            
            (promote 1)
        
        ''')), Type.number)

    def test_basis_alias_to_check_variable(self):
        self.assertEqual(eva_tc.tc(to_eva_block('''
                (var (x Index) 1)

                x
        ''')), Type.number)
