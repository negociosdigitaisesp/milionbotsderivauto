import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def init_supabase() -> Client:
    """Inicializar cliente Supabase"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        raise ValueError("Variáveis SUPABASE_URL e SUPABASE_ANON_KEY são obrigatórias")
    
    return create_client(url, key)

def main():
    try:
        supabase = init_supabase()
        
        print("🔍 VERIFICANDO STATUS DE SEGURANÇA DOS BOTS")
        print("=" * 50)
        
        # Buscar configurações dos bots
        response = supabase.table('bot_configurations') \
            .select('id, bot_name, status, is_safe_to_operate, status_reason, last_heartbeat') \
            .execute()
        
        if not response.data:
            print("❌ Nenhuma configuração de bot encontrada")
            return
        
        print(f"📊 Total de bots configurados: {len(response.data)}")
        print()
        
        for bot in response.data:
            bot_id = bot['id']
            bot_name = bot['bot_name']
            status = bot['status']
            is_safe = bot.get('is_safe_to_operate', True)
            status_reason = bot.get('status_reason', 'N/A')
            last_heartbeat = bot.get('last_heartbeat')
            
            print(f"🤖 Bot: {bot_name} (ID: {bot_id})")
            print(f"   • Status: {status}")
            print(f"   • Seguro para operar: {'✅ SIM' if is_safe else '❌ NÃO'}")
            print(f"   • Motivo: {status_reason}")
            print(f"   • Último heartbeat: {last_heartbeat}")
            
            # Verificar se o bot está ativo mas não seguro
            if status == 'running' and not is_safe:
                print(f"   ⚠️ ATENÇÃO: Bot está rodando mas não está seguro para operar!")
            
            print()
        
        # Verificar operações recentes por bot
        print("\n📈 OPERAÇÕES RECENTES POR BOT (últimas 24h)")
        print("=" * 50)
        
        # Data de 24 horas atrás
        yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
        
        for bot in response.data:
            bot_id = bot['id']
            bot_name = bot['bot_name']
            
            # Buscar operações do bot nas últimas 24h
            ops_response = supabase.table('bot_operation_logs') \
                .select('operation_result, timestamp') \
                .eq('bot_id', bot_id) \
                .gte('timestamp', yesterday) \
                .order('timestamp', desc=True) \
                .execute()
            
            operations = ops_response.data if ops_response.data else []
            
            print(f"🤖 {bot_name}:")
            if operations:
                wins = len([op for op in operations if op['operation_result'] == 'WIN'])
                losses = len([op for op in operations if op['operation_result'] == 'LOSS'])
                others = len([op for op in operations if op['operation_result'] not in ['WIN', 'LOSS']])
                
                print(f"   • Total de operações: {len(operations)}")
                print(f"   • Wins: {wins}")
                print(f"   • Losses: {losses}")
                print(f"   • Outras: {others}")
                
                if len(operations) > 0:
                    last_op = operations[0]
                    print(f"   • Última operação: {last_op['operation_result']} em {last_op['timestamp']}")
            else:
                print(f"   • ❌ Nenhuma operação nas últimas 24h")
            
            print()
        
        # Verificar se há padrões sendo detectados mas não executados
        print("\n🎯 ANÁLISE DE DETECÇÃO DE PADRÕES")
        print("=" * 50)
        print("💡 Para verificar se padrões estão sendo detectados, verifique os logs do orquestrador.")
        print("💡 Procure por mensagens como '🎯 PADRÃO DETECTADO!' nos logs.")
        print("💡 Se padrões são detectados mas operações não são executadas, pode ser:")
        print("   • Bot em modo não seguro (is_safe_to_operate = false)")
        print("   • Problemas de conexão com a API Deriv")
        print("   • Saldo insuficiente")
        print("   • Limite de posições atingido")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()