#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar as colunas da tabela bot_configurations
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def main():
    # Conectar ao Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Variáveis de ambiente SUPABASE_URL ou SUPABASE_ANON_KEY não encontradas")
        return
    
    supabase: Client = create_client(url, key)
    print("✅ Conexão com Supabase estabelecida")
    
    try:
        # Buscar um registro para ver todas as colunas
        response = supabase.table('bot_configurations') \
            .select('*') \
            .limit(1) \
            .execute()
        
        if not response.data:
            print("❌ Nenhum bot encontrado")
            return
        
        bot = response.data[0]
        
        print("\n📊 COLUNAS DA TABELA bot_configurations:")
        print("=" * 60)
        
        for key, value in bot.items():
            print(f"• {key}: {value} (tipo: {type(value).__name__})")
                
    except Exception as e:
        print(f"❌ Erro ao buscar configurações: {e}")

if __name__ == "__main__":
    main()