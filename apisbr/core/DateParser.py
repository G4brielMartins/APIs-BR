from typing import Optional

import dateparser

class DateParser():
    settings = {'DATE_ORDER': 'DMY', 'PREFER_DAY_OF_MONTH': 'last', 'PREFER_MONTH_OF_YEAR': 'last'}
    """Configuração para a função dateparser.parse()"""
    
    def __init__(self, settings: Optional[dict[str, str]] = None) -> None:
        if settings is not None:
            self.settings = settings
    
    def set_settings(self, settings: dict[str, str]) -> None:
        """
        Atualiza as configurações utilizadas pelo parser de datas.

        Parameters
        ----------
        parsing_settings : dict
            Dicionário contendo as configurações do parser.  
            São utilizadas as [opções do dataparser](https://dateparser.readthedocs.io/en/latest/settings.html).
        """        
        self.settings = settings
    
    def parse(self, date_string: str, prefer_first=False):
        settings = self.settings.copy()
        if prefer_first:
            settings['PREFER_DAY_OF_MONTH'] = 'first'
            settings['PREFER_MONTH_OF_YEAR'] = 'first'
        return dateparser.parse(date_string, settings=settings)