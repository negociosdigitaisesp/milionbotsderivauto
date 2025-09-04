#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Conexão e Registro no Supabase
Verifica se as operações estão sendo registradas corretamente
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def test_supabase_connection():
    """Testa conexão básica com Supabase"""
    print("🧪 TESTE DE CONEXÃO COM SUPABASE")
    print("=" * 50)
    
    try:
        # Verificar variáveis de ambiente
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        print(f"📍 SUPABASE_URL: {'✅ Definida' if url else '❌ Não definida'}")
        print(f"🔑 SUPABASE_ANON_KEY: {'✅ Definida' if key else '❌ Não definida'}")
        
        if not url or not key:
            print("❌ Variáveis de ambiente não configuradas!")
            return False
        
        # Criar cliente
        supabase = create_client(url, key)
        print("✅ Cliente Supabase criado")
        
        # Testar conexão com tabela bot_configurations
        print("\n🔍 Testando acesso à tabela bot_configurations...")
        response = supabase.table('bot_configurations').select('id, bot_name, status').limit(5).execute()
        
        if response.data:
            print(f"✅ Tabela bot_configurations acessível - {len(response.data)} registros encontrados")
            for bot in response.data:
                print(f"   📋 Bot ID: {bot.get('id')} - Nome: {bot.get('bot_name')} - Status: {bot.get('status')}")
        else:
            print("⚠️ Tabela bot_configurations vazia ou inacessível")
        
        # Testar conexão com tabela bot_operation_logs
        print("\n🔍 Testando acesso à tabela bot_operation_logs...")
        logs_response = supabase.table('bot_operation_logs').select('*').limit(5).execute()
        
        if logs_response.data:
            print(f"✅ Tabela bot_operation_logs acessível - {len(logs_response.data)} registros encontrados")
            for log in logs_response.data:
                print(f"   📝 Bot ID: {log.get('bot_id')} - Resultado: {log.get('operation_result')} - Data: {log.get('created_at')}")
        else:
            print("⚠️ Tabela bot_operation_logs vazia")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com Supabase: {e}")
        return False

def test_operation_logging():
    """Testa inserção de log de operação"""
    print("\n🧪 TESTE DE REGISTRO DE OPERAÇÃO")
    print("=" * 50)
    
    try:
        # Criar cliente
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase = create_client(url, key)
        
        # Dados de teste - usando UUID válido
        test_data = {
            'bot_id': 'f8eeac8d-64dd-4f6f-b73c-d6cc922422e8',  # UUID válido existente
            'operation_result': 'WON',
            'profit_percentage': 85.5,
            'stake_value': 1.0,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"📝 Inserindo dados de teste: {test_data}")
        
        # Inserir dados
        result = supabase.table('bot_operation_logs').insert(test_data).execute()
        
        print(f"📊 Resposta do Supabase: {result}")
        
        if result.data and len(result.data) > 0:
            print("✅ Operação de teste registrada com sucesso!")
            print(f"   📋 ID do registro: {result.data[0].get('id')}")
            return True
        else:
            print("❌ Falha ao registrar operação de teste")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar registro de operação: {e}")
        return False

def test_bot_instance_logging():
    """Testa o método log_operation da classe BotInstance"""
    print("\n🧪 TESTE DO MÉTODO log_operation DA CLASSE BotInstance")
    print("=" * 50)
    
    try:
        # Importar BotInstance
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from bot_instance import BotInstance
        
        # Criar instância de teste - usando UUID válido
        bot = BotInstance('f8eeac8d-64dd-4f6f-b73c-d6cc922422e8')
        
        # Testar log_operation
        async def test_async():
            result = await bot.log_operation(
                operation_result='LOST',
                profit_percentage=-100.0,
                stake_value=2.0
            )
            return result
        
        # Executar teste assíncrono
        result = asyncio.run(test_async())
        
        if result:
            print("✅ Método log_operation funcionando corretamente!")
        else:
            print("❌ Método log_operation falhou")
            
        return result
        
    except Exception as e:
        print(f"❌ Erro ao testar BotInstance.log_operation: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DE SUPABASE")
    print("=" * 60)
    
    tests = [
        ("Conexão Básica", test_supabase_connection),
        ("Registro de Operação", test_operation_logging),
        ("BotInstance.log_operation", test_bot_instance_logging)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Executando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! O sistema está funcionando corretamente.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima para mais detalhes.")

if __name__ == "__main__":
    main()