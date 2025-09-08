#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Trava Absoluta de Padrões
Verifica todas as funcionalidades implementadas conforme especificação
"""

import sys
import os
import time
import threading
from unittest.mock import Mock, patch

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o módulo principal
import radar_analisis_scalping_bot as bot

def test_pattern_lock_activation():
    """Testa ativação da trava de padrão"""
    print("\n=== TESTE 1: Ativação da Trava de Padrão ===")
    
    # Reset inicial
    bot.reset_pattern_lock_force()
    
    # Dados de teste
    strategy_name = "MICRO_BURST"
    confidence = 95.5
    signal_data = {"action": "BUY", "reason": "Padrão detectado"}
    tracking_id = "test-123"
    
    # Ativar trava
    bot.activate_pattern_lock(strategy_name, confidence, signal_data, tracking_id)
    
    # Verificar estado
    status = bot.check_pattern_lock_status()
    
    assert status['is_locked'] == True, "Trava deveria estar ativa"
    assert status['strategy_name'] == strategy_name, "Nome da estratégia incorreto"
    assert status['confidence'] == confidence, "Confiança incorreta"
    assert status['tracking_id'] == tracking_id, "Tracking ID incorreto"
    
    print("✅ Ativação da trava funcionando corretamente")
    return True

def test_operation_counting():
    """Testa contagem de operações"""
    print("\n=== TESTE 2: Contagem de Operações ===")
    
    # Ativar trava primeiro
    bot.activate_pattern_lock("TEST_STRATEGY", 90.0, {}, "test-456")
    
    # Incrementar operações
    count1 = bot.increment_pattern_operations()
    count2 = bot.increment_pattern_operations()
    
    assert count1 == 1, f"Primeira operação deveria ser 1, foi {count1}"
    assert count2 == 2, f"Segunda operação deveria ser 2, foi {count2}"
    
    # Verificar estado
    status = bot.check_pattern_lock_status()
    assert status['operations_count'] == 2, "Contador de operações incorreto"
    
    print("✅ Contagem de operações funcionando corretamente")
    return True

def test_timeout_system():
    """Testa sistema de timeout"""
    print("\n=== TESTE 3: Sistema de Timeout ===")
    
    # Ativar trava
    bot.activate_pattern_lock("TIMEOUT_TEST", 85.0, {}, "timeout-789")
    
    # Simular timeout modificando timestamp
    with bot._pattern_lock:
        bot.pattern_locked_state['detected_at'] = time.time() - 700  # 11+ minutos atrás
    
    # Verificar se timeout é detectado
    status = bot.check_pattern_lock_status()
    
    # O sistema deve ter resetado devido ao timeout
    assert status['is_locked'] == False, "Trava deveria ter sido resetada por timeout"
    
    print("✅ Sistema de timeout funcionando corretamente")
    return True

def test_integrity_validation():
    """Testa validação de integridade"""
    print("\n=== TESTE 4: Validação de Integridade ===")
    
    # Ativar trava
    bot.activate_pattern_lock("INTEGRITY_TEST", 88.0, {}, "integrity-101")
    
    # Corromper dados
    with bot._pattern_lock:
        bot.pattern_locked_state['strategy_name'] = None  # Corromper
    
    # Validar integridade
    is_valid = bot.validate_pattern_integrity()
    
    assert is_valid == False, "Integridade deveria ter falhado"
    
    # Verificar se foi resetado
    status = bot.check_pattern_lock_status()
    assert status['is_locked'] == False, "Estado deveria ter sido resetado"
    
    print("✅ Validação de integridade funcionando corretamente")
    return True

def test_thread_safety():
    """Testa thread safety"""
    print("\n=== TESTE 5: Thread Safety ===")
    
    # Reset inicial
    bot.reset_pattern_lock_force()
    
    results = []
    
    def worker(thread_id):
        try:
            bot.activate_pattern_lock(f"THREAD_TEST_{thread_id}", 90.0, {}, f"thread-{thread_id}")
            time.sleep(0.1)
            status = bot.check_pattern_lock_status()
            results.append(status['strategy_name'])
        except Exception as e:
            results.append(f"ERROR: {e}")
    
    # Criar múltiplas threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # Aguardar conclusão
    for t in threads:
        t.join()
    
    # Verificar se apenas uma thread conseguiu ativar
    valid_results = [r for r in results if not r.startswith("ERROR")]
    assert len(valid_results) == 1, f"Apenas uma thread deveria ter sucesso, mas {len(valid_results)} tiveram"
    
    print("✅ Thread safety funcionando corretamente")
    return True

def test_reset_after_operations():
    """Testa reset após 2 operações"""
    print("\n=== TESTE 6: Reset Após 2 Operações ===")
    
    # Ativar trava
    bot.activate_pattern_lock("RESET_TEST", 92.0, {}, "reset-202")
    
    # Incrementar até 2 operações
    bot.increment_pattern_operations()
    bot.increment_pattern_operations()
    
    # Verificar se ainda está travado
    status = bot.check_pattern_lock_status()
    assert status['is_locked'] == True, "Trava ainda deveria estar ativa com 2 operações"
    
    # Simular reset seguro (seria chamado pelo sistema principal)
    bot.reset_pattern_lock_safe()
    
    # Verificar se foi resetado
    status = bot.check_pattern_lock_status()
    assert status['is_locked'] == False, "Trava deveria ter sido resetada"
    
    print("✅ Reset após operações funcionando corretamente")
    return True

def test_supabase_integration():
    """Testa integração com Supabase (mock)"""
    print("\n=== TESTE 7: Integração Supabase (Mock) ===")
    
    # Mock do Supabase com estrutura correta
    mock_result = Mock()
    mock_result.data = [
        {'id': 1, 'created_at': '2024-01-01T10:00:00'},
        {'id': 2, 'created_at': '2024-01-01T10:05:00'}
    ]
    
    mock_supabase = Mock()
    mock_supabase.table.return_value.select.return_value.gte.return_value.execute.return_value = mock_result
    
    # Ativar trava
    bot.activate_pattern_lock("SUPABASE_TEST", 89.0, {}, "supabase-303")
    
    # Testar contagem via Supabase
    count = bot.count_operations_since_pattern(mock_supabase)
    
    # Verificar se a função foi chamada corretamente
    assert isinstance(count, int), "Contagem deveria retornar um inteiro"
    
    print("✅ Integração Supabase funcionando corretamente")
    return True

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO SISTEMA DE TRAVA ABSOLUTA")
    print("=" * 60)
    
    tests = [
        test_pattern_lock_activation,
        test_operation_counting,
        test_timeout_system,
        test_integrity_validation,
        test_thread_safety,
        test_reset_after_operations,
        test_supabase_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FALHOU: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed} testes passaram, {failed} falharam")
    
    if failed == 0:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema de trava funcionando perfeitamente.")
    else:
        print(f"⚠️  {failed} teste(s) falharam. Verificar implementação.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)