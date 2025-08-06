#!/usr/bin/env python3
"""
Script para corrigir o logging em todas as ferramentas Chatwoot
"""

import os

# Lista de ferramentas para corrigir
tools_to_fix = [
    "cadastros_tool.py",
    "duvidas_tool.py",
    "atribui_cidade_tool.py",
    "contato_categoria_tool.py"
]

# Template de imports para adicionar
logging_imports = """import os
import requests
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()"""

for tool_file in tools_to_fix:
    file_path = f"tools/{tool_file}"
    if os.path.exists(file_path):
        print(f"Corrigindo {tool_file}...")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Substituir imports
        if "import logging" not in content:
            content = content.replace(
                "import os\nimport requests\nfrom dotenv import load_dotenv\n\nload_dotenv()",
                logging_imports
            )

        # Substituir prints de DEBUG
        content = content.replace('print(f"[DEBUG] Fazendo POST para: {url}")', 'logger.debug(f"[{self.__class__.__name__}] POST para: {url}")')
        content = content.replace('print(f"[DEBUG] Headers: {headers}")', '# Headers logados apenas em debug se necessário')
        content = content.replace('print(f"[DEBUG] Body: {body}")', 'logger.debug(f"[{self.__class__.__name__}] Body: {body}")')
        content = content.replace('print(f"[DEBUG] Status code: {response.status_code}")', 'logger.info(f"[{self.__class__.__name__}] Status: {response.status_code}")')
        content = content.replace('print(f"[DEBUG] Response: {response.text}")', 'if response.status_code != 200: logger.error(f"[{self.__class__.__name__}] Erro: {response.text}")')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ {tool_file} corrigido!")
    else:
        print(f"❌ {tool_file} não encontrado!")

print("\n🎉 Todas as ferramentas foram corrigidas para usar logging adequado!")
print("Agora os logs aparecerão corretamente no EasyPanel!")
