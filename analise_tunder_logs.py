#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise Detalhada dos Logs do Tunder Bot
========================================

Este script analisa os dados enviados para a tabela 'tunder_bot_logs' 
e verifica se estão sendo enviados corretamente.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

def analisar_tunder_logs():
    """Análise completa dos logs do Tunder Bot"""
    
    print("🔍 ANÁLISE DETALHADA - TUNDER BOT LOGS")
    print("=" * 60)
    
    try:
        # Conectar ao Supabase
        supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        print("✅ Conectado ao Supabase")
        
        # 1. ANÁLISE GERAL DA TABELA
        print("\n📊 1. ANÁLISE GERAL DA TABELA")
        print("-" * 40)
        
        # Buscar todos os registros recentes (últimas 24 horas)
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        response = supabase.table('tunder_bot_logs') \
            .select('*') \
            .gte('created_at', yesterday) \
            .order('created_at', desc=True) \
            .execute()
        
        total_records = len(response.data)
        print(f"📈 Total de registros (últimas 24h): {total_records}")
        
        if total_records == 0:
            print("⚠️ Nenhum registro encontrado nas últimas 24 horas")
            return
        
        # 2. ANÁLISE DOS CAMPOS
        print("\n📋 2. ESTRUTURA DOS DADOS")
        print("-" * 30)
        
        sample_record = response.data[0]
        print("🔍 Campos presentes no registro mais recente:")
        
        for field, value in sample_record.items():
            field_type = type(value).__name__
            print(f"   • {field}: {field_type} = {value}")
        
        # 3. ANÁLISE DE RESULTADOS
        print("\n📈 3. ANÁLISE DE RESULTADOS")
        print("-" * 35)
        
        wins = [r for r in response.data if r.get('operation_result') == 'WIN']
        losses = [r for r in response.data if r.get('operation_result') == 'LOSS']
        
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_records * 100) if total_records > 0 else 0
        
        print(f"🎯 Operações WIN: {win_count}")
        print(f"❌ Operações LOSS: {loss_count}")
        print(f"📊 Taxa de Sucesso: {win_rate:.1f}%")
        
        # 4. ANÁLISE DE LUCROS
        print("\n💰 4. ANÁLISE DE LUCROS")
        print("-" * 25)
        
        total_profit = 0
        for record in response.data:
            stake = record.get('stake_value', 0)
            profit_pct = record.get('profit_percentage', 0)
            profit = (stake * profit_pct / 100)
            total_profit += profit
        
        print(f"💵 Lucro Total: ${total_profit:.2f}")
        print(f"📊 Lucro Médio por Operação: ${total_profit/total_records:.2f}")
        
        # 5. ANÁLISE TEMPORAL
        print("\n⏰ 5. ANÁLISE TEMPORAL")
        print("-" * 25)
        
        if total_records >= 2:
            first_record = response.data[-1]  # Mais antigo
            last_record = response.data[0]    # Mais recente
            
            first_time = datetime.fromisoformat(first_record['created_at'].replace('Z', '+00:00'))
            last_time = datetime.fromisoformat(last_record['created_at'].replace('Z', '+00:00'))
            
            time_diff = last_time - first_time
            
            print(f"🕐 Primeiro registro: {first_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🕐 Último registro: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️ Período analisado: {time_diff}")
            
            if time_diff.total_seconds() > 0:
                ops_per_hour = total_records / (time_diff.total_seconds() / 3600)
                print(f"📊 Operações por hora: {ops_per_hour:.1f}")
        
        # 6. ÚLTIMOS REGISTROS DETALHADOS
        print("\n📋 6. ÚLTIMOS 5 REGISTROS DETALHADOS")
        print("-" * 45)
        
        for i, record in enumerate(response.data[:5], 1):
            created_at = record.get('created_at', 'N/A')
            operation_result = record.get('operation_result', 'N/A')
            profit_percentage = record.get('profit_percentage', 0)
            stake_value = record.get('stake_value', 0)
            account_name = record.get('account_name', 'N/A')
            bot_name = record.get('bot_name', 'N/A')
            
            # Calcular lucro real
            profit_real = (stake_value * profit_percentage / 100)
            
            print(f"\n   📊 REGISTRO #{i} (ID: {record.get('id', 'N/A')})")
            print(f"      🕐 Data/Hora: {created_at}")
            print(f"      🎯 Resultado: {operation_result}")
            print(f"      💰 Stake: ${stake_value}")
            print(f"      📈 Profit %: {profit_percentage:.2f}%")
            print(f"      💵 Profit $: ${profit_real:.2f}")
            print(f"      👤 Conta: {account_name}")
            print(f"      🤖 Bot: {bot_name}")
        
        # 7. VERIFICAÇÃO DE INTEGRIDADE
        print("\n🔍 7. VERIFICAÇÃO DE INTEGRIDADE")
        print("-" * 40)
        
        # Verificar campos obrigatórios
        missing_fields = []
        for record in response.data[:10]:  # Verificar os 10 mais recentes
            required_fields = ['operation_result', 'profit_percentage', 'stake_value', 'created_at']
            for field in required_fields:
                if field not in record or record[field] is None:
                    missing_fields.append(f"ID {record.get('id')}: {field}")
        
        if missing_fields:
            print("⚠️ Campos obrigatórios ausentes:")
            for missing in missing_fields:
                print(f"   • {missing}")
        else:
            print("✅ Todos os campos obrigatórios estão presentes")
        
        # Verificar valores válidos
        invalid_values = []
        for record in response.data[:10]:
            if record.get('operation_result') not in ['WIN', 'LOSS']:
                invalid_values.append(f"ID {record.get('id')}: operation_result inválido")
            
            if not isinstance(record.get('profit_percentage'), (int, float)):
                invalid_values.append(f"ID {record.get('id')}: profit_percentage não numérico")
            
            if not isinstance(record.get('stake_value'), (int, float)):
                invalid_values.append(f"ID {record.get('id')}: stake_value não numérico")
        
        if invalid_values:
            print("⚠️ Valores inválidos encontrados:")
            for invalid in invalid_values:
                print(f"   • {invalid}")
        else:
            print("✅ Todos os valores estão válidos")
        
        print("\n" + "=" * 60)
        print("✅ ANÁLISE CONCLUÍDA!")
        print(f"📊 Resumo: {total_records} registros analisados")
        print(f"🎯 Taxa de Sucesso: {win_rate:.1f}%")
        print(f"💰 Lucro Total: ${total_profit:.2f}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ ERRO durante a análise: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")

if __name__ == "__main__":
    analisar_tunder_logs()