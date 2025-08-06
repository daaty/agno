"""
Ferramenta de busca DuckDuckGo para a Alice da Urban
"""

import urllib.request
import urllib.parse
import json
from typing import Dict, Any


def duckduckgo_search(query: str) -> Dict[str, Any]:
    """
    Ferramenta de busca DuckDuckGo para informações complementares.

    Use quando:
    - knowledge_base não tiver a resposta
    - Usuário perguntar sobre horários de transporte, localizações específicas
    - Problemas técnicos que precisam de soluções atualizadas
    - Informações sobre cidades específicas da região

    Args:
        query: Consulta de busca

    Returns:
        Dict com resultados da busca
    """
    print(f"[DuckDuckGo] Buscando: {query}")

    try:
        # API do DuckDuckGo Instant Answer
        base_url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'pretty': '1',
            'no_redirect': '1',
            'no_html': '1',
            'skip_disambig': '1'
        }

        # Construir URL com parâmetros
        url = base_url + '?' + urllib.parse.urlencode(params)

        # Fazer requisição
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        # Extrair informações relevantes
        result = {
            "status": "success",
            "abstract": data.get('Abstract', ''),
            "abstract_text": data.get('AbstractText', ''),
            "abstract_url": data.get('AbstractURL', ''),
            "instant_answer": data.get('Answer', ''),
            "definition": data.get('Definition', ''),
            "related_topics": []
        }

        # Adicionar tópicos relacionados (limitado a 3)
        if data.get('RelatedTopics'):
            for topic in data.get('RelatedTopics', [])[:3]:
                if isinstance(topic, dict) and topic.get('Text'):
                    result["related_topics"].append({
                        "text": topic.get('Text', ''),
                        "url": topic.get('FirstURL', '')
                    })

        # Log do resultado
        info_found = result.get('abstract') or result.get('instant_answer') or result.get('definition')
        has_related = result.get('related_topics') and len(result['related_topics']) > 0

        if info_found or has_related:
            print(f"[DuckDuckGo] Resultado encontrado: {str(info_found or 'Tópicos relacionados')[:100]}...")
            # Adiciona campo results para compatibilidade
            result["results"] = []
            if info_found:
                result["results"].append({
                    "title": "Informação Principal",
                    "content": info_found,
                    "url": result.get('abstract_url', '')
                })
            # Adiciona tópicos relacionados como resultados
            for topic in result.get('related_topics', []):
                result["results"].append({
                    "title": topic.get('text', '').split(' - ')[0],
                    "content": topic.get('text', ''),
                    "url": topic.get('url', '')
                })
        else:
            print("[DuckDuckGo] Nenhuma resposta específica encontrada")

        # Adiciona um resumo melhor
        if result.get('abstract'):
            result["summary"] = result['abstract'][:200] + "..." if len(result['abstract']) > 200 else result['abstract']
        elif result.get('related_topics'):
            result["summary"] = f"Encontrei {len(result['related_topics'])} tópicos relacionados sobre '{query}'"
        else:
            result["summary"] = f"Busca por '{query}' não retornou resultados específicos"

        return result

    except Exception as e:
        error_msg = str(e).lower()
        if 'timeout' in error_msg:
            print("[DuckDuckGo] Timeout na busca")
            return {
                "status": "timeout",
                "message": "A busca demorou mais que o esperado. Vou te conectar com um atendente para uma resposta mais rápida."
            }
        else:
            print(f"[DuckDuckGo] Erro: {str(e)}")
            return {
                "status": "error",
                "message": "Não consegui fazer a busca no momento. Deixe-me te conectar com nossa equipe."
            }


# Registrar a ferramenta
def register_duckduckgo_tool():
    """Registra a ferramenta DuckDuckGo"""
    return duckduckgo_search
