def invert_dict(dict_: dict) -> dict:
    """
    Inverte as chaves e valores do dicionários.

    Parameters
    ----------
    dict_ : dict
        Dicionário a inverter.

    Returns
    -------
    dict
        Dicionário invertido.
    """    
    new_dict = dict()
    for key, value in dict_.copy().items():
        new_dict[value] = key
    return new_dict