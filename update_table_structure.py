#!/usr/bin/env python3
"""
Script para atualizar a estrutura da tabela radar_de_apalancamiento_signals
Adicionando a coluna strategy_used necessária para o sistema de portfólio
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def inicializar_supabase():
    """Inicializa conexão com Supabase"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Credenciais do Supabase não encontradas no arquivo .env")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conexão com Supabase estabelecida com sucesso")
        return supabase
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        return None

def verificar_coluna_existe(supabase):
    """Verifica se a coluna strategy_used já existe"""
    try:
        # Tentar fazer uma query que usa a coluna strategy_used
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('strategy_used') \
            .limit(1) \
            .execute()
        
        print("✅ Coluna 'strategy_used' já existe na tabela")
        return True
        
    except Exception as e:
        if "Could not find the 'strategy_used' column" in str(e):
            print("ℹ️ Coluna 'strategy_used' não existe - será criada")
            return False
        else:
            print(f"❌ Erro ao verificar coluna: {e}")
            return False

def adicionar_coluna_strategy_used(supabase):
    """Adiciona a coluna strategy_used via SQL"""
    try:
        # SQL para adicionar a coluna
        sql_query = """
        ALTER TABLE public.radar_de_apalancamiento_signals 
        ADD COLUMN IF NOT EXISTS strategy_used TEXT NULL;
        """
        
        # Executar via RPC (se disponível) ou tentar via postgrest
        print("🔧 Tentando adicionar coluna 'strategy_used'...")
        
        # Nota: O Supabase Python client não suporta DDL diretamente
        # A coluna precisa ser adicionada via Dashboard do Supabase ou SQL Editor
        print("⚠️ ATENÇÃO: A coluna precisa ser adicionada manualmente no Supabase")
        print("📋 Execute este SQL no SQL Editor do Supabase Dashboard:")
        print("\n" + "="*60)
        print(sql_query)
        print("="*60 + "\n")
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        return False

def main():
    print("🚀 Iniciando atualização da estrutura da tabela...\n")
    
    # Conectar ao Supabase
    supabase = inicializar_supabase()
    if not supabase:
        return
    
    # Verificar se a coluna já existe
    if verificar_coluna_existe(supabase):
        print("\n✅ Tabela já está atualizada!")
        return
    
    # Tentar adicionar a coluna
    adicionar_coluna_strategy_used(supabase)
    
    print("\n📝 INSTRUÇÕES:")
    print("1. Acesse o Supabase Dashboard")
    print("2. Vá para SQL Editor")
    print("3. Execute o comando SQL mostrado acima")
    print("4. Execute este script novamente para verificar")
    print("\n🔄 Após adicionar a coluna, o radar_analyzer.py funcionará corretamente")

if __name__ == "__main__":
    main()