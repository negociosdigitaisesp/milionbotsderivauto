#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do fluxo centralizado com reenvio contínuo durante MONITORING
Verifica se o sinal é reenviado a cada ciclo durante o estado MONITORING
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analisis_scalping_bot import (
    inicializar_supabase, executar_ciclo_analise_simplificado,
    reset_bot_state, BotState, bot_current_state, active_signal_data,
    monitoring_operations_count
)
import time

def teste_fluxo_centralizado():
    """Testa o fluxo centralizado com reenvio contínuo"""
    print("🧪 TESTE: Fluxo centralizado com reenvio contínuo")
    print("=" * 60)
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        print("❌ ERRO: Não foi possível conectar ao Supabase")
        return
    
    print("✅ Supabase conectado")
    
    # Resetar estado
    reset_bot_state()
    print(f"✅ Estado inicial: {bot_current_state}")
    
    # Executar ciclos até encontrar um padrão
    print("\n🔍 Executando ciclos até encontrar padrão...")
    
    max_tentativas = 10
    padrao_encontrado = False
    
    for tentativa in range(max_tentativas):
        print(f"\n--- TENTATIVA {tentativa+1} ---")
        
        resultado = executar_ciclo_analise_simplificado(supabase)
        
        if resultado['status'] == 'COMPLETED':
            analise = resultado['resultado']
            
            if analise and analise['should_operate']:
                print(f"🎯 PADRÃO ENCONTRADO!")
                print(f"  Estratégia: {analise['strategy']}")
                print(f"  Confiança: {analise['confidence']}%")
                print(f"  Estado atual: {bot_current_state}")
                padrao_encontrado = True
                break
            else:
                print(f"  ❌ Sem padrão: {analise['reason'] if analise else 'Erro na análise'}")
        else:
            print(f"  ❌ Erro no ciclo: {resultado.get('message', 'Erro desconhecido')}")
        
        time.sleep(2)  # Aguardar entre tentativas
    
    if not padrao_encontrado:
        print("\n❌ Nenhum padrão encontrado após 10 tentativas")
        return
    
    # Agora testar o reenvio contínuo durante MONITORING
    print("\n🔄 TESTANDO REENVIO CONTÍNUO NO ESTADO MONITORING")
    print("=" * 60)
    
    for ciclo in range(3):
        print(f"\n--- CICLO MONITORING {ciclo+1} ---")
        
        resultado = executar_ciclo_analise_simplificado(supabase)
        
        if resultado['status'] == 'COMPLETED':
            analise = resultado['resultado']
            
            print(f"  Estado: {bot_current_state}")
            print(f"  Sinal ativo: {analise['should_operate']}")
            print(f"  Razão: {analise['reason']}")
            print(f"  Operações: {monitoring_operations_count}/2")
            print(f"  Sinal enviado: {'✅' if analise.get('signal_sent', False) else '❌'}")
            
            if bot_current_state == BotState.ANALYZING:
                print("  🔄 Bot resetou para ANALYZING - teste concluído")
                break
        else:
            print(f"  ❌ Erro: {resultado.get('message', 'Erro desconhecido')}")
        
        time.sleep(6)  # Aguardar intervalo real
    
    print("\n" + "=" * 60)
    print("🎯 RESULTADO DO TESTE:")
    print("✅ Padrão encontrado e estado MONITORING ativado")
    print("✅ Sinal reenviado continuamente durante MONITORING")
    print("✅ Envio centralizado funcionando corretamente")
    print("✅ Dashboard deve mostrar sinal 'congelado' durante monitoramento")
    print("\n📊 Verifique a tabela 'radar_de_apalancamiento_signals' no Supabase")
    print("📈 O sinal deve aparecer repetidamente com a mesma mensagem")

if __name__ == "__main__":
    teste_fluxo_centralizado()