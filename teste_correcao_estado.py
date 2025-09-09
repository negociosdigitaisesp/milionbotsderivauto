#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar a correção do problema de estado do bot
Simula o cenário onde um padrão é encontrado e verifica se o reset funciona após 2 operações
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import radar_analisis_scalping_bot as bot_module
from radar_analisis_scalping_bot import (
    BotState, reset_bot_state, activate_monitoring_state, 
    check_new_operations, should_reset_to_analyzing
)

def test_estado_monitoring():
    """Testa o comportamento do estado MONITORING"""
    print("=== TESTE DE CORREÇÃO DO ESTADO MONITORING ===")
    
    # 1. Resetar estado inicial
    print("\n1. Resetando estado inicial...")
    reset_bot_state()
    print(f"   Estado atual: {bot_module.bot_current_state}")
    print(f"   Contador operações: {bot_module.monitoring_operations_count}")
    
    # 2. Simular encontro de padrão
    print("\n2. Simulando encontro de padrão...")
    signal_data = {
        'strategy': 'PRECISION_SURGE',
        'confidence': 93.5,
        'reason': 'Patrón encontrado para teste'
    }
    
    # Ativar estado MONITORING com operação ID 1000
    activate_monitoring_state(signal_data, "1000")
    print(f"   Estado atual: {bot_module.bot_current_state}")
    print(f"   Contador operações: {bot_module.monitoring_operations_count}")
    print(f"   ID operação do sinal: {bot_module.last_operation_id_when_signal}")
    print(f"   ID última verificada: {bot_module.last_checked_operation_id}")
    
    # 3. Simular primeira operação após o sinal
    print("\n3. Simulando primeira operação após sinal (ID: 1001)...")
    nova_op = check_new_operations("1001")
    print(f"   Nova operação detectada: {nova_op}")
    print(f"   Contador operações: {bot_module.monitoring_operations_count}")
    print(f"   ID última verificada: {bot_module.last_checked_operation_id}")
    print(f"   Deve resetar? {should_reset_to_analyzing()}")
    
    # 4. Simular segunda operação após o sinal
    print("\n4. Simulando segunda operação após sinal (ID: 1002)...")
    nova_op = check_new_operations("1002")
    print(f"   Nova operação detectada: {nova_op}")
    print(f"   Contador operações: {bot_module.monitoring_operations_count}")
    print(f"   ID última verificada: {bot_module.last_checked_operation_id}")
    print(f"   Deve resetar? {should_reset_to_analyzing()}")
    
    # 5. Verificar se deve resetar após 2 operações
    if should_reset_to_analyzing():
        print("\n5. ✅ CORREÇÃO FUNCIONOU! Resetando para ANALYZING...")
        reset_bot_state()
        print(f"   Estado atual: {bot_module.bot_current_state}")
        print(f"   Contador operações: {bot_module.monitoring_operations_count}")
    else:
        print("\n5. ❌ PROBLEMA AINDA EXISTE! Não resetou após 2 operações")
    
    # 6. Testar que não conta a mesma operação duas vezes
    print("\n6. Testando que não conta a mesma operação duas vezes...")
    activate_monitoring_state(signal_data, "2000")
    print(f"   Estado: {bot_module.bot_current_state}, Contador: {bot_module.monitoring_operations_count}")
    
    # Verificar mesma operação
    nova_op1 = check_new_operations("2001")
    print(f"   Primeira verificação ID 2001: {nova_op1}, Contador: {bot_module.monitoring_operations_count}")
    
    nova_op2 = check_new_operations("2001")  # Mesma operação
    print(f"   Segunda verificação ID 2001: {nova_op2}, Contador: {bot_module.monitoring_operations_count}")
    
    if bot_module.monitoring_operations_count == 1:
        print("   ✅ Correto! Não contou a mesma operação duas vezes")
    else:
        print("   ❌ Erro! Contou a mesma operação múltiplas vezes")

if __name__ == "__main__":
    test_estado_monitoring()