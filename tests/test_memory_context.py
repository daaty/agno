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

class DummyAgent(playground.MemoryOptimizedAgent):
    pass

def test_update_memory_city_and_category():
    agent = DummyAgent()
    session_id = "sess1"
    # Mensagem com cidade e categoria
    msg = "Olá, sou passageiro de Alta Floresta"
    agent.update_memory(msg, session_id)
    ctx = agent.context_memory[session_id]
    assert ctx["custom_attributes_city"] == "Alta Floresta"
    assert ctx["custom_attributes_category"] == "Passageiro"

    # Mensagem só com categoria
    msg2 = "Quero atendimento como motorista"
    agent.update_memory(msg2, session_id)
    ctx2 = agent.context_memory[session_id]
    assert ctx2["custom_attributes_category"] == "Motorista"

    # Mensagem só com cidade
    msg3 = "Resido em Matupá"
    agent.update_memory(msg3, session_id)
    ctx3 = agent.context_memory[session_id]
    assert ctx3["custom_attributes_city"] == "Matupa"

def test_update_memory_priority_context():
    agent = DummyAgent()
    session_id = "sess2"
    # Mensagem com cidade diferente, mas contexto explícito deve prevalecer
    msg = "Sou de Peixoto"
    context = {"custom_attributes_city": "Alta Floresta", "custom_attributes_category": "Passageiro"}
    agent.update_memory(msg, session_id, context)
    ctx = agent.context_memory[session_id]
    # O contexto explícito deve prevalecer
    assert ctx["custom_attributes_city"] == "Alta Floresta"
    assert ctx["custom_attributes_category"] == "Passageiro"
