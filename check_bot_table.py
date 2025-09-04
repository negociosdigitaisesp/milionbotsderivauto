#!/usr/bin/env python3
"""
Script para verificar a estrutura da tabela bot_configurations
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Erro: Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas")
    sys.exit(1)

# Criar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_bot_table():
    """Verifica a estrutura da tabela bot_configurations"""
    try:
        print("🔍 Verificando tabela bot_configurations...")
        
        # Buscar todos os bots
        response = supabase.table('bot_configurations').select('*').execute()
        
        if not response.data:
            print("❌ Nenhum bot encontrado no banco de dados")
            return
        
        print(f"📊 Encontrados {len(response.data)} bots")
        print("\n📋 Estrutura dos dados:")
        
        for i, bot in enumerate(response.data):
            print(f"\n--- Bot {i+1} ---")
            for key, value in bot.items():
                print(f"  {key}: {value}")
            
            if i == 0:  # Mostrar apenas o primeiro para ver a estrutura
                print("\n🔑 Campos disponíveis:")
                for key in bot.keys():
                    print(f"  - {key}")
                break
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabela: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_bot_table()