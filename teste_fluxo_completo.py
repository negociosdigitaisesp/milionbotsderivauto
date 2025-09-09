#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do fluxo completo do bot com envio incondicional de status
Verifica se o bot envia atualizações a cada ciclo independente do resultado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analisis_scalping_bot import (
    inicializar_supabase, executar_ciclo_analise_simplificado,
    reset_bot_state, BotState, bot_current_state
)
import time

def teste_fluxo_completo():
    """Testa o fluxo completo do bot com envio incondicional"""
    print("🧪 TESTE: Fluxo completo com envio incondicional")
    print("=" * 50)
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        print("❌ ERRO: Não foi possível conectar ao Supabase")
        return
    
    print("✅ Supabase conectado")
    
    # Resetar estado
    reset_bot_state()
    print(f"✅ Estado resetado: {bot_current_state}")
    
    # Executar 3 ciclos de análise
    print("\n🔄 Executando 3 ciclos de análise...")
    
    for i in range(3):
        print(f"\n--- CICLO {i+1} ---")
        
        resultado = executar_ciclo_analise_simplificado(supabase)
        
        if resultado['status'] == 'COMPLETED':
            analise = resultado['resultado']
            status = "PADRÃO ENCONTRADO" if analise['should_operate'] else "SEM PADRÃO"
            signal_sent = "✅ ENVIADO" if analise.get('signal_sent', False) else "❌ FALHA"
            
            print(f"  Status: {status}")
            print(f"  Razão: {analise['reason']}")
            print(f"  Sinal: {signal_sent}")
            print(f"  Estado atual: {bot_current_state}")
        else:
            print(f"  ❌ Erro no ciclo: {resultado.get('message', 'Erro desconhecido')}")
        
        # Aguardar 6 segundos entre ciclos (simular intervalo real)
        if i < 2:  # Não aguardar após o último ciclo
            print("  ⏳ Aguardando 6 segundos...")
            time.sleep(6)
    
    print("\n" + "=" * 50)
    print("🎯 RESULTADO DO TESTE:")
    print("✅ O bot deve ter enviado 3 atualizações para o Supabase")
    print("✅ Cada ciclo deve ter resultado em um envio, independente do padrão")
    print("✅ Verifique a tabela 'radar_de_apalancamiento_signals' no Supabase")
    print("\n📊 Dashboard deve mostrar atualizações em tempo real a cada 5-6 segundos")

if __name__ == "__main__":
    teste_fluxo_completo()