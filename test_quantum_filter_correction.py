#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para validar a correção do filtro da estratégia Quantum+
Verifica se o filtro agora aceita 7 vitórias em 10 operações no curto prazo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import direto da função do arquivo radartunder1.5.py
import importlib.util
spec = importlib.util.spec_from_file_location("radartunder1_5", "radartunder1.5.py")
radartunder_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radartunder_module)
analisar_estrategia_quantum_plus = radartunder_module.analisar_estrategia_quantum_plus

def test_quantum_filter_correction():
    """
    Testa se o filtro corrigido aceita 7 vitórias em 10 operações
    """
    print("\n🧪 TESTE: Correção do Filtro Quantum+ - 7 vitórias em 10 operações")
    print("=" * 70)
    
    # Cenário 1: Gatilho LLL com 7 vitórias em 10 operações no curto prazo
    # Estrutura: [LLL] + [7W + 3L] + [8W + 12L] + [2W extras para atingir 35]
    historico_lll_7wins = (
        ['LOSS', 'LOSS', 'LOSS'] +  # Gatilho LLL (3 ops)
        ['WIN'] * 7 + ['LOSS'] * 3 +  # Curto prazo: 7 vitórias em 10 (10 ops)
        ['WIN'] * 8 + ['LOSS'] * 12 +  # Longo prazo: 8 vitórias em 20 (20 ops)
        ['WIN'] * 2  # Extras para atingir 35 operações (2 ops)
    )
    
    print(f"\n📊 Cenário 1 - Gatilho LLL com 7 vitórias no curto prazo:")
    print(f"   Gatilho (0-2): {' '.join(historico_lll_7wins[:3])}")
    print(f"   Curto prazo (3-12): {' '.join(historico_lll_7wins[3:13])} - {historico_lll_7wins[3:13].count('WIN')}/10 vitórias")
    print(f"   Longo prazo (13-32): {historico_lll_7wins[13:33].count('WIN')}/20 vitórias")
    
    resultado_1 = analisar_estrategia_quantum_plus(historico_lll_7wins)
    print(f"\n🎯 Resultado: {resultado_1['should_operate']}")
    print(f"📝 Razão: {resultado_1['reason']}")
    print(f"🔢 Confiança: {resultado_1['confidence']}%")
    
    if resultado_1['should_operate']:
        print("✅ SUCESSO: Filtro aceita 7 vitórias em 10 operações!")
    else:
        print("❌ FALHA: Filtro ainda rejeita 7 vitórias em 10 operações")
    
    # Cenário 2: Gatilho LLLW com 7 vitórias em 10 operações no curto prazo
    historico_lllw_7wins = (
        ['WIN', 'LOSS', 'LOSS', 'LOSS'] +  # Gatilho LLLW (4 ops)
        ['WIN'] * 7 + ['LOSS'] * 3 +  # Curto prazo: 7 vitórias em 10 (10 ops)
        ['WIN'] * 8 + ['LOSS'] * 12 +  # Longo prazo: 8 vitórias em 20 (20 ops)
        ['WIN'] * 1  # Extra para atingir 35 operações (1 op)
    )
    
    print(f"\n📊 Cenário 2 - Gatilho LLLW com 7 vitórias no curto prazo:")
    print(f"   Gatilho (0-3): {' '.join(historico_lllw_7wins[:4])}")
    print(f"   Curto prazo (4-13): {' '.join(historico_lllw_7wins[4:14])} - {historico_lllw_7wins[4:14].count('WIN')}/10 vitórias")
    print(f"   Longo prazo (14-33): {historico_lllw_7wins[14:34].count('WIN')}/20 vitórias")
    
    resultado_2 = analisar_estrategia_quantum_plus(historico_lllw_7wins)
    print(f"\n🎯 Resultado: {resultado_2['should_operate']}")
    print(f"📝 Razão: {resultado_2['reason']}")
    print(f"🔢 Confiança: {resultado_2['confidence']}%")
    
    if resultado_2['should_operate']:
        print("✅ SUCESSO: Filtro aceita 7 vitórias em 10 operações!")
    else:
        print("❌ FALHA: Filtro ainda rejeita 7 vitórias em 10 operações")
    
    # Cenário 3: Teste de limite - 8 vitórias (deve rejeitar)
    historico_lll_8wins = (
        ['LOSS', 'LOSS', 'LOSS'] +  # Gatilho LLL (3 ops)
        ['WIN'] * 8 + ['LOSS'] * 2 +  # Curto prazo: 8 vitórias em 10 (10 ops)
        ['WIN'] * 8 + ['LOSS'] * 12 +  # Longo prazo: 8 vitórias em 20 (20 ops)
        ['WIN'] * 2  # Extras para atingir 35 operações (2 ops)
    )
    
    print(f"\n📊 Cenário 3 - Teste de limite com 8 vitórias (deve rejeitar):")
    print(f"   Curto prazo (3-12): {historico_lll_8wins[3:13].count('WIN')}/10 vitórias")
    
    resultado_3 = analisar_estrategia_quantum_plus(historico_lll_8wins)
    print(f"\n🎯 Resultado: {resultado_3['should_operate']}")
    print(f"📝 Razão: {resultado_3['reason']}")
    
    if not resultado_3['should_operate']:
        print("✅ CORRETO: Filtro rejeita 8 vitórias (acima do limite)")
    else:
        print("⚠️ ATENÇÃO: Filtro aceita 8 vitórias (pode estar muito permissivo)")
    
    print("\n" + "=" * 70)
    print("📋 RESUMO DOS TESTES:")
    print(f"   Cenário 1 (LLL + 7 wins): {'✅ PASSOU' if resultado_1['should_operate'] else '❌ FALHOU'}")
    print(f"   Cenário 2 (LLLW + 7 wins): {'✅ PASSOU' if resultado_2['should_operate'] else '❌ FALHOU'}")
    print(f"   Cenário 3 (LLL + 8 wins): {'✅ CORRETO' if not resultado_3['should_operate'] else '⚠️ PERMISSIVO'}")
    
    return resultado_1['should_operate'] and resultado_2['should_operate']

if __name__ == "__main__":
    try:
        sucesso = test_quantum_filter_correction()
        if sucesso:
            print("\n🎉 CORREÇÃO VALIDADA: Filtro Quantum+ agora aceita 7 vitórias em 10 operações!")
        else:
            print("\n❌ CORREÇÃO FALHOU: Filtro ainda não aceita 7 vitórias em 10 operações")
    except Exception as e:
        print(f"\n💥 ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()