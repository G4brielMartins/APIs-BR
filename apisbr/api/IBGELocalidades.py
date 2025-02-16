import requests

from ..utils import invert_dict

class IBGELocalidades():
    server_url = "https://servicodados.ibge.gov.br/api/v1/localidades"
    
    @classmethod
    def get_id_dict(cls, key: str = 'nome', *, verifier: bool = True) -> dict[str, int]:  
        match key:
            case 'nome':
                invert = False
            case 'id':
                invert = True
            case _:
                raise ValueError
        query = cls.server_url + "/municipios"
        id_dict = dict()
        for municipio in requests.get(query).json():
            uf = municipio['microrregiao']['mesorregiao']['UF']['sigla']
            value = municipio['id'] if verifier else int(municipio['id']/10)
            id_dict[f"{municipio['nome']} - {uf}"] = value
        if invert:
            id_dict = invert_dict(id_dict)
        return id_dict