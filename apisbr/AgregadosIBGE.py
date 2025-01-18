from typing import Optional

import requests

from . import API


class AgregadosIBGE(API):
    """
    Classe para auxiliar com requisições na [API IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3).
    """
    server_url = "https://servicodados.ibge.gov.br/api/v3/agregados"
    
    def get_id(self, title: str, /, pesquisa: Optional[str] = None) -> str:
        query = self.server_url
        
        dict_nomes_semelhantes = dict()
        for pesq in requests.get(query).json():
            if (pesquisa is not None) and (pesq['nome'].lower() != pesquisa.lower()):
                continue # Seleciona a pesquisa em que o agregado deve estar
            for agregado in pesq['agregados']:
                if title.lower() == agregado['nome'].lower():
                    return agregado['id']
                elif all(palavra in agregado['nome'] for palavra in title.split()):
                # Se as palavras pesquisadas estão no titulo do conjunto de dados:
                        dict_nomes_semelhantes[agregado['nome']] = agregado['id']
        raise self.NoMatchFound(dict_nomes_semelhantes)
    
    def get_data(self, identifier: str, /, **kwargs):
        if not identifier.isdigit():
            identifier = self.get_id(identifier, **kwargs)
        
        call_url = f"{self.server_url}/{identifier}"
        