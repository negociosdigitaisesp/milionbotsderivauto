from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('.env.accumulator')

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

try:
    result = supabase.table('bot_configurations').select('*').execute()
    print('Registros encontrados na tabela bot_configurations:')
    for r in result.data:
        print(f'ID: {r["id"]}, Nome: {r["bot_name"]}, Tipo ID: {type(r["id"])}')
except Exception as e:
    print(f'Erro: {e}')