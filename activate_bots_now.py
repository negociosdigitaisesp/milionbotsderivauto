#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ativar todos os bots no Supabase
Altera o status dos bots de 'stopped' para 'running'
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def init_supabase() -> Client:
    """Inicializa conexão com Supabase"""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            raise Exception("Variáveis SUPABASE_URL e SUPABASE_ANON_KEY não encontradas")
            
        supabase = create_client(url, key)
        print("✅ Conexão com Supabase estabelecida")
        return supabase
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        sys.exit(1)

def activate_all_bots():
    """Ativa todos os bots alterando status para 'running'"""
    supabase = init_supabase()
    
    try:
        # Buscar todos os bots
        print("🔍 Buscando bots no banco de dados...")
        response = supabase.table('bot_configurations').select('*').execute()
        
        if not response.data:
            print("⚠️ Nenhum bot encontrado no banco de dados")
            return
            
        print(f"📋 Encontrados {len(response.data)} bots")
        
        # Ativar cada bot
        activated_count = 0
        for bot in response.data:
            bot_id = bot['id']
            bot_name = bot['bot_name']
            current_status = bot.get('status', 'stopped')
            
            print(f"\n🤖 Bot: {bot_name} (ID: {bot_id})")
            print(f"   Status atual: {current_status}")
            
            if current_status == 'running':
                print("   ✅ Bot já está ativo")
                continue
                
            # Atualizar status para 'running'
            update_response = supabase.table('bot_configurations').update({
                'status': 'running',
                'is_active': True
            }).eq('id', bot_id).execute()
            
            if update_response.data:
                print("   🚀 Bot ativado com sucesso!")
                activated_count += 1
            else:
                print("   ❌ Erro ao ativar bot")
                
        print(f"\n📊 RESUMO:")
        print(f"   Total de bots: {len(response.data)}")
        print(f"   Bots ativados: {activated_count}")
        print(f"\n🎉 Processo concluído! O orchestrator detectará as mudanças no próximo ciclo.")
        
    except Exception as e:
        print(f"❌ Erro ao ativar bots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 ATIVADOR DE BOTS - Million Bots System")
    print("=" * 50)
    activate_all_bots()