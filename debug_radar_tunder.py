#!/usr/bin/env python3
"""
Script para debugar o radar_analyzer_tunder.py
"""

import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
BOT_NAME = 'Tunder Bot'
TABELA_LOGS = 'tunder_bot_logs'
OPERACOES_MINIMAS = 10  # ajustado para Tunder Bot
OPERACOES_HISTORICO = 30

def main():
    try:
        # Conectar ao Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Credenciais do Supabase não encontradas")
            return
        
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Conectado ao Supabase")
        
        # Buscar operações como o radar faz
        print(f"\n🔍 Buscando últimas {OPERACOES_HISTORICO} operações do Tunder Bot...")
        
        response = supabase.table(TABELA_LOGS) \
            .select('profit_percentage, created_at') \
            .order('id', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        print(f"📊 Total de registros retornados: {len(response.data)}")
        
        if not response.data:
            print("❌ Nenhuma operação encontrada")
            return
        
        # Converter para histórico V/D
        historico = []
        timestamps = []
        
        print("\n📈 Convertendo operações:")
        for i, operacao in enumerate(response.data):
            profit_percentage = operacao.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            historico.append(resultado)
            timestamps.append(operacao.get('created_at'))
            
            if i < 10:  # Mostrar apenas os primeiros 10
                print(f"   {i+1}. Profit: {profit_percentage}% -> {resultado} ({operacao.get('created_at')})")
        
        print(f"\n🎯 Histórico completo ({len(historico)} operações): {' '.join(historico)}")
        
        # Análise de padrões
        print(f"\n🔍 ANÁLISE DE PADRÕES:")
        print(f"   • Operações encontradas: {len(historico)}")
        print(f"   • Operações mínimas necessárias: {OPERACOES_MINIMAS}")
        print(f"   • Status: {'✅ Suficiente' if len(historico) >= OPERACOES_MINIMAS else '❌ Insuficiente'}")
        
        if len(historico) >= OPERACOES_MINIMAS:
            # Análise das últimas 20 operações
            ultimas_20 = historico[:20]
            derrotas_ultimas_20 = ultimas_20.count('D')
            
            print(f"\n📊 Análise das últimas 20 operações:")
            print(f"   • Operações: {' '.join(ultimas_20)}")
            print(f"   • Derrotas: {derrotas_ultimas_20}")
            print(f"   • Filtro Mercado Instável (>2): {'❌ FALHOU' if derrotas_ultimas_20 > 2 else '✅ PASSOU'}")
            print(f"   • Filtro de Espera (>1): {'❌ FALHOU' if derrotas_ultimas_20 > 1 else '✅ PASSOU'}")
            
            # Verificar padrão V-D-V
            if len(historico) >= 3:
                padrao_vdv = historico[0] == 'V' and historico[1] == 'D' and historico[2] == 'V'
                print(f"\n🎯 Padrão V-D-V:")
                print(f"   • Últimas 3: {historico[0]}-{historico[1]}-{historico[2]}")
                print(f"   • Status: {'✅ ENCONTRADO' if padrao_vdv else '❌ NÃO ENCONTRADO'}")
                
                if padrao_vdv:
                    # Filtro 1 - 10 operações anteriores
                    if len(historico) >= 13:
                        operacoes_anteriores_10 = historico[3:13]
                        derrotas_anteriores_10 = operacoes_anteriores_10.count('D')
                        print(f"\n🔍 Filtro 1 (Condição Geral):")
                        print(f"   • 10 operações anteriores: {' '.join(operacoes_anteriores_10)}")
                        print(f"   • Derrotas: {derrotas_anteriores_10}")
                        print(f"   • Status (≤1): {'✅ PASSOU' if derrotas_anteriores_10 <= 1 else '❌ FALHOU'}")
                    
                    # Filtro 2 - 5 operações anteriores
                    if len(historico) >= 8:
                        operacoes_anteriores_5 = historico[3:8]
                        vitorias_anteriores_5 = operacoes_anteriores_5.count('V')
                        print(f"\n🔍 Filtro 2 (Condição Imediata):")
                        print(f"   • 5 operações anteriores: {' '.join(operacoes_anteriores_5)}")
                        print(f"   • Vitórias: {vitorias_anteriores_5}")
                        print(f"   • Status (≥4): {'✅ PASSOU' if vitorias_anteriores_5 >= 4 else '❌ FALHOU'}")
        
        # Verificar último sinal enviado
        print(f"\n📡 ÚLTIMO SINAL ENVIADO:")
        response_signal = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .eq('bot_name', BOT_NAME) \
            .order('id', desc=True) \
            .limit(1) \
            .execute()
        
        if response_signal.data:
            signal = response_signal.data[0]
            print(f"   • ID: {signal.get('id')}")
            print(f"   • Safe: {signal.get('is_safe_to_operate')}")
            print(f"   • Reason: {signal.get('reason')}")
            print(f"   • Created: {signal.get('created_at')}")
        else:
            print("   • Nenhum sinal encontrado")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()