from typing import Optional

import requests

from ..core import API

def get_agregados_dict() -> dict[str, str]:
    agregados_dict = dict()
    for pesquisa in requests.get("https://servicodados.ibge.gov.br/api/v3/agregados").json():
        for agregado in pesquisa['agregados']:
            agregados_dict[agregado['nome']] = agregado['id']
    return agregados_dict


class AgregadosIBGE(API):
    """
    Classe para auxiliar com requisições na [API IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3).
    """
    server_url = "https://servicodados.ibge.gov.br/api/v3/agregados"
    agregados_dict = get_agregados_dict()
    "Dicionário com todos os agregados disponíveis [chaves] e seus IDs [valores]."
    
    def get_id(self, title: list[str]) -> str|dict[str, str]:
        if not isinstance(title, str):
            output_dict = dict()
            for nome in title:
                output_dict[title] = self.get_id(nome)
            return output_dict
        
        match title.split(":"):
            case [x, y]:
                nome_agregado, nome_variavel = x, y
            case [x]:
                nome_agregado, nome_variavel = x, None
        
        id_agregado = None
        dict_semelhantes = dict()
        try:
            if nome_agregado.isdigit():
                id_agregado = nome_agregado
            else:
                id_agregado = self.agregados_dict[nome_agregado]
        except KeyError:
            for agregado in self.agregados_dict.items():
                if all(palavra in agregado[0] for palavra in title.split()):
                # Se as palavras pesquisadas estão no titulo do agregdo:
                    dict_semelhantes[f"Agregado - {agregado[0]}"] = agregado[1]
                    raise self.NoMatchFoundError(dict_semelhantes)
        if not id_agregado:
            raise self.NoMatchFoundError()
        if nome_variavel is None:
            return id_agregado
        
        query = f"{self.server_url}/{id_agregado}/metadados" 
        json = requests.get(query).json()
        for variavel in json['variaveis']:
            output_id = f"{id_agregado}-{variavel['id']}"
            if nome_variavel == variavel['nome']:
               return output_id
            if all(palavra in variavel['nome'] for palavra in nome_variavel.split()):
            # Se as palavras pesquisadas estão no titulo da variável:
                key = f"Variavel - {variavel['nome']}"
                id_ = f"{id_agregado}-{variavel['id']}"
                dict_semelhantes[key] = id_
        raise self.NoMatchFoundError(dict_semelhantes)
    
    def get_data(self, identifier: str, /, **kwargs):
        if not identifier.isdigit():
            identifier = self.get_id(identifier, **kwargs)
        
        call_url = f"{self.server_url}/{identifier}"
        return 0
        