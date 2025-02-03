def invert_dict(dict_: dict) -> dict:
    new_dict = dict()
    for key, value in dict_.copy().items():
        new_dict[value] = key
    return new_dict