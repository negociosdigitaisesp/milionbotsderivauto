from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Conectar ao Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

print("=== VERIFICAÇÃO DE OPERAÇÕES RECENTES ===")

# Verificar operações dos últimos 10 minutos
now = datetime.now()
ten_minutes_ago = (now - timedelta(minutes=10)).isoformat()

print(f"\nBuscando operações desde: {ten_minutes_ago}")
print(f"Horário atual: {now.isoformat()}")

result = supabase.table('bot_operation_logs').select('*').gte('timestamp', ten_minutes_ago).order('timestamp', desc=True).execute()

print(f"\nOperações encontradas nos últimos 10 minutos: {len(result.data)}")

if result.data:
    for i, log in enumerate(result.data, 1):
        timestamp = log.get('timestamp', 'N/A')
        operation_result = log.get('operation_result', 'N/A')
        bot_id = log.get('bot_id', 'N/A')
        profit = log.get('profit_percentage', 'N/A')
        stake = log.get('stake_value', 'N/A')
        
        print(f"  {i}. {timestamp} - {operation_result} - Bot: {bot_id[:8]}... - Profit: {profit}% - Stake: {stake}")
else:
    print("  Nenhuma operação encontrada nos últimos 10 minutos.")

# Verificar todas as operações de hoje
today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
today_result = supabase.table('bot_operation_logs').select('*').gte('timestamp', today_start).execute()

print(f"\nTotal de operações hoje: {len(today_result.data)}")

# Verificar últimas 5 operações independente do horário
last_operations = supabase.table('bot_operation_logs').select('*').order('timestamp', desc=True).limit(5).execute()

print(f"\nÚltimas 5 operações (independente do horário):")
for i, log in enumerate(last_operations.data, 1):
    timestamp = log.get('timestamp', 'N/A')
    operation_result = log.get('operation_result', 'N/A')
    bot_id = log.get('bot_id', 'N/A')
    profit = log.get('profit_percentage', 'N/A')
    
    print(f"  {i}. {timestamp} - {operation_result} - Bot: {bot_id[:8]}... - Profit: {profit}%")