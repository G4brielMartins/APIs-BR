import re
import datetime as dt
from urllib.parse import quote

import requests

from ..core import API, is_similar_text, parse_period_input

class DadosAbertos(API):
    """
    Wrapper para auxiliar com requisões na [API REST do Portal de Dados Abertos](https://dados.gov.br/swagger-ui/index.html).

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
    
    def get_id(self, title: str, /, depth: int = 10) -> str:
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
            Lista conjuntos de dados com nomes semelhantes ao pesquisado.
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
    
    def get_data(self, identifier: str, /, period: str = 'all',
                    file_type: str = 'csv') -> dict[str, bytes]:
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
        dict[str, list[str, str]]
            Dicionário com os nomes dos recuros encontrados como chaves.
            Os valores são listas, contendo a extensão do arquivo no índice 0 e seu link de download no índice 1.
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
            recursos_dict[key] = requests.get(recurso['link']).content
            
        return recursos_dict