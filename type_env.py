from __future__ import annotations


class TypeEnvironment(object):
    """
        mapping from names to type
    """

    def __init__(self, record: dict, parent: TypeEnvironment = None):
        """
            creates an Environment with given record
        :param record:
        :param parent:
        """
        self.record = record
        self.parent = parent

    def define(self, name, _type):
        """
            create a method with the given name and type
        :param name:
        :param _type:
        :return:
        """
        self.record[name] = _type
        return _type

    def look_up(self, name):
        return self.__resolve(name).record[name]

    def __resolve(self, name):
        """
            find an environment which contains the variable, or throw an exception
        :param name: name of variable
        :return:
        """
        if self.record.get(name):
            return self

        if self.parent is None:
            raise RuntimeError(f"Variable {name} has not defined")

        # parent is an Environment, NOT dict
        return self.parent.__resolve(name)
