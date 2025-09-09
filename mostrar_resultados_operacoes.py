#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para mostrar resultados das últimas operações
Exibe contagem de wins e losses das últimas 20 e 10 operações
"""

import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def inicializar_supabase():
    """Inicializa conexão com Supabase"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Credenciais do Supabase não encontradas no arquivo .env")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conexão com Supabase estabelecida com sucesso")
        return supabase
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        return None

def buscar_ultimas_operacoes(supabase, limite=20):
    """Busca as últimas operações do Supabase"""
    try:
        print(f"🔍 Buscando últimas {limite} operações...")
        
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('profit_percentage, created_at, operation_result') \
            .order('created_at', desc=True) \
            .limit(limite) \
            .execute()
        
        if not response.data:
            print("⚠️ Nenhuma operação encontrada")
            return []
        
        operacoes = []
        for i, op in enumerate(response.data, 1):
            profit_percentage = op.get('profit_percentage', 0)
            created_at = op.get('created_at', 'N/A')
            operation_result = op.get('operation_result', 'N/A')
            
            # Determinar resultado baseado no profit_percentage
            if profit_percentage > 0:
                resultado = 'WIN'
            elif profit_percentage < 0:
                resultado = 'LOSS'
            else:
                resultado = 'EMPATE'
            
            operacoes.append({
                'numero': i,
                'resultado': resultado,
                'profit_percentage': profit_percentage,
                'created_at': created_at,
                'operation_result': operation_result
            })
        
        return operacoes
        
    except Exception as e:
        print(f"❌ Erro ao buscar operações: {e}")
        return []

def calcular_estatisticas(operacoes):
    """Calcula estatísticas das operações"""
    if not operacoes:
        return {'total': 0, 'wins': 0, 'losses': 0, 'empates': 0, 'win_rate': 0}
    
    total = len(operacoes)
    wins = sum(1 for op in operacoes if op['resultado'] == 'WIN')
    losses = sum(1 for op in operacoes if op['resultado'] == 'LOSS')
    empates = sum(1 for op in operacoes if op['resultado'] == 'EMPATE')
    win_rate = (wins / total * 100) if total > 0 else 0
    
    return {
        'total': total,
        'wins': wins,
        'losses': losses,
        'empates': empates,
        'win_rate': win_rate
    }

def exibir_resultados(operacoes, titulo):
    """Exibe os resultados das operações"""
    print(f"\n{'='*60}")
    print(f"📊 {titulo}")
    print(f"{'='*60}")
    
    if not operacoes:
        print("❌ Nenhuma operação encontrada")
        return
    
    # Calcular estatísticas
    stats = calcular_estatisticas(operacoes)
    
    # Exibir resumo
    print(f"\n📈 RESUMO:")
    print(f"   Total de operações: {stats['total']}")
    print(f"   🟢 WINs: {stats['wins']}")
    print(f"   🔴 LOSSes: {stats['losses']}")
    if stats['empates'] > 0:
        print(f"   ⚪ Empates: {stats['empates']}")
    print(f"   📊 Win Rate: {stats['win_rate']:.1f}%")
    
    # Exibir operações detalhadas
    print(f"\n📋 OPERAÇÕES DETALHADAS:")
    print(f"{'#':<3} {'Resultado':<8} {'Profit %':<10} {'Data/Hora':<20}")
    print(f"{'-'*50}")
    
    for op in operacoes:
        emoji = '🟢' if op['resultado'] == 'WIN' else '🔴' if op['resultado'] == 'LOSS' else '⚪'
        data_formatada = op['created_at'][:19] if op['created_at'] != 'N/A' else 'N/A'
        
        print(f"{op['numero']:<3} {emoji} {op['resultado']:<6} {op['profit_percentage']:>8.2f}% {data_formatada:<20}")
    
    # Sequência de resultados
    sequencia = ' '.join([op['resultado'][0] for op in operacoes])  # W, L, E
    print(f"\n🔄 Sequência: {sequencia}")

def main():
    """Função principal"""
    print("🤖 ANÁLISE DE RESULTADOS DAS OPERAÇÕES")
    print("=" * 50)
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        return
    
    try:
        # Buscar últimas 20 operações
        operacoes_20 = buscar_ultimas_operacoes(supabase, 20)
        exibir_resultados(operacoes_20, "ÚLTIMAS 20 OPERAÇÕES")
        
        # Buscar últimas 10 operações (subset das 20)
        operacoes_10 = operacoes_20[:10] if len(operacoes_20) >= 10 else operacoes_20
        exibir_resultados(operacoes_10, "ÚLTIMAS 10 OPERAÇÕES")
        
        # Comparação
        if operacoes_20 and operacoes_10:
            stats_20 = calcular_estatisticas(operacoes_20)
            stats_10 = calcular_estatisticas(operacoes_10)
            
            print(f"\n{'='*60}")
            print(f"📊 COMPARAÇÃO")
            print(f"{'='*60}")
            print(f"Últimas 20: {stats_20['wins']}W / {stats_20['losses']}L ({stats_20['win_rate']:.1f}% WR)")
            print(f"Últimas 10: {stats_10['wins']}W / {stats_10['losses']}L ({stats_10['win_rate']:.1f}% WR)")
            
            # Tendência
            if stats_10['win_rate'] > stats_20['win_rate']:
                print(f"📈 Tendência: MELHORANDO (+{stats_10['win_rate'] - stats_20['win_rate']:.1f}%)")
            elif stats_10['win_rate'] < stats_20['win_rate']:
                print(f"📉 Tendência: PIORANDO ({stats_10['win_rate'] - stats_20['win_rate']:.1f}%)")
            else:
                print(f"➡️ Tendência: ESTÁVEL")
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()