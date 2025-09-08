#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a correção do profit_percentage está funcionando
"""

import sys
import os
from unittest.mock import Mock

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar o módulo principal
import radar_analisis_scalping_bot as bot

def test_profit_percentage_conversion():
    """Testa se a conversão de profit_percentage para V/D está funcionando"""
    print("\n=== TESTE: Conversão profit_percentage para V/D ===")
    
    # Mock do Supabase com dados de profit_percentage
    mock_result = Mock()
    mock_result.data = [
        {'profit_percentage': 5.2, 'created_at': '2024-01-01T10:00:00'},  # WIN
        {'profit_percentage': -3.1, 'created_at': '2024-01-01T09:55:00'}, # LOSS
        {'profit_percentage': 2.8, 'created_at': '2024-01-01T09:50:00'},  # WIN
        {'profit_percentage': 0.0, 'created_at': '2024-01-01T09:45:00'},  # LOSS (0 = empate = LOSS)
        {'profit_percentage': 1.5, 'created_at': '2024-01-01T09:40:00'},  # WIN
    ]
    
    mock_supabase = Mock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
    
    # Executar a função
    historico, timestamps = bot.buscar_operacoes_historico(mock_supabase)
    
    # Verificar resultados esperados
    expected_historico = ['V', 'D', 'V', 'D', 'V']  # 5.2>0=V, -3.1<0=D, 2.8>0=V, 0.0=D, 1.5>0=V
    expected_timestamps = [
        '2024-01-01T10:00:00',
        '2024-01-01T09:55:00', 
        '2024-01-01T09:50:00',
        '2024-01-01T09:45:00',
        '2024-01-01T09:40:00'
    ]
    
    # Verificações
    assert historico == expected_historico, f"Histórico incorreto: esperado {expected_historico}, obtido {historico}"
    assert timestamps == expected_timestamps, f"Timestamps incorretos: esperado {expected_timestamps}, obtido {timestamps}"
    
    print(f"✅ Conversão funcionando corretamente:")
    print(f"   Dados originais: [5.2, -3.1, 2.8, 0.0, 1.5]")
    print(f"   Convertido para: {historico}")
    print(f"   Timestamps: {len(timestamps)} registros")
    
    return True

def test_edge_cases():
    """Testa casos extremos da conversão"""
    print("\n=== TESTE: Casos Extremos ===")
    
    # Mock com casos extremos
    mock_result = Mock()
    mock_result.data = [
        {'profit_percentage': 0.01, 'created_at': '2024-01-01T10:00:00'},  # WIN mínimo
        {'profit_percentage': -0.01, 'created_at': '2024-01-01T09:55:00'}, # LOSS mínimo
        {'profit_percentage': 100.0, 'created_at': '2024-01-01T09:50:00'}, # WIN máximo
        {'profit_percentage': -100.0, 'created_at': '2024-01-01T09:45:00'}, # LOSS máximo
        {'created_at': '2024-01-01T09:40:00'},  # Sem profit_percentage (default 0)
    ]
    
    mock_supabase = Mock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
    
    # Executar a função
    historico, timestamps = bot.buscar_operacoes_historico(mock_supabase)
    
    # Verificar resultados esperados
    expected_historico = ['V', 'D', 'V', 'D', 'D']  # 0.01>0=V, -0.01<0=D, 100>0=V, -100<0=D, None/0=D
    
    assert historico == expected_historico, f"Casos extremos incorretos: esperado {expected_historico}, obtido {historico}"
    
    print(f"✅ Casos extremos funcionando:")
    print(f"   0.01 -> V, -0.01 -> D, 100.0 -> V, -100.0 -> D, None -> D")
    print(f"   Resultado: {historico}")
    
    return True

def run_tests():
    """Executa todos os testes"""
    print("🔧 TESTANDO CORREÇÃO: profit_percentage -> V/D")
    print("=" * 50)
    
    tests = [
        test_profit_percentage_conversion,
        test_edge_cases
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
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADOS: {passed} testes passaram, {failed} falharam")
    
    if failed == 0:
        print("🎉 CORREÇÃO VALIDADA! profit_percentage -> V/D funcionando perfeitamente.")
    else:
        print(f"⚠️  {failed} teste(s) falharam. Verificar implementação.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)