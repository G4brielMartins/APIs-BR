import re
from os.path import join as join_path

import requests
import pandas as pd

from ..core import API, is_similar_text, parse_period_input
from ..utils import format_to_path

def _get_series_dict() -> dict[str, str]:
    """
    Lista as séries de dados disponíveis na plataforma IPEAData.

    Returns
    -------
    dict[str, str]
        Dicionário com nomes e códigos das séries de dados.
    """    
    series_dict = dict()
    query = "http://www.ipeadata.gov.br/api/odata4/Metadados"
    for serie in requests.get(query).json()['value']:
        series_dict[serie['SERNOME']] = serie['SERCODIGO']
    return series_dict


def _get_territorios_dict() -> dict[str, str]:
    """
    Lista os territórios disponíveis na plataforma IPEAData.

    Returns
    -------
    dict[str, str]
        Dicionário com nomes de territórios e seus códigos.
    """    
    territorios_dict = dict()
    query = "http://www.ipeadata.gov.br/api/odata4/Territorios"
    for territorio in requests.get(query).json()['value']:
        territorios_dict[territorio['TERCODIGO']] = territorio['TERNOME']
    return territorios_dict


class IPEAData(API):
    """
    Wrapper para executar requisições na API do [IPEAData](http://www.ipeadata.gov.br/)
    """    
    server_url = "http://www.ipeadata.gov.br/api/odata4"
    id_regex = re.compile(r"[0-Z]+(_[0-Z]+)+")
    series_dict = _get_series_dict()
    """Dicionário com as séries de dados disponíveis (chaves) e seus IDs (valores)."""
    territorios_dict = _get_territorios_dict()
    """Dicionário com os territórios disponíveis (valores) e seus IDs (chaves)""" 
    
    def get_id(self, title: str) -> str:
        """
        Procura por um conjunto de dados com o nome idêntico à [title] e retorna seu ID.

        Parameters
        ----------
        title : str
            Título a ser procurado.

        Returns
        -------
        str
            ID do conjunto de dados pesquisado.

        Raises
        ------
        self.NoMatchFoundError
            Erro de ausência de correspondência.  
            Dá print nos conjuntos de dados com nomes semelhantes ao pesquisado.
        """        
        try:
            return self.series_dict[title]
        except KeyError:
            dict_semelhantes = dict()
            for nome_serie, id_serie in self.series_dict.items():
                if is_similar_text(title, nome_serie):
                    dict_semelhantes[nome_serie] = id_serie
            raise self.NoMatchFoundError(dict_semelhantes)
    
    def get_data(self, identifier: str, level: str = None,
                 period: str = 'all') -> pd.DataFrame:
        """
        Importa os dados da API IPEA Data como um data frame.

        Parameters
        ----------
        identifier : str
            Título exato ou ID do conjunto de dados de interesse.
        period : str, optional
            Filtro de período em que os recursos foram publicados.  
            *Aceita qualquer formato de data compatível com o dateparser, no formato DMY.  
            Exemplos de uso:  
            - '2021' : procura por recursos publicados em 2021  
            - '2019-2021' : procura por recursos publicados entre 2019 e 2021  
            - 'all' : procura por qualquer recurso, sem filtrar data de publicação (padrão)
        level : str, optional
            Agrupa os dados pelo [level] de agregação.

        Returns
        -------
        pd.DataFrame
            Data frame do conjunto de dados selecionado.
        """        
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
            
        var_name_json = requests.get(self.server_url+f"/Metadados('{identifier}')/").json()
        var_name = var_name_json['value'][0]['SERNOME']
        return pd.concat({var_name: df}, axis=1)
    
    def download_data(self, identifier: str, output_folder: str, **kwargs) -> None:
        """
        Faz o download da tabela encontrada em [output_folder].

        Parameters
        ----------
        identifier : str
            Título exato ou ID do conjunto de dados de interesse.
        output_folder : str
            Caminho da pasta onde os dados devem ser salvos.
        period : str, optional
            Filtro de período em que os recursos foram publicados.  
            *Aceita qualquer formato de data compatível com o dateparser, no formato DMY.  
            Exemplos de uso:  
            - '2021' : procura por recursos publicados em 2021  
            - '2019-2021' : procura por recursos publicados entre 2019 e 2021  
            - 'all' : procura por qualquer recurso, sem filtrar data de publicação (padrão)
        level : str, optional
            Agrupa os dados pelo [level] de agregação.
        """        
        super().download_data(identifier, output_folder, **kwargs)