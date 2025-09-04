#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar o padrão de shutdown dos bots
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
    print("🔍 ANÁLISE DO PADRÃO DE SHUTDOWN")
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
            
        # Análise da causa do shutdown
        print("\n🔍 ANÁLISE DA CAUSA DO SHUTDOWN:")
        print("=" * 40)
        
        active_bots = [bot for bot in response.data if bot['is_active']]
        running_bots = [bot for bot in response.data if bot['status'] == 'running']
        
        print(f"📊 Bots ativos (is_active=True): {len(active_bots)}")
        print(f"📊 Bots rodando (status=running): {len(running_bots)}")
        
        print("\n🔍 DIAGNÓSTICO DETALHADO:")
        print("-" * 30)
        
        if len(active_bots) > 0 and len(running_bots) == 0:
            print("⚠️  PROBLEMA IDENTIFICADO: Bots ativos mas com status 'stopped'")
            print("\n📋 POSSÍVEIS CAUSAS:")
            print("   1. 🛑 Sinal de shutdown detectado no heartbeat")
            print("   2. 🔄 Orquestrador está parando os bots automaticamente")
            print("   3. 🚫 Alguma condição de parada está sendo ativada")
            print("   4. ⚡ Erro na inicialização que força o shutdown")
            
            print("\n💡 SOLUÇÕES RECOMENDADAS:")
            print("   1. 🔍 Verificar logs do orquestrador para identificar a causa")
            print("   2. 🔧 Verificar se há alguma lógica de auto-shutdown")
            print("   3. 📊 Analisar o código do heartbeat para ver o que está causando o shutdown")
            print("   4. 🛠️  Verificar se há alguma configuração que está forçando a parada")
            
            # Verificar se há algum padrão nos timestamps
            print("\n📅 ANÁLISE DE TIMESTAMPS:")
            for bot in active_bots:
                if bot.get('updated_at') and bot.get('last_heartbeat'):
                    print(f"   🤖 {bot['bot_name']}:")
                    print(f"      📝 Última atualização: {bot['updated_at']}")
                    print(f"      💓 Último heartbeat: {bot['last_heartbeat']}")
                    
                    # Calcular diferença de tempo
                    try:
                        from datetime import datetime
                        updated = datetime.fromisoformat(bot['updated_at'].replace('Z', '+00:00'))
                        heartbeat = datetime.fromisoformat(bot['last_heartbeat'].replace('Z', '+00:00'))
                        diff = (updated - heartbeat).total_seconds()
                        print(f"      ⏱️  Diferença: {diff:.2f} segundos")
                        
                        if abs(diff) < 60:  # Menos de 1 minuto
                            print(f"      ✅ Bot foi atualizado logo após o heartbeat (shutdown rápido)")
                        else:
                            print(f"      ⚠️  Grande diferença entre heartbeat e atualização")
                    except Exception as e:
                        print(f"      ❌ Erro ao calcular diferença: {e}")
                        
        elif len(active_bots) == 0:
            print("⚠️  CAUSA: Todos os bots estão com is_active=False")
            print("   💡 Solução: Ativar os bots usando activate_bots_now.py")
        else:
            print("✅ Configuração parece normal")
            print("   🔍 Verificar logs do orquestrador para mais detalhes")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()