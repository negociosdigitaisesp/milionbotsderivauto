#!/usr/bin/env python3
"""
Script para verificar dados na tabela tunder_bot_logs
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

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
        
        # Verificar dados na tabela tunder_bot_logs
        print("\n📊 Verificando tabela tunder_bot_logs...")
        
        response = supabase.table('tunder_bot_logs').select('*').order('id', desc=True).limit(10).execute()
        
        print(f"📈 Total de registros encontrados: {len(response.data)}")
        
        if response.data:
            print("\n🔍 Últimos registros:")
            for i, record in enumerate(response.data[:5]):
                print(f"   {i+1}. ID: {record.get('id')}, Profit: {record.get('profit_percentage')}%, Created: {record.get('created_at')}")
        else:
            print("⚠️ Nenhum registro encontrado na tabela tunder_bot_logs")
            print("\n💡 Possíveis soluções:")
            print("   1. Executar o tunderbot.py para gerar dados")
            print("   2. Verificar se a tabela existe no Supabase")
            print("   3. Verificar as credenciais de acesso")
        
        # Verificar também a tabela de sinais
        print("\n📡 Verificando tabela radar_de_apalancamiento_signals...")
        
        response_signals = supabase.table('radar_de_apalancamiento_signals').select('*').eq('bot_name', 'Tunder Bot').order('id', desc=True).limit(3).execute()
        
        print(f"📈 Sinais do Tunder Bot: {len(response_signals.data)}")
        
        if response_signals.data:
            print("\n🔍 Últimos sinais:")
            for i, signal in enumerate(response_signals.data):
                print(f"   {i+1}. ID: {signal.get('id')}, Safe: {signal.get('is_safe_to_operate')}, Reason: {signal.get('reason')[:50]}...")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()