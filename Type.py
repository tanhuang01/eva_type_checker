from __future__ import annotations

import re


def has_own_property(name):
    return globals().get(name) is not None


def get_property(name):
    return globals().get(name)


def add_property(name, alais_type):
    globals()[name] = alais_type


class Type():
    """
        Type class
    """

    def __init__(self, name):
        self.name = name

    @staticmethod
    def from_string(type_str: str):
        """
            'number' -> Type.number
        :param type_str:
        :return:
        """
        if globals().get(type_str):
            return globals().get(type_str)

        if type_str.startswith("Fn"):  # a function-type in str
            return FunctionType.from_string(type_str)

        raise RuntimeError(f"Unknown type {type_str}")

    def __eq__(self, other):
        if isinstance(other, Alias):
            return other.__eq__(self)
        return self.name == other.name

    def __str__(self):
        return f"Type.{self.name}"

    def __repr__(self):
        return self.__str__()


class FunctionType(Type):

    def __init__(self, name: str = None, param_types: list = None, return_type: Type = None):
        super().__init__(name)
        self.param_types = param_types
        self.return_type = return_type
        self.name = self.__get_name()

    def __get_name(self):
        """
        :return: Return name: 'Fn<return_type<arg1_type,arg2_type,...>>
            e.g
            Fn<number> - function which returns a number
            Fn<number<number,number>> - function which returns a number, and accepts two number types params
        """
        if self.name:  # name has been specified from outside.
            return self.name

        name_lst = ['Fn<', self.return_type.name]
        # params
        if len(self.param_types):
            params_tp = [param_type.name for param_type in self.param_types]
            param_name = "<{}>".format(','.join(params_tp))
            name_lst.append(param_name)
        name_lst.append('>')
        return ''.join(name_lst)

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def from_string(type_str: str):
        """
            From string: 'Fn<number>' -> Type.Function('Fn<number>', [], Type.number)
        :param type_str: It's also the name of the Type.Function
        :return:
        """
        # Already compiled
        if globals().get(type_str):
            globals().get(type_str)

        # todo: deal with nested function type: 'Fn<Fn<number<number>>>
        # with params
        _match = re.match('Fn<(\\w+)<([\\w,]+)>>', type_str)
        if _match:
            return_type, param_strs = _match.group(1), _match.group(2),
            param_types = [Type.from_string(param) for param in param_strs.split(',')]
            fn_type = FunctionType(type_str, param_types, Type.from_string(return_type))
            # add it to the globals() environment
            globals()[type_str] = fn_type
            return fn_type

        # without params
        _match = re.match('Fn<(\\w+)>', type_str)
        if _match:
            return_type = _match.group(1)
            fn_type = FunctionType(type_str, [], Type.from_string(return_type))

            # add it to the globals() environment
            globals()[type_str] = fn_type
            return fn_type

        raise RuntimeError(f"TypeFunction.from_string: Unknown type: {type_str}.")


class Alias(Type):
    def __init__(self, name, parent: Alias):
        super().__init__(name)
        self.parent = parent

    def __eq__(self, other):
        # todo, modify the logic of code that determine whether two Types are equal
        if self.name == other.name:
            return True

        return self.parent.__eq__(other)


# Number Type
number = Type('number')

# String Type
string = Type('string')

# boolean Type
boolean = Type('boolean')

# function Type
functions = FunctionType

# simplify the function call
from_string = Type.from_string
