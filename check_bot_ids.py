#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar bot_ids disponíveis no Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def main():
    # Configurar Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Erro: SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidos no .env.accumulator")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Buscar todos os bots
        response = supabase.table('bot_configurations').select('id, bot_name, status, is_active').execute()
        
        if response.data:
            print("\n" + "="*60)
            print("🤖 BOTS DISPONÍVEIS NO BANCO DE DADOS")
            print("="*60)
            
            for bot in response.data:
                status_icon = "✅" if bot['is_active'] else "❌"
                print(f"{status_icon} ID: {bot['id']} | Nome: {bot['bot_name']} | Status: {bot['status']}")
            
            print("\n" + "="*60)
            print("💡 Para executar um bot, use:")
            print("   python bot_instance.py --bot_id <ID>")
            print("\n   Exemplo:")
            if response.data:
                first_bot = response.data[0]
                print(f"   python bot_instance.py --bot_id {first_bot['id']}")
            print("="*60)
        else:
            print("❌ Nenhum bot encontrado no banco de dados")
            print("💡 Execute o setup_supabase_tables.sql primeiro")
            
    except Exception as e:
        print(f"❌ Erro ao conectar com o Supabase: {e}")
        print("💡 Verifique suas credenciais no .env.accumulator")

if __name__ == "__main__":
    main()