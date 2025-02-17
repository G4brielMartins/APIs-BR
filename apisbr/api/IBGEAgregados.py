import re
import os
from pathlib import Path
from typing import Optional

import requests
import pandas as pd

from ..core import API, is_similar_text
from ..utils import invert_dict

type JSON = dict[str]

def _get_agregados_dict() -> dict[str, str]:
    """
    Lista os agregados disponíveis na API IBGE Agregados.

    Returns
    -------
    dict[str, str]
        Dicionário com nomes e códigos dos agregados.
    """    
    agregados_dict = dict()
    query = "https://servicodados.ibge.gov.br/api/v3/agregados"
    for pesquisa in requests.get(query).json():
        for agregado in pesquisa['agregados']:
            agregados_dict[agregado['nome']] = agregado['id']
    return agregados_dict


def _get_niveis_geo_dict() -> dict[str, str]:
    # Importa o arquivo com todos os identificadores de nível geográfico
    # *Não foi encontrada uma forma de obter os identificadores via API
    assets_dir = Path(os.path.abspath(__file__)).parents[1]
    file_path = os.path.join(assets_dir, 'assets', 'ibge_level_identifiers.txt')
    
    localidades_dict = dict()
    with open(file_path) as identifiers_txt:
        for line in identifiers_txt:
            split_point = line.find("-")
            nivel = line[:split_point-1] # Remove o espaço antes de -
            descricao = line[split_point+2:-1] # Remove o espaço após - e o \n no fim da linha
            localidades_dict[nivel] = descricao
    return localidades_dict


