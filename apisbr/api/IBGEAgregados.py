import re
import os
from pathlib import Path
from typing import Optional

import requests
import pandas as pd
import numpy as np

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
    """
    Importa o arquivo com todos os identificadores de nível geográfico
    *Não foi encontrada uma forma de obter os identificadores via API

    Returns
    -------
    dict[str, str]
        Dicionário com os nomes e códigos de níveis geográficos.
    """
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


def _process_identifier_input(identifier: str, api) -> tuple[str]:
    """
    Processa o input de identificador.

    Parameters
    ----------
    identifier : str
        Idenficador a ser processado.
    api : _type_
        Instância da classe IBGEAgregados.

    Returns
    -------
    tuple[str]
        id_agregado, id_variavel
    """    
    try:
        match identifier.split(';'):
            case [agregado, variavel]:
                id_agregado, id_variavel = api.get_id(identifier).split(';')
            case [agregado]:
                id_agregado, id_variavel = api.get_id(agregado), None
            case _:
                raise ValueError
    except ValueError:
        raise ValueError("O [identifier] apresenta formato inválido.")
    return id_agregado, id_variavel


class IBGEAgregados(API):
    """
    Wrapper para auxiliar com requisições na [API IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3).
    """
    server_url = "https://servicodados.ibge.gov.br/api/v3/agregados"
    id_regex = re.compile(r"[0-9]{4};[0-9]*")
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
                    out_str += str(variavel['id']) + "|"
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
        return f"{id_agregado};{id_variavel}"
    
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
                 classify: Optional[dict[str]] = None, named_var: bool = True,
                 keep_special: bool = False) -> pd.DataFrame:
        """
        Importa os dados da API IBGE Agregados como um data frame.  
        * Argumentos incorretos resultam em consultas (e.g. [level] inválido irá listar os níveis disponíveis).

        Parameters
        ----------
        identifier : str
            Título ou ID do agregado e variável de interesse.  
            Segue o formato "[título_ou_id_agregado];[titulo_ou_id_var]"  
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
        named_var : bool, optional
            Define se o nome base da variável será utilizado na indexação dos dados. Por padrão, insere o nome base (True).  
            Útil para desambiguação caso haja concatenação de vários dados em uma única estrutura.
        keep_special : bool, optional
            Mantém os valores especiais. Por padrão, 'False' - converte os valores para np.nan.  
            Valores especiais possíveis:  
            - '-'  : Dado numérico igual a zero não resultante de arredondamento  
            - '..' : Não se aplica dado numérico  
            - '...': Dado numérico não disponível  
            - 'X'  : Dado numérico omitido a fim de evitar a individualização da informação

        Returns
        -------
        pd.DataFrame|dict[str, pd.DataFrame]
            Retorna um data frame com os dados solicitados.

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
        id_agregado, id_variavel = _process_identifier_input(identifier, self)
        
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
        
        # Aplica o parâmetro de classificação ao query
        if classify is not None:
            class_dict = get_class_dict()
            if (not isinstance(classify, dict)) or (len(classify) == 0):
                raise ValueError(get_error_msg(class_dict))
            query += get_parametro_classificacao()
        
        # ----- Obtenção do data frame
        # Navegação pela árvore JSON: Metadados
        # Coleta metadados das variáveis solicitadas (nome da variável e categorias de agregação)
        json = requests.get(query).json()
        
        temp_df = pd.json_normalize(json)
        data_name = temp_df['variavel'][0]
        
        temp_df = pd.json_normalize(json, ['resultados'])
        
        def get_categorias(x: str) -> str:
            # Extrai o nome das categorias de agregação de cada conjunto de dados
            categorias = np.array([list(clas['categoria'].values())[0] for clas in x])
            
            # A flag 'Total' indica que não houve agregação por alguma das categorias disponíveis
            # É mantida apenas quando nenhuma agregação é utilizada (irrelevante em outras situações)
            categorias = categorias[categorias != 'Total']
            if len(categorias) == 0:
                return 'Total'
            return ', '.join(categorias)
        temp_df['classificacoes'] = temp_df['classificacoes'].apply(get_categorias)
        
        # Insere o nome base das variáveis caso seja solicitado
        if named_var:
            temp_df['classificacoes'] = data_name + " - " + temp_df['classificacoes']
        
        # Navegação pela árvore JSON: Dados
        # Acessa os valores das variáveis solicitadas
        temp_df['series'] = temp_df['series'].apply(lambda x: pd.json_normalize(x))
        temp_df = temp_df.set_index('classificacoes')
        temp_df = pd.concat(temp_df.to_dict()['series'], axis=1)

        # Extrai os nomes de localidade e os utiliza na indexação dos dados
        temp_df_columns = np.array(temp_df.columns.to_list())
        series_columns = [str(col) for col in temp_df_columns[:, 1] if col.split('.')[0] == 'serie']
        temp_df = temp_df.loc[:, (slice(None), ['localidade.nome'] + series_columns)]
        temp_df = temp_df.set_index((temp_df_columns[0, 0], 'localidade.nome'))
        temp_df.index.rename(None, inplace=True)
        temp_df = temp_df.drop(['localidade.nome'], axis=1, level=1)

        # Renomeia as colunas para tornar a informação mais legível
        new_names = pd.Series(series_columns).apply(lambda x: x.split('.')[1])
        name_mapper = {k: v for k, v in zip(series_columns, new_names)}
        df: pd.DataFrame = temp_df.rename(name_mapper, level=1, axis=1)
        
        # Trata os possíveis valores especiais retornados pela API
        if not keep_special:
            valores_especiais = {
                '-': 0., # Dado numérico igual a zero não resultante de arredondamento
                '..': np.nan, # Não se aplica dado numérico
                '...': np.nan, # Dado numérico não disponível
                'X': np.nan # Dado numérico omitido a fim de evitar a individualização da informação
            }
            def treat_special(x: float|str) -> float:
                try:
                    return float(x)
                except ValueError:
                    return valores_especiais[x]
            df = df.map(treat_special)
        
        return df
    
    def download_data(self, identifier: str, output_folder: str, **kwargs) -> None:
        """
        Faz o download do conjunto de dados encontrado em [output_folder].

        Parameters
        ----------
        identifier : str
            Título ou ID do agregado e variável de interesse.  
            Segue o formato "[título_ou_id_agregado];[titulo_ou_id_var]"  
            Para pesquisar agregados ou variáveis disponíveis:  
            - [palavras chave] -> Procura agregados que contenham as palavras no seu título  
            - [título ou ID agregado] -> Lista as varíaveis disponíveis no agregado
        output_folder : str
            Caminho da pasta onde os dados devem ser salvos.
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
        named_var : bool, optional
            Define se o nome base da variável será utilizado na indexação dos dados.  
            Útil para desambiguação caso haja concatenação de vários dados em uma única estrutura.  
            Por padrão, insere o nome base (True).
        keep_special : bool, optional
            Mantém os valores especiais. Por padrão, 'False' - converte os valores para np.nan.  
            Valores especiais possíveis:  
            - '-'  : Dado numérico igual a zero não resultante de arredondamento  
            - '..' : Não se aplica dado numérico  
            - '...': Dado numérico não disponível  
            - 'X'  : Dado numérico omitido a fim de evitar a individualização da informação
        """        
        super().download_data(identifier, output_folder, **kwargs)