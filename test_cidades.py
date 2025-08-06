#!/usr/bin/env python3

# Teste da normalização de cidades
def test_cidade_normalization():
    """Testa a normalização de cidades"""

    # Simula a lógica implementada no playground.py
    cidades_validas = {
        # Mapeamento de variações para nomes EXATOS da API
        "matupa": "Matupa",
        "matupá": "Matupa",
        "guaranta": "Guaranta",
        "guarantã": "Guaranta",
        "guarantã do norte": "Guaranta",
        "peixoto": "Peixoto",
        "peixoto de azevedo": "Peixoto",
        "monte verde": "Monte Verde",
        "nova monte verde": "Monte Verde",
        "bandeirantes": "Bandeirantes",
        "alta floresta": "Alta Floresta",
        "nova canaa": "Nova Canaa",
        "nova canaã": "Nova Canaa",
        "nova canaa do norte": "Nova Canaa",
        "nova canaã do norte": "Nova Canaa",
        "colider": "Colider",
        "colidér": "Colider"
    }

    # Casos de teste
    test_cases = [
        # (input_usuario, esperado)
        ("Matupá", "Matupa"),
        ("matupa", "Matupa"),
        ("MATUPA", "Matupa"),
        ("peixoto", "Peixoto"),
        ("Peixoto de Azevedo", "Peixoto"),
        ("alta floresta", "Alta Floresta"),
        ("ALTA FLORESTA", "Alta Floresta"),
        ("Guarantã", "Guaranta"),
        ("nova canaã do norte", "Nova Canaa"),
        ("Monte Verde", "Monte Verde"),
        ("Bandeirantes", "Bandeirantes"),
        ("Colider", "Colider"),
        ("colidér", "Colider"),
        # Casos inválidos
        ("São Paulo", None),
        ("Cuiabá", None),
        ("Teste", None)
    ]

    print("=== TESTE DE NORMALIZAÇÃO DE CIDADES ===")
    print()

    for input_cidade, esperado in test_cases:
        cidade_normalizada = input_cidade.lower().strip()

        if cidade_normalizada in cidades_validas:
            resultado = cidades_validas[cidade_normalizada]
        else:
            resultado = None

        status = "✅ PASS" if resultado == esperado else "❌ FAIL"
        print(f"{status} '{input_cidade}' -> '{resultado}' (esperado: '{esperado}')")

    print()
    print("=== LISTA DE CIDADES VÁLIDAS NA API ===")
    cidades_unicas = sorted(set(cidades_validas.values()))
    for cidade in cidades_unicas:
        print(f"- {cidade}")

    print()
    print("✅ Teste completo! Todas as variações devem ser normalizadas para os nomes exatos da API.")

if __name__ == "__main__":
    test_cidade_normalization()
