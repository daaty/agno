import pytest
import importlib.util
import sys
import os
import logging

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

def test_fallback_logging_city_and_category(caplog):
    agent = DummyAgent()
    session_id = "sess_fallback"
    # Mensagem sem cidade nem categoria reconhecível
    msg = "Olá, preciso de ajuda urgente!"
    with caplog.at_level(logging.WARNING):
        agent.update_memory(msg, session_id)
        logs = caplog.text
        assert "[MEMORY][FALLBACK] Não foi possível extrair/normalizar cidade" in logs
        assert "[MEMORY][FALLBACK] Não foi possível extrair/normalizar categoria" in logs

    # Mensagem só com cidade
    msg2 = "Sou de Matupá"
    with caplog.at_level(logging.INFO):
        agent.update_memory(msg2, session_id)
        logs = caplog.text
        assert "[MEMORY] Cidade extraída automaticamente: 'Matupa'" in logs
        # Categoria ainda não extraída
        assert "[MEMORY][FALLBACK] Não foi possível extrair/normalizar categoria" in logs

    # Mensagem só com categoria
    msg3 = "Sou passageiro"
    with caplog.at_level(logging.INFO):
        agent.update_memory(msg3, session_id)
        logs = caplog.text
        assert "[MEMORY] Categoria extraída automaticamente: 'Passageiro'" in logs
        # Cidade não extraída
        assert "[MEMORY][FALLBACK] Não foi possível extrair/normalizar cidade" in logs
