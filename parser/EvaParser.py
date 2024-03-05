from sexpdata import loads, Symbol


def to_eva_block(raw: str) -> list:
    """
    :param raw: eva code raw: (var x 10)
    :return: a list equals code with block keyword 'begin'
        (begin
            (var x 10)
        )
    """
    return to_eva_lst(f"(begin {raw})")


def to_eva_lst(raw: str) -> list:
    return remove_symbol(loads(raw))


def remove_symbol(obj):
    if isinstance(obj, list):
        return [remove_symbol(item) for item in obj]
    elif isinstance(obj, Symbol):
        return obj.value()
    else:
        return obj


def add_quote(obj):
    if isinstance(obj, list):
        return [add_quote(item) for item in obj]
    elif isinstance(obj, str):
        return '"%s"'.format(str)
    else:
        return obj


if __name__ == '__main__':
    result = to_eva_lst('''
        (begin
            (var x 10)
            (var y \\"10\\")
            (var z (+ x y))
        )
    ''')
    print(result)
