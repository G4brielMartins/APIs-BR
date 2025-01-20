import requests

class LocalidadesIBGE():
    server_url = "https://servicodados.ibge.gov.br/api/v1/localidades"
    
    @classmethod
    def get_id_dict(cls) -> dict[str, int]:
        query = cls.server_url + "/municipios"
        id_dict = dict()
        for municipio in requests.get(query).json():
            id_dict[municipio['nome']] = municipio['id']
        return id_dict        