#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Configurar Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(url, key)

print("Verificando estrutura da tabela bot_operation_logs...\n")

# Tentar inserir um registro mínimo para descobrir quais colunas existem
test_data = {
    'bot_id': 'test-uuid',
    'operation_type': 'TEST',
    'status': 'info'
}

try:
    result = supabase.table('bot_operation_logs').insert(test_data).execute()
    print("✅ Inserção básica bem-sucedida!")
    print(f"Registro inserido: {result.data[0]}")
    
    # Mostrar todas as colunas do registro inserido
    print("\nColunas disponíveis na tabela:")
    for key, value in result.data[0].items():
        print(f"  - {key}: {type(value).__name__}")
    
    # Deletar o registro de teste
    supabase.table('bot_operation_logs').delete().eq('operation_type', 'TEST').execute()
    print("\n✅ Registro de teste removido")
    
except Exception as e:
    print(f"❌ Erro na inserção básica: {e}")
    
    # Tentar com ainda menos campos
    minimal_data = {
        'operation_type': 'TEST'
    }
    
    try:
        result = supabase.table('bot_operation_logs').insert(minimal_data).execute()
        print("\n✅ Inserção mínima bem-sucedida!")
        print(f"Registro inserido: {result.data[0]}")
        
        # Mostrar todas as colunas do registro inserido
        print("\nColunas disponíveis na tabela:")
        for key, value in result.data[0].items():
            print(f"  - {key}: {type(value).__name__}")
        
        # Deletar o registro de teste
        supabase.table('bot_operation_logs').delete().eq('operation_type', 'TEST').execute()
        print("\n✅ Registro de teste removido")
        
    except Exception as e2:
        print(f"❌ Erro na inserção mínima: {e2}")

print("\n" + "="*50)
print("Testando inserção com campos opcionais como None...")

# Testar inserção com campos None
test_data_with_nulls = {
    'bot_id': 'test-uuid-2',
    'operation_type': 'TEST2',
    'status': 'info',
    'stake': None,
    'payout': None,
    'profit_loss': None,
    'result_details': {},
    'signal_data': {},
    'error_message': None,
    'execution_time_ms': None
}

try:
    result = supabase.table('bot_operation_logs').insert(test_data_with_nulls).execute()
    print("✅ Inserção com campos None bem-sucedida!")
    
    # Deletar o registro de teste
    supabase.table('bot_operation_logs').delete().eq('operation_type', 'TEST2').execute()
    print("✅ Registro de teste removido")
    
except Exception as e:
    print(f"❌ Erro na inserção com campos None: {e}")