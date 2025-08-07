import pytest
import importlib.util
import sys
import os

# Garante import local do playground
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

spec = importlib.util.spec_from_file_location("playground", os.path.join(project_root, "playground.py"))
playground = importlib.util.module_from_spec(spec)
sys.modules["playground"] = playground
spec.loader.exec_module(playground)

AppConfig = playground.AppConfig

# Helper para extrair cidade de uma frase usando o método do agente
class DummyAgent(playground.MemoryOptimizedAgent):
    pass

def extract_city_from_text(text):
    agent = DummyAgent()
    facts = agent.extract_facts_from_conversation(text, session_id="test")
    for fact in facts:
        if fact.startswith("cidade:"):
            return fact.split(":", 1)[1].strip()
    return None

def test_extract_city_variations():
    # Frases variadas para cada cidade
    test_cases = [
        ("Eu moro em Matupá", "matupá", "Matupa"),
        ("Sou de Peixoto de Azevedo", "peixoto de azevedo", "Peixoto"),
        ("Minha cidade é Alta Floresta", "alta floresta", "Alta Floresta"),
        ("Resido em Guarantã do Norte", "guarantã do norte", "Guaranta"),
        ("Vivo em Nova Canaã do Norte", "nova canaã do norte", "Nova Canaa"),
        ("Estou em Monte Verde", "monte verde", "Monte Verde"),
        ("Sou de Bandeirantes", "bandeirantes", "Bandeirantes"),
        ("Moro em Colidér", "colidér", "Colider"),
        ("Sou de Colider", "colider", "Colider"),
    ]
    cidades_validas = AppConfig.load_valid_cities()
    for frase, entrada, esperado in test_cases:
        extraida = extract_city_from_text(frase)
        assert extraida is not None, f"Não extraiu cidade de: {frase}"
        # Normaliza para lookup
        normalizada = cidades_validas.get(extraida.lower().strip())
        assert normalizada == esperado, f"Normalização falhou para '{extraida}' -> '{normalizada}', esperado: '{esperado}'"

def test_normalizacao_cidades():
    cidades_validas = AppConfig.load_valid_cities()
    # Todas as variações devem mapear para o nome correto
    variacoes = [
        ("matupa", "Matupa"), ("matupá", "Matupa"),
        ("guaranta", "Guaranta"), ("guarantã", "Guaranta"), ("guarantã do norte", "Guaranta"),
        ("peixoto", "Peixoto"), ("peixoto de azevedo", "Peixoto"),
        ("monte verde", "Monte Verde"), ("nova monte verde", "Monte Verde"),
        ("bandeirantes", "Bandeirantes"),
        ("alta floresta", "Alta Floresta"),
        ("nova canaa", "Nova Canaa"), ("nova canaã", "Nova Canaa"), ("nova canaa do norte", "Nova Canaa"), ("nova canaã do norte", "Nova Canaa"),
        ("colider", "Colider"), ("colidér", "Colider")
    ]
    for entrada, esperado in variacoes:
        assert cidades_validas.get(entrada) == esperado, f"Falha na normalização: {entrada} -> {cidades_validas.get(entrada)} (esperado: {esperado})"
