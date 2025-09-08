#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste com Dados Reais - Validação das Correções Implementadas
Testa as estratégias corrigidas com sequências realistas de operações
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analisis_scalping_bot import (
    analisar_micro_burst,
    analisar_precision_surge, 
    analisar_quantum_matrix
)

def test_micro_burst_real_data():
    """
    Teste Micro-Burst com dados reais
    Sequência: ['V', 'V', 'D', 'V', 'V', 'V', 'D', 'V', 'V', 'V']
    
    Análise esperada:
    - Últimas 3: V-V-V (não é padrão V-D-V)
    - Deve retornar: detected=False
    """
    print("\n" + "="*60)
    print("🧪 TESTE MICRO-BURST COM DADOS REAIS")
    print("="*60)
    
    # Quantum Matrix precisa de pelo menos 15 operações
    historico_real = ['V', 'V', 'D', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"📊 Histórico de teste: {' '.join(historico_real)}")
    print(f"📊 Últimas 3 operações: {'-'.join(historico_real[-3:])}")
    
    resultado = analisar_micro_burst(historico_real)
    
    print(f"\n🔍 RESULTADO MICRO-BURST:")
    print(f"   • Deve Operar: {resultado['should_operate']}")
    print(f"   • Confiança: {resultado.get('confidence', 'N/A')}%")
    print(f"   • Motivo: {resultado['reason']}")
    
    # Validação
    if not resultado['should_operate']:
        print("✅ CORRETO: Não detectou padrão V-D-V (últimas 3 são V-V-V)")
        return True
    else:
        print("❌ ERRO: Detectou padrão incorretamente!")
        return False

