import re

import requests
import pandas as pd

from ..core import API, is_similar_text, parse_period_input


def get_series_dict() -> dict[str, str]:
    series_dict = dict()
    query = "http://www.ipeadata.gov.br/api/odata4/Metadados"
    for serie in requests.get(query).json()['value']:
        series_dict[serie['SERNOME']] = serie['SERCODIGO']
    return series_dict


def get_territorios_dict() -> dict[str, str]:
    territorios_dict = dict()
    query = "http://www.ipeadata.gov.br/api/odata4/Territorios"
    for territorio in requests.get(query).json()['value']:
        territorios_dict[territorio['TERCODIGO']] = territorio['TERNOME']
    return territorios_dict


class IPEAData(API):
    server_url = "http://www.ipeadata.gov.br/api/odata4/"
    id_regex = re.compile(r"([0-Z]|_)*")
    series_dict = get_series_dict()
    """Dicionário com as séries de dados disponíveis (chaves) e seus IDs (valores)."""
    territorios_dict = get_territorios_dict()
    """Dicionário com os territórios disponíveis (valores) e seus IDs (chaves)""" 
    
    def get_id(self, title) -> str:
        try:
            return self.series_dict[title]
        except KeyError:
            dict_semelhantes = dict()
            for nome_serie, id_serie in self.series_dict.items():
                if is_similar_text(title, nome_serie):
                    dict_semelhantes[nome_serie] = id_serie
            raise self.NoMatchFoundError(dict_semelhantes)
    
    def get_df(self, identifier, /, period: str = 'all', level: str = None) -> pd.DataFrame:
        if not self.id_regex.fullmatch(identifier):
            identifier = self.get_id(identifier)
        
        query = self.server_url+f"/Metadados('{identifier}')/Valores"
        json = requests.get(query).json()
        df = pd.DataFrame(json['value'])
        
        # Renomeando colunas de interesse para melhor compreensão
        rename_dict = {
            'VALDATA': 'Data',
            'TERCODIGO': 'Territorio',
            'NIVNOME': 'Nivel',
            'VALVALOR': 'Valor'
        }
        df = df.rename(rename_dict, axis=1)
        
        # Filtrando por período
        df['Data'] = df['Data'].apply(lambda x: self.date_parser.parse(x).replace(tzinfo=None))
        
        min_date, max_date = parse_period_input(period, self.date_parser)
        df = df[(df['Data'] >= min_date) & (df['Data'] <= max_date)]
        
        # Tranformando códigos de território em nomes de território
        df['Territorio'] = df['Territorio'].apply(lambda x: self.territorios_dict[x])
        
        if level is not None:
            df = df[df['Nivel'] == level.title()]
            df = df.pivot(columns='Data', index='Territorio', values='Valor')

        return df