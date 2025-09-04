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
    # Configurar Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Erro: SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidos no .env.accumulator")
        return
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Verificar tabela bot_operation_logs
        print("\n" + "="*60)
        print("📋 VERIFICANDO TABELA bot_operation_logs")
        print("="*60)
        
        try:
            # Tentar buscar um registro para ver as colunas disponíveis
            response = supabase.table('bot_operation_logs').select('*').limit(1).execute()
            
            if response.data:
                print("✅ Tabela bot_operation_logs existe e tem dados")
                log_entry = response.data[0]
                print("\nColunas disponíveis:")
                for column, value in log_entry.items():
                    print(f"  • {column}: {type(value).__name__} = {value}")
            else:
                print("⚠️ Tabela bot_operation_logs existe mas está vazia")
                # Tentar inserir dados de teste para descobrir estrutura
                test_data = {
                    'bot_id': 1,
                    'operation_result': 'WIN',
                    'profit_percentage': 10.5,
                    'stake_value': 50.0
                }
                try:
                    result = supabase.table('bot_operation_logs').insert(test_data).execute()
                    print("✅ Inserção de teste bem-sucedida!")
                    if result.data:
                        print("Estrutura descoberta:")
                        for column, value in result.data[0].items():
                            print(f"  • {column}: {type(value).__name__}")
                        # Limpar dados de teste
                        supabase.table('bot_operation_logs').delete().eq('id', result.data[0]['id']).execute()
                except Exception as insert_error:
                    print(f"❌ Erro na inserção de teste: {insert_error}")
                    
        except Exception as table_error:
            print(f"❌ Erro ao acessar tabela bot_operation_logs: {table_error}")
            
            # Verificar se a tabela existe
            try:
                # Tentar uma operação simples
                supabase.table('bot_operation_logs').select('count').execute()
                print("✅ Tabela existe mas pode ter problemas de estrutura")
            except Exception as exists_error:
                 print(f"❌ Tabela bot_operation_logs não existe: {exists_error}")
            else:
                print("✅ Todas as colunas necessárias estão presentes")
                
        else:
            print("❌ Nenhum registro encontrado na tabela")
            
    except Exception as e:
        print(f"❌ Erro ao verificar tabela: {e}")
        print("💡 Verifique se a tabela bot_configurations existe")

if __name__ == "__main__":
    main()