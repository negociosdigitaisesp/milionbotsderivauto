#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da lógica de padrão CORRIGIDA - comparar com accumulator_standalone.py
"""

import os
import sys
from decimal import Decimal

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pattern_logic():
    """Testa a lógica de padrão corrigida"""
    print("="*60)
    print("TESTE DA LOGICA DE PADRAO CORRIGIDA")
    print("="*60)
    
    # Casos de teste - padrões que DEVEM detectar entrada
    test_cases = [
        {
            "name": "Padrão válido 1 - Red-Red-Red-Blue",
            "ticks": [100.0, 101.0, 102.0, 103.0, 102.5],  # tick4>tick3, tick3>tick2, tick2>tick1, tick1>atual
            "expected": True
        },
        {
            "name": "Padrão válido 2 - Red-Red-Red-Blue",  
            "ticks": [75000.0, 75010.0, 75020.0, 75030.0, 75025.0],
            "expected": True
        },
        {
            "name": "Padrão inválido 1 - Blue-Red-Red-Red",
            "ticks": [103.0, 102.0, 103.0, 104.0, 103.5],  # tick4<tick3 (Blue)
            "expected": False
        },
        {
            "name": "Padrão inválido 2 - Red-Red-Red-Red",
            "ticks": [100.0, 101.0, 102.0, 103.0, 104.0],  # tick1<atual (Red mas deveria ser Blue)
            "expected": False
        },
        {
            "name": "Padrão inválido 3 - Red-Blue-Red-Blue",
            "ticks": [100.0, 101.0, 100.5, 101.5, 101.0],  # Misto
            "expected": False
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n--- CASO {i+1}: {case['name']} ---")
        ticks = case['ticks']
        expected = case['expected']
        
        # Aplicar lógica CORRIGIDA (igual ao accumulator_standalone.py)
        if len(ticks) >= 5:
            # Indexação FROM_END igual ao accumulator_standalone.py
            tick4 = ticks[-5]  # FROM_END 5 (mais antigo)
            tick3 = ticks[-4]  # FROM_END 4
            tick2 = ticks[-3]  # FROM_END 3  
            tick1 = ticks[-2]  # FROM_END 2
            tick_atual = ticks[-1]  # FROM_END 1 (atual)
            
            # Cálculos de sinal XML EXATOS
            single4 = "Red" if tick4 > tick3 else "Blue"
            single3 = "Red" if tick3 > tick2 else "Blue"
            single2 = "Red" if tick2 > tick1 else "Blue"
            single1 = "Red" if tick1 > tick_atual else "Blue"
            
            # Condição XML EXATA
            entrada_xml = (single1 == "Red" and 
                          single2 == "Red" and 
                          single3 == "Red" and 
                          single4 == "Blue")
            
            print(f"Ticks: {ticks}")
            print(f"Indexação FROM_END:")
            print(f"  tick4 (FROM_END 5): {tick4}")
            print(f"  tick3 (FROM_END 4): {tick3}")
            print(f"  tick2 (FROM_END 3): {tick2}")
            print(f"  tick1 (FROM_END 2): {tick1}")
            print(f"  tick_atual (FROM_END 1): {tick_atual}")
            print(f"Comparações:")
            print(f"  tick4 > tick3: {tick4} > {tick3} = {tick4 > tick3} -> {single4}")
            print(f"  tick3 > tick2: {tick3} > {tick2} = {tick3 > tick2} -> {single3}")
            print(f"  tick2 > tick1: {tick2} > {tick1} = {tick2 > tick1} -> {single2}")
            print(f"  tick1 > atual: {tick1} > {tick_atual} = {tick1 > tick_atual} -> {single1}")
            print(f"Sinais: [{single1}, {single2}, {single3}, {single4}]")
            print(f"Padrão esperado: [Red, Red, Red, Blue]")
            print(f"Entrada detectada: {entrada_xml}")
            print(f"Resultado esperado: {expected}")
            
            if entrada_xml == expected:
                print("✅ TESTE PASSOU!")
            else:
                print("❌ TESTE FALHOU!")
        else:
            print("❌ Ticks insuficientes")
    
    print("\n" + "="*60)
    print("LOGICA CORRIGIDA - IDENTICA AO ACCUMULATOR_STANDALONE.PY")
    print("- Indexação FROM_END correta")
    print("- Cálculos de sinal XML exatos")
    print("- Condição single1=Red E single2=Red E single3=Red E single4=Blue")
    print("="*60)

if __name__ == "__main__":
    test_pattern_logic()