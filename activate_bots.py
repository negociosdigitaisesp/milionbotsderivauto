#!/usr/bin/env python3
"""
Script para ativar os bots no banco de dados
Altera o status dos bots de 'stopped' para 'running'
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Erro: Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas")
    sys.exit(1)

# Criar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def activate_bots():
    """Ativa todos os bots alterando status para 'running'"""
    try:
        print("🔍 Verificando bots no banco de dados...")
        
        # Buscar todos os bots
        response = supabase.table('bot_configurations').select('*').execute()
        
        if not response.data:
            print("❌ Nenhum bot encontrado no banco de dados")
            return
        
        print(f"📊 Encontrados {len(response.data)} bots:")
        
        for bot in response.data:
            bot_id = bot['id']
            bot_name = bot['bot_name']
            current_status = bot['status']
            
            print(f"  - {bot_name} (ID: {bot_id}): Status atual = {current_status}")
            
            if current_status == 'stopped':
                # Ativar o bot
                update_response = supabase.table('bot_configurations').update({
                    'status': 'running'
                }).eq('id', bot_id).execute()
                
                if update_response.data:
                    print(f"  ✅ {bot_name} ativado com sucesso!")
                else:
                    print(f"  ❌ Erro ao ativar {bot_name}")
            else:
                print(f"  ℹ️ {bot_name} já está com status: {current_status}")
        
        print("\n🎉 Processo de ativação concluído!")
        print("💡 Execute 'python orchestrator.py' para iniciar o gerenciamento dos bots")
        
    except Exception as e:
        print(f"❌ Erro ao ativar bots: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Ativando bots no banco de dados...")
    activate_bots()