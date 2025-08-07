
import os
import sys
import pytest
import importlib.util

# Adiciona o diretório do projeto à sys.path para permitir imports relativos
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa AppConfig diretamente do playground.py local
spec = importlib.util.spec_from_file_location("playground", os.path.abspath("playground.py"))
playground = importlib.util.module_from_spec(spec)
sys.modules["playground"] = playground
spec.loader.exec_module(playground)
AppConfig = playground.AppConfig

def test_load_valid_cities_json_exists(tmp_path, monkeypatch):
    # Cria um arquivo cidades.json temporário
    cities = {"cidade1": "Cidade1", "cidade2": "Cidade2"}
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cities_file = config_dir / "cidades.json"
    cities_file.write_text('{"cidade1": "Cidade1", "cidade2": "Cidade2"}', encoding="utf-8")

    # Testa leitura usando o caminho temporário
    result = AppConfig.load_valid_cities(cities_file=str(cities_file))
    assert result == cities

def test_load_valid_cities_fallback(monkeypatch):
    # Simula arquivo inexistente
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    result = AppConfig.load_valid_cities()
    assert "matupa" in result and result["matupa"] == "Matupa"
    assert "alta floresta" in result
