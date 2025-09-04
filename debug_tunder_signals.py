#!/usr/bin/env python3
"""
Script para debugar os sinais do Tunder Bot na tabela radar_de_apalancamiento_signals
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def main():
    """Verifica os sinais do Tunder Bot"""
    try:
        # Conectar ao Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Credenciais do Supabase não encontradas")
            return
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conectado ao Supabase")
        
        # Buscar registros do Tunder Bot
        print("\n🔍 Buscando sinais do Tunder Bot...")
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .eq('bot_name', 'Tunder Bot') \
            .order('created_at', desc=True) \
            .limit(5) \
            .execute()
        
        if response.data:
            print(f"\n📊 Encontrados {len(response.data)} registros do Tunder Bot:")
            print("=" * 100)
            
            for i, record in enumerate(response.data, 1):
                print(f"\n🔸 Registro {i}:")
                print(f"   ID: {record.get('id', 'N/A')}")
                print(f"   Bot Name: '{record.get('bot_name', 'N/A')}'")
                print(f"   Is Safe: {record.get('is_safe_to_operate', 'N/A')}")
                print(f"   Reason: '{record.get('reason', 'N/A')}'")
                print(f"   Last Pattern: '{record.get('last_pattern_found', 'N/A')}'")
                print(f"   Losses (10 ops): {record.get('losses_in_last_10_ops', 'N/A')}")
                print(f"   Wins (5 ops): {record.get('wins_in_last_5_ops', 'N/A')}")
                print(f"   Historical Accuracy: {record.get('historical_accuracy', 'N/A')}")
                print(f"   Pattern Found At: {record.get('pattern_found_at', 'N/A')}")
                print(f"   Operations After Pattern: {record.get('operations_after_pattern', 'N/A')}")
                print(f"   Auto Disable After: {record.get('auto_disable_after_ops', 'N/A')}")
                print(f"   Created At: {record.get('created_at', 'N/A')}")
                print("-" * 80)
                
                # Verificar se o reason está vazio ou None
                reason = record.get('reason')
                if not reason or reason.strip() == '':
                    print(f"   ⚠️ PROBLEMA: Campo 'reason' está vazio ou None!")
                else:
                    print(f"   ✅ Campo 'reason' está preenchido corretamente")
        else:
            print("⚠️ Nenhum registro do Tunder Bot encontrado")
        
        # Testar envio manual de sinal
        print("\n🧪 Testando envio manual de sinal...")
        test_data = {
            'bot_name': 'Tunder Bot',
            'is_safe_to_operate': False,
            'reason': 'TESTE MANUAL - Verificando envio do campo reason',
            'last_pattern_found': 'Aguardando',
            'losses_in_last_10_ops': 0,
            'wins_in_last_5_ops': 0,
            'historical_accuracy': 0.0,
            'auto_disable_after_ops': 3
        }
        
        print(f"Dados do teste: {test_data}")
        
        # Tentar fazer UPSERT
        try:
            # Primeiro tentar atualizar
            update_response = supabase.table('radar_de_apalancamiento_signals') \
                .update(test_data) \
                .eq('bot_name', 'Tunder Bot') \
                .execute()
            
            if update_response.data:
                print(f"✅ Sinal atualizado com sucesso! ID: {update_response.data[0]['id']}")
                print(f"   Reason enviado: '{update_response.data[0].get('reason', 'N/A')}'")
            else:
                # Se não atualizou, inserir novo
                insert_response = supabase.table('radar_de_apalancamiento_signals') \
                    .insert(test_data) \
                    .execute()
                
                if insert_response.data:
                    print(f"✅ Novo sinal inserido com sucesso! ID: {insert_response.data[0]['id']}")
                    print(f"   Reason enviado: '{insert_response.data[0].get('reason', 'N/A')}'")
                else:
                    print("❌ Falha ao inserir novo sinal")
                    
        except Exception as test_error:
            print(f"❌ Erro no teste manual: {test_error}")
        
        # Verificar novamente após o teste
        print("\n🔍 Verificando após teste manual...")
        response_after = supabase.table('radar_de_apalancamiento_signals') \
            .select('id, reason, created_at') \
            .eq('bot_name', 'Tunder Bot') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        if response_after.data:
            latest = response_after.data[0]
            print(f"✅ Último registro: ID {latest['id']}, Reason: '{latest.get('reason', 'N/A')}'")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()