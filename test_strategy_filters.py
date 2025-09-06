#!/usr/bin/env python3
"""
Teste específico dos filtros de cada estratégia
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# Desabilitar logs de debug
logging.getLogger().setLevel(logging.CRITICAL)

# Debug: Force complete fresh import
import importlib
if 'radar_analyzer' in sys.modules:
    del sys.modules['radar_analyzer']
    
import radar_analyzer
from radar_analyzer import analisar_estrategias_portfolio

def test_premium_recovery_filters():
    """
    Testa especificamente os filtros da PREMIUM_RECOVERY
    """
    print("\n=== TESTE FILTROS PREMIUM_RECOVERY ===")
    
    # CORREÇÃO 5: Resetar estado de persistência antes do teste
    radar_analyzer.estrategia_ativa_persistente = None
    radar_analyzer.timestamp_estrategia_detectada = None
    radar_analyzer.operations_after_pattern_global = 0
    # Também usar a função oficial de reset como backup
    radar_analyzer.reset_persistence_state_safe()
    print("Estado de persistência resetado para teste limpo (manual + oficial)")
    
    # CORREÇÃO 3: Histórico adequado para PREMIUM_RECOVERY (30+ operações)
    # Filtro 1: <=6 WINs nas posições 2-8 (7 operações) - exatamente 6 WINs
    # Filtro 2: <=3 LOSSes nas últimas 20 posições (posições 0-19)
    # Filtro 3: 0 LOSSes nas posições 2-6 (5 operações)
    # SOLUÇÃO: DD + 6 WINs em 7 posições (2-8) + resto com alta taxa de WIN
    # Posições 0-1: DD, 2-7: VVVVVV, 8: D, 9+: VVVVVVVVVVVVVVVVVVVVV
    # Filtro 1: 6 WINs nas posições 2-8 (6V+1D=6 WINs <=6) ✓
    # Filtro 2: 3 LOSSes nas posições 0-19 (DD+D=3 LOSSes <=3) ✓
    # Filtro 3: 0 LOSSes nas posições 2-6 (VVVVV=0 LOSSes) ✓
    historico = ['D', 'D'] + ['V'] * 6 + ['D'] + ['V'] * 21  # 30 operações total
    
    print(f"Histórico: {' '.join(historico[:10])}...")
    print(f"Dupla LOSS: {historico[0]} {historico[1]}")
    print(f"Posições 2-8 (7 ops): {' '.join(historico[2:9])}")
    print(f"WINs nas posições 2-8: {historico[2:9].count('V')}/7 (filtro rejeita se >=7)")
    print(f"LOSSes nas últimas 20: {historico[:20].count('D')}/20 (filtro rejeita se >=3)")
    print(f"LOSSes nas posições 2-6: {historico[2:7].count('D')}/5 (filtro rejeita se >0)")
    
    resultado = analisar_estrategias_portfolio(historico)
    
    premium_found = any(
        estrategia.get('strategy') == 'PREMIUM_RECOVERY' 
        for estrategia in resultado.get('estrategias_disponiveis', [])
    )
    
    print(f"\nPREMIUM_RECOVERY detectada: {premium_found}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    
    return premium_found

def test_momentum_shift_filters():
    """
    Testa especificamente os filtros da MOMENTUM_SHIFT
    """
    print("\n=== TESTE FILTROS MOMENTUM_SHIFT ===")
    
    # CORREÇÃO 5: Resetar estado de persistência antes do teste
    radar_analyzer.estrategia_ativa_persistente = None
    radar_analyzer.timestamp_estrategia_detectada = None
    radar_analyzer.operations_after_pattern_global = 0
    # Também usar a função oficial de reset como backup
    radar_analyzer.reset_persistence_state_safe()
    print("Estado de persistência resetado para teste limpo (manual + oficial)")
    
    # CORREÇÃO 3: Histórico adequado para MOMENTUM_SHIFT (30+ operações)
    # Filtro 1: Baseline (janela antiga) ≤60%
    # Filtro 2: Melhoria ≥25%
    # Filtro 3: Win rate recente ≥80%
    # Filtro 4: ≤1 LOSS nas últimas 10 operações (excluindo atual)
    # SOLUÇÃO: Baseline baixo + melhoria significativa + LOSS isolada
    # Posições: 0:D, 1-10:VVVVVVVVVD (9V+1D=90%), 11-16:DDDDVV (2V+4D=33.3%), 17+:VVVVVVVVVVVVVV
    # Janela recente (1-8): 8V = 100% ≥80% ✓
    # Janela antiga (9-16): 1V+1D+4D+2V = 3V+5D = 37.5% ≤60% ✓
    # Melhoria: 100% - 37.5% = 62.5% ≥25% ✓
    # Últimas 10 (1-10): 9V+1D = 1 LOSS ≤1 ✓
    historico = ['D'] + ['V'] * 9 + ['D'] + ['D', 'D', 'D', 'D', 'V', 'V'] + ['V'] * 14  # 32 operações total
    
    print(f"Histórico: {' '.join(historico[:15])}...")
    print(f"LOSS isolada: {historico[0]}")
    print(f"Janela recente (1-8): {' '.join(historico[1:9])} - WR: {historico[1:9].count('V')/8*100:.1f}%")
    print(f"Janela antiga (9-16): {' '.join(historico[9:17])} - WR: {historico[9:17].count('V')/8*100:.1f}%")
    print(f"Melhoria: {historico[1:9].count('V')/8*100:.1f}% - {historico[9:17].count('V')/8*100:.1f}% = {(historico[1:9].count('V')/8 - historico[9:17].count('V')/8)*100:.1f}%")
    print(f"Últimas 10 antes da LOSS (1-10): {' '.join(historico[1:11])} - LOSSes: {historico[1:11].count('D')}")
    

    
    resultado = analisar_estrategias_portfolio(historico)
    
    momentum_found = any(
        estrategia.get('strategy') == 'MOMENTUM_SHIFT' 
        for estrategia in resultado.get('estrategias_disponiveis', [])
    )
    
    print(f"\nMOMENTUM_SHIFT detectada: {momentum_found}")
    print(f"Should operate: {resultado.get('should_operate', False)}")
    
    return momentum_found

def test_cycle_transition_filters():
    """
    Testa especificamente os filtros da CYCLE_TRANSITION
    FILTROS:
    1. Posição 1-5 no ciclo (baseado no tamanho do histórico)
    2. ≥5 WINs nas últimas 6 operações antes da LOSS
    3. ≤1 LOSS nas últimas 12 operações antes da LOSS
    4. ≥75% win rate no ciclo anterior (20 operações)
    
    SOLUÇÃO: 21 operações = posição 1 no ciclo
    Últimas 6: VVVVVV (6 WINs)
    Últimas 12: VVVVVVVVVVVV (0 LOSSes)
    Ciclo anterior (20): 16V + 4D = 80% win rate
    """
    print("\n=== TESTE FILTROS CYCLE_TRANSITION ===")
    
    # CORREÇÃO 5: Resetar estado de persistência antes do teste
    radar_analyzer.estrategia_ativa_persistente = None
    radar_analyzer.timestamp_estrategia_detectada = None
    radar_analyzer.operations_after_pattern_global = 0
    # Também usar a função oficial de reset como backup
    radar_analyzer.reset_persistence_state_safe()
    print("Estado de persistência resetado para teste limpo (manual + oficial)")
    
    # CORREÇÃO 3: Histórico adequado para CYCLE_TRANSITION (21 operações = posição 1 no ciclo)
    # CYCLE_TRANSITION: posição 1-5, ≥5 WINs nas últimas 6, ≤1 LOSS nas últimas 12, ≥75% win rate anterior
    # MOMENTUM_SHIFT: baseline ≤60%, melhoria ≥25%, recente ≥80%, ≤1 LOSS nas últimas 10
    # PREMIUM_RECOVERY: dupla LOSS (DD) nas posições 0-1
    # 
    # SOLUÇÃO: LOSS isolada na posição 1 do ciclo (21 operações)
    # Posição 0: D (LOSS isolada)
    # Posições 1-20: VVVVVVVVVVVVVVVVVVVV (20 WINs consecutivos)
    # Total: 21 operações = posição 1 no ciclo ((21-1) % 20) + 1 = 1 ✓
    # CYCLE_TRANSITION: LOSS isolada em posição 0, posição 1 no ciclo ✓
    # PREMIUM_RECOVERY: Precisa DD (posições 0-1), mas temos DV ✗
    # Últimas 6: VVVVVV = 6 WINs ≥5 ✓
    # Últimas 12: VVVVVVVVVVVV = 0 LOSSes ≤1 ✓
    # Win rate anterior (20 ops): 20/20 = 100% ≥75% ✓
    historico = ['D'] + ['V'] * 20  # 21 operações total, posição 1 no ciclo
    
    print(f"Histórico: {' '.join(historico[:10])}... ({len(historico)} operações total)")
    print(f"Posição no ciclo: {((len(historico)-1) % 20) + 1}/20")
    print(f"Últimas 6 antes da LOSS: {' '.join(historico[1:7])} - WINs: {historico[1:7].count('V')}/6")
    print(f"Últimas 12 antes da LOSS: {' '.join(historico[1:13])} - LOSSes: {historico[1:13].count('D')}/12")
    print(f"Ciclo anterior (20 ops): WINs: {historico[1:21].count('V')}/20 = {(historico[1:21].count('V')/20)*100:.1f}%")
    print(f"Win rate recente MOMENTUM_SHIFT (1-8): {historico[1:9].count('V')}/8 = {(historico[1:9].count('V')/8)*100:.1f}% (deve ser <80% para falhar)")
    
    print(f"\nChamando analisar_estrategias_portfolio com {len(historico)} operações...")
    print(f"\n=== DEBUG CYCLE_TRANSITION TEST ===")
    print(f"History being tested: {historico[:5]}... (length: {len(historico)})")
    print(f"Expected: D at pos 0, V at pos 1")
    print(f"Actual: {historico[0]} at pos 0, {historico[1]} at pos 1")
    

    
    resultado = analisar_estrategias_portfolio(historico)
    
    if resultado is not None:
        print(f"\nFull result keys: {list(resultado.keys())}")
        print(f"Should operate: {resultado.get('should_operate', False)}")
        print(f"Best strategy: {resultado.get('melhor_estrategia', {}).get('strategy', 'None')}")
        print(f"Available strategies: {[estrategia.get('strategy') for estrategia in resultado.get('estrategias_disponiveis', [])]}")
        
        cycle_found = any(
            estrategia.get('strategy') == 'CYCLE_TRANSITION' 
            for estrategia in resultado.get('estrategias_disponiveis', [])
        )
    else:
        print("\nResultado é None - erro na análise")
        cycle_found = False
    
    print(f"\nCYCLE_TRANSITION detectada: {cycle_found}")
    
    return cycle_found

def main():
    print("TESTE ESPECÍFICO DOS FILTROS DAS ESTRATÉGIAS")
    print("="*60)
    
    resultados = {
        'PREMIUM_RECOVERY': test_premium_recovery_filters(),
        'MOMENTUM_SHIFT': test_momentum_shift_filters(),
        'CYCLE_TRANSITION': test_cycle_transition_filters()
    }
    
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for estrategia, funcionou in resultados.items():
        status = "✓ FUNCIONOU" if funcionou else "✗ FALHOU"
        print(f"{estrategia}: {status}")
    
    total_funcionando = sum(resultados.values())
    print(f"\nTotal funcionando: {total_funcionando}/{len(resultados)}")
    
    if total_funcionando == len(resultados):
        print("🎯 TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")

if __name__ == "__main__":
    main()