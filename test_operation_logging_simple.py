#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o logging de operações na tabela bot_operation_logs
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def test_operation_logging():
    """Testa o registro de operações"""
    
    print("="*60)
    print("TESTE DE LOGGING DE OPERACOES")
    print("="*60)
    
    try:
        # Conectar ao Supabase
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            raise ValueError("Credenciais Supabase não encontradas")
        
        supabase = create_client(url, key)
        print("Conexao com Supabase estabelecida")
        
        # 1. Verificar estrutura da tabela
        print("\nVerificando estrutura da tabela...")
        try:
            response = supabase.table('bot_operation_logs').select('*').limit(1).execute()
            
            if response.data:
                print("Tabela existe e tem dados")
                print("Estrutura descoberta:")
                for column, value in response.data[0].items():
                    print(f"   - {column}: {type(value).__name__}")
            else:
                print("Tabela existe mas está vazia")
                
        except Exception as e:
            print(f"Erro ao verificar estrutura: {e}")
            return
        
        # 2. Testar inserção com diferentes formatos
        test_bot_id = "test-bot-123"
        
        print(f"\nTestando inserções com bot_id: {test_bot_id}")
        
        # Teste 1: Formato simples
        print("\nTeste 1: Formato simples")
        try:
            data1 = {
                'bot_id': test_bot_id,
                'result': 'WIN'
            }
            
            result = supabase.table('bot_operation_logs').insert(data1).execute()
            
            if result.data:
                print("Inserção simples bem-sucedida!")
                print(f"ID: {result.data[0].get('id')}")
                
                # Limpar
                supabase.table('bot_operation_logs').delete().eq('id', result.data[0]['id']).execute()
                print("Registro de teste removido")
            else:
                print(f"Falha na inserção: {result}")
                
        except Exception as e:
            print(f"Erro no teste 1: {e}")
        
        # Teste 2: Formato completo
        print("\nTeste 2: Formato completo")
        try:
            data2 = {
                'bot_id': test_bot_id,
                'result': 'WIN',
                'profit_percentage': 5.25,
                'stake_amount': 50.0,
                'timestamp': datetime.now().isoformat()
            }
            
            result = supabase.table('bot_operation_logs').insert(data2).execute()
            
            if result.data:
                print("Inserção completa bem-sucedida!")
                print(f"ID: {result.data[0].get('id')}")
                
                # Limpar
                supabase.table('bot_operation_logs').delete().eq('id', result.data[0]['id']).execute()
                print("Registro de teste removido")
            else:
                print(f"Falha na inserção: {result}")
                
        except Exception as e:
            print(f"Erro no teste 2: {e}")
        
        # Teste 3: Buscar por bot_id
        print(f"\nTeste 3: Buscar operações de bot específico")
        try:
            # Primeiro inserir um registro
            data3 = {
                'bot_id': test_bot_id,
                'result': 'LOSS',
                'profit_percentage': -3.5,
                'stake_amount': 25.0
            }
            
            insert_result = supabase.table('bot_operation_logs').insert(data3).execute()
            
            if insert_result.data:
                print("Registro inserido para busca")
                
                # Buscar
                search_result = supabase.table('bot_operation_logs') \
                    .select('*') \
                    .eq('bot_id', test_bot_id) \
                    .execute()
                
                if search_result.data:
                    print(f"Encontrado {len(search_result.data)} registro(s)")
                    for record in search_result.data:
                        print(f"   - ID: {record.get('id')}")
                        print(f"   - Bot ID: {record.get('bot_id')}")
                        print(f"   - Result: {record.get('result')}")
                        print(f"   - Profit: {record.get('profit_percentage')}%")
                        print(f"   - Stake: ${record.get('stake_amount')}")
                        print(f"   - Timestamp: {record.get('timestamp', record.get('created_at'))}")
                else:
                    print("Nenhum registro encontrado na busca")
                
                # Limpar
                for record in insert_result.data:
                    supabase.table('bot_operation_logs').delete().eq('id', record['id']).execute()
                print("Registros de teste removidos")
                
        except Exception as e:
            print(f"Erro no teste 3: {e}")
        
        print("\n" + "="*60)
        print("TESTES CONCLUÍDOS")
        print("="*60)
        
    except Exception as e:
        print(f"Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_operation_logging()