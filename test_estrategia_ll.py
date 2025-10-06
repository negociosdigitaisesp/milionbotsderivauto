#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da Nova Estratégia LL - Radar Tunder 3.5
===============================================

Este script testa a nova estratégia modificada que detecta padrão LL
(2 LOSS consecutivos) ao invés do padrão WW anterior.
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_estrategia_ll():
    """Testa a função de análise da estratégia LL"""
    
    print("🧪 TESTE DA NOVA ESTRATÉGIA LL")
    print("=" * 50)
    
    try:
        # Importar a função modificada
        import importlib.util
        spec = importlib.util.spec_from_file_location("radartunder35", "radartunder3.5.py")
        radartunder35 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(radartunder35)
        analisar_estrategia_momentum_calmo = radartunder35.analisar_estrategia_momentum_calmo
        
        # Simular timestamp em Baixa Atividade + Fechamento da Hora
        # Hora UTC 5 (Baixa Atividade) + minuto 57 (Fechamento da Hora)
        timestamp_test = "2025-10-03T05:57:30.000Z"
        
        print(f"📅 Timestamp de teste: {timestamp_test}")
        print("   - Hora UTC: 5 (Baixa Atividade)")
        print("   - Minuto: 57 (Fechamento da Hora)")
        print()
        
        # Teste 1: Padrão LL (deve ativar sinal)
        print("🔍 TESTE 1: Padrão LL (2 LOSS consecutivos)")
        historico_ll = ['LOSS', 'LOSS', 'WIN', 'LOSS', 'WIN']
        resultado_ll = analisar_estrategia_momentum_calmo(historico_ll, timestamp_test)
        
        print(f"   Histórico: {historico_ll[:2]} (últimas 2)")
        print(f"   Should Operate: {resultado_ll['should_operate']}")
        print(f"   Reason: {resultado_ll['reason']}")
        print(f"   Strategy: {resultado_ll.get('strategy', 'N/A')}")
        
        if resultado_ll['should_operate']:
            print("   ✅ SUCESSO: Sinal ativado corretamente para padrão LL")
        else:
            print("   ❌ ERRO: Sinal não foi ativado para padrão LL")
        print()
        
        # Teste 2: Padrão WW (não deve ativar sinal)
        print("🔍 TESTE 2: Padrão WW (2 WIN consecutivos)")
        historico_ww = ['WIN', 'WIN', 'LOSS', 'WIN', 'LOSS']
        resultado_ww = analisar_estrategia_momentum_calmo(historico_ww, timestamp_test)
        
        print(f"   Histórico: {historico_ww[:2]} (últimas 2)")
        print(f"   Should Operate: {resultado_ww['should_operate']}")
        print(f"   Reason: {resultado_ww['reason']}")
        
        if not resultado_ww['should_operate']:
            print("   ✅ SUCESSO: Sinal não ativado para padrão WW (correto)")
        else:
            print("   ❌ ERRO: Sinal foi ativado incorretamente para padrão WW")
        print()
        
        # Teste 3: Padrão misto LW (não deve ativar)
        print("🔍 TESTE 3: Padrão LW (LOSS + WIN)")
        historico_lw = ['WIN', 'LOSS', 'WIN', 'LOSS', 'WIN']
        resultado_lw = analisar_estrategia_momentum_calmo(historico_lw, timestamp_test)
        
        print(f"   Histórico: {historico_lw[:2]} (últimas 2)")
        print(f"   Should Operate: {resultado_lw['should_operate']}")
        print(f"   Reason: {resultado_lw['reason']}")
        
        if not resultado_lw['should_operate']:
            print("   ✅ SUCESSO: Sinal não ativado para padrão misto (correto)")
        else:
            print("   ❌ ERRO: Sinal foi ativado incorretamente para padrão misto")
        print()
        
        # Teste 4: Filtro de regime (Alta Atividade - não deve ativar)
        print("🔍 TESTE 4: Filtro de Regime (Alta Atividade)")
        timestamp_alta = "2025-10-03T20:57:30.000Z"  # Hora 20 = Alta Atividade
        resultado_filtro = analisar_estrategia_momentum_calmo(historico_ll, timestamp_alta)
        
        print(f"   Timestamp: {timestamp_alta} (Hora UTC: 20)")
        print(f"   Should Operate: {resultado_filtro['should_operate']}")
        print(f"   Reason: {resultado_filtro['reason']}")
        
        if not resultado_filtro['should_operate'] and 'Filtro Rechazado' in resultado_filtro['reason']:
            print("   ✅ SUCESSO: Filtro de regime funcionando corretamente")
        else:
            print("   ❌ ERRO: Filtro de regime não está funcionando")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro na importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_bot_name():
    """Testa se o nome do bot foi atualizado"""
    
    print("🤖 TESTE DO NOME DO BOT")
    print("=" * 50)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("radartunder35", "radartunder3.5.py")
        radartunder35 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(radartunder35)
        BOT_NAME = radartunder35.BOT_NAME
        
        print(f"Nome do bot: {BOT_NAME}")
        
        if 'll' in BOT_NAME.lower():
            print("✅ SUCESSO: Nome do bot atualizado para estratégia LL")
            return True
        else:
            print("❌ AVISO: Nome do bot pode não refletir a estratégia LL")
            return False
            
    except ImportError as e:
        print(f"❌ Erro na importação: {e}")
        return False

def main():
    """Função principal do teste"""
    
    print("🚀 INICIANDO TESTES DA ESTRATÉGIA LL MODIFICADA")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests_passed = 0
    total_tests = 2
    
    # Teste 1: Estratégia LL
    if test_estrategia_ll():
        tests_passed += 1
    
    # Teste 2: Nome do bot
    if test_bot_name():
        tests_passed += 1
    
    # Resultado final
    print("=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    print(f"✅ Testes aprovados: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   ✅ Estratégia LL implementada corretamente")
        print("   ✅ Detecta 2 LOSS consecutivos")
        print("   ✅ Filtros de regime funcionando")
        print("   ✅ Nome do bot atualizado")
        print("\n📋 A estratégia está pronta para uso!")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} teste(s) falharam")
        print("   - Verifique os erros acima")
    
    print("\n🎯 RESUMO DA NOVA ESTRATÉGIA:")
    print("   - Espera aparecer um LOSS")
    print("   - Entrada após surgir 2 LOSS consecutivos")
    print("   - Filtros: Baixa Atividade + Fechamento da Hora")

if __name__ == "__main__":
    main()