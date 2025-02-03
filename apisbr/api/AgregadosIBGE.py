import re
from typing import Optional

import requests

from ..core import API, is_similar_text


def get_agregados_dict() -> dict[str, str]:
    agregados_dict = dict()
    query = "https://servicodados.ibge.gov.br/api/v3/agregados"
    for pesquisa in requests.get(query).json():
        for agregado in pesquisa['agregados']:
            agregados_dict[agregado['nome']] = agregado['id']
    return agregados_dict


class AgregadosIBGE(API):
    """
    Wrapper para auxiliar com requisições na [API IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3).
    """
    server_url = "https://servicodados.ibge.gov.br/api/v3/agregados"
    id_regex = re.compile(r"[0-9]{4}-[0-9]*")
    agregados_dict = get_agregados_dict()
    """Dicionário com os agregados disponíveis (chaves) e seus IDs (valores)."""
    
    def get_id_agregado(self, title: str) -> str:
        try:
            return self.agregados_dict[title]
        except KeyError:
            dict_semelhantes = dict()
            for nome_agregado, id_agregado in self.agregados_dict.items():
                if is_similar_text(title, nome_agregado):
                    dict_semelhantes[f"Agregado - {nome_agregado}"] = id_agregado
            raise self.NoMatchFoundError(dict_semelhantes)
    
    def get_id_variavel(self, title: str, id_agregado: str) -> str:
        query = f"{self.server_url}/{id_agregado}/metadados" 
        json = requests.get(query).json()
        
        out_str = ''
        dict_semelhantes = dict()
        for var_title in title.split('|'):
            for variavel in json['variaveis']:
                if var_title == variavel['nome']:
                    out_str += variavel['id'] + "|"
                if is_similar_text(var_title, variavel['nome']):
                    key = f"Variavel - {variavel['nome']}"
                    id_ = f"{id_agregado}-{variavel['id']}"
                    dict_semelhantes[key] = id_
        if out_str:
            return out_str[:-1]
        raise self.NoMatchFoundError(dict_semelhantes)
    
    def get_id(self, title: str) -> str:
        match title.split(";"):
            case [x, y]:
                agregado, variavel = x, y
            case [x]:
                agregado, variavel = x, None
            case _:
                raise ValueError("O [title] apresenta formato inválido.")
        
        id_agregado = agregado if agregado.isdigit() else self.get_id_agregado(agregado)
        if not variavel:
            return id_agregado
        
        id_variavel = self.get_id_variavel(variavel, id_agregado)
        return f"{id_agregado}-{id_variavel}"
    
    def get_metadata(self, identifier: str):
        id_agregado = identifier if identifier.isdigit() else self.get_id_agregado(identifier)
        
        query = self.server_url+f"/{id_agregado}/metadados"
        return requests.get(query).json()
    
    
    def get_data(self, identifier: str, /, **kwargs):
        match identifier:
            case id_agreg_var if self.id_regex.fullmatch(id_agreg_var):
                id_agregado, id_variavel = id_agreg_var.split('-')
                
            case id_agregado if id_agregado.isdigit():
                id_agregado, id_variavel = id_agregado, ""
                
            case titulo_agreg_var if titulo_agreg_var.find(';'):
                id_agregado, id_variavel = self.get_id(titulo_agreg_var).split('-')
                
            case titulo_agregado if titulo_agregado.find(';') == -1:
                id_agregado, id_variavel = self.get_id(titulo_agregado), ""
            
            case _:
                raise ValueError("O [title] apresenta formato inválido.")
        
        query = self.server_url+f"/{id_agregado}/variaveis/{id_variavel}"