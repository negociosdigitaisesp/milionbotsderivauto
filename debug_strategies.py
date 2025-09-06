#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para analisar estratégias individualmente
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from radar_analyzer import analisar_estrategias_portfolio
    
    print("Testando estratégias individualmente...")
    print("="*80)
    
    # Teste 1: PREMIUM_RECOVERY
    print("\n1. TESTANDO PREMIUM_RECOVERY:")
    # Dupla LOSS no início + exatamente 6 WINs antes da 1ª LOSS + máximo 2 LOSSes em 20 ops
    # Estrutura: [D, D] + [6 WINs nas posições 2-7] + [resto com máximo 2 LOSSes em 20 ops]
    historico_premium = ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    resultado = analisar_estrategias_portfolio(historico_premium)
    print(f"Resultado: {resultado}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    print(f"Strategy: {resultado.get('strategy', 'None')}")
    
    # Teste 2: MOMENTUM_SHIFT
    print("\n2. TESTANDO MOMENTUM_SHIFT:")
    # Janela antiga (ops 10-19): 5V + 5D = 50% win rate (≤60%)
    # Janela recente (ops 0-9): 8V + 2D = 80% win rate (≥80%)
    historico_momentum = ['V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D',  # Recente: 80% win rate
                         'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V',  # Antiga: 50% win rate
                         'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    resultado = analisar_estrategias_portfolio(historico_momentum)
    print(f"Resultado: {resultado}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    print(f"Strategy: {resultado.get('strategy', 'None')}")
    
    # Teste 3: CYCLE_TRANSITION
    print("\n3. TESTANDO CYCLE_TRANSITION:")
    # Exatamente 20 operações para garantir posição 1 no ciclo
    historico_cycle = ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V',
                      'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V']  # Exatamente 20 ops
    resultado = analisar_estrategias_portfolio(historico_cycle)
    print(f"Resultado: {resultado}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    print(f"Strategy: {resultado.get('strategy', 'None')}")
    
    # Teste 4: FIBONACCI_RECOVERY
    print("\n4. TESTANDO FIBONACCI_RECOVERY:")
    # LOSS isolada com padrões específicos, win rate realista
    historico_fib = ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V',
                    'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V',  # 90% win rate
                    'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'D']
    resultado = analisar_estrategias_portfolio(historico_fib)
    print(f"Resultado: {resultado}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    print(f"Strategy: {resultado.get('strategy', 'None')}")
    
    # Teste 5: STABILITY_BREAK
    print("\n5. TESTANDO STABILITY_BREAK:")
    # LOSS isolada + 8+ WINs consecutivos no final + alta estabilidade geral
    historico_stability = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V',  # LOSS isolada + 9 WINs consecutivos
                          'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V',  # Mais WINs para estabilidade
                          'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']  # 96.7% win rate
    resultado = analisar_estrategias_portfolio(historico_stability)
    print(f"Resultado: {resultado}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    print(f"Strategy: {resultado.get('strategy', 'None')}")
    
except ImportError as e:
    print(f"Erro ao importar radar_analyzer: {e}")
except Exception as e:
    print(f"Erro durante a execução: {e}")
    import traceback
    traceback.print_exc()