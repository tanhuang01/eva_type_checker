import unittest
from tests import eva_tc
from parser.EvaParser import to_eva_lst, to_eva_block
import Type


class TestFuncitons(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_function_from_string(self):
        self.assertEqual(Type.FunctionType.from_string("Fn<number>").name, "Fn<number>")
        self.assertEqual(Type.FunctionType.from_string("Fn<number<string,number>>").name,
                         "Fn<number<string,number>>")
        self.assertEqual(Type.FunctionType.from_string("Fn<number<number,number>>").name,
                         "Fn<number<number,number>>")
        self.assertEqual(Type.FunctionType.from_string("Fn<number<number,string>>").name,
                         "Fn<number<number,string>>")

        # todo: support nested function type
        # self.assertEqual(Type.FunctionType.from_string("Fn<number<Fn<number>>,string>>").name,
        #                  "Fn<number<Fn<number>>,string>>")

    def test_basic_function(self):
        self.assertEqual(eva_tc.tc(to_eva_block('''
                (def square ((x number)) -> number 
                    (* x x))
                    
                
            ''')), Type.FunctionType.from_string('Fn<number<number>>'))

    def test_complex_function(self):
        self.assertEqual(eva_tc.tc(to_eva_block('''
                (def calc ((x number) (y number)) -> number 
                    (begin 
                        (var z 30)
                        (+ (* x y) z)
                    ))
                
                
            ''')), Type.Type.from_string('Fn<number<number,number>>'))

    def test_complex_function_call(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (def calc ((x number) (y number)) -> number 
                    (begin 
                        (var z 30)
                        (+ (* x y) z)
                    ))
                    
                 (calc 10 10)
                
            ''')), Type.number)

    def test_inner_function_call(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (var value 100)
            
                (def calc ((x number) (y number)) -> Fn<number<number>> 
                    (begin 
                        (var z (+ x y))
                        (def inner ((foo number)) -> number
                            (+ (+ foo z) value)
                        )
                        inner
                    ))
                    
                (var fn (calc 10 20))
                
                (fn 30)
                
            ''')), Type.number)

    def test_factorial_function(self):
        self.assertEqual(eva_tc.tc_global(to_eva_block('''
                (def factorial ((x number)) -> number 
                    (if (== x 1) 
                        1
                        (* x (factorial (- x 1)))
                    )   
                )

                 (factorial 5)

            ''')), Type.number)

