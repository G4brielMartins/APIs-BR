from ..utils.text_format_funcs import remove_accents
from ..utils.basic_functions import invert_dict

_uf_name2abbrev ={
    'Acre': 'AC',
    'Alagoas': 'AL',
    'Amapa': 'AP',
    'Amazonas': 'AM',
    'Bahia': 'BA',
    'Ceara': 'CE',
    'Distrito Federal': 'DF',
    'Espirito Santo': 'ES',
    'Goias': 'GO',
    'Maranhao': 'MA',
    'Mato Grosso': 'MT',
    'Mato Grosso Do Sul': 'MS',
    'Minas Gerais': 'MG',
    'Para': 'PA',
    'Paraiba': 'PB',
    'Parana': 'PR',
    'Pernambuco': 'PE',
    'Piaui': 'PI',
    'Rio De Janeiro': 'RJ',
    'Rio Grande Do Norte': 'RN',
    'Rio Grande Do Sul': 'RS',
    'Rondonia': 'RO',
    'Roraima': 'RR',
    'Santa Catarina': 'SC',
    'Sao Paulo': 'SP',
    'Sergipe': 'SE',
    'Tocantins': 'TO'
}

_uf_abbrev2name = invert_dict(_uf_name2abbrev)

def get_uf_abbrev(uf_name: str) -> str:
    """
    Recebe o nome de uma UF e retorna sua abreviação (SC, MT, DF...).

    Parameters
    ----------
    uf_name : str
        Nome da UF, com ou sem acento, com ou sem letras maiúsculas.

    Returns
    -------
    str
        Sigla referente à UF em letras maiúsculas.
    """
    name = remove_accents(uf_name).title()
    return _uf_name2abbrev[name]

def get_uf_name(uf_abbrev: str) -> str:
    """
    Recebe a abreviação de uma UF (SC, MT, DF...) e retorna seu nome.

    Parameters
    ----------
    uf_abbrev : str
        Abreviação da UF, com ou sem letras maiúsculas.

    Returns
    -------
    str
        Nome da UF com palavras capitalizadas e sem acento (Sao Paulo, Maranhao...).
    """
    abbrev = uf_abbrev.upper()
    return _uf_abbrev2name[abbrev]