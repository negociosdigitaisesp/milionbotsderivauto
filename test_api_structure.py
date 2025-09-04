#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da Estrutura de Parâmetros ACCU conforme Documentação Oficial da Deriv
Baseado em: https://developers.deriv.com/docs/accumulator-options
"""

import json
import asyncio
from accumulator_standalone import GROWTH_RATE, ATIVO

def test_official_structure():
    """Testa estrutura conforme documentação oficial da Deriv"""
    print("🔍 TESTE - ESTRUTURA OFICIAL DERIV API")
    print("=" * 60)
    
    # Estrutura EXATA conforme documentação oficial
    # https://developers.deriv.com/docs/accumulator-options
    official_proposal = {
        "proposal": 1,
        "contract_type": "ACCU",
        "symbol": ATIVO,
        "amount": 10,
        "basis": "stake",
        "currency": "USD",
        "growth_rate": 0.03,  # Exemplo da documentação
        "limit_order": {
            "take_profit": 150  # Exemplo da documentação
        }
    }
    
    # Estrutura sem limit_order (fallback)
    official_proposal_simple = {
        "proposal": 1,
        "contract_type": "ACCU",
        "symbol": ATIVO,
        "amount": 10,
        "basis": "stake",
        "currency": "USD",
        "growth_rate": 0.03
    }
    
    # Nossa estrutura atual
    current_proposal = {
        "proposal": 1,
        "contract_type": "ACCU",
        "symbol": ATIVO,
        "amount": 10,
        "basis": "stake",
        "currency": "USD",
        "growth_rate": GROWTH_RATE,
        "limit_order": {
            "take_profit": 50.0
        }
    }
    
    print("📋 ESTRUTURA OFICIAL (com limit_order):")
    print(json.dumps(official_proposal, indent=2))
    print()
    
    print("📋 ESTRUTURA OFICIAL (sem limit_order):")
    print(json.dumps(official_proposal_simple, indent=2))
    print()
    
    print("📋 NOSSA ESTRUTURA ATUAL:")
    print(json.dumps(current_proposal, indent=2))
    print()
    
    # Comparação detalhada
    print("🔍 COMPARAÇÃO DETALHADA:")
    print(f"• Growth Rate Oficial: {official_proposal['growth_rate']} (tipo: {type(official_proposal['growth_rate'])})")
    print(f"• Growth Rate Nosso: {current_proposal['growth_rate']} (tipo: {type(current_proposal['growth_rate'])})")
    print(f"• Take Profit Oficial: {official_proposal['limit_order']['take_profit']}")
    print(f"• Take Profit Nosso: {current_proposal['limit_order']['take_profit']}")
    print()
    
    # Verificar diferenças estruturais
    print("🎯 DIFERENÇAS IDENTIFICADAS:")
    
    # Verificar chaves
    official_keys = set(official_proposal.keys())
    current_keys = set(current_proposal.keys())
    
    if official_keys == current_keys:
        print("✅ Chaves principais idênticas")
    else:
        missing = official_keys - current_keys
        extra = current_keys - official_keys
        if missing:
            print(f"❌ Chaves ausentes: {missing}")
        if extra:
            print(f"⚠️ Chaves extras: {extra}")
    
    # Verificar valores
    differences = []
    for key in official_keys & current_keys:
        if key == 'growth_rate':
            # Growth rate pode ser diferente, mas deve estar no intervalo
            if not (0.01 <= current_proposal[key] <= 0.05):
                differences.append(f"Growth rate fora do intervalo: {current_proposal[key]}")
        elif key == 'limit_order':
            # Verificar estrutura do limit_order
            if 'take_profit' not in current_proposal[key]:
                differences.append("take_profit ausente em limit_order")
        elif official_proposal[key] != current_proposal[key]:
            if key not in ['amount', 'symbol']:  # Estes podem ser diferentes
                differences.append(f"{key}: oficial='{official_proposal[key]}' vs atual='{current_proposal[key]}'")
    
    if differences:
        print("❌ Diferenças encontradas:")
        for diff in differences:
            print(f"   • {diff}")
    else:
        print("✅ Estruturas compatíveis")
    
    print()
    print("🚀 RECOMENDAÇÕES:")
    print("1. Testar com growth_rate = 0.03 (exemplo da documentação)")
    print("2. Testar com take_profit = 150 (exemplo da documentação)")
    print("3. Verificar se o problema está na validação do servidor")
    print("4. Testar estrutura sem limit_order primeiro")
    
    return official_proposal, official_proposal_simple, current_proposal

def test_growth_rate_variations():
    """Testa diferentes valores de growth_rate permitidos"""
    print("\n🔬 TESTE - VARIAÇÕES DE GROWTH_RATE")
    print("=" * 60)
    
    # Valores permitidos conforme documentação
    allowed_rates = [0.01, 0.02, 0.03, 0.04, 0.05]
    
    for rate in allowed_rates:
        proposal = {
            "proposal": 1,
            "contract_type": "ACCU",
            "symbol": ATIVO,
            "amount": 10,
            "basis": "stake",
            "currency": "USD",
            "growth_rate": rate
        }
        
        print(f"📋 Growth Rate {rate*100}%:")
        print(f"   • Valor: {rate}")
        print(f"   • Tipo: {type(rate)}")
        print(f"   • Válido: {0.01 <= rate <= 0.05}")
        print(f"   • JSON: {json.dumps(proposal, indent=2)}")
        print()

if __name__ == "__main__":
    test_official_structure()
    test_growth_rate_variations()