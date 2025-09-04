#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar a causa do shutdown dos bots
"""

import os
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Configuração do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

def main():
    print("🔍 VERIFICADOR DE CAUSA DO SHUTDOWN")
    print("=" * 50)
    
    try:
        # Conectar ao Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexão com Supabase estabelecida")
        
        # Buscar configurações dos bots
        print("\n🔍 Verificando configurações dos bots...")
        response = supabase.table('bot_configurations').select('*').execute()
        
        if not response.data:
            print("❌ Nenhum bot encontrado")
            return
            
        print(f"📋 Encontrados {len(response.data)} bots\n")
        
        for bot in response.data:
            print(f"🤖 Bot: {bot['bot_name']} (ID: {bot['id']})")
            print(f"   📊 Status: {bot['status']}")
            print(f"   🔄 Is Active: {bot['is_active']}")
            print(f"   💰 Stake: ${bot['param_stake_inicial']}")
            print(f"   📈 Take Profit: {bot['param_take_profit']}%")
            
            # Verificar param_overrides
            if bot.get('param_overrides'):
                print(f"   🔧 Overrides: {bot['param_overrides']}")
            else:
                print("   🔧 Overrides: Nenhum")
                
            # Verificar timestamps
            if bot.get('updated_at'):
                print(f"   🕒 Última atualização: {bot['updated_at']}")
            if bot.get('last_heartbeat'):
                print(f"   💓 Último heartbeat: {bot['last_heartbeat']}")
            if bot.get('process_id'):
                print(f"   🆔 Process ID: {bot['process_id']}")
                
            print()
            
        # Verificar logs recentes de operações
        print("\n📋 Verificando logs recentes...")
        logs_response = supabase.table('bot_operation_logs').select('*').order('created_at', desc=True).limit(10).execute()
        
        if logs_response.data:
            print(f"📊 Últimas {len(logs_response.data)} operações:")
            for log in logs_response.data:
                print(f"   • {log['created_at']}: {log['bot_id']} - {log.get('operation_type', 'N/A')} - Stake: ${log.get('stake_amount', 0)} - Profit: {log.get('profit_percentage', 0)}%")
        else:
            print("❌ Nenhum log encontrado")
            
        # Análise da causa do shutdown
        print("\n🔍 ANÁLISE DA CAUSA DO SHUTDOWN:")
        print("=" * 40)
        
        active_bots = [bot for bot in response.data if bot['is_active']]
        running_bots = [bot for bot in response.data if bot['status'] == 'running']
        
        print(f"📊 Bots ativos (is_active=True): {len(active_bots)}")
        print(f"📊 Bots rodando (status=running): {len(running_bots)}")
        
        if len(active_bots) == 0:
            print("⚠️  CAUSA PROVÁVEL: Todos os bots estão com is_active=False")
            print("   💡 Solução: Ativar os bots usando activate_bots_now.py")
        elif len(running_bots) == 0:
            print("⚠️  CAUSA PROVÁVEL: Todos os bots estão com status=stopped")
            print("   💡 Solução: Os bots estão sendo finalizados pelo orquestrador")
        else:
            print("✅ Configuração parece normal")
            print("   🔍 Verificar logs do orquestrador para mais detalhes")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()