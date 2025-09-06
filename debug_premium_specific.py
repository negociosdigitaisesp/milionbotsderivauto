#!/usr/bin/env python3
"""
Debug específico para PREMIUM_RECOVERY
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from radar_analyzer import analisar_estrategias_portfolio

def debug_premium_recovery():
    """
    Debug específico da PREMIUM_RECOVERY
    """
    print("=== DEBUG PREMIUM_RECOVERY ===")
    
    # Histórico mais simples: dupla LOSS + só WINs (atende todos os filtros)
    historico = ['D', 'D'] + ['V'] * 28
    
    print(f"Histórico total: {len(historico)} operações")
    print(f"Primeiras 10: {' '.join(historico[:10])}")
    print(f"Dupla LOSS: {historico[0]} {historico[1]}")
    print(f"Posições 2-8 (7 ops): {' '.join(historico[2:9])}")
    print(f"WINs nas posições 2-8: {historico[2:9].count('V')}/7")
    print(f"LOSSes nas últimas 20: {historico[:20].count('D')}/20")
    print(f"LOSSes nas posições 2-6: {historico[2:7].count('D')}/5")
    
    print("\nChamando analisar_estrategias_portfolio...")
    resultado = analisar_estrategias_portfolio(historico)
    
    print(f"\nResultado:")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    print(f"Reason: {resultado.get('reason', 'N/A')}")
    
    if resultado.get('melhor_estrategia'):
        print(f"Melhor estratégia: {resultado['melhor_estrategia']['strategy']}")
        print(f"Confiança: {resultado['melhor_estrategia']['confidence']}%")
    else:
        print("Nenhuma estratégia detectada")
    
    print(f"\nEstratégias disponíveis: {len(resultado.get('estrategias_disponiveis', []))}")
    for i, estrategia in enumerate(resultado.get('estrategias_disponiveis', [])):
        print(f"  {i+1}. {estrategia.get('strategy', 'N/A')} - {estrategia.get('confidence', 0)}%")
    
    # Verificar se PREMIUM_RECOVERY está na lista
    premium_found = any(
        estrategia.get('strategy') == 'PREMIUM_RECOVERY' 
        for estrategia in resultado.get('estrategias_disponiveis', [])
    )
    
    print(f"\nPREMIUM_RECOVERY encontrada: {premium_found}")
    
    return resultado

if __name__ == "__main__":
    debug_premium_recovery()