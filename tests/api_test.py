import os

import pytest
from dotenv import load_dotenv

from apisbr import API, DadosAbertos

load_dotenv()

API_TOKEN = os.getenv("dados_abertos_token")


test_apis = [
    (DadosAbertos(API_TOKEN), "bolsa família")
]

@pytest.mark.parametrize("api,title", test_apis)
class TestAPI():        
    def test_get_id(self, api: API, title: str):
        id = api.get_id(title)
        assert isinstance(id, str)
    
    def test_get_id_no_match(self, api: API, title: str):
        with pytest.raises(API.NoMatchFound):
            api.get_id(title.split()[0])
    
    def test_get_data_by_name(self, api: API, title: str):
        data_dict = api.get_data(title)
        values = list(data_dict.values())
        assert isinstance(data_dict, dict) and isinstance(values[0], bytes)
    
    @pytest.mark.slow
    def test_get_data_by_id(self, api: API, title: str):
        data_dict = api.get_data(api.get_id(title))
        values = list(data_dict.values())
        assert isinstance(data_dict, dict) and isinstance(values[0], bytes)
    
    @pytest.mark.slow
    def test_download_data(self, api: API, title: str, tmp_path):
        api.download_data(title, tmp_path)
        abs_file_paths = [os.path.join(tmp_path, file_path) for file_path in os.listdir(tmp_path)]
        assert all(os.path.isfile(path) for path in abs_file_paths)