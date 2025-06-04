import requests

from ..utils import invert_dict, remove_accents

class IBGELocalidades():
    server_url = "https://servicodados.ibge.gov.br/api/v1/localidades"
    
    @classmethod
    def get_id_dict(cls, key: str = 'nome', *, verifier: bool = True) -> dict[str, int]|dict[int, str]:
        """
        Gera um dicionário com todos os códigos IBGE de localidade dos municípios brasileiros.  
        *Nomes de municípios no formato 'Nome Do Municipio - UF'.

        Parameters
        ----------
        key : str, optional
            O tipo de chave desejado.  
            - 'nome': (padrão) dicionário com nomes das localidades como chaves, retornando seus IDs.  
            - 'id': dicionáario com IDs das localidades como chaves, retornando seus nomes.
        verifier : bool, optional
            Inclui o dígito verificador para IDs de 7 dígitos (True) ou utiliza IDs de 6 dígitos (False).  
            Por padrão, True.

        Returns
        -------
        dict[str, int]|dict[int, str]
            Dicionário com os IDs e nomes de localidades.  
            A depender do parâmetro 'key', pode receber nomes e retornar IDs (dict[str, int]) ou receber IDs e retornar nomes (dict[int, str]).

        Raises
        ------
        ValueError
            Parâmetros incorretos.
        """
        match key:
            case 'nome':
                invert = False
            case 'id':
                invert = True
            case _:
                raise ValueError("Valor inválido para o parâmetro 'key'.")
        query = cls.server_url + "/municipios"
        id_dict = dict()
        for municipio in requests.get(query).json():
            uf = municipio['regiao-imediata']['regiao-intermediaria']['UF']['sigla']
            value = municipio['id'] if verifier else int(municipio['id']/10)
            id_dict[f"{remove_accents(municipio['nome']).title()} - {uf}"] = value
        if invert:
            id_dict = invert_dict(id_dict)
        return id_dict

def get_muni_name(ibge_id: str|int) -> str:
    """
    Retorna o nome de um município a partir de seu código IBGE.

    Parameters
    ----------
    ibge_id : str | int
        Código de localidade IBGE (6 ou 7 dígitos).

    Returns
    -------
    str
        Nome do município no formato 'Nome Do Municipio - UF'.
    """
    verifier = False
    if isinstance(ibge_id, int):
        ibge_id = str(ibge_id)
    if len(ibge_id) == 7:
        verifier = True
    try:
        return IBGELocalidades.get_id_dict('id', verifier=verifier)[int(ibge_id)]
    except KeyError:
        raise KeyError("Identificador IBGE inválido.")

def get_muni_id(muni_name: str, uf: str, verifier: bool = True) -> int:
    """
    Retorna o código de localidade IBGE de um município.

    Parameters
    ----------
    muni_name : str
        Nome do município.
    uf : str
        Sigla da UF do município (SC, MT...).  
        Utilizado para desambiguar municípios de mesmo nome.
    verifier : bool, optional
        Inclui o dígito verificador para IDs de 7 dígitos (True) ou utiliza IDs de 6 dígitos (False).  
        Por padrão, True.


    Returns
    -------
    int
        Código de localidade IBGE.
    """
    muni_name = remove_accents(muni_name).title() + ' - ' + uf.upper()
    try:
        return IBGELocalidades.get_id_dict(verifier=verifier)[muni_name]
    except KeyError:
        raise KeyError("Nome de município não encontrado.")