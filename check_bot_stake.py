from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

response = client.table('bot_configurations').select('bot_name, param_stake_inicial, param_overrides').eq('id', 'f8eeac8d-64dd-4f6f-b73c-d6cc922422e8').single().execute()

print(f'Bot: {response.data["bot_name"]}')
print(f'Stake Inicial: {response.data["param_stake_inicial"]}')
print(f'Param Overrides: {response.data.get("param_overrides", "None")}')