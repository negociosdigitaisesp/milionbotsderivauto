from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Conectar ao Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

print("Verificando logs recentes na tabela bot_operation_logs...")

# Buscar os últimos 10 logs
result = supabase.table('bot_operation_logs').select('*').order('timestamp', desc=True).limit(10).execute()

print(f"\nTotal de logs encontrados: {len(result.data)}")

if result.data:
    print("\nÚltimos 10 logs:")
    for i, log in enumerate(result.data, 1):
        timestamp = log.get('timestamp', 'N/A')
        operation_result = log.get('operation_result', 'N/A')
        bot_id = log.get('bot_id', 'N/A')
        profit = log.get('profit_percentage', 'N/A')
        stake = log.get('stake_value', 'N/A')
        
        print(f"  {i}. {operation_result} - Bot: {bot_id[:8]}... - Profit: {profit}% - Stake: {stake} - {timestamp}")
else:
    print("\nNenhum log encontrado na tabela.")

# Verificar logs dos últimos 5 minutos
from datetime import datetime, timedelta
five_minutes_ago = (datetime.now() - timedelta(minutes=5)).isoformat()

recent_result = supabase.table('bot_operation_logs').select('*').gte('timestamp', five_minutes_ago).execute()

print(f"\nLogs dos últimos 5 minutos: {len(recent_result.data)}")
for log in recent_result.data:
    print(f"  • {log['operation_result']} - Bot: {log['bot_id'][:8]}... - {log['timestamp']}")