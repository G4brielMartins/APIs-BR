import pytest

from apisbr.api import LocalidadesIBGE

api_localidades = LocalidadesIBGE()

@pytest.mark.parametrize("obj,key,id_",[
    (LocalidadesIBGE, "Cabixi - RO", 1100031),
    (api_localidades, "Espigão D'Oeste - RO", 1100098)
    ])
class TestIdDict():
    @pytest.mark.core
    def test_get_name_to_id_dict(self, obj, key, id_):
        id_dict = obj.get_id_dict()
        assert id_dict[key] == id_
    
    def test_get_id_to_name_dict(self, obj, key, id_):
        id_dict = obj.get_id_dict('id')
        assert id_dict[id_] == key
    
    def test_get_id_dict_without_verifier_digit(self, obj, key, id_):
        id_dict = obj.get_id_dict(verifier=False)
        assert id_dict[key] == int(id_/10)