#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de debug específico para validação das estratégias
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from radar_analyzer import analisar_estrategias_portfolio

def test_individual_strategies():
    """
    Testa cada estratégia individualmente com os históricos corrigidos
    """
    print("TESTE INDIVIDUAL DAS ESTRATÉGIAS")
    print("="*80)
    
    # 1. PREMIUM_RECOVERY
    print("\n1. TESTANDO PREMIUM_RECOVERY:")
    historico_premium = ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V'] + ['V'] * 22
    print(f"Histórico: {' '.join(historico_premium[:15])}...")
    resultado = analisar_estrategias_portfolio(historico_premium)
    print(f"Should operate: {resultado.get('should_operate', False)}")
    if resultado.get('melhor_estrategia'):
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
    else:
        print("Nenhuma estratégia detectada")
    
    # 2. MOMENTUM_SHIFT
    print("\n2. TESTANDO MOMENTUM_SHIFT:")
    historico_momentum = ['D'] + ['V', 'V', 'V', 'V', 'V', 'V', 'D'] + ['V', 'D', 'V', 'D', 'V', 'D', 'V', 'D'] + ['V'] * 14
    print(f"Histórico: {' '.join(historico_momentum[:15])}...")
    resultado = analisar_estrategias_portfolio(historico_momentum)
    print(f"Should operate: {resultado.get('should_operate', False)}")
    if resultado.get('melhor_estrategia'):
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
    else:
        print("Nenhuma estratégia detectada")
    
    # 3. CYCLE_TRANSITION
    print("\n3. TESTANDO CYCLE_TRANSITION:")
    historico_cycle = ['V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D']
    print(f"Histórico: {' '.join(historico_cycle)}")
    resultado = analisar_estrategias_portfolio(historico_cycle)
    print(f"Should operate: {resultado.get('should_operate', False)}")
    if resultado.get('melhor_estrategia'):
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
    else:
        print("Nenhuma estratégia detectada")
    
    # 4. FIBONACCI_RECOVERY
    print("\n4. TESTANDO FIBONACCI_RECOVERY:")
    historico_fib = ['D', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"Histórico: {' '.join(historico_fib[:15])}...")
    resultado = analisar_estrategias_portfolio(historico_fib)
    print(f"Should operate: {resultado.get('should_operate', False)}")
    if resultado.get('melhor_estrategia'):
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
    else:
        print("Nenhuma estratégia detectada")
    
    # 5. STABILITY_BREAK
    print("\n5. TESTANDO STABILITY_BREAK:")
    historico_stability = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"Histórico: {' '.join(historico_stability[:15])}...")
    resultado = analisar_estrategias_portfolio(historico_stability)
    print(f"Should operate: {resultado.get('should_operate', False)}")
    if resultado.get('melhor_estrategia'):
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
    else:
        print("Nenhuma estratégia detectada")
    
    print("\n" + "="*80)
    print("TESTE INDIVIDUAL CONCLUÍDO")
    print("="*80)

if __name__ == "__main__":
    test_individual_strategies()