"""
Teste da ferramenta DuckDuckGo integrada na Alice
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.duckduckgo_search_tool import duckduckgo_search

def test_duckduckgo():
    """Testa a ferramenta DuckDuckGo com queries relevantes para Urban"""

    test_queries = [
        "horarios onibus Sinop MT",
        "terminal rodoviario Colider",
        "transporte publico Cuiaba MT",
        "linha de onibus urbano",
        "app erro 504 gateway timeout"
    ]

    print("🔍 TESTANDO FERRAMENTA DUCKDUCKGO DA ALICE 🔍\n")

    for i, query in enumerate(test_queries, 1):
        print(f"--- TESTE {i}: {query} ---")
        result = duckduckgo_search(query)

        print(f"Status: {result.get('status', 'unknown')}")

        if result.get('status') == 'success':
            if result.get('abstract'):
                print(f"Resposta: {result['abstract'][:200]}...")
            elif result.get('instant_answer'):
                print(f"Resposta Instantânea: {result['instant_answer']}")
            elif result.get('definition'):
                print(f"Definição: {result['definition'][:200]}...")
            else:
                print("Nenhuma resposta específica encontrada")

            if result.get('related_topics'):
                print("Tópicos relacionados:")
                for topic in result['related_topics']:
                    print(f"  • {topic['text'][:100]}...")
        else:
            print(f"Erro: {result.get('message', 'Desconhecido')}")

        print("-" * 60)
        print()

if __name__ == "__main__":
    test_duckduckgo()