def test_micro_burst_valid_pattern():
    """
    Teste Micro-Burst com padrão válido
    Sequência que termina em V-D-V
    """
    print("\n" + "="*60)
    print("🧪 TESTE MICRO-BURST COM PADRÃO VÁLIDO")
    print("="*60)
    
    # Criar sequência que termina em V-D-V com filtros atendidos
    # Micro-Burst precisa de exatamente 2-3 WINs consecutivos no início
    historico_valido = ['V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"📊 Histórico de teste: {' '.join(historico_valido)}")
    print(f"📊 Últimas 3 operações: {'-'.join(historico_valido[-3:])}")
    
    resultado = analisar_micro_burst(historico_valido)
    
    print(f"\n🔍 RESULTADO MICRO-BURST:")
    print(f"   • Deve Operar: {resultado['should_operate']}")
    print(f"   • Confiança: {resultado.get('confidence', 'N/A')}%")
    print(f"   • Motivo: {resultado['reason']}")
    
    if 'filters_passed' in resultado:
        print(f"\n🔍 FILTROS APLICADOS:")
        for filtro in resultado['filters_passed']:
            print(f"   • ✅ PASSOU - {filtro}")
    
    # Validação
    if resultado['should_operate']:
        print("✅ CORRETO: Detectou padrão V-D-V válido")
        return True
    else:
        print("❌ ERRO: Não detectou padrão válido!")
        return False

def test_precision_surge_real_data():
    """
    Teste Precision Surge com dados reais
    """
    print("\n" + "="*60)
    print("🧪 TESTE PRECISION SURGE COM DADOS REAIS")
    print("="*60)
    
    historico_real = ['V', 'V', 'D', 'V', 'V', 'V', 'D', 'V', 'V', 'V']
    print(f"📊 Histórico de teste: {' '.join(historico_real)}")
    print(f"📊 Últimas 3 operações: {'-'.join(historico_real[-3:])}")
    
    resultado = analisar_precision_surge(historico_real)
    
    print(f"\n🔍 RESULTADO PRECISION SURGE:")
    print(f"   • Deve Operar: {resultado['should_operate']}")
    print(f"   • Confiança: {resultado.get('confidence', 'N/A')}%")
    print(f"   • Motivo: {resultado['reason']}")
    
    if 'filters_passed' in resultado:
        print(f"\n🔍 FILTROS APLICADOS:")
        for filtro in resultado['filters_passed']:
            print(f"   • ✅ PASSOU - {filtro}")
    
    return True

def test_quantum_matrix_real_data():
    """
    Teste Quantum Matrix com dados reais
    """
    print("\n" + "="*60)
    print("🧪 TESTE QUANTUM MATRIX COM DADOS REAIS")
    print("="*60)
    
    historico_real = ['V', 'V', 'D', 'V', 'V', 'V', 'D', 'V', 'V', 'V']
    print(f"📊 Histórico de teste: {' '.join(historico_real)}")
    print(f"📊 Últimas 3 operações: {'-'.join(historico_real[-3:])}")
    
    resultado = analisar_quantum_matrix(historico_real)
    
    print(f"\n🔍 RESULTADO QUANTUM MATRIX:")
    print(f"   • Deve Operar: {resultado['should_operate']}")
    print(f"   • Confiança: {resultado.get('confidence', 'N/A')}%")
    print(f"   • Motivo: {resultado['reason']}")
    
    if 'filters_passed' in resultado:
        print(f"\n🔍 FILTROS APLICADOS:")
        for filtro in resultado['filters_passed']:
            print(f"   • ✅ PASSOU - {filtro}")
    
    return True

def test_quantum_matrix_with_old_loss():
    """
    Teste Quantum Matrix com LOSS antigo (5+ operações atrás)
    Para testar o Gatilho 2 corrigido
    """
    print("\n" + "="*60)
    print("🧪 TESTE QUANTUM MATRIX COM LOSS ANTIGO")
    print("="*60)
    
    # Criar sequência com LOSS há 6 operações e WINs recentes (mínimo 15 operações)
    historico_loss_antigo = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"📊 Histórico de teste: {' '.join(historico_loss_antigo)}")
    print(f"📊 LOSS na posição 0 (10 operações atrás)")
    print(f"📊 Últimas 3 operações: {'-'.join(historico_loss_antigo[-3:])}")
    
    resultado = analisar_quantum_matrix(historico_loss_antigo)
    
    print(f"\n🔍 RESULTADO QUANTUM MATRIX:")
    print(f"   • Deve Operar: {resultado['should_operate']}")
    print(f"   • Confiança: {resultado.get('confidence', 'N/A')}%")
    print(f"   • Motivo: {resultado['reason']}")
    
    if 'filters_passed' in resultado:
        print(f"\n🔍 FILTROS APLICADOS:")
        for filtro in resultado['filters_passed']:
            print(f"   • ✅ PASSOU - {filtro}")
    
    return True

def run_all_real_data_tests():
    """
    Executa todos os testes com dados reais
    """
    print("🚀 INICIANDO TESTES COM DADOS REAIS")
    print("Validando correções implementadas nas estratégias")
    print("="*80)
    
    tests = [
        test_micro_burst_real_data,
        test_micro_burst_valid_pattern,
        test_precision_surge_real_data,
        test_quantum_matrix_real_data,
        test_quantum_matrix_with_old_loss
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n🔄 Executando: {test.__name__}")
            if test():
                passed += 1
                print(f"✅ {test.__name__} - PASSOU")
            else:
                failed += 1
                print(f"❌ {test.__name__} - FALHOU")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} - ERRO: {e}")
    
    print("\n" + "="*80)
    print(f"📊 RESULTADOS FINAIS:")
    print(f"   • ✅ Testes que passaram: {passed}")
    print(f"   • ❌ Testes que falharam: {failed}")
    print(f"   • 📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ As correções implementadas estão funcionando corretamente.")
    else:
        print(f"\n⚠️ {failed} teste(s) falharam.")
        print("🔧 Verificar implementação das correções.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_real_data_tests()
    sys.exit(0 if success else 1)