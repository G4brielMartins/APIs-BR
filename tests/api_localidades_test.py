import pytest

from apisbr.api import LocalidadesIBGE

api_localidades = LocalidadesIBGE()

@pytest.mark.parametrize("obj,key,id_",[
    (LocalidadesIBGE, "Cabixi", 1100031),
    (api_localidades, "Espigão D'Oeste", 1100098)
    ])
def test_get_id_dict(obj, key, id_):
    id_dict = obj.get_id_dict()
    assert id_dict[key] == id_