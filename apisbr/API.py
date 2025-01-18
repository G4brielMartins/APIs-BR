from typing import Optional
from os.path import join

class API():
    """
    Classe base para implementação das demais APIs.  
    ** APRESENTA MÉTODOS QUE DEVEM SER IMPLEMENTADOS PARA FUNCIONAR CORRETAMENTE **

    Raises
    ------
    NotImplementedError
        Provocado quando métodos essenciais e não implementados são chamados.
    """    
    DATEPARSER_SETTINGS = {'DATE_ORDER': 'DMY', 'PREFER_DAY_OF_MONTH': 'last', 'PREFER_MONTH_OF_YEAR': 'last'}
    """Configuração para o dateparser quando datas são lidas das APIs"""
    
    server_url = ''
    """URL do servidor da API."""
    
    def get_id(self, title: str) -> str:
        """
        Retorna o ID do conjunto de dados com nome equivalente a [title].  
        *Implementado nas classes filhas.
        """
        raise NotImplementedError
    
    def get_data(self, identifier: str) -> dict[str, bytes]:
        """
        Retorna um dicionário com os nomes dos conjuntos de dados como chaves e seu conteúdo em bytes.  
        *Implementado nas classes filhas.
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
    
    def set_dateparser_settings(self, parser_settings: dict) -> None:
        """
        Atualiza as configurações utilizadas pelo parser de datas.  
        ** DEVE SER UTILIZADO APENAS QUANDO OS FILTROS DE DATA NÃO FUNCIONAREM CORRETAMENTE **

        Parameters
        ----------
        parsing_settings : dict
            Dicionário contendo as configurações do parser.  
            São utilizadas as [opções do dataparser](https://dateparser.readthedocs.io/en/latest/settings.html).
        """        
        self.DATE_SETTINGS = parser_settings
    
    class NoMatchFound(Exception):
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