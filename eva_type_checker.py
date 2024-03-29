"""
Typed eva: static type-checker
"""
import re

import Type
from type_env import TypeEnvironment

global_env = TypeEnvironment({
    "VERSION": Type.string,
    "False": Type.boolean,
    "True": Type.boolean,
    "sum": Type.Type.from_string("Fn<number<number,number>>"),
    "typeof": Type.Type.from_string("Fn<string<Any>>"),
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

            if base[0] == 'or':
                options = base[1:]
                option_types = [Type.from_string(option_type_str) for option_type_str in options]
                return Type.add_property(name, Type.Union(name, option_types))
            else:
                # Type alias:
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
        # class declaration: (class <name> <super_class> <body>)
        if exp[0] == 'class':
            _tag, name, super_class_name, body = exp

            # resolve super class
            super_class_type = Type.get_property(super_class_name)

            # new class type
            class_type = Type.ClassType(name, super_class_type)

            # Class is accessible by name
            Type.add_property(name, class_type)
            # add to the cur environment
            env.define(name, class_type)

            # body is evaluate in the class environment
            self.__tc_block(body, class_type.env)
            return class_type

        # ------------------------------------------------------------
        # class instantiation: (new <class_name> <arguments> ...)
        if exp[0] == 'new':
            _tag, class_name, *arg_values = exp

            class_type = Type.get_property(class_name)
            if class_type is None:
                raise RuntimeError(f"Unknown class {class_name}")
            arg_types = [self.tc(arg_type) for arg_type in arg_values]

            return self.__check_function_call(
                class_type.get_field('constructor'),
                [class_type, *arg_types],
                env,
                exp
            )

        # ------------------------------------------------------------
        # Super expression: (super <class_name>)
        if exp[0] == 'super':
            _tag, class_name = exp

            class_type = Type.get_property(class_name)

            if class_type is None:
                raise RuntimeError(f"Unknown class {class_name}")

            return class_type.super_class

        # ------------------------------------------------------------
        # Property access: (prop <instance> <name>)
        if exp[0] == 'prop':
            _tag, instance, name = exp
            instance_type = self.tc(instance, env)  # instance_type is a ClassType
            return instance_type.get_field(name)

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
        # set:
        # e.g: (set x 10)
        # e.g: (set (prop self x) 10)
        if exp[0] == 'set':
            _tag, ref, val, = exp
            # 1. property assignment
            if ref[0] == 'prop':
                _tag, instance, prop_name = ref
                instance_type = self.tc(instance, env)
                value_type = self.tc(val, env)
                prop_type = instance_type.get_field(prop_name)
                return self.__expect(value_type, prop_type, val, exp)

            # 2. simple assignment
            var_type = self.tc(ref, env)
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

            # Initially, environment used to tc consequent part
            # is the same as the main env, however can be updated
            # for the union type for the type casting
            consequent_env = env

            # check is the if condition is a type casting rule.
            # This is used with union type to make a type concrete:
            #
            # (if (== (typeof foo) \\"string\\") ... )
            #
            if self.__is_type_cast_condition(condition):
                name, specific_type = self.__get_specific_type(condition)
                # update environment with the concrete type for this name
                consequent_env = TypeEnvironment(
                    {name: Type.from_string(specific_type)},
                    env
                )

            t2 = self.tc(consequence, consequent_env)
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

            # transfer the 'def' into 'lambda'
            var_exp = self.__transform_def_to_var_lambda(exp)

            if not self.__is_generic_define_function(exp):
                # extract for recursive check.
                _tag, name, params, _ret_del, return_type_str, body = exp

                # We have to extend environment with the function name BEFORE evaluating the body
                # this is need to support recursive function calls:
                param_types = [Type.Type.from_string(type_str) for name, type_str in params]
                return_type = Type.Type.from_string(return_type_str)
                env.define(name, Type.FunctionType(None, param_types, return_type))

            # delegate to lambda
            return self.tc(var_exp, env)

        # ------------------------------------------------------------
        # lambda function:  (lambda ((x number)) -> number (* x x))
        if exp[0] == 'lambda':
            if self.__is_generic_lambda_function(exp):
                return self.__create_generic_function_type(exp, env)

            # simple declaration:
            return self.__create_simple_function_type(exp, env)

        # ------------------------------------------------------------
        # function call: (square 2)
        if isinstance(exp, (tuple, list)):

            # 1. simple function call
            fn = self.tc(exp[0], env)
            arg_values = exp[1:]

            actual_fn = fn

            # 2. generic function call
            if isinstance(fn, Type.GenericFunction):
                actual_types = self.__extract_actual_call_types(exp)

                # map the generic types to actual types
                # e.g {K:number}
                generics_type_map = self.__get_generic_types_map(fn.generic_types, actual_types)

                # bind parameters and return-types
                bound_params, bound_return_type = self.__bind_function_types(
                    fn.params,
                    fn.return_type,
                    generics_type_map
                )

                # check the function body with the bound parameter types:
                # This creates an actual function type
                # NOTE: we pass environment as fn.env, i.e. closured environment
                actual_fn = self.__tc_function(
                    bound_params,
                    bound_return_type,
                    fn.body,
                    fn.env
                )

                # In generics function call, parameters are passed from index 2
                arg_values = exp[2:]

            arg_types = [self.tc(arg, env) for arg in arg_values]
            return self.__check_function_call(actual_fn, arg_types, env, exp)

        raise RuntimeError(f"Unknown type for expression {exp}")

    def __create_simple_function_type(self, exp, env):
        """
        Simple function declaration (no generic parameters)
        Such functions are type-checked during declaration time.
        :return:
        """
        _tag, params, _ret_del, return_type_str, body = exp
        return self.__tc_function(params, return_type_str, body, env)

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
        # Union Types:
        if isinstance(_type, Type.Union):
            if all([element_type in allow_types for element_type in _type.option_types]):
                return
        # other types
        elif _type in allow_types:
            return
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
        actual_type = self.__tc_block(body, fn_env, isinstance(body, list) and body[0] == 'begin')

        # check the return type
        if not return_type == actual_type:
            raise RuntimeError(f"Expect function {body} to return {return_type}, but got {actual_type}")

        # Function type records it params and return type,
        # so we can use tem to validate function calls.
        # NOTE: The name of the function need to be None, which will generate by the __init__
        return Type.functions(None, param_types, return_type)

    # check function call
    def __check_function_call(self, fn: Type.FunctionType, arg_types, env, exp):

        # check arity
        if len(fn.param_types) != len(arg_types):
            raise RuntimeError(f"\nFunction {exp[0]} {fn.name} expects {len(fn.param_types)}"
                               f" arguments, {len(arg_types)} given in {exp}.\n")

        # check if the argument types matches the parameter types
        for i in range(len(arg_types)):
            if fn.param_types[i] == Type.Any:
                continue
            self.__expect(arg_types[i], fn.param_types[i], arg_types[i], exp)

        return fn.return_type

    def __transform_def_to_var_lambda(self, exp):
        # 1. generic function
        if self.__is_generic_define_function(exp):
            _tag, name, generic_type_str, params, _ret_del, return_type_str, body = exp
            return ['var', name, ['lambda', generic_type_str, params, _ret_del, return_type_str, body]]

        # 2. Simple functions
        _tag, name, params, _ret_del, return_type_str, body = exp
        return ['var', name, ['lambda', params, _ret_del, return_type_str, body]]

    @staticmethod
    def __is_type_cast_condition(condition):
        """
        Whether an if-condition is type casting/specification
        ,this is used with union types to make a type concrete:
        e.g. (if (== (typeof foo) "string" ) ... )
        :param condition:
        :return:
        """
        op, *lhs = condition
        return op == '==' and lhs[0][0] == 'typeof'

    @staticmethod
    def __get_specific_type(condition):
        op, [_typeof, name], specific_type = condition
        return [name, specific_type[1:-1]]

    @staticmethod
    def __is_generic_define_function(exp):
        """
        Whether a function is generic
        (def foo <K> (x K) -> K (+ x x))
        :param exp:
        :return:
        """
        return len(exp) == 7 and re.match('^<[^>]+>$', exp[2])

    @staticmethod
    def __create_generic_function_type(exp, env):
        """
        Generic function declaration
        Such functions are not checked at the declaration,
        instead, they are checked at call time, when all generic parameters are bounded
        """
        _tag, generic_type_str, params, _ret_del, return_type_str, body = exp

        return Type.GenericFunction(
            None,
            generic_type_str[1:-1],
            params,
            return_type_str,
            body,
            env
        )

    @staticmethod
    def __is_generic_lambda_function(exp):
        """
        Whether a function is generic
        (lambda <K> (x K) -> K (+ x x))
        :param exp:
        :return:
        """
        return len(exp) == 6 and re.match('^<[^>]+>$', exp[1])

    def __extract_actual_call_types(self, exp):
        """
        Extracts types for generics parameter types
        :param exp: (combine <string> "hello")
        :return: [Type.string]
        """
        actual_param_type_str = re.match('^<[^<]+>$', exp[1]).group(0)[1:-1].split(',')

        if actual_param_type_str is None:
            raise RuntimeError(f"No actual type provided in Generic call: {exp}")

        return actual_param_type_str

    @staticmethod
    def __get_generic_types_map(generic_types, actual_types):
        bound_types = {generic_types[i]: actual_types[i] for i in range(len(actual_types))}
        return bound_types

    @staticmethod
    def __bind_function_types(params, return_type, generics_type_map):
        # bind parameters
        actual_params = []
        for i in range(len(params)):
            param_name, param_type = params[i]  # generic type here. e.g: K
            actual_param_type = param_type
            if generics_type_map.get(param_type):
                actual_param_type = generics_type_map.get(param_type)
            actual_params.append([param_name, actual_param_type])

        # bind return-type
        actual_return_type = return_type
        if generics_type_map.get(actual_return_type):
            actual_return_type = generics_type_map.get(actual_return_type)

        return [actual_params, actual_return_type]
