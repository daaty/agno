"""
Configuração de logging para produção no EasyPanel
"""

import logging
import sys
import os

# Tentar importar pythonjsonlogger, mas não quebrar se não estiver disponível
try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False
    print("AVISO: pythonjsonlogger não disponível. Usando formato de log simples.")

def setup_logging():
    """
    Configura logging estruturado para funcionar bem no EasyPanel/Docker
    """
    # Nível de log baseado na variável de ambiente
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Formato estruturado para produção
    if HAS_JSON_LOGGER and os.getenv('ENVIRONMENT') == 'production':
        # JSON logs para produção
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
    else:
        # Formato simples para desenvolvimento ou quando JSON logger não está disponível
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Handler para stdout (padrão do Docker)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Limpa handlers existentes
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    # Configurar loggers específicos para nossas ferramentas
    for logger_name in ['tools', 'agno', 'duckduckgo', 'chatwoot']:
        specific_logger = logging.getLogger(logger_name)
        specific_logger.setLevel(logging.INFO)

    return root_logger

# Configurar automaticamente quando o módulo for importado
logger = setup_logging()
