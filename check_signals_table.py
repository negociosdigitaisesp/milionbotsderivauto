#!/usr/bin/env python3
"""
Verificar estrutura da tabela radar_de_apalancamiento_signals
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def main():
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Conexao OK")
        
        # Buscar registros para ver as colunas disponiveis
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .limit(5) \
            .execute()
        
        if response.data:
            print("Colunas disponiveis:")
            for col in response.data[0].keys():
                print(f"  - {col}")
            
            print(f"\nRegistros existentes:")
            for record in response.data:
                print(f"  {record}")
        else:
            print("Tabela vazia ou nao existe")
            
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()