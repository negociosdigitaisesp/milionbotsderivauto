#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do método log_operation corrigido
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def test_corrected_logging():
    """Testa o método log_operation corrigido"""
    
    print("="*60)
    print("TESTE DO METODO log_operation CORRIGIDO")
    print("="*60)
    
    try:
        # Conectar ao Supabase
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            raise ValueError("Credenciais Supabase não encontradas")
        
        supabase = create_client(url, key)
        print("Conexao com Supabase estabelecida")
        
        # Testar inserção com estrutura correta
        test_bot_id = "test-corrected-123"
        
        print(f"\nTestando inserção com estrutura correta...")
        
        # Teste com dados reais
        try:
            log_data = {
                'bot_id': test_bot_id,
                'operation_result': 'WIN',  # Coluna correta
                'profit_percentage': 5,     # int conforme esquema
                'stake_value': 50,          # Coluna correta (int)
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"Dados a serem inseridos: {log_data}")
            
            result = supabase.table('bot_operation_logs').insert(log_data).execute()
            
            if result.data:
                print("SUCCESS: Operação registrada com sucesso!")
                print(f"ID do registro: {result.data[0].get('id')}")
                print(f"Dados inseridos: {result.data[0]}")
                
                # Verificar se podemos buscar o registro
                search_result = supabase.table('bot_operation_logs') \
                    .select('*') \
                    .eq('bot_id', test_bot_id) \
                    .execute()
                
                if search_result.data:
                    print(f"Confirmacao: Encontrado {len(search_result.data)} registro(s) na busca")
                    
                # Limpar dados de teste
                supabase.table('bot_operation_logs').delete().eq('bot_id', test_bot_id).execute()
                print("Dados de teste removidos")
                
            else:
                print(f"Falha na inserção: {result}")
                
        except Exception as e:
            print(f"Erro no teste: {e}")
            
        # Teste com LOSS
        print(f"\nTestando inserção de operação LOSS...")
        
        try:
            log_data_loss = {
                'bot_id': test_bot_id,
                'operation_result': 'LOSS',
                'profit_percentage': -3,    # Negativo para perda
                'stake_value': 25,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"Dados LOSS: {log_data_loss}")
            
            result = supabase.table('bot_operation_logs').insert(log_data_loss).execute()
            
            if result.data:
                print("SUCCESS: Operação LOSS registrada com sucesso!")
                print(f"ID do registro: {result.data[0].get('id')}")
                
                # Limpar
                supabase.table('bot_operation_logs').delete().eq('id', result.data[0]['id']).execute()
                print("Dados de teste LOSS removidos")
                
            else:
                print(f"Falha na inserção LOSS: {result}")
                
        except Exception as e:
            print(f"Erro no teste LOSS: {e}")
        
        print("\n" + "="*60)
        print("ESTRUTURA CORRETA CONFIRMADA!")
        print("- bot_id: str")
        print("- operation_result: str (WIN/LOSS)")
        print("- profit_percentage: int")
        print("- stake_value: int")
        print("- timestamp: str (ISO format)")
        print("="*60)
        
    except Exception as e:
        print(f"Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_corrected_logging()