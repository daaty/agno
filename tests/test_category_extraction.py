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

# Helper para extrair categoria de uma frase usando o método do agente
class DummyAgent(playground.MemoryOptimizedAgent):
    pass

def extract_category_from_text(text):
    agent = DummyAgent()
    facts = agent.extract_facts_from_conversation(text, session_id="test")
    for fact in facts:
        if fact.startswith("categoria:"):
            return fact.split(":", 1)[1].strip()
    return None

def test_extract_category_variations():
    test_cases = [
        ("Sou passageiro", "Passageiro"),
        ("Sou motorista", "Motorista"),
        ("Atendimento como passageiro", "Passageiro"),
        ("Meu atendimento é como motorista", "Motorista"),
        ("Preciso de suporte como passageiro", "Passageiro"),
        ("Quero atendimento como motorista", "Motorista"),
        ("sou Passageiro", "Passageiro"),
        ("SOU MOTORISTA", "Motorista"),
    ]
    for frase, esperado in test_cases:
        extraida = extract_category_from_text(frase)
        # Normaliza para o formato aceito
        if extraida:
            extraida_norm = extraida.capitalize()
        else:
            extraida_norm = None
        assert extraida_norm == esperado, f"Falha na extração/normalização: '{frase}' -> '{extraida_norm}', esperado: '{esperado}'"

def test_validate_category():
    validate_category = playground.validate_category
    assert validate_category("Passageiro")
    assert validate_category("Motorista")
    assert not validate_category("Cliente")
    assert not validate_category("")
    assert not validate_category(None)
