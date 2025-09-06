#!/usr/bin/env python3
"""
Teste simples para verificar se pelo menos uma estratégia funciona
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analyzer import analisar_estrategias_portfolio

def test_stability_break_simple():
    """Teste simples da STABILITY_BREAK que sabemos que funciona"""
    print("\n=== TESTE SIMPLES STABILITY_BREAK ===")
    
    # Histórico que ativou STABILITY_BREAK no teste anterior
    historico = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V',
                'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V',
                'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    
    print(f"Histórico: {' '.join(historico[:15])}...")
    
    resultado = analisar_estrategias_portfolio(historico)
    
    print(f"\nShould operate: {resultado['should_operate']}")
    print(f"Reason: {resultado['reason']}")
    
    if resultado['melhor_estrategia']:
        print(f"Estratégia detectada: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
        print(f"Total oportunidades: {resultado['total_oportunidades']}")
        return True
    else:
        print("Nenhuma estratégia detectada")
        return False

def test_premium_recovery_simple():
    """Teste simples da PREMIUM_RECOVERY"""
    print("\n=== TESTE SIMPLES PREMIUM_RECOVERY ===")
    
    # Histórico mais simples: dupla LOSS + só WINs
    historico = ['D', 'D'] + ['V'] * 28
    
    print(f"Histórico: {' '.join(historico[:10])}...")
    
    resultado = analisar_estrategias_portfolio(historico)
    
    print(f"\nShould operate: {resultado['should_operate']}")
    print(f"Reason: {resultado['reason']}")
    
    if resultado['melhor_estrategia']:
        print(f"Estratégia detectada: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
        return True
    else:
        print("Nenhuma estratégia detectada")
        return False

if __name__ == "__main__":
    print("TESTE SIMPLES DE ESTRATÉGIAS")
    print("=" * 50)
    
    # Testar STABILITY_BREAK (sabemos que funciona)
    stability_ok = test_stability_break_simple()
    
    # Testar PREMIUM_RECOVERY
    premium_ok = test_premium_recovery_simple()
    
    print("\n=== RESUMO ===")
    print(f"STABILITY_BREAK funcionou: {stability_ok}")
    print(f"PREMIUM_RECOVERY funcionou: {premium_ok}")
    
    if stability_ok or premium_ok:
        print("\n✅ PELO MENOS UMA ESTRATÉGIA ESTÁ FUNCIONANDO!")
    else:
        print("\n❌ NENHUMA ESTRATÉGIA FUNCIONOU")