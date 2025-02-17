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


def remove_accents(text: str) -> str:
    """
    Remove os acentos do texto.

    Parameters
    ----------
    text : str
        Texto a formatar.

    Returns
    -------
    str
        Texto sem acentos.
    """    
    from unicodedata import normalize, category
    
    return ''.join(c for c in normalize('NFD', text) if category(c) != 'Mn')


def format_to_path(text: str) -> str:
    """
    Formata o texto para facilitar referências ao seu caminho.

    Parameters
    ----------
    text : str
        Texto a formatar.

    Returns
    -------
    str
        Texto sem espaços ou acentos.
    """    
    return remove_accents(text.replace(' ', '_'))