#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the entire module and access the function
import radar_analyzer

# Test history: DV pattern to avoid PREMIUM_RECOVERY, then 20 consecutive wins
# PREMIUM_RECOVERY precisa DD (posições 0-1), mas temos DV
# CYCLE_TRANSITION precisa LOSS isolada em posição 0 (D + não-D)
historico = ['D', 'V'] + ['V'] * 20

print("=== DIRECT CYCLE_TRANSITION TEST ===")
print(f"History: {historico[:10]}... (total: {len(historico)})")
print(f"Position: {((len(historico)-1) % 20) + 1}")
print(f"Last 6: {historico[-6:]} - WINs: {historico[-6:].count('V')}")
print(f"Last 12: {historico[-12:]} - LOSSes: {historico[-12:].count('D')}")
print()

try:
    # Access the function from the module
    result = radar_analyzer.estrategia_cycle_transition(historico)
    print(f"CYCLE_TRANSITION result: {result}")
except Exception as e:
    print(f"Error calling CYCLE_TRANSITION: {e}")
    import traceback
    traceback.print_exc()

print()
print("=== FULL PORTFOLIO ANALYSIS ===")
try:
    full_result = radar_analyzer.analisar_estrategias_portfolio(historico)
    print(f"Full analysis result: {full_result}")
except Exception as e:
    print(f"Error in full analysis: {e}")
    import traceback
    traceback.print_exc()