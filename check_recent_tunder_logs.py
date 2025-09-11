#!/usr/bin/env python3
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Carregar variáveis de ambiente
load_dotenv()

def main():
    try:
        # Conectar ao Supabase
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        print(f"⏰ Horário atual: {datetime.now()}")
        print("\n📊 Verificando logs recentes do Tunder Bot...")
        
        # Buscar os últimos 10 registros
        response = supabase.table('tunder_bot_logs').select('*').order('id', desc=True).limit(10).execute()
        
        if response.data:
            print(f"\n📈 Total de registros encontrados: {len(response.data)}")
            print("\n🔍 Últimos registros:")
            
            for i, record in enumerate(response.data, 1):
                created_at = record.get('created_at', 'N/A')
                profit = record.get('profit_percentage', 0)
                operation_result = record.get('operation_result', 'N/A')
                stake = record.get('stake_value', 0)
                
                print(f"   {i}. ID: {record.get('id')}, Result: {operation_result}, Profit: {profit}%, Stake: ${stake}, Created: {created_at}")
            
            # Verificar se há logs recentes (últimos 10 minutos)
            ten_minutes_ago = datetime.now() - timedelta(minutes=10)
            recent_logs = []
            
            for record in response.data:
                created_at_str = record.get('created_at', '')
                if created_at_str:
                    # Remover timezone info para comparação simples
                    created_at_clean = created_at_str.replace('+00:00', '').replace('Z', '')
                    try:
                        created_at_dt = datetime.fromisoformat(created_at_clean)
                        if created_at_dt > ten_minutes_ago:
                            recent_logs.append(record)
                    except:
                        pass
            
            print(f"\n⚡ Logs dos últimos 10 minutos: {len(recent_logs)}")
            
            if recent_logs:
                print("✅ O bot está enviando logs em tempo real!")
                for log in recent_logs:
                    print(f"   • {log.get('operation_result')} - Profit: {log.get('profit_percentage')}% - {log.get('created_at')}")
            else:
                print("⚠️ Nenhum log recente encontrado nos últimos 10 minutos")
                print("💡 Possíveis causas:")
                print("   1. O bot não está executando operações")
                print("   2. O bot não está rodando")
                print("   3. Problema na conexão com Supabase")
                
        else:
            print("❌ Nenhum registro encontrado na tabela tunder_bot_logs")
            
    except Exception as e:
        print(f"❌ Erro ao verificar logs: {e}")

if __name__ == "__main__":
    main()