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


def remove_hyphen(text: str) -> str:
    """
    Remove o caractere hifem ('-') do texto.  
    Também remove possíveis espaços duplos - comuns após remoção do hifem.

    Parameters
    ----------
    text : str
        Texto a formatar.

    Returns
    -------
    str
        Texto sem hifem ('-').
    """    
    return text.replace('-', '').replace('  ', ' ')


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
    text = remove_accents(text)
    text = remove_hyphen(text)
    return text.replace(' ', '_')