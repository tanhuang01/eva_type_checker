"""
Typed eva: static type-checker
"""

import Type
from type_env import TypeEnvironment

global_env = TypeEnvironment({
    "VERSION": Type.string,
    "False": Type.boolean,
    "True": Type.boolean,
    "sum": Type.Type.from_string("Fn<number<number,number>>")
})


class EvaTC(object):
    """
        Infers and validate type of expression
    """

    def __init__(self):
        """
            create an instance with global environment
        """
        self.global_evn = global_env

    def tc_global(self, exp):
        return self.__tc_block(exp, global_env, True)

    def tc(self, exp, env: TypeEnvironment = global_env):

        # ------------------------------------------------------------
        # self-evaluating:
        # number: 10
        if self.__is_number(exp, env):
            return Type.number

        # boolean: True, 'True', 'False', False
        if self.__is_boolean(exp, env):
            return Type.boolean

        # string: "42"
        if self.__is_string(exp, env) and exp[0] == '"' and exp[0] == '"':
            return Type.string

        # ------------------------------------------------------------
        # binary, Math operations:
        # (+ 10 8)
        # (+ "hello", "world")
        if self.__is_binary(exp):
            return self.__binary(exp, env)

        # ------------------------------------------------------------
        # boolean binary:
        if self.__is_boolean_binary(exp):
            return self.__boolean_binary(exp, env)

        # ------------------------------------------------------------
        # type declaration: (type <name_new_type> <base>)
        # e.g (type int number)
        if exp[0] == 'type':
            _tag, name, base = exp

            # Type already defined
            if Type.has_own_property(name):
                raise RuntimeError(f"Type {name} has already defined")

            # No base type
            if not Type.has_own_property(base):
                raise RuntimeError(f"Type {base} is not defined")

            alias = Type.Alias(name, Type.get_property(base))
            Type.add_property(name, alias)

            return alias

        # ------------------------------------------------------------
        # Variable declaration: (var x 10)
        #
        # With type-check: (var (x number) "foo") # error!
        if exp[0] == 'var':
            _tag, name, value = exp
            value_type = self.tc(value, env)

            # with type check
            if isinstance(name, (list, tuple)):
                var_name, type_str = name
                expected_type = Type.Type.from_string(type_str)
                # check the type
                self.__expect(value_type, expected_type, value, exp)
                return env.define(var_name, expected_type)

            # single value
            return env.define(name, value_type)

        # ------------------------------------------------------------
        # Variable access: foo
        if self.__is_variable_name(exp):
            return env.look_up(exp)

        # ------------------------------------------------------------
        # set: (set x 10)
        if exp[0] == 'set':
            _tag, name, val = exp

            var_type = self.tc(name, env)
            val_type = self.tc(val, env)

            return self.__expect(val_type, var_type, val, exp)

        # ------------------------------------------------------------
        # Block: sequence of expressions:
        if exp[0] == 'begin':
            block_env = TypeEnvironment({}, env)  # parent environment is the current env
            return self.__tc_block(exp, block_env)

        #  --------------------------------------------
        #    if-expression:
        #   Γ ⊢ e1 : boolean  Γ ⊢ e2 : t  Γ ⊢ e3 : t
        #      ___________________________________________
        #
        #              Γ ⊢ (if e1 e2 e3) : t
        #
        #    Both branches should return the same time t.
        if exp[0] == 'if':
            _tag, condition, consequence, alternative = exp

            # boolean condition
            t1 = self.tc(condition, env)
            self.__expect(t1, Type.boolean, condition, exp)

            t2 = self.tc(consequence, env)
            t3 = self.tc(alternative, env)

            # same types for both branches:
            return self.__expect(t3, t2, exp, exp)

        if exp[0] == 'while':
            _tag, condition, body = exp

            # boolean condition
            t1 = self.tc(condition, env)
            self.__expect(t1, Type.boolean, condition, exp)

            # todo modify to support multilines of while body.
            return self.tc(body, env)

        # ------------------------------------------------------------
        # function declaration: (def square ((x number)) -> number (* x x))
        #
        # syntactic sugar: (var square (lambda ((x number)) -> number (* x x)) )
        if exp[0] == 'def':
            # extract for recursive check.
            _tag, name, params, _ret_del, return_type_str, body = exp

            # We have to extend environment with the function name BEFORE evaluating the body
            # this is need to support recursive function calls:
            param_types = [Type.Type.from_string(type_str) for name, type_str in params]
            return_type = Type.Type.from_string(return_type_str)
            env.define(name, Type.FunctionType(None, param_types, return_type))

            # delegate the 'def' to 'lambda'
            var_exp = self.__transform_def_to_var_lambda(exp)

            return self.tc(var_exp, env)

        # ------------------------------------------------------------
        # lambda function:  (lambda ((x number)) -> number (* x x))
        if exp[0] == 'lambda':
            _tag, params, _ret_del, return_type_str, body = exp
            return self.__tc_function(params, return_type_str, body, env)

        # ------------------------------------------------------------
        # function call: (square 2)
        if isinstance(exp, (tuple, list)):
            fn = self.tc(exp[0], env)
            arg_values = exp[1:]

            return self.__check_function_call(fn, arg_values, env, exp)

        raise RuntimeError(f"Unknown type for expression {exp}")

    @staticmethod
    def __is_number(exp, env):
        return isinstance(exp, (int, float))

    @staticmethod
    def __check_arity(exp, arity):
        if len(exp) - 1 != arity:
            raise RuntimeError(f"\nOperator {exp[0]} expects {arity} operands, {len(exp) - 1} "
                               f"given in {exp}")

    @staticmethod
    def __is_string(exp, env):
        return isinstance(exp, str)

    @staticmethod
    def __is_boolean(exp, env):
        return isinstance(exp, bool) or exp == '"True"' or exp == '"False"'

    @staticmethod
    def __is_binary(exp):
        return exp[0] in ['+', '-', '*', '/']

    @staticmethod
    def __is_boolean_binary(exp):
        return exp[0] in ('>', '<', '>=', '<=', '!=', '==')

    def __binary(self, exp, env):
        """
            binary operators.
        :param exp:
        :return:
        """
        self.__check_arity(exp, 2)

        t1 = self.tc(exp[1], env)
        t2 = self.tc(exp[2], env)

        allow_types = self.__get_operand_types_for_operator(exp[0])
        self.__expect_operator_type(t1, allow_types, exp)
        self.__expect_operator_type(t2, allow_types, exp)

        return self.__expect(t2, t1, exp[2], exp)

    def __expect(self, actual_type, expected_type, value, expression):
        if not actual_type.__eq__(expected_type):
            self.__throw(actual_type, expected_type, value, expression)
        return actual_type

    def __throw(self, actual_type, expected_type, value, expression):
        raise RuntimeError(f"Expected {expected_type} type for {value} in expression "
                           f"but got {actual_type} type.\n")

    @staticmethod
    def __get_operand_types_for_operator(operator):
        match operator:
            case '+':
                return [Type.number, Type.string, ]
            case '-':
                return [Type.number, ]
            case '*':
                return [Type.number, ]
            case '/':
                return [Type.number, ]
            case _:
                raise RuntimeError(f"Unsupported operator {operator}")

    @staticmethod
    def __expect_operator_type(_type, allow_types, exp):
        if not _type in allow_types:
            raise RuntimeError(f"\nUnSupported type : {_type} in {exp}, allowed: {allow_types}")

    @staticmethod
    def __is_variable_name(name):
        return isinstance(name, str) and name.isidentifier()

    # check the block.
    # sometimes, like `while`, `if`, `class`, etc., we 've got a block without 'begin'
    def __tc_block(self, block, env, with_begin=True):
        if with_begin:
            _tag, *expressions = block
        else:
            expressions = [block]  # put the command in a list for iterate
        result = None
        for exp in expressions:
            result = self.tc(exp, env)
        return result

    def __boolean_binary(self, exp, env):
        self.__check_arity(exp, 2)

        t1 = self.tc(exp[1], env)
        t2 = self.tc(exp[2], env)

        self.__expect(t2, t1, exp[2], env)
        return Type.boolean

    def __tc_function(self, params, return_type_str, body, env):
        return_type = Type.Type.from_string(return_type_str)

        # params environment and types
        params_record = {}
        param_types = []
        for name, type_str in params:
            param_type = Type.Type.from_string(type_str)
            params_record[name] = param_type
            param_types.append(param_type)

        fn_env = TypeEnvironment(params_record, env)

        # check the body in the fn_env
        actual_type = self.__tc_block(body, fn_env, body[0] == 'begin')

        # check the return type
        if not return_type == actual_type:
            raise RuntimeError(f"Expect function {body} to return {return_type}, but got {actual_type}")

        # Function type records it params and return type,
        # so we can use tem to validate function calls.
        # NOTE: The name of the function need to be None, which will generate by the __init__
        return Type.functions(None, param_types, return_type)

    # check function call
    def __check_function_call(self, fn: Type.FunctionType, arg_values, env, exp):
        arg_types = [self.tc(arg, env) for arg in arg_values]

        # check arity
        if len(fn.param_types) != len(arg_types):
            raise RuntimeError(f"\nFunction {exp[0]} {fn.name} expects {len(fn.param_types)}"
                               f" arguments, {len(arg_types)} given in {exp}.\n")

        # check if the argument types matches the parameter types
        for i in range(len(arg_types)):
            self.__expect(arg_types[i], fn.param_types[i], arg_values[i], exp)

        return fn.return_type

    def __transform_def_to_var_lambda(self, exp):
        _tag, name, params, _ret_del, return_type_str, body = exp
        return ['var', name, ['lambda', params, _ret_del, return_type_str, body]]
