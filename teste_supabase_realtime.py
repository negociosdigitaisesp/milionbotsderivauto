#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se as atualizações em tempo real estão sendo enviadas para o Supabase
"""

import radar_analisis_scalping_bot as bot_module
import time
from datetime import datetime

def simular_padrao_encontrado():
    """Simula um padrão encontrado e testa o envio para Supabase"""
    print("\n=== TESTE SUPABASE REAL-TIME ===")
    print(f"Estado inicial: {bot_module.bot_current_state}")
    
    # Inicializar Supabase
    supabase = bot_module.inicializar_supabase()
    if not supabase:
        print("❌ Erro: Não foi possível conectar ao Supabase")
        return
    
    print("✅ Conexão com Supabase estabelecida")
    
    # Resetar estado para garantir início limpo
    bot_module.reset_bot_state()
    
    # Simular dados de operações para análise
    operacoes_simuladas = [
        {'id': '14007', 'resultado': 'WIN'},
        {'id': '14008', 'resultado': 'WIN'},
        {'id': '14009', 'resultado': 'WIN'},
        {'id': '14010', 'resultado': 'WIN'},
        {'id': '14011', 'resultado': 'WIN'}
    ]
    
    print("\n1. Executando ciclo de análise completo...")
    
    # Executar ciclo de análise que pode encontrar padrão
    resultado_ciclo = bot_module.executar_ciclo_analise_simplificado(supabase)
    
    print(f"Resultado do ciclo: {resultado_ciclo}")
    
    if resultado_ciclo['status'] == 'COMPLETED' and resultado_ciclo['resultado'].get('should_operate'):
        print("\n✅ PADRÃO ENCONTRADO! Bot ativado")
        print(f"Estado atual: {bot_module.bot_current_state}")
        
        # Simular operações subsequentes
        print("\n2. Simulando operações após sinal...")
        
        # Primeira operação
        print("\n   - Simulando operação 14012...")
        resultado_1 = bot_module.executar_ciclo_analise_simplificado(supabase)
        print(f"   Resultado: {resultado_1['resultado']['reason']}")
        
        time.sleep(1)
        
        # Segunda operação
        print("\n   - Simulando operação 14013...")
        resultado_2 = bot_module.executar_ciclo_analise_simplificado(supabase)
        print(f"   Resultado: {resultado_2['resultado']['reason']}")
        
        print(f"\n✅ TESTE CONCLUÍDO")
        print(f"Estado final: {bot_module.bot_current_state}")
        print("Verificar tabela 'radar_de_apalancamiento_signals' no Supabase para as atualizações")
        
    else:
        print("\n⚠️ Padrão não encontrado neste teste")
        print("Isso é normal - o padrão PRECISION_SURGE requer condições específicas")

if __name__ == "__main__":
    simular_padrao_encontrado()