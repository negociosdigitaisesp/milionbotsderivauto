#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste limpo para ver apenas os resultados das estratégias
"""

import sys
import os
import logging

# Desabilitar logs de debug
logging.getLogger().setLevel(logging.CRITICAL)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from radar_analyzer import analisar_estrategias_portfolio

def test_strategies_clean():
    """
    Testa estratégias sem logs de debug
    """
    print("TESTE LIMPO DAS ESTRATÉGIAS")
    print("="*50)
    
    estrategias_testadas = [
        {
            'nome': 'PREMIUM_RECOVERY',
            'historico': ['D', 'D'] + ['V'] * 28
        },
        {
            'nome': 'MOMENTUM_SHIFT', 
            'historico': ['D'] + ['V', 'V', 'V', 'V', 'V', 'V', 'D'] + ['V', 'D', 'V', 'D', 'V', 'D', 'V', 'D'] + ['V'] * 14
        },
        {
            'nome': 'CYCLE_TRANSITION',
            'historico': ['V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D']
        },
        {
            'nome': 'FIBONACCI_RECOVERY',
            'historico': ['D', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
        },
        {
            'nome': 'STABILITY_BREAK',
            'historico': ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
        }
    ]
    
    resultados = []
    
    for estrategia in estrategias_testadas:
        print(f"\nTestando {estrategia['nome']}...")
        resultado = analisar_estrategias_portfolio(estrategia['historico'])
        
        funcionou = resultado.get('should_operate', False)
        estrategia_detectada = None
        confianca = 0
        
        if funcionou and resultado.get('melhor_estrategia'):
            estrategia_detectada = resultado['melhor_estrategia']['strategy']
            confianca = resultado['melhor_estrategia']['confidence']
        
        resultados.append({
            'nome': estrategia['nome'],
            'funcionou': funcionou,
            'estrategia_detectada': estrategia_detectada,
            'confianca': confianca
        })
        
        if funcionou:
            print(f"✓ {estrategia['nome']}: FUNCIONOU - {estrategia_detectada} ({confianca}%)")
        else:
            print(f"✗ {estrategia['nome']}: FALHOU")
    
    print("\n" + "="*50)
    print("RESUMO DOS RESULTADOS")
    print("="*50)
    
    funcionando = 0
    for resultado in resultados:
        status = "✓ FUNCIONOU" if resultado['funcionou'] else "✗ FALHOU"
        print(f"{resultado['nome']}: {status}")
        if resultado['funcionou']:
            funcionando += 1
    
    print(f"\nTotal funcionando: {funcionando}/5")
    
    if funcionando >= 4:
        print("🎉 SISTEMA APROVADO!")
    else:
        print("❌ SISTEMA REPROVADO")

if __name__ == "__main__":
    test_strategies_clean()