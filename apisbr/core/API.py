import re
from typing import Optional
from os.path import join

from .DateParser import DateParser

class API():
    """
    Classe base para implementação das demais APIs.  
    ** APRESENTA MÉTODOS QUE DEVEM SER IMPLEMENTADOS PARA FUNCIONAR CORRETAMENTE **

    Raises
    ------
    NotImplementedError
        Provocado quando métodos essenciais e não implementados são chamados.
    """    
    date_parser = DateParser()
    """Parser de datas para uso interno de filtros e leitura de inputs."""
    server_url = str()
    """URL do servidor da API."""
    id_regex : re.Pattern = ''
    """Regex para identifcar IDs dos conjuntos de dados."""
    
    def __getitem__(self, title: str) -> str:
        """
        Método alternativo de chamar a função self.get_id().  
        * Suporta apenas o parâmetro [title], ignorando as opções extras de self.get_id()

        Parameters
        ----------
        title : str
            Título a ser procurado na API.

        Returns
        -------
        str
            ID do conjunto de dados encontrado na API.
        """
        return self.get_id(title)
    
    def get_id(self, title: str) -> str:
        """
        Retorna o ID do conjunto de dados com nome equivalente a [title].  
        *Implementado nas classes filhas.
        """
        raise NotImplementedError
    
    def get_data(self, identifier: str) -> dict[str, bytes]:
        """
        Retorna um dicionário com os nomes dos conjuntos de dados como chaves e seu conteúdo em bytes.  
        
        * Implementado nas classes filhas.
        """
        raise NotImplementedError
    
    def download_data(self, identifier: str, output_folder: str, /,
                      data: Optional[dict[str, bytes]] = None, **kwargs) -> None:
        """
        Baixa os arquivos retornados pelo método get_data([identifier]) na pasta [output_folder]. 

        Parameters
        ----------
        identifier : str
            Identificador do conjunto de dados a ser procurado na API.
        output_folder : str
            Pasta em que os arquivos serão salvos.
        data : dict
            Dicionário com os arquivos (bytes) a serem salvos.  
            Quando empregado, get_data() não é chamado.
        **kwargs : 
            Outros parâmetros a serem passados para get_data().
        """
        if data is None:
            data = self.get_data(identifier, **kwargs)
        for name, file_bytes in data.items():
            with open(join(output_folder, name), 'wb') as f:
                f.write(file_bytes)
    
    def update_dateparser(self, new_settings: dict[str, str]) -> None:
        """
        Atualiza as configurações utilizadas pelo parser de datas.  
        
        ** DEVE SER UTILIZADO APENAS QUANDO OS FILTROS DE DATA NÃO FUNCIONAREM CORRETAMENTE **

        Parameters
        ----------
        parsing_settings : dict
            Dicionário contendo as configurações do parser.  
            São utilizadas as [opções do dataparser](https://dateparser.readthedocs.io/en/latest/settings.html).
        """        
        self.date_parser.set_settings(new_settings)
    
    class NoMatchFoundError(Exception):
        """
        Erro chamado para indicar falha em encontrar correspondência exata com o termo pesquisado.  
        O atributo [semelhantes] pode ser acessado para obter resultados próximos ao pesquisado.
        """    
        def __init__(self, semelhantes: Optional[dict] = None):
            self.semelhantes = semelhantes
            mensagem = "Nenhuma correspondência encontrada."
            
            if semelhantes is not None:
                mensagem += " Seguem possíveis resultados:"
                for nome, id in semelhantes.items():
                    mensagem += (f"\n{nome} : {id}")
                
            super().__init__(mensagem)