#!/usr/bin/env python3
"""
Teste de Conexao do Radar Analyzer
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

def testar_conexao_supabase():
    """Testa conexao com Supabase"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        print(f"URL: {supabase_url[:30]}...")
        print(f"KEY: {supabase_key[:30]}...")
        
        if not supabase_url or not supabase_key:
            print("ERRO: Credenciais nao encontradas")
            return None
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("OK - Conexao com Supabase criada")
        return supabase
        
    except Exception as e:
        print(f"ERRO: {e}")
        return None

def testar_busca_operacoes(supabase):
    """Testa busca de operacoes"""
    try:
        print("\n--- TESTANDO BUSCA DE OPERACOES ---")
        
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('id, profit_percentage, operation_result') \
            .order('id', desc=True) \
            .limit(5) \
            .execute()
        
        print(f"Operacoes encontradas: {len(response.data)}")
        
        for op in response.data[:3]:
            profit_percentage = op.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            print(f"  ID: {op.get('id')}, P%: {profit_percentage}%, Resultado: {resultado}")
        
        return response.data
        
    except Exception as e:
        print(f"ERRO na busca: {e}")
        return []

def testar_envio_sinal(supabase):
    """Testa envio de sinal"""
    try:
        print("\n--- TESTANDO ENVIO DE SINAL ---")
        
        payload = {
            'bot_name': 'Scalping Bot',
            'is_safe_to_operate': False,
            'reason': 'TESTE - Conexao funcionando'
        }
        
        print(f"Payload: {payload}")
        
        response = supabase.table('radar_de_apalancamiento_signals') \
            .insert(payload) \
            .execute()
        
        print("OK - Sinal enviado com sucesso!")
        print(f"Response: {response.data}")
        
        return True
        
    except Exception as e:
        print(f"ERRO no envio: {e}")
        return False

def main():
    print("=== TESTE DE CONEXAO RADAR ANALYZER ===")
    
    # Teste 1: Conexao
    supabase = testar_conexao_supabase()
    if not supabase:
        print("FALHA: Nao foi possivel conectar")
        return
    
    # Teste 2: Busca
    operacoes = testar_busca_operacoes(supabase)
    if not operacoes:
        print("FALHA: Nao foi possivel buscar operacoes")
        return
    
    # Teste 3: Envio
    sucesso = testar_envio_sinal(supabase)
    if not sucesso:
        print("FALHA: Nao foi possivel enviar sinal")
        return
    
    print("\n=== TODOS OS TESTES PASSARAM! ===")
    print("O radar_analyzer.py deve funcionar corretamente.")

if __name__ == "__main__":
    main()