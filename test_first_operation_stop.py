#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se o bot para de enviar sinais após a primeira operação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar as funções necessárias
from radar_tunder_new import (
    analisar_estrategia_quantum_plus,
    BotState,
    PERSISTENCIA_OPERACOES,
    should_reset_to_analyzing,
    check_new_operations
)

def test_persistencia_operacoes():
    """Testa se PERSISTENCIA_OPERACOES está configurado para 1"""
    print(f"\n🧪 Testando configuração PERSISTENCIA_OPERACOES...")
    print(f"📊 Valor atual: {PERSISTENCIA_OPERACOES}")
    
    if PERSISTENCIA_OPERACOES == 1:
        print("✅ SUCESSO: PERSISTENCIA_OPERACOES configurado para 1 operação")
        return True
    else:
        print(f"❌ FALHA: PERSISTENCIA_OPERACOES deveria ser 1, mas é {PERSISTENCIA_OPERACOES}")
        return False

def test_quantum_plus_strategy():
    """Testa se a estratégia Quantum+ ainda funciona corretamente"""
    print(f"\n🧪 Testando estratégia Quantum+...")
    
    # Teste com gatilho LLLW válido
    historico_teste = (
        ['WIN', 'LOSS', 'LOSS', 'LOSS'] +  # Sequência LLLW
        (['WIN'] * 6 + ['LOSS'] * 4) +      # 6 wins em 10 ops
        (['WIN'] * 11 + ['LOSS'] * 9) +     # 11 wins em 20 ops
        (['WIN'] * 5 + ['LOSS'] * 1)        # Dados extras
    )
    
    resultado = analisar_estrategia_quantum_plus(historico_teste)
    
    if resultado['should_operate']:
        print("✅ SUCESSO: Estratégia Quantum+ detecta padrão corretamente")
        print(f"   Razão: {resultado['reason']}")
        print(f"   Confiança: {resultado['confidence']}%")
        return True
    else:
        print("❌ FALHA: Estratégia Quantum+ não detectou padrão válido")
        print(f"   Razão: {resultado['reason']}")
        return False

def test_reset_logic():
    """Testa a lógica de reset após primeira operação"""
    print(f"\n🧪 Testando lógica de reset...")
    
    # Simular estado inicial
    global monitoring_operations_count
    from radar_tunder_new import monitoring_operations_count
    
    # Simular que temos 0 operações
    print(f"📊 Operações antes: {monitoring_operations_count}")
    
    # Verificar se deve resetar com 0 operações
    should_reset_0 = should_reset_to_analyzing()
    print(f"📊 Deve resetar com 0 ops: {should_reset_0}")
    
    # Simular 1 operação (modificar diretamente para teste)
    import radar_tunder_new
    radar_tunder_new.monitoring_operations_count = 1
    
    # Verificar se deve resetar com 1 operação
    should_reset_1 = should_reset_to_analyzing()
    print(f"📊 Deve resetar com 1 op: {should_reset_1}")
    
    # Restaurar estado
    radar_tunder_new.monitoring_operations_count = 0
    
    if not should_reset_0 and should_reset_1:
        print("✅ SUCESSO: Lógica de reset funciona corretamente")
        print("   - Não reseta com 0 operações")
        print("   - Reseta com 1 operação")
        return True
    else:
        print("❌ FALHA: Lógica de reset não está funcionando")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES - PARAR APÓS PRIMEIRA OPERAÇÃO")
    print("=" * 60)
    
    resultados = []
    
    # Teste 1: Configuração PERSISTENCIA_OPERACOES
    resultados.append(test_persistencia_operacoes())
    
    # Teste 2: Estratégia Quantum+ ainda funciona
    resultados.append(test_quantum_plus_strategy())
    
    # Teste 3: Lógica de reset
    resultados.append(test_reset_logic())
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL DOS TESTES")
    print("=" * 60)
    
    sucessos = sum(resultados)
    total = len(resultados)
    
    print(f"✅ Testes passaram: {sucessos}/{total}")
    
    if sucessos == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O bot agora para de enviar sinais após a primeira operação")
        return True
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("⚠️  Verificar implementação")
        return False

if __name__ == "__main__":
    main()