#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Configurar Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')
supabase = create_client(url, key)

print("Criando tabela bot_operation_logs...\n")

# SQL para criar a tabela bot_operation_logs
create_table_sql = """
CREATE TABLE IF NOT EXISTS public.bot_operation_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Identificação
    bot_id TEXT NOT NULL,  -- Mudando para TEXT para aceitar UUIDs
    bot_name TEXT NOT NULL,
    
    -- Dados da Operação
    operation_type TEXT NOT NULL, -- 'BUY', 'SELL', 'HEARTBEAT', 'START', 'STOP', 'ERROR'
    contract_id TEXT,
    stake DECIMAL(10,2),
    payout DECIMAL(10,2),
    profit_loss DECIMAL(10,2),
    
    -- Status e Resultado
    status TEXT NOT NULL, -- 'pending', 'won', 'lost', 'error', 'info'
    result_details JSONB DEFAULT '{}',
    
    -- Contexto Técnico
    signal_data JSONB DEFAULT '{}',
    market_conditions JSONB DEFAULT '{}',
    
    -- Debugging
    error_message TEXT,
    execution_time_ms INTEGER
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_bot_operation_logs_bot_id ON public.bot_operation_logs (bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_operation_logs_created_at ON public.bot_operation_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_bot_operation_logs_operation_type ON public.bot_operation_logs (operation_type);
CREATE INDEX IF NOT EXISTS idx_bot_operation_logs_status ON public.bot_operation_logs (status);
"""

try:
    # Executar o SQL usando RPC
    result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
    print("✅ Tabela bot_operation_logs criada com sucesso!")
except Exception as e:
    print(f"❌ Erro ao criar tabela via RPC: {e}")
    print("\nTentando criar manualmente...")
    
    # Tentar inserir um registro de teste para verificar se a tabela existe
    try:
        test_data = {
            'bot_id': 'test-uuid',
            'bot_name': 'Test Bot',
            'operation_type': 'TEST',
            'status': 'info'
        }
        supabase.table('bot_operation_logs').insert(test_data).execute()
        print("✅ Tabela bot_operation_logs já existe e está funcionando!")
        
        # Deletar o registro de teste
        supabase.table('bot_operation_logs').delete().eq('operation_type', 'TEST').execute()
        print("✅ Registro de teste removido")
        
    except Exception as insert_error:
        print(f"❌ Tabela não existe ou tem estrutura incorreta: {insert_error}")
        print("\n⚠️  AÇÃO NECESSÁRIA:")
        print("1. Acesse o Supabase SQL Editor")
        print("2. Execute o conteúdo do arquivo setup_supabase_tables.sql")
        print("3. Execute este script novamente")

print("\nVerificando estrutura final...")
try:
    response = supabase.table('bot_operation_logs').select('*').limit(1).execute()
    print(f"✅ Tabela acessível. Registros encontrados: {len(response.data)}")
except Exception as e:
    print(f"❌ Erro ao acessar tabela: {e}")