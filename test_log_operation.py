#!/usr/bin/env python3

import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_instance import BotInstance

async def test_log_operation():
    """Testa o método log_operation com dados reais"""
    print("🧪 Testando método log_operation...\n")
    
    try:
        # Criar uma instância do bot para teste
        # Usar um bot_id existente da tabela bot_configurations
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        supabase = create_client(supabase_url, supabase_key)
        
        # Buscar um bot existente
        response = supabase.table('bot_configurations').select('id').limit(1).execute()
        if not response.data:
            print("❌ Nenhum bot encontrado na tabela bot_configurations")
            return
            
        bot_id = response.data[0]['id']
        print(f"📋 Usando bot_id: {bot_id}")
        
        # Criar instância do bot
        bot = BotInstance(str(bot_id))
        
        # Testar log de operação WIN
        print("\n🟢 Testando log de operação WIN...")
        await bot.log_operation(
            operation_result='WIN',
            profit_percentage=15.5,
            stake_value=50.0
        )
        
        # Testar log de operação LOSS
        print("\n🔴 Testando log de operação LOSS...")
        await bot.log_operation(
            operation_result='LOSS',
            profit_percentage=-100.0,
            stake_value=50.0
        )
        
        # Verificar se os logs foram inseridos
        print("\n📊 Verificando logs inseridos...")
        logs_response = supabase.table('bot_operation_logs') \
            .select('*') \
            .eq('bot_id', str(bot_id)) \
            .order('timestamp', desc=True) \
            .limit(5) \
            .execute()
            
        if logs_response.data:
            print(f"✅ {len(logs_response.data)} logs encontrados:")
            for log in logs_response.data:
                print(f"  • {log['operation_result']} - Profit: {log['profit_percentage']}% - Stake: ${log['stake_value']} - {log['timestamp']}")
        else:
            print("❌ Nenhum log encontrado")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_log_operation())