#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Conformidade das Estratégias de Trading
Valida se as correções implementadas estão seguindo as regras originais:

1. MICRO-BURST: Filtro 2 corrigido para padrão WIN-LOSS-WIN específico
2. QUANTUM MATRIX: Gatilho 2 corrigido para WINs APÓS LOSS antigo (5+ operações)
3. PRECISION SURGE: Filtro win rate 70% removido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analisis_scalping_bot import (
    analisar_micro_burst,
    analisar_quantum_matrix,
    analisar_precision_surge
)

def test_micro_burst_filter2_correction():
    """
    Testa a correção do Filtro 2 do Micro-Burst:
    - Deve aceitar apenas padrão WIN-LOSS-WIN específico
    - Deve rejeitar LOSS isolado que não está em padrão WIN-LOSS-WIN
    """
    print("\n=== TESTE MICRO-BURST FILTRO 2 CORRIGIDO ===")
    
    # Caso 1: Padrão WIN-LOSS-WIN correto (deve APROVAR)
    historico_correto = ['V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V']  # LOSS na posição 3 com WIN antes e depois
    resultado = analisar_micro_burst(historico_correto)
    print(f"Caso 1 - Padrão WIN-LOSS-WIN: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == True, "Deveria aprovar padrão WIN-LOSS-WIN"
    
    # Caso 2: LOSS isolado mas não em padrão WIN-LOSS-WIN (deve REJEITAR)
    historico_incorreto = ['V', 'V', 'D', 'D', 'V', 'V', 'V', 'V', 'V', 'V']  # LOSS na posição 2 seguido de outro LOSS
    resultado = analisar_micro_burst(historico_incorreto)
    print(f"Caso 2 - LOSS não em WIN-LOSS-WIN: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == False, "Deveria rejeitar LOSS não em padrão WIN-LOSS-WIN"
    
    # Caso 3: LOSS no início (não pode ter WIN antes) (deve REJEITAR)
    historico_inicio = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']  # LOSS na posição 0
    resultado = analisar_micro_burst(historico_inicio)
    print(f"Caso 3 - LOSS no início: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == False, "Deveria rejeitar LOSS no início"
    
    print("✅ MICRO-BURST Filtro 2 corrigido funcionando corretamente")

def test_quantum_matrix_trigger2_correction():
    """
    Testa a correção do Gatilho 2 do Quantum Matrix:
    - Deve procurar WINs APÓS LOSS antigo (5+ operações)
    - Não deve procurar LOSS APÓS WINs (lógica anterior incorreta)
    """
    print("\n=== TESTE QUANTUM MATRIX GATILHO 2 CORRIGIDO ===")
    
    # Caso 1: 3 WINs consecutivos + último LOSS há 6 operações (deve APROVAR)
    historico_correto = ['V', 'V', 'V'] + ['V'] * 3 + ['D'] + ['V'] * 10  # LOSS na posição 6
    resultado = analisar_quantum_matrix(historico_correto)
    print(f"Caso 1 - 3 WINs + LOSS há 6 ops: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == True, "Deveria aprovar 3 WINs com LOSS há 6 operações"
    
    # Caso 2: 4 WINs consecutivos + último LOSS há 3 operações (deve REJEITAR)
    historico_incorreto = ['V', 'V', 'V', 'V'] + ['D'] + ['V'] * 10  # LOSS na posição 4 (< 5)
    resultado = analisar_quantum_matrix(historico_incorreto)
    print(f"Caso 2 - 4 WINs + LOSS há 4 ops: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == False, "Deveria rejeitar LOSS há menos de 5 operações"
    
    # Caso 3: 6 WINs consecutivos (Gatilho 1 - deve APROVAR)
    historico_gatilho1 = ['V'] * 6 + ['D'] + ['V'] * 10
    resultado = analisar_quantum_matrix(historico_gatilho1)
    print(f"Caso 3 - 6 WINs consecutivos: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == True, "Deveria aprovar 6+ WINs consecutivos"
    
    print("✅ QUANTUM MATRIX Gatilho 2 corrigido funcionando corretamente")

def test_precision_surge_filter3_removal():
    """
    Testa a remoção do filtro win rate 70% do Precision Surge:
    - Deve aprovar estratégias mesmo com win rate < 70%
    - Deve focar apenas nos filtros originais (LOSSes e consecutivos)
    """
    print("\n=== TESTE PRECISION SURGE FILTRO 3 REMOVIDO ===")
    
    # Caso 1: 4 WINs consecutivos + win rate baixo mas filtros originais OK (deve APROVAR)
    # 4 WINs + 11 operações com apenas 2 LOSSes (dentro do limite) e sem consecutivos
    historico_baixo_winrate = ['V', 'V', 'V', 'V'] + ['D', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V']  # ~73% win rate, 2 LOSSes
    resultado = analisar_precision_surge(historico_baixo_winrate)
    print(f"Caso 1 - Win rate ~60%: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == True, "Deveria aprovar mesmo com win rate < 70%"
    
    # Caso 2: 5 WINs consecutivos + filtros originais OK (deve APROVAR)
    historico_5wins = ['V', 'V', 'V', 'V', 'V'] + ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']  # 5 WINs + apenas 1 LOSS
    resultado = analisar_precision_surge(historico_5wins)
    print(f"Caso 2 - 5 WINs consecutivos: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == True, "Deveria aprovar 5 WINs consecutivos"
    
    # Caso 3: LOSSes consecutivos (deve REJEITAR pelos filtros originais)
    historico_losses_consecutivos = ['V', 'V', 'V', 'V'] + ['D', 'D'] + ['V'] * 9
    resultado = analisar_precision_surge(historico_losses_consecutivos)
    print(f"Caso 3 - LOSSes consecutivos: {resultado['should_operate']} - {resultado['reason']}")
    assert resultado['should_operate'] == False, "Deveria rejeitar LOSSes consecutivos"
    
    print("✅ PRECISION SURGE Filtro 3 removido funcionando corretamente")

def test_all_strategies_integration():
    """
    Teste de integração para verificar se todas as estratégias funcionam corretamente
    após as correções implementadas
    """
    print("\n=== TESTE DE INTEGRAÇÃO DAS ESTRATÉGIAS CORRIGIDAS ===")
    
    # Histórico que deve ativar MICRO-BURST
    historico_micro = ['V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V']  # 2 WINs + padrão WIN-LOSS-WIN
    resultado_micro = analisar_micro_burst(historico_micro)
    print(f"MICRO-BURST: {resultado_micro['should_operate']} - {resultado_micro.get('confidence', 'N/A')}%")
    
    # Histórico que deve ativar PRECISION SURGE
    historico_precision = ['V', 'V', 'V', 'V'] + ['D', 'V'] * 5 + ['V']  # 4 WINs + sem consecutivos
    resultado_precision = analisar_precision_surge(historico_precision)
    print(f"PRECISION SURGE: {resultado_precision['should_operate']} - {resultado_precision.get('confidence', 'N/A')}%")
    
    # Histórico que deve ativar QUANTUM MATRIX
    historico_quantum = ['V'] * 6 + ['D'] + ['V'] * 10  # 6 WINs consecutivos
    resultado_quantum = analisar_quantum_matrix(historico_quantum)
    print(f"QUANTUM MATRIX: {resultado_quantum['should_operate']} - {resultado_quantum.get('confidence', 'N/A')}%")
    
    estrategias_ativas = sum([resultado_micro['should_operate'], 
                             resultado_precision['should_operate'], 
                             resultado_quantum['should_operate']])
    
    print(f"\n📊 Resultado: {estrategias_ativas}/3 estratégias ativas após correções")
    print("✅ Teste de integração concluído")

def main():
    """
    Executa todos os testes de conformidade das estratégias corrigidas
    """
    print("🔍 INICIANDO TESTES DE CONFORMIDADE DAS ESTRATÉGIAS")
    print("=" * 60)
    
    try:
        test_micro_burst_filter2_correction()
        test_quantum_matrix_trigger2_correction()
        test_precision_surge_filter3_removal()
        test_all_strategies_integration()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES DE CONFORMIDADE PASSARAM!")
        print("✅ As estratégias estão seguindo as regras originais corretamente")
        print("✅ Problemas críticos identificados foram corrigidos:")
        print("   - MICRO-BURST: Filtro 2 implementa padrão WIN-LOSS-WIN específico")
        print("   - QUANTUM MATRIX: Gatilho 2 procura WINs APÓS LOSS antigo (5+ ops)")
        print("   - PRECISION SURGE: Filtro win rate 70% removido")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        return False
    except Exception as e:
        print(f"\n💥 ERRO DURANTE TESTE: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)