class IBGEAgregados(API):
    """
    Wrapper para auxiliar com requisições na [API IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3).
    """
    server_url = "https://servicodados.ibge.gov.br/api/v3/agregados"
    id_regex = re.compile(r"[0-9]{4}-[0-9]*")
    agregados_dict = _get_agregados_dict()
    """Dicionário com os agregados disponíveis (chaves) e seus IDs (valores)."""
    niveis_geo_dict = _get_niveis_geo_dict()
    """Dicionário com os níveis geográficos de agregação (valores) e seus IDs (chaves)."""
    
    def get_id_agregado(self, title: str) -> str:
        """
        Procura por um agregado com o nome idêntico à [title] e retorna seu ID.

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
            return self.agregados_dict[title]
        except KeyError:
            dict_semelhantes = dict()
            for nome_agregado, id_agregado in self.agregados_dict.items():
                if is_similar_text(title, nome_agregado):
                    dict_semelhantes[f"Agregado - {nome_agregado}"] = id_agregado
            raise self.NoMatchFoundError(dict_semelhantes)
    
    def get_id_variavel(self, title: str, agregado: str) -> str:
        """
        Procura por uma variavel com o nome idêntico à [title] dentro de um agregado e retorna seu ID.

        Parameters
        ----------
        title : str
            Título a ser procurado.
        agregado : str
            ID ou título do agregado onde a variável será procurada.

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
        if not agregado.isdigit():
            agregado = self.get_id_agregado(agregado)
        query = f"{self.server_url}/{agregado}/metadados" 
        json = requests.get(query).json()
        
        out_str = ''
        dict_semelhantes = dict()
        for var_title in title.split('|'):
            for variavel in json['variaveis']:
                if var_title == variavel['nome']:
                    out_str += variavel['id'] + "|"
                if is_similar_text(var_title, variavel['nome']):
                    key = f"Variavel - {variavel['nome']}"
                    id_ = f"{agregado}-{variavel['id']}"
                    dict_semelhantes[key] = id_
        if out_str:
            return out_str[:-1]
        raise self.NoMatchFoundError(dict_semelhantes)
    
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
        
        id_variavel = variavel if variavel.isdigit() else self.get_id_variavel(variavel, id_agregado)
        return f"{id_agregado}-{id_variavel}"
    
    def get_metadata(self, identifier: str) -> JSON:
        """
        Pesquisa os metadados referentes ao agregado de interesse.

        Parameters
        ----------
        identifier : str
            ID ou título do agregado.

        Returns
        -------
        JSON
            Arquivo JSON com os metadados transformado em dicionário.
        """        
        id_agregado = identifier if identifier.isdigit() else self.get_id_agregado(identifier)
        
        query = self.server_url+f"/{id_agregado}/metadados"
        return requests.get(query).json()
    
    
    def get_data(self, identifier: str, level: str = 'N1', period: str = '-6', *,
                 classify: Optional[dict[str]] = None) -> pd.DataFrame|dict[str, pd.DataFrame]:
        """
        Importa os dados da API IBGE Agregados como um data frame.  
        * Argumentos incorretos resultam em consultas (e.g. [level] inválido irá listar os níveis disponíveis).

        Parameters
        ----------
        identifier : str
            Título ou ID do agregado e variável de interesse.  
            Segue os formatos:  
            - [título agregado];[titulo var]  
            - [ID agregado]-[ID var]  
            Para pesquisar agregados ou variáveis disponíveis:  
            - [palavras chave] -> Procura agregados que contenham as palavras no seu título  
            - [título ou ID agregado] -> Lista as varíaveis disponíveis no agregado
        level : str, optional
            Nível de agregação dos dados (e.g. dados municipais, estaduais...).  
            Deve ser o nome do nível de agregação ou um identificador IBGE (formato N*).  
            Por padrão, assume o valor N1 (Brasil).
        period : str, optional
            Período de referência dos dados.  
            Segue os formatos:  
            - 2020|2022 -> Dados de 2020 e de 2022  
            - 2020-2022 -> Dados de 2020 até 2022  
            - -6 (padrão) -> Dados mais recentes (últimos seis períodos)  
            - 202201-202206 -> Dados do mês 1 até o mês 6 de 2022 (primeiro semestre)
        classify : Optional[dict[str]], optional
            Dicionário de classificadores para subdividir os dados.  
            Por exemplo, "População residente, por sexo" pode receber classify = {'Sexo': 'Homens'} para obter somente a população masculina.  
            Quando um classificador for omitido em [classify], não é realizada subdivisão.  
            Por padrão, não realiza subdivisões.

        Returns
        -------
        pd.DataFrame|dict[str, pd.DataFrame]
            Retorna um data frame com os dados solicitados.  
            Se [classify] for fornecido, retorna um dicionário com nome da variável + subdivisão como chave para os data frames.

        Raises
        ------
        self.NoMatchFoundError
            Erro de ausência de correspondência do agregado.  
            Dá print nos conjuntos de dados com nomes semelhantes ao pesquisado.
        ValueError
            Erro de argumento inválido.  
            Dá print nos valores disponíveis para o argumento inválido.
        """        
        # ----- Input handler
        match identifier:
            case id_agreg_e_id_var if self.id_regex.fullmatch(id_agreg_e_id_var):
                id_agregado, id_variavel = id_agreg_e_id_var.split('-')

            case id_agregado if id_agregado.isdigit():
                id_agregado, id_variavel = id_agregado, None
                
            case titulo_agreg_e_titulo_var if titulo_agreg_e_titulo_var.find(';') > -1:
                id_agregado, id_variavel = self.get_id(titulo_agreg_e_titulo_var).split('-')
                
            case titulo_agregado if titulo_agregado.find(';') == -1:
                id_agregado, id_variavel = self.get_id(titulo_agregado), None

            case _:
                raise ValueError("O [title] apresenta formato inválido.")
        
        if id_variavel is None:
            msg = "Nenhuma variável fornecida. Seguem variaveis disponíveis:"
            for var in self.get_metadata(id_agregado)['variaveis']:
                 msg += f"\n{var['nome']} : {var['id']}"
            raise ValueError(msg)
        
        # ----- Definição do query base
        query = self.server_url+f"/{id_agregado}/periodos/{period}/variaveis/{id_variavel}?"
        
        # ----- Definição dos parâmetros do query
        # Parâmetro: Localidade
        niveis_disponiveis = self.get_metadata(id_agregado)['nivelTerritorial']['Administrativo']
        if not re.fullmatch("N[0-9]+", level):
            try:
                level = invert_dict(self.niveis_geo_dict)[level]
            except KeyError:
                pass
        if level not in niveis_disponiveis:
            msg = "O nível geográfico [level] não está disponível. Selecione:"
            for nivel in niveis_disponiveis:
                msg += f"\n{nivel} : {self.niveis_geo_dict[nivel]}"
            raise ValueError(msg)
        query += f"localidades={level}[all]"
        
        # Parâmetro: Categoria
        def get_class_dict() -> dict:
            class_dict = dict()
            for class_ in self.get_metadata(id_agregado)['classificacoes']:
                # Extrai nomes e IDs das categorias em um dicionário
                categorias_dict = dict([(cat['nome'], cat['id']) for cat in class_['categorias']])
                # Cria dicionario com valores [ID classificação, dict categorias]
                class_dict[class_['nome']] = [class_['id'], categorias_dict]
            return class_dict
        
        def get_error_msg(class_dict: dict) -> str:
            msg = "O dicionário [classify] é inválido. Classes disponíveis:"
            for class_, (_, cat_dict) in class_dict.items():
                msg += f"\n{class_}:"
                for cat in cat_dict:
                    msg += f"\n  - {cat}"
            return msg
        
        def get_parametro_classificacao() -> str:
            parametro_class = '&classificacao='
            for class_, categoria in classify.items():
                if class_ not in class_dict:
                    raise ValueError(get_error_msg(class_dict))
                if isinstance(categoria, str):
                    categoria = [categoria]
                # Adiciona o ID da classe ao parâmetro
                parametro_class += f"{class_dict[class_][0]}"
                # Adiciona os IDs das categorias pertencentes a classe
                ids_cat = [class_dict[class_][1][cat] for cat in categoria]
                parametro_class += str(ids_cat).replace(' ', '') + '|'
            return parametro_class[:-1] # Remove o último caráctere pipe (|)
        
        if classify is not None:
            class_dict = get_class_dict()
            if (not isinstance(classify, dict)) or (len(classify) == 0):
                raise ValueError(get_error_msg(class_dict))
            query += get_parametro_classificacao()
        
        # ----- Obtenção do data frame
        # A série de for loops representa a navegação pelo JSON retornado pela API
        # *Há uma forma de navegar por JSON trees com código mais limpo?
        json = requests.get(query).json()
    
        df_dict = dict()
        for variavel in json:
            for classificacoes in variavel['resultados']:
                df = pd.DataFrame()
                for local in classificacoes['series']:              
                    local_stamp = local['localidade']['nome']
                    for periodo, valor in local['serie'].items():
                        df.loc[local_stamp, periodo] = float(valor)
                
                class_stamp = str()
                for categoria in classificacoes['classificacoes']:
                    class_stamp += f" - {str(*categoria['categoria'].values())}"
                var_stamp = variavel['variavel'] + class_stamp
                df_dict[var_stamp] = df
        
        if len(df_dict) == 1:
            return [*df_dict.values()][0]
        return df_dict