import unittest
from tests import eva_tc
from parser import to_eva_lst, to_eva_block
import Type


class TestLambda(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_lambda_function(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            (lambda ((x number)) -> number (* x x))

            ''')), Type.from_string('Fn<number<number>>'))

    def test_lambda_function_instant_call(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            ((lambda ((x number)) -> number (* x x)) 2)

            ''')), Type.number)

    def test_pass_lambda_as_parameter(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            (def onClick ((callback Fn<number<number>>)) -> number
                (begin 
                    (var x 20)
                    (var y 30)
                    (callback (+ x y))
                )
            )
            
            (onClick (lambda ((data number)) -> number (* data 10)))

            ''')), Type.number)

    def test_save_lambda_to_a_variable(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
            (var _square (lambda ((x number)) -> number (* x x)) )

            (_square 2)
            ''')), Type.number)
