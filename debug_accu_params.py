#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Debug para Parâmetros ACCU
Verifica a estrutura exata dos parâmetros sendo enviados para a API
"""

import json
from accumulator_standalone import GROWTH_RATE, ATIVO

def debug_accu_parameters():
    """Debug detalhado dos parâmetros ACCU"""
    print("🔍 DEBUG - PARÂMETROS ACCU")
    print("=" * 50)
    
    # Simular valores do bot
    stake = 10.0
    take_profit_amount = 50.0
    
    # Estrutura 1: Com limit_order (como no código atual)
    required_params = {
        "proposal": 1,
        "contract_type": "ACCU",
        "symbol": ATIVO,
        "amount": stake,
        "basis": "stake",
        "currency": "USD",
        "growth_rate": GROWTH_RATE,
        "limit_order": {
            "take_profit": take_profit_amount
        }
    }
    
    # Estrutura 2: Sem limit_order (fallback)
    required_params_simple = {
        "proposal": 1,
        "contract_type": "ACCU",
        "symbol": ATIVO,
        "amount": stake,
        "basis": "stake",
        "currency": "USD",
        "growth_rate": GROWTH_RATE
    }
    
    # Estrutura 3: Conforme accu_parameters.py
    from accu_parameters import build_accu_parameters
    accu_params = build_accu_parameters(ATIVO, stake, take_profit_amount)
    
    print("📋 ESTRUTURA 1 (Com limit_order):")
    print(json.dumps(required_params, indent=2))
    print(f"Growth Rate: {required_params['growth_rate']} (tipo: {type(required_params['growth_rate'])})")
    print()
    
    print("📋 ESTRUTURA 2 (Sem limit_order):")
    print(json.dumps(required_params_simple, indent=2))
    print(f"Growth Rate: {required_params_simple['growth_rate']} (tipo: {type(required_params_simple['growth_rate'])})")
    print()
    
    print("📋 ESTRUTURA 3 (accu_parameters.py):")
    print(json.dumps(accu_params, indent=2))
    print(f"Growth Rate: {accu_params['parameters']['growth_rate']} (tipo: {type(accu_params['parameters']['growth_rate'])})")
    print()
    
    # Verificar diferenças
    print("🔍 ANÁLISE DE DIFERENÇAS:")
    print(f"• GROWTH_RATE constante: {GROWTH_RATE} (tipo: {type(GROWTH_RATE)})")
    print(f"• ATIVO: {ATIVO}")
    print(f"• Stake: {stake}")
    print(f"• Take Profit: {take_profit_amount}")
    print()
    
    # Verificar se growth_rate está no intervalo correto
    if 0.01 <= GROWTH_RATE <= 0.05:
        print("✅ Growth Rate está no intervalo correto (0.01 - 0.05)")
    else:
        print("❌ Growth Rate fora do intervalo (0.01 - 0.05)")
    
    # Verificar tipo
    if isinstance(GROWTH_RATE, float):
        print("✅ Growth Rate é do tipo float")
    else:
        print(f"❌ Growth Rate não é float: {type(GROWTH_RATE)}")
    
    print()
    print("🎯 POSSÍVEIS PROBLEMAS:")
    print("1. Estrutura de parâmetros incorreta")
    print("2. API esperando estrutura diferente")
    print("3. Problema na validação do servidor")
    print("4. Versão da API incompatível")
    
    return required_params, required_params_simple, accu_params

if __name__ == "__main__":
    debug_accu_parameters()