from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('.env.accumulator')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

result = supabase.table('bot_configurations').select('*').limit(1).execute()
if result.data:
    columns = list(result.data[0].keys())
    growth_columns = [col for col in columns if 'growth' in col.lower()]
    print('Colunas relacionadas ao growth:', growth_columns)
    print('Todas as colunas:', columns)
else:
    print('Nenhum dado encontrado')