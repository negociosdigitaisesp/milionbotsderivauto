#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from supabase import create_client
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Supabase
SUPABASE_URL = "https://xwclmxjeombwabfdvyij.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3Y2xteGplb21id2FiZmR2eWlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MjY0NTQsImV4cCI6MjA2ODEwMjQ1NH0.lB4EBPozpPUJS0oI5wpatJdo_HCTcuDRFmd42b_7i9U"

def check_bot_status():
    try:
        # Conectar ao Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexão com Supabase estabelecida")
        
        # Buscar status dos bots
        result = supabase.table('bot_configurations').select('bot_name, status, is_active').execute()
        
        print("\n📊 STATUS DOS BOTS:")
        print("=" * 50)
        
        for bot in result.data:
            print(f"🤖 {bot['bot_name']}:")
            print(f"   Status: {bot['status']}")
            print(f"   Ativo: {bot['is_active']}")
            print()
            
        print(f"Total de bots: {len(result.data)}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")

if __name__ == "__main__":
    check_bot_status()