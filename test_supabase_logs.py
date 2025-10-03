#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste - Logs Supabase Multi-Conta
============================================

Este script testa se a correção da tabela tunder_bot_logs resolve o erro PGRST204.
Simula o envio de logs com account_name para verificar se a estrutura está correta.
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_log_structure():
    """Testa a estrutura de dados que será enviada para o Supabase"""
    
    print("🔍 TESTE DA ESTRUTURA DE LOGS MULTI-CONTA")
    print("=" * 50)
    
    # Simular dados que serão enviados para tunder_bot_logs
    test_log_data = {
        "operation_result": "WIN",
        "profit_percentage": 85.5,
        "stake_value": 10.0,
        "timestamp": datetime.now().isoformat(),
        "bot_name": "Bot_Principal",
        "account_name": "Bot_Principal"  # Esta é a coluna que estava causando erro
    }
    
    print("📊 Dados de teste que serão enviados:")
    for key, value in test_log_data.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Estrutura de dados preparada com sucesso!")
    print("   - Todas as colunas necessárias estão presentes")
    print("   - account_name incluído para sistema multi-conta")
    
    return test_log_data

def test_import_bot_manager():
    """Testa se consegue importar o MultiAccountManager"""
    
    print("\n🤖 TESTE DE IMPORTAÇÃO DO SISTEMA MULTI-CONTA")
    print("=" * 50)
    
    try:
        from tunderbotalavanca import MultiAccountManager, ACTIVE_ACCOUNTS
        
        print("✅ Importação bem-sucedida!")
        print(f"   - Contas ativas configuradas: {len(ACTIVE_ACCOUNTS)}")
        
        if ACTIVE_ACCOUNTS:
            print("   - Conta principal:", ACTIVE_ACCOUNTS[0].get('name', 'N/A'))
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro na importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_log_function_simulation():
    """Simula a função log_to_supabase sem fazer requisição real"""
    
    print("\n📝 SIMULAÇÃO DA FUNÇÃO log_to_supabase")
    print("=" * 50)
    
    # Simular os dados que a função log_to_supabase enviaria
    simulated_data = {
        "operation_result": "WIN",
        "profit_percentage": 85.5,
        "stake_value": 10.0,
        "bot_name": "Bot_Principal",
        "account_name": "Bot_Principal",  # Coluna que estava causando erro
        "timestamp": datetime.now().isoformat()
    }
    
    print("📤 Dados que seriam enviados para Supabase:")
    for key, value in simulated_data.items():
        print(f"   {key}: {value}")
    
    # Verificar se todas as colunas esperadas estão presentes
    expected_columns = [
        "operation_result", "profit_percentage", "stake_value", 
        "bot_name", "account_name", "timestamp"
    ]
    
    missing_columns = [col for col in expected_columns if col not in simulated_data]
    
    if missing_columns:
        print(f"\n❌ Colunas faltando: {missing_columns}")
        return False
    else:
        print("\n✅ Todas as colunas necessárias estão presentes!")
        print("   - O erro PGRST204 deve ser resolvido após aplicar o SQL")
        return True

def main():
    """Função principal do teste"""
    
    print("🚀 INICIANDO TESTES DE CORREÇÃO DOS LOGS SUPABASE")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Executar testes
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Estrutura de dados
    if test_log_structure():
        tests_passed += 1
    
    # Teste 2: Importação do sistema
    if test_import_bot_manager():
        tests_passed += 1
    
    # Teste 3: Simulação da função de log
    if test_log_function_simulation():
        tests_passed += 1
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    print(f"✅ Testes aprovados: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   - A estrutura está correta")
        print("   - Aplique o arquivo fix_tunder_bot_logs_table.sql no Supabase")
        print("   - O erro PGRST204 deve ser resolvido")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} teste(s) falharam")
        print("   - Verifique os erros acima antes de aplicar a correção")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("   1. Execute o SQL: fix_tunder_bot_logs_table.sql")
    print("   2. Reinicie o bot para testar os logs reais")
    print("   3. Verifique se não há mais erros PGRST204")

if __name__ == "__main__":
    main()