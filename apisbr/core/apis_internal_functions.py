import datetime as dt

from .DateParser import DateParser
from ..utils import remove_accents

type MinDate = dt.datetime
type MaxDate = dt.datetime

def is_similar_text(target: str, current: str) -> bool:
    """
    Verifica se dois textos são semelhantes: [target] vs [current].
    
    Parameters
    ----------
    target : str
        Texto sendo buscado.
    current : str
        Texto onde [target] será procurado.
        
    Returns
    -------
    bool
        Retorna verdadeiro se todas as palavras de [target] estão em [current].
    """
    target = remove_accents(target).lower()
    current = remove_accents(current).lower()
    return all(palavra in current for palavra in target.split())


def parse_period_input(period: str, date_parser: DateParser = DateParser()) -> tuple[MinDate, MaxDate]:
    """
    Trata os inputs de períodos quando solicitados pelos wrappers de APIs.  
    *Aceita qualquer formato de data compatível com a biblioteca dateparser, no formato DMY (padrão).  

    Parameters
    ----------
    period : str
        String de período no formato especificado.  
        Exemplos de uso:  
        - '2021' : procura por recursos publicados em 2021  
        - '2019-2021' : procura por recursos publicados entre 2019 e 2021  
        - 'all' : procura por qualquer recurso, sem filtrar data de publicação (padrão)  
    date_parser : DateParser
        DateParser a ser utilizado. Caso não fornecido, utiliza o DateParser padrão

    Returns
    -------
    tuple[MinDate, MaxDate]
        Data inicial (MinDate) e final (MaxDate) do período selecionado, no formato datetime.

    Raises
    ------
    ValueError
        _description_
    """
    match period.split('-'):
        case ['all']:
            min_date = dt.datetime.min
            max_date = dt.datetime.max
        case [x]:
            d = date_parser.parse(x)
            min_date = dt.datetime(d.year, 1, 1)
            max_date = d
        case [x, y]:
            min_date = date_parser.parse(x)
            max_date = date_parser.parse(y)
        case _:
            raise ValueError("Valor de [period] não pôde ser reconhecido.")
    return min_date, max_date