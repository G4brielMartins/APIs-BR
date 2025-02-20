import re
import os
from urllib.parse import quote

import requests
import pandas as pd

from ..core import API, is_similar_text, parse_period_input
from ..utils import format_to_path

class DadosAbertos(API):
    """
    Wrapper para executar requisões na [API REST do Portal de Dados Abertos](https://dados.gov.br/swagger-ui/index.html).

    Parameters
    ----------
    auth_token : str
        Token de autenticação da API. * USO BRIGATÓRIO *  
        Pode ser obtido gratuitamente pelo [site Dados Abertos](https://dados.gov.br/dados/conteudo/como-acessar-a-api-do-portal-de-dados-abertos-com-o-perfil-de-consumidor).
    """        
    server_url = "https://dados.gov.br"
    id_regex = re.compile(r"[0-z]{8}-([0-z]{4}-){3}[0-z]{12}")
    
    def __init__(self, auth_token: str):
        self.token = auth_token
        self.header = {'chave-api-dados-abertos': auth_token}
    
    def get_id(self, title: str, *, depth: int = 10) -> str:
        """
        Procura por um conjunto de dados com o nome idêntico à [title] e retorna seu ID.

        Parameters
        ----------
        title : str
            Título a ser procurado.
        depth : int, optional
            Profundidade da pesquisa.
            Quanto maior, mais páginas exploradas na procura de correspondêcias.  
            Valor padrão: 10.

        Returns
        -------
        str
            ID do conjunto de dados pesquisado.

        Raises
        ------
        NoMatchFound
            Erro de ausência de correspondência.  
            Dá print nos conjuntos de dados com nomes semelhantes ao pesquisado.
        """
        call_url = self.server_url + "/dados/api/publico/conjuntos-dados"
        call_parameters = "?isPrivado=false&nomeConjuntoDados=" + quote(title)
        
        dict_nomes_semelhantes = dict()
        for pagina_pesquisa in range(1, depth+1):
            query = call_url + call_parameters + f"&pagina={pagina_pesquisa}"
            req = requests.get(query, headers=self.header)
            
            for conjunto in req.json():
                titulo_conjunto = conjunto['title'].lower()
                titulo_pesquisado = title.lower()
                
                if titulo_conjunto == titulo_pesquisado:
                    return conjunto['id']
                elif is_similar_text(titulo_pesquisado, titulo_conjunto):
                    dict_nomes_semelhantes[conjunto['title']] = conjunto['id']
        raise self.NoMatchFoundError(dict_nomes_semelhantes)
    
    def list_recursos(self, identifier: str, period: str = 'all',
                    file_type: str = 'csv') -> dict[str, str]:
        """
        Procura os recursos (arquivos para download) disponíveis no conjunto de dados pesquisado e retorna seus URLs.

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
        file_type : str, optional
            Filtro de extensão dos arquivos pesquisados.  
            Se 'all', procura por qualquer recurso, sem filtrar tipo de aquivo.  
            Por padrão, procura por 'csv'.  

        Returns
        -------
        dict[str, str]
            Dicionário com os nomes dos recuros encontrados como chaves e seus links.
        """
        if not self.id_regex.fullmatch(identifier):
            identifier = self.get_id(identifier)
        
        query = self.server_url + f"/dados/api/publico/conjuntos-dados/{identifier}"
        req = requests.get(query, headers=self.header)
        
        min_date, max_date = parse_period_input(period, self.date_parser)
        
        recursos_dict = dict()
        for recurso in req.json()['recursos']:
            extensao_errada = file_type not in [recurso['formato'].lower(), 'all']
            data_errada = not (min_date <= self.date_parser.parse(recurso['dataCatalogacao']) <= max_date)
            
            if extensao_errada or data_errada:
                continue
            
            key = f"{recurso['titulo']}.{recurso['formato'].lower()}"
            recursos_dict[key] = recurso['link']
            
        return recursos_dict
    
    def get_data(self, identifier: str, period: str = 'all',
                 **kwargs) -> pd.DataFrame:
        """
        Importa os dados da API como um data frame.

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
        **kwargs :
            Configurações extras para a função [pd.read_csv()](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html).

        Returns
        -------
        pd.DataFrame|dict[str, pd.DataFrame]
            Data frame do conjunto de dados selecionado.
        """        
        recursos = self.list_recursos(identifier, period=period, file_type='csv')
        if len(recursos) == 1:
            return pd.read_csv(*[recursos.values()], **kwargs)
        
        dfs = dict()
        for nome, link in recursos.items():
            dfs[nome] = pd.read_csv(link, **kwargs)
        return pd.concat(dfs, axis=1)
    
    def download_data(self, identifier: str, output_folder: str, **kwargs) -> None:
        """
        Faz o download dos recursos encontrados em [output_folder].

        Parameters
        ----------
        identifier : str
            Título exato ou ID do conjunto de dados de interesse.
        output_folder : str
            Caminho da pasta onde os dados devem ser salvos.
        **kwargs** :  
            Parâmetros passados à list_recursos() para filtrar os arquivos encontrados.
        """
        data = dict()
        for nome, link in self.list_recursos(identifier, **kwargs).items():
            data[nome] = requests.get(link).content
        for nome, file_bytes in data.items():
            file_name = format_to_path(nome)
            with open(os.path.join(output_folder, file_name), 'wb') as f:
                f.write(file_bytes)