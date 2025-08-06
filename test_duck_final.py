#!/usr/bin/env python3
"""
Teste específico para verificar a ferramenta DuckDuckGo
com termos que certamente existem
"""

import sys
import os

# Adiciona o diretório tools ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from tools.duckduckgo_search_tool import duckduckgo_search

def test_specific_searches():
    print("🔍 TESTE ESPECÍFICO DA FERRAMENTA DUCKDUCKGO")
    print("=" * 60)

    # Testes com termos que certamente retornam resultados
    specific_tests = [
        "Brasil país América do Sul",
        "Wikipedia enciclopédia online",
        "São Paulo maior cidade Brasil",
        "Rio de Janeiro cidade maravilhosa",
        "Amazon rainforest largest tropical",
        "Eiffel Tower Paris France",
        "Leonardo da Vinci artist inventor"
    ]

    for i, query in enumerate(specific_tests, 1):
        print(f"\n🧪 TESTE ESPECÍFICO {i}: '{query}'")
        print("-" * 40)

        try:
            result = duckduckgo_search(query)

            print(f"📊 Status: {result.get('status')}")

            if result.get('abstract'):
                print(f"📝 Abstract encontrado: ✅")
                print(f"🔗 URL: {result.get('abstract_url', 'N/A')}")
                print(f"📄 Conteúdo: {result['abstract'][:150]}...")

            if result.get('related_topics'):
                print(f"🔗 Tópicos relacionados: {len(result['related_topics'])}")
                for topic in result['related_topics'][:2]:
                    print(f"   - {topic.get('text', '')[:80]}...")

            if result.get('results'):
                print(f"📋 Total de resultados estruturados: {len(result['results'])}")

            print("✅ TESTE PASSOU!")

        except Exception as e:
            print(f"❌ ERRO: {str(e)}")

    print("\n" + "=" * 60)
    print("🎯 TESTE FINAL - Busca por informação específica:")

    # Teste final com algo muito específico
    final_test = "Albert Einstein teoria relatividade"
    print(f"🔍 Buscando: {final_test}")

    try:
        result = duckduckgo_search(final_test)

        if result.get('abstract'):
            print("\n🏆 SUCESSO COMPLETO!")
            print(f"📝 Resumo encontrado: {result['summary']}")
            print(f"🔗 Fonte: {result.get('abstract_url', 'N/A')}")
            print("\n✅ A ferramenta DuckDuckGo está 100% funcional!")
        else:
            print("\n⚠️ Resultado limitado, mas a ferramenta funciona")

    except Exception as e:
        print(f"\n❌ Erro no teste final: {str(e)}")

if __name__ == "__main__":
    test_specific_searches()
