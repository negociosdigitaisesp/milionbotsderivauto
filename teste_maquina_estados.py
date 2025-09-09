#!/usr/bin/env python3
"""
Teste da Máquina de Estados do Radar Analisis Scalping Bot
Demonstra o funcionamento dos estados ANALYZING e MONITORING
"""

import sys
import time
from datetime import datetime

# Simular importações do bot principal
class BotState:
    ANALYZING = "ANALYZING"
    MONITORING = "MONITORING"

# Variáveis globais simuladas
bot_current_state = BotState.ANALYZING
monitoring_operations_count = 0
last_operation_id_when_signal = None
monitoring_start_time = None
active_signal_data = None
PERSISTENCIA_OPERACOES = 2
PERSISTENCIA_TIMEOUT = 300

def reset_bot_state():
    """Reseta o bot para o estado ANALYZING"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, monitoring_start_time, active_signal_data
    
    print("[STATE] 🔄 Reiniciando estado a ANALYZING")
    bot_current_state = BotState.ANALYZING
    monitoring_operations_count = 0
    last_operation_id_when_signal = None
    monitoring_start_time = None
    active_signal_data = None

def activate_monitoring_state(signal_data: dict, latest_operation_id: str):
    """Ativa o estado MONITORING após encontrar um padrão"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, monitoring_start_time, active_signal_data
    
    print(f"[STATE] ⚡ Activando estado MONITORING - Señal: {signal_data['strategy']}")
    bot_current_state = BotState.MONITORING
    monitoring_operations_count = 0
    last_operation_id_when_signal = latest_operation_id
    monitoring_start_time = time.time()
    active_signal_data = signal_data.copy()

def check_new_operations(current_operation_id: str) -> bool:
    """Verifica se houve novas operações desde o sinal"""
    global monitoring_operations_count, last_operation_id_when_signal
    
    if last_operation_id_when_signal is None:
        return False
        
    # Se o ID atual é diferente do armazenado, houve nova operação
    if current_operation_id != last_operation_id_when_signal:
        monitoring_operations_count += 1
        last_operation_id_when_signal = current_operation_id
        print(f"[STATE] 📈 Nueva operación detectada. Contador: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        return True
    
    return False

def should_reset_to_analyzing() -> bool:
    """Verifica se deve resetar para estado ANALYZING"""
    global monitoring_operations_count, monitoring_start_time
    
    # Verificar se atingiu o limite de operações
    if monitoring_operations_count >= PERSISTENCIA_OPERACOES:
        print(f"[STATE] ✅ Límite de operaciones alcanzado: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        return True
    
    # Verificar timeout (simulado com 10 segundos para teste)
    if monitoring_start_time and (time.time() - monitoring_start_time) > 10:
        print(f"[STATE] ⏰ Timeout alcanzado: 10s (simulado)")
        return True
    
    return False

def simular_ciclo_analyzing():
    """Simula um ciclo no estado ANALYZING"""
    print("\n🔍 [ANALYZING] Buscando patrones en el mercado...")
    
    # Simular análise (70% chance de não encontrar padrão)
    import random
    encontrou_padrao = random.random() > 0.7
    
    if encontrou_padrao:
        # Padrão encontrado!
        signal_data = {
            'strategy': 'PRECISION_SURGE',
            'confidence': 93.5,
            'reason': 'Patron Encontrado, Activar Bot Ahora! - PRECISION_SURGE (93.5%)'
        }
        
        print(f"🎯 PATRÓN ENCONTRADO: {signal_data['reason']}")
        activate_monitoring_state(signal_data, f"op_{int(time.time())}")
        return True
    else:
        print("⏳ Gatillo no cumplido: esperando patrón adecuado")
        return False

def simular_ciclo_monitoring():
    """Simula um ciclo no estado MONITORING"""
    remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count
    print(f"\n👁️ [MONITORING] Estrategia {active_signal_data['strategy']} activa - esperando {remaining_ops} operaciones")
    
    # Simular nova operação (50% chance)
    import random
    nova_operacao = random.random() > 0.5
    
    if nova_operacao:
        new_op_id = f"op_{int(time.time())}_{random.randint(1000, 9999)}"
        check_new_operations(new_op_id)
    else:
        print("[STATE] 📊 Ninguna nueva operación detectada")
    
    # Verificar se deve resetar
    if should_reset_to_analyzing():
        print(f"✅ Monitoreo finalizado - {monitoring_operations_count} operaciones completadas")
        reset_bot_state()
        return True
    
    return False

def executar_teste_completo():
    """Executa um teste completo da máquina de estados"""
    print("🚀 TESTE DA MÁQUINA DE ESTADOS")
    print("=" * 50)
    print(f"📊 Configuración: {PERSISTENCIA_OPERACOES} operaciones para reset")
    print(f"⏰ Timeout simulado: 10 segundos")
    print("\nPressione Ctrl+C para parar\n")
    
    ciclo = 0
    
    try:
        while True:
            ciclo += 1
            print(f"\n--- CICLO {ciclo} ---")
            print(f"Estado atual: {bot_current_state}")
            
            if bot_current_state == BotState.ANALYZING:
                simular_ciclo_analyzing()
            elif bot_current_state == BotState.MONITORING:
                simular_ciclo_monitoring()
            
            # Aguardar próximo ciclo
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Prueba interrumpida por el usuario")
        print(f"📊 Estado final: {bot_current_state}")
        if bot_current_state == BotState.MONITORING:
            print(f"⚡ Operaciones monitoreadas: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")

def demonstrar_fluxo_estados():
    """Demonstra o fluxo completo dos estados"""
    print("📋 DEMONSTRAÇÃO DO FLUXO DE ESTADOS")
    print("=" * 40)
    
    # Estado inicial
    print(f"\n1️⃣ Estado inicial: {bot_current_state}")
    
    # Simular encontrar padrão
    print("\n2️⃣ Simulando patrón encontrado...")
    signal_data = {
        'strategy': 'PRECISION_SURGE',
        'confidence': 93.5,
        'reason': 'Patron Encontrado, Activar Bot Ahora! - PRECISION_SURGE (93.5%)'
    }
    activate_monitoring_state(signal_data, "op_12345")
    print(f"   Estado atual: {bot_current_state}")
    
    # Simular operações
    print("\n3️⃣ Simulando operaciones subsecuentes...")
    for i in range(3):
        print(f"\n   Operación {i+1}:")
        new_op_id = f"op_1234{6+i}"
        if check_new_operations(new_op_id):
            if should_reset_to_analyzing():
                reset_bot_state()
                break
    
    print(f"\n4️⃣ Estado final: {bot_current_state}")
    print("\n✅ Demostración concluida!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demonstrar_fluxo_estados()
    else:
        executar_teste_completo()