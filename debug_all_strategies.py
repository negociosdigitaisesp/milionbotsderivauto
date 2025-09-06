#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test all strategies individually with DV pattern
"""

import sys
sys.path.append('.')
import radar_analyzer

# Test history: DV pattern + 20 consecutive wins
historico = ['D', 'V'] + ['V'] * 20

print("=== TESTING ALL STRATEGIES WITH DV PATTERN ===")
print(f"History: {' '.join(historico[:10])}... (total: {len(historico)})")
print(f"Pattern: D at pos 0, V at pos 1")
print()

# Get the strategy functions from the analyzer
strategy_functions = {
    'PREMIUM_RECOVERY': 'estrategia_premium_recovery',
    'MOMENTUM_CONTINUATION': 'estrategia_momentum_continuation', 
    'VOLATILITY_BREAK': 'estrategia_volatility_break',
    'CYCLE_TRANSITION': 'estrategia_cycle_transition',
    'FIBONACCI_RECOVERY': 'estrategia_fibonacci_recovery'
}

for strategy_name, func_name in strategy_functions.items():
    print(f"\n--- Testing {strategy_name} ---")
    try:
        if hasattr(radar_analyzer, func_name):
            func = getattr(radar_analyzer, func_name)
            result = func(historico)
            print(f"Result: {result}")
        else:
            print(f"Function {func_name} not found")
    except Exception as e:
        print(f"Error: {e}")

print("\n=== FULL PORTFOLIO ANALYSIS ===")
try:
    resultado = radar_analyzer.analisar_estrategias_portfolio(historico)
    print(f"Should operate: {resultado.get('should_operate')}")
    print(f"Best strategy: {resultado.get('melhor_estrategia', {}).get('strategy')}")
    print(f"Available strategies: {[s.get('strategy') for s in resultado.get('estrategias_disponiveis', [])]}")
except Exception as e:
    print(f"Error in full analysis: {e}")