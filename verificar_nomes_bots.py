#!/usr/bin/env python3
"""
Script para verificar se os nomes dos bots estão corretos na tabela radar_de_apalancamiento_signals
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def main():
    """Verifica os nomes dos bots na tabela"""
    try:
        # Conectar ao Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Credenciais do Supabase não encontradas")
            return
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conectado ao Supabase")
        
        # Buscar todos os registros únicos por bot_name
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('bot_name, id, created_at, is_safe_to_operate, reason') \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        print(f"\n📊 Últimos 10 registros na tabela:")
        print("=" * 80)
        
        if response.data:
            for record in response.data:
                bot_name = record.get('bot_name', 'N/A')
                record_id = record.get('id', 'N/A')
                is_safe = record.get('is_safe_to_operate', 'N/A')
                reason = record.get('reason', 'N/A')[:50] + '...' if record.get('reason') else 'N/A'
                created_at = record.get('created_at', 'N/A')[:19] if record.get('created_at') else 'N/A'
                
                # Verificar se o nome está correto
                status = "✅" if bot_name in ['Scalping Bot', 'Tunder Bot'] else "❌"
                
                print(f"{status} ID: {record_id} | Bot: '{bot_name}' | Safe: {is_safe} | {created_at}")
                print(f"   Reason: {reason}")
                print("-" * 80)
        else:
            print("⚠️ Nenhum registro encontrado")
        
        # Buscar registros únicos por bot_name
        print("\n🔍 Nomes únicos de bots encontrados:")
        print("=" * 50)
        
        response_unique = supabase.table('radar_de_apalancamiento_signals') \
            .select('bot_name') \
            .execute()
        
        if response_unique.data:
            unique_names = set(record['bot_name'] for record in response_unique.data)
            for name in sorted(unique_names):
                status = "✅" if name in ['Scalping Bot', 'Tunder Bot'] else "❌"
                print(f"{status} '{name}'")
        
        print("\n📋 Nomes corretos esperados:")
        print("✅ 'Scalping Bot' - para o radar original")
        print("✅ 'Tunder Bot' - para o radar do Tunder Bot")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()