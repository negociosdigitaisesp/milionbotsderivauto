#!/usr/bin/env python3
"""
Teste para verificar se as estratégias estão sendo detectadas e enviadas corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analyzer import analisar_estrategias_portfolio

def test_premium_recovery():
    """Teste da estratégia PREMIUM_RECOVERY com dupla LOSS"""
    print("\n=== TESTE PREMIUM_RECOVERY ===")
    
    # Histórico que deve ativar PREMIUM_RECOVERY: dupla LOSS no início
    historico_test = ['D', 'D'] + ['V'] * 23  # Dupla LOSS + 23 WINs
    
    print(f"Histórico teste: {' '.join(historico_test[:10])}...")
    
    resultado = analisar_estrategias_portfolio(historico_test)
    
    print(f"Should operate: {resultado['should_operate']}")
    print(f"Reason: {resultado['reason']}")
    
    if resultado['melhor_estrategia']:
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
        print(f"Total oportunidades: {resultado['total_oportunidades']}")
    
    return resultado

def test_momentum_continuation():
    """Teste da estratégia MOMENTUM_CONTINUATION"""
    print("\n=== TESTE MOMENTUM_CONTINUATION ===")
    
    # Histórico que deve ativar MOMENTUM: LOSS isolada após 5 WINs
    historico_test = ['D'] + ['V'] * 5 + ['V'] * 19  # LOSS + 5 WINs + mais WINs
    
    print(f"Histórico teste: {' '.join(historico_test[:10])}...")
    
    resultado = analisar_estrategias_portfolio(historico_test)
    
    print(f"Should operate: {resultado['should_operate']}")
    print(f"Reason: {resultado['reason']}")
    
    if resultado['melhor_estrategia']:
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
        print(f"Total oportunidades: {resultado['total_oportunidades']}")
    
    return resultado

def test_pattern_reversal():
    """Teste da estratégia PATTERN_REVERSAL"""
    print("\n=== TESTE PATTERN_REVERSAL ===")
    
    # Histórico que deve ativar PATTERN_REVERSAL: padrão específico
    # Lembrar que o histórico é invertido (mais recente primeiro)
    historico_test = ['D', 'V', 'V', 'D', 'V', 'V'] + ['V'] * 19  # Padrão + mais operações
    
    print(f"Histórico teste: {' '.join(historico_test[:10])}...")
    
    resultado = analisar_estrategias_portfolio(historico_test)
    
    print(f"Should operate: {resultado['should_operate']}")
    print(f"Reason: {resultado['reason']}")
    
    if resultado['melhor_estrategia']:
        print(f"Estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
        print(f"Total oportunidades: {resultado['total_oportunidades']}")
    
    return resultado

if __name__ == "__main__":
    print("TESTANDO DETECÇÃO DE ESTRATÉGIAS")
    print("=" * 50)
    
    # Executar testes
    test1 = test_premium_recovery()
    test2 = test_momentum_continuation()
    test3 = test_pattern_reversal()
    
    print("\n=== RESUMO DOS TESTES ===")
    print(f"PREMIUM_RECOVERY ativou: {test1['should_operate']}")
    print(f"MOMENTUM_CONTINUATION ativou: {test2['should_operate']}")
    print(f"PATTERN_REVERSAL ativou: {test3['should_operate']}")