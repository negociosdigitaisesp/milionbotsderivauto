#!/usr/bin/env python3
"""
Script de Teste para Estatísticas dos Bots
Testa a consulta e exibição das estatísticas dos bots de trading
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase (usando as mesmas variáveis do bot_trading_system.py)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def conectar_supabase():
    """Conecta ao Supabase e retorna o cliente"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexão com Supabase estabelecida!")
        return supabase
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        return None

def buscar_operacoes_recentes(supabase, limite=10):
    """Busca as operações mais recentes dos bots"""
    try:
        print(f"\n🔍 Buscando {limite} operações mais recentes...")
        
        response = supabase.table('operacoes').select('*').order('created_at', desc=True).limit(limite).execute()
        
        if response.data:
            print(f"✅ {len(response.data)} operações encontradas!")
            return response.data
        else:
            print("📭 Nenhuma operação encontrada")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao buscar operações: {e}")
        return []

def calcular_estatisticas_por_bot(operacoes):
    """Calcula estatísticas agrupadas por bot"""
    print("\n📊 Calculando estatísticas por bot...")
    
    stats_por_bot = {}
    
    for operacao in operacoes:
        nome_bot = operacao.get('nome_bot', 'Desconhecido')
        lucro = float(operacao.get('lucro', 0))
        
        if nome_bot not in stats_por_bot:
            stats_por_bot[nome_bot] = {
                'total_operacoes': 0,
                'lucro_total': 0,
                'vitorias': 0,
                'derrotas': 0,
                'maior_lucro': 0,
                'maior_perda': 0
            }
        
        stats = stats_por_bot[nome_bot]
        stats['total_operacoes'] += 1
        stats['lucro_total'] += lucro
        
        if lucro > 0:
            stats['vitorias'] += 1
            if lucro > stats['maior_lucro']:
                stats['maior_lucro'] = lucro
        else:
            stats['derrotas'] += 1
            if lucro < stats['maior_perda']:
                stats['maior_perda'] = lucro
    
    # Calcular percentuais de vitória
    for nome_bot, stats in stats_por_bot.items():
        if stats['total_operacoes'] > 0:
            stats['taxa_vitoria'] = (stats['vitorias'] / stats['total_operacoes']) * 100
        else:
            stats['taxa_vitoria'] = 0
    
    return stats_por_bot

def exibir_estatisticas(stats_por_bot):
    """Exibe as estatísticas de forma organizada"""
    print("\n" + "="*80)
    print("📈 ESTATÍSTICAS DOS BOTS DE TRADING")
    print("="*80)
    
    # Ordenar bots por lucro total (decrescente)
    bots_ordenados = sorted(stats_por_bot.items(), key=lambda x: x[1]['lucro_total'], reverse=True)
    
    for i, (nome_bot, stats) in enumerate(bots_ordenados, 1):
        print(f"\n🤖 {i}. {nome_bot}")
        print("-" * 50)
        print(f"   💰 Lucro Total: ${stats['lucro_total']:.2f}")
        print(f"   📊 Total de Operações: {stats['total_operacoes']}")
        print(f"   ✅ Vitórias: {stats['vitorias']}")
        print(f"   ❌ Derrotas: {stats['derrotas']}")
        print(f"   📈 Taxa de Vitória: {stats['taxa_vitoria']:.1f}%")
        print(f"   🏆 Maior Lucro: ${stats['maior_lucro']:.2f}")
        print(f"   📉 Maior Perda: ${stats['maior_perda']:.2f}")

def buscar_estatisticas_view(supabase):
    """Tenta buscar dados da view estatisticas_bots (se existir)"""
    try:
        print("\n🔍 Tentando buscar da view 'estatisticas_bots'...")
        
        response = supabase.table('estatisticas_bots').select('*').order('lucro_total', desc=True).execute()
        
        if response.data:
            print(f"✅ View encontrada! {len(response.data)} registros")
            print("\n📊 DADOS DA VIEW ESTATISTICAS_BOTS:")
            print("-" * 60)
            
            for bot in response.data:
                print(f"🤖 {bot.get('nome_bot', 'N/A')}")
                print(f"   💰 Lucro Total: ${bot.get('lucro_total', 0):.2f}")
                print(f"   📊 Total Operações: {bot.get('total_operacoes', 0)}")
                print(f"   📈 Taxa Vitória: {bot.get('taxa_vitoria', 0):.1f}%")
                print()
            
            return response.data
        else:
            print("📭 View 'estatisticas_bots' não encontrada ou vazia")
            return []
            
    except Exception as e:
        print(f"⚠️ View 'estatisticas_bots' não existe ou erro: {e}")
        return []

def main():
    """Função principal do teste"""
    print("🚀 INICIANDO TESTE DE ESTATÍSTICAS DOS BOTS")
    print("=" * 60)
    
    # Conectar ao Supabase
    supabase = conectar_supabase()
    if not supabase:
        return
    
    # Tentar buscar da view primeiro
    dados_view = buscar_estatisticas_view(supabase)
    
    # Buscar operações recentes
    operacoes = buscar_operacoes_recentes(supabase, 50)
    
    if operacoes:
        # Calcular estatísticas manualmente
        stats = calcular_estatisticas_por_bot(operacoes)
        exibir_estatisticas(stats)
        
        # Mostrar algumas operações recentes
        print("\n" + "="*80)
        print("📋 ÚLTIMAS 5 OPERAÇÕES")
        print("="*80)
        
        for i, op in enumerate(operacoes[:5], 1):
            lucro = float(op.get('lucro', 0))
            status = "✅ VITÓRIA" if lucro > 0 else "❌ DERROTA"
            print(f"{i}. {op.get('nome_bot', 'N/A')} - {status} - ${lucro:.2f}")
    
    else:
        print("📭 Nenhuma operação encontrada para calcular estatísticas")
    
    print(f"\n🕒 Teste concluído em {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()