#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das correções do executor_momentum_medio_v1.py

Testa os cenários:
1. LLWL sendo interpretado corretamente como LLWL (não LLW)
2. Padrão L-L-L detectado e sinal mantido ativo até primeira operação
3. Primeira operação após padrão executada e sinal desativado
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path para importar o módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar a função que queremos testar
from executor_momentum_medio_v1 import analisar_estrategia_momentum_medio, pattern_state

def reset_pattern_state():
    """Reseta o estado global do padrão para cada teste"""
    global pattern_state
    pattern_state['pattern_detected'] = False
    pattern_state['pattern_timestamp'] = None
    pattern_state['pattern_operations_ids'] = []
    pattern_state['waiting_first_operation'] = False
    pattern_state['last_analyzed_operation_id'] = None

def test_scenario_1_llwl_analysis():
    """Teste 1: Verificar se LLWL é analisado corretamente como LLWL (não LLW)"""
    print("\n=== TESTE 1: Análise correta de LLWL ===")
    reset_pattern_state()
    
    # Histórico: LLWL (mais recente primeiro, como vem do Supabase)
    historico = ['LOSS', 'WIN', 'LOSS', 'LOSS']  # LLWL em ordem DESC
    timestamp = datetime.now().isoformat()
    operation_id = "test_op_1"
    
    resultado = analisar_estrategia_momentum_medio(historico, timestamp, operation_id)
    
    print(f"Histórico testado: {historico} (ordem DESC - mais recente primeiro)")
    print(f"Resultado: {resultado['reason']}")
    print(f"Should operate: {resultado['should_operate']}")
    
    # Verificar se o padrão atual é mostrado corretamente
    expected_pattern = "LWL"  # Últimas 3 operações em ordem cronológica: LWL
    if 'current_pattern' in resultado:
        actual_pattern = resultado['current_pattern']
        print(f"Padrão detectado: {actual_pattern}")
        print(f"Padrão esperado: {expected_pattern}")
        assert actual_pattern == expected_pattern, f"Erro: esperado {expected_pattern}, obtido {actual_pattern}"
        print("✅ TESTE 1 PASSOU: LLWL analisado corretamente como LWL")
    else:
        print("❌ TESTE 1 FALHOU: current_pattern não encontrado no resultado")

def test_scenario_2_lll_pattern_detection():
    """Teste 2: Verificar detecção do padrão L-L-L e ativação do sinal"""
    print("\n=== TESTE 2: Detecção do padrão L-L-L ===")
    reset_pattern_state()
    
    # Histórico: LLL (mais recente primeiro)
    historico = ['LOSS', 'LOSS', 'LOSS']  # LLL em ordem DESC
    timestamp = datetime.now().isoformat()
    operation_id = "test_op_2"
    
    resultado = analisar_estrategia_momentum_medio(historico, timestamp, operation_id)
    
    print(f"Histórico testado: {historico}")
    print(f"Resultado: {resultado['reason']}")
    print(f"Should operate: {resultado['should_operate']}")
    print(f"Strategy: {resultado.get('strategy', 'N/A')}")
    
    # Verificar se o padrão foi detectado e sinal ativado
    assert resultado['should_operate'] == True, "Erro: sinal deveria estar ativo"
    assert resultado.get('pattern_detected') == True, "Erro: padrão deveria estar detectado"
    assert 'L-L-L-Pattern-Active' in resultado.get('strategy', ''), "Erro: estratégia incorreta"
    
    print("✅ TESTE 2 PASSOU: Padrão L-L-L detectado e sinal ativado")
    
    return operation_id

def test_scenario_3_signal_persistence():
    """Teste 3: Verificar se sinal permanece ativo após detecção do padrão"""
    print("\n=== TESTE 3: Persistência do sinal após detecção ===")
    
    # Primeiro, detectar o padrão L-L-L
    last_op_id = test_scenario_2_lll_pattern_detection()
    
    # Agora simular uma nova análise SEM nova operação (mesmo operation_id)
    historico = ['LOSS', 'LOSS', 'LOSS']
    timestamp = datetime.now().isoformat()
    
    resultado = analisar_estrategia_momentum_medio(historico, timestamp, last_op_id)
    
    print(f"\nSegunda análise (sem nova operação):")
    print(f"Resultado: {resultado['reason']}")
    print(f"Should operate: {resultado['should_operate']}")
    
    # Verificar se o sinal ainda está ativo
    assert resultado['should_operate'] == True, "Erro: sinal deveria permanecer ativo"
    assert 'ATIVO' in resultado['reason'] or 'ACTIVE' in resultado.get('strategy', ''), "Erro: sinal deveria estar ativo"
    
    print("✅ TESTE 3 PASSOU: Sinal permanece ativo enquanto aguarda primeira operação")

def test_scenario_4_first_operation_after_pattern():
    """Teste 4: Verificar desativação do sinal após primeira operação pós-padrão"""
    print("\n=== TESTE 4: Primeira operação após padrão L-L-L ===")
    
    # Primeiro, detectar o padrão L-L-L
    test_scenario_2_lll_pattern_detection()
    
    # Simular nova operação após o padrão (WIN)
    historico = ['WIN', 'LOSS', 'LOSS', 'LOSS']  # Nova operação WIN + padrão anterior LLL
    timestamp = datetime.now().isoformat()
    new_operation_id = "test_op_4_new"  # ID diferente = nova operação
    
    resultado = analisar_estrategia_momentum_medio(historico, timestamp, new_operation_id)
    
    print(f"Histórico com nova operação: {historico}")
    print(f"Resultado: {resultado['reason']}")
    print(f"Should operate: {resultado['should_operate']}")
    print(f"Strategy: {resultado.get('strategy', 'N/A')}")
    
    # Verificar se o sinal foi desativado após a primeira operação
    assert resultado['should_operate'] == False, "Erro: sinal deveria estar desativado"
    assert resultado.get('pattern_completed') == True, "Erro: padrão deveria estar marcado como completo"
    assert 'WIN' in resultado['reason'], "Erro: resultado da primeira operação deveria aparecer"
    
    print("✅ TESTE 4 PASSOU: Sinal desativado após primeira operação pós-padrão")

def test_scenario_5_llwl_no_false_positive():
    """Teste 5: Verificar que LLWL não gera falso positivo"""
    print("\n=== TESTE 5: LLWL não deve gerar sinal ===")
    reset_pattern_state()
    
    # Histórico: LLWL (mais recente primeiro)
    historico = ['LOSS', 'WIN', 'LOSS', 'LOSS']  # LLWL em ordem DESC
    timestamp = datetime.now().isoformat()
    operation_id = "test_op_5"
    
    resultado = analisar_estrategia_momentum_medio(historico, timestamp, operation_id)
    
    print(f"Histórico testado: {historico}")
    print(f"Resultado: {resultado['reason']}")
    print(f"Should operate: {resultado['should_operate']}")
    
    # Verificar que não há sinal ativo
    assert resultado['should_operate'] == False, "Erro: LLWL não deveria gerar sinal"
    assert resultado.get('pattern_detected') == False, "Erro: padrão L-L-L não deveria estar detectado"
    
    print("✅ TESTE 5 PASSOU: LLWL corretamente não gera sinal")

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO EXECUTOR_MOMENTUM_MEDIO_V1")
    print("=" * 60)
    
    try:
        test_scenario_1_llwl_analysis()
        test_scenario_2_lll_pattern_detection()
        test_scenario_3_signal_persistence()
        test_scenario_4_first_operation_after_pattern()
        test_scenario_5_llwl_no_false_positive()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("✅ As correções estão funcionando corretamente.")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        return False
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)