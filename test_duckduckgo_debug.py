#!/usr/bin/env python3
"""
Script de teste avançado para a ferramenta DuckDuckGo
Testa com várias consultas diferentes para verificar funcionamento
"""

import sys
import os

# Adiciona o diretório tools ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

from tools.duckduckgo_search_tool import duckduckgo_search

def test_duckduckgo():
    print("🔍 TESTANDO FERRAMENTA DUCKDUCKGO")
    print("=" * 50)

    # Lista de testes que devem retornar resultados
    test_queries = [
        "Python programming language",
        "OpenAI GPT",
        "FastAPI framework",
        "SQLite database",
        "GitHub repository",
        "Stack Overflow programming",
        "Microsoft Windows",
        "Google search engine"
    ]

    successful_tests = 0
    failed_tests = 0

    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 TESTE {i}: '{query}'")
        print("-" * 30)

        try:
            result = duckduckgo_search(query)

            if result and isinstance(result, dict):
                if result.get("status") == "success" and result.get("results"):
                    print(f"✅ SUCESSO!")
                    print(f"📊 Status: {result.get('status')}")
                    print(f"📝 Resumo: {result.get('summary', 'N/A')[:100]}...")
                    print(f"🔗 Links encontrados: {len(result.get('results', []))}")
                    successful_tests += 1
                else:
                    print(f"⚠️ RESULTADO VAZIO")
                    print(f"📊 Status: {result.get('status', 'N/A')}")
                    print(f"📝 Resultado completo: {result}")
                    failed_tests += 1
            else:
                print(f"❌ ERRO: Resultado inválido")
                print(f"📝 Resultado: {result}")
                failed_tests += 1

        except Exception as e:
            print(f"💥 EXCEÇÃO: {str(e)}")
            failed_tests += 1

    print("\n" + "=" * 50)
    print("📈 RELATÓRIO FINAL:")
    print(f"✅ Testes bem-sucedidos: {successful_tests}")
    print(f"❌ Testes falharam: {failed_tests}")
    print(f"📊 Taxa de sucesso: {(successful_tests/(successful_tests+failed_tests)*100):.1f}%")

    if successful_tests > 0:
        print("\n🎉 A ferramenta DuckDuckGo está funcionando!")
    else:
        print("\n🚨 PROBLEMA: A ferramenta DuckDuckGo não está funcionando corretamente!")
        print("\nPossíveis causas:")
        print("1. Problemas de conectividade")
        print("2. API do DuckDuckGo indisponível")
        print("3. Problema na implementação da ferramenta")

if __name__ == "__main__":
    test_duckduckgo()
