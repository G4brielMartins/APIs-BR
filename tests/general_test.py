import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from apisbr.core import API
from apisbr.api import *

load_dotenv()

API_TOKEN = os.getenv("dados_abertos_token")

test_apis = [
    # (DadosAbertos(API_TOKEN), ("bolsa família", "7ed7c95a-ec15-45ed-a4cd-1c07fe70d45d"))
    (AgregadosIBGE(), ("1685;Número de unidades locais", "1685-706"))
]
@pytest.mark.parametrize("api,title", test_apis)
class TestAPI():
    @pytest.mark.core
    def test_get_id(self, api: API, title: str):
        id = api.get_id(title[0])
        assert id == title[1]
    
    def test_get_id_no_match(self, api: API, title: str):
        with pytest.raises(API.NoMatchFound):
            api.get_id(title[0].split()[0])
    
    @pytest.mark.core
    @pytest.mark.slow
    def test_get_data_by_name(self, api: API, title: str):
        data_dict = api.get_data(title[0])
        values = list(data_dict.values())
        assert isinstance(data_dict, dict) and isinstance(values[0], bytes)
    
    @pytest.mark.slow
    def test_get_data_by_id(self, api: API, title: str):
        data_dict = api.get_data(title[1])
        values = list(data_dict.values())
        assert isinstance(data_dict, dict) and isinstance(values[0], bytes)
    
    @pytest.mark.slow
    def test_download_data(self, api: API, title: str, tmp_path: Path):
        api.download_data(title[1], tmp_path)
        abs_file_paths = [os.path.join(tmp_path, file_path) for file_path in os.listdir(tmp_path)]
        assert all(os.path.isfile(path) for path in abs_file_paths)