#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da Estratégia LL Simplificada (Sem Filtros de Horário)

Este script testa a função analisar_estrategia_momentum_calmo
para garantir que ela detecta corretamente o padrão LL sem
aplicar filtros de horário.
"""

import sys
import importlib.util
from datetime import datetime

# Importar a função do arquivo radartunder3.5.py
spec = importlib.util.spec_from_file_location("radartunder3_5", "radartunder3.5.py")
radartunder3_5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radartunder3_5)

# Importar a função e constantes necessárias
analisar_estrategia_momentum_calmo = radartunder3_5.analisar_estrategia_momentum_calmo
BOT_NAME = radartunder3_5.BOT_NAME

def test_ll_pattern_detection():
    """Testa se a estratégia detecta corretamente o padrão LL."""
    print("=== TESTE: Detecção do Padrão LL ===")
    
    # Teste 1: Padrão LL deve ativar a estratégia
    historico_ll = ['LOSS', 'LOSS', 'WIN', 'LOSS']
    timestamp_qualquer = datetime.now().isoformat()
    
    resultado = analisar_estrategia_momentum_calmo(historico_ll, timestamp_qualquer)
    
    assert resultado['should_operate'] == True, "Deveria ativar para padrão LL"
    assert resultado['strategy'] == 'Momentum-Calmo-LL', "Estratégia incorreta"
    assert 'LL detectado' in resultado['reason'], "Razão incorreta"
    
    print("✅ Teste 1 PASSOU: Padrão LL detectado corretamente")
    
    # Teste 2: Padrão WW não deve ativar
    historico_ww = ['WIN', 'WIN', 'LOSS', 'WIN']
    resultado = analisar_estrategia_momentum_calmo(historico_ww, timestamp_qualquer)
    
    assert resultado['should_operate'] == False, "Não deveria ativar para padrão WW"
    assert 'WW' in resultado['reason'], "Deveria mostrar padrão WW"
    
    print("✅ Teste 2 PASSOU: Padrão WW rejeitado corretamente")
    
    # Teste 3: Padrão LW não deve ativar
    historico_lw = ['WIN', 'LOSS', 'WIN', 'LOSS']
    resultado = analisar_estrategia_momentum_calmo(historico_lw, timestamp_qualquer)
    
    assert resultado['should_operate'] == False, "Não deveria ativar para padrão LW"
    assert 'LW' in resultado['reason'], "Deveria mostrar padrão LW"
    
    print("✅ Teste 3 PASSOU: Padrão LW rejeitado corretamente")
    
    # Teste 4: Padrão WL não deve ativar
    historico_wl = ['LOSS', 'WIN', 'LOSS', 'WIN']
    resultado = analisar_estrategia_momentum_calmo(historico_wl, timestamp_qualquer)
    
    assert resultado['should_operate'] == False, "Não deveria ativar para padrão WL"
    assert 'WL' in resultado['reason'], "Deveria mostrar padrão WL"
    
    print("✅ Teste 4 PASSOU: Padrão WL rejeitado corretamente")

def test_no_time_filters():
    """Testa se a estratégia funciona em qualquer horário (sem filtros)."""
    print("\n=== TESTE: Sem Filtros de Horário ===")
    
    # Teste com diferentes horários - todos devem funcionar se o padrão for LL
    horarios_teste = [
        "2024-01-15T03:30:00Z",  # Baixa atividade (antes)
        "2024-01-15T12:45:00Z",  # Média atividade (antes)
        "2024-01-15T20:15:00Z",  # Alta atividade (antes)
        "2024-01-15T05:57:00Z",  # Fechamento da hora (antes)
        "2024-01-15T14:25:00Z",  # Meio da hora (antes)
    ]
    
    historico_ll = ['LOSS', 'LOSS', 'WIN', 'LOSS']
    
    for i, timestamp in enumerate(horarios_teste, 1):
        resultado = analisar_estrategia_momentum_calmo(historico_ll, timestamp)
        
        assert resultado['should_operate'] == True, f"Deveria ativar em qualquer horário (teste {i})"
        assert 'LL detectado' in resultado['reason'], f"Razão incorreta para horário {i}"
        
        print(f"✅ Teste {i} PASSOU: LL detectado em {timestamp}")

def test_minimum_history():
    """Testa o comportamento com histórico insuficiente."""
    print("\n=== TESTE: Histórico Mínimo ===")
    
    # Teste com apenas 1 operação
    historico_insuficiente = ['LOSS']
    timestamp_qualquer = datetime.now().isoformat()
    
    resultado = analisar_estrategia_momentum_calmo(historico_insuficiente, timestamp_qualquer)
    
    assert resultado['should_operate'] == False, "Não deveria ativar com histórico insuficiente"
    assert 'historial mínimo' in resultado['reason'], "Razão incorreta para histórico insuficiente"
    
    print("✅ Teste PASSOU: Histórico insuficiente rejeitado corretamente")

def test_bot_name_update():
    """Testa se o nome do bot foi atualizado corretamente."""
    print("\n=== TESTE: Nome do Bot ===")
    
    assert 'll' in BOT_NAME.lower(), f"Nome do bot deveria conter 'll': {BOT_NAME}"
    
    print(f"✅ Teste PASSOU: Nome do bot atualizado: {BOT_NAME}")

def main():
    """Executa todos os testes."""
    print("INICIANDO TESTES DA ESTRATÉGIA LL SIMPLIFICADA")
    print("=" * 50)
    
    try:
        test_ll_pattern_detection()
        test_no_time_filters()
        test_minimum_history()
        test_bot_name_update()
        
        print("\n" + "=" * 50)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A estratégia LL simplificada está funcionando corretamente")
        print("✅ Filtros de horário foram removidos com sucesso")
        print("✅ Apenas o padrão LL é detectado")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()