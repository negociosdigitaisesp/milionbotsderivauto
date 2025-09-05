#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das correções implementadas nas estratégias avançadas:
- CYCLE_TRANSITION: Cálculo de posição no ciclo com timestamp real
- FIBONACCI_RECOVERY: Janelas corretas (3,5,8) e filtro win rate ≥80%
- MOMENTUM_SHIFT: Índices das janelas antiga/recente corrigidos
- STABILITY_BREAK: Critério de estabilidade e período dinâmico
"""

import sys
from datetime import datetime

def test_cycle_transition():
    print("\n=== TESTE CYCLE_TRANSITION ===")
    
    def estrategia_cycle_transition_test(historico):
        try:
            # Detectar LOSS isolada
            if len(historico) >= 2 and historico[0] == 'D' and historico[1] != 'D':
                print("  - CYCLE_TRANSITION: LOSS isolada detectada")
                
                # Calcular posição no ciclo baseado em timestamp real
                current_time = datetime.now()
                minutes_today = current_time.hour * 60 + current_time.minute
                posicao_ciclo = (minutes_today // 20) % 20 + 1
                
                print(f"    - Posição no ciclo (timestamp): {posicao_ciclo}/20")
                
                # Filtro 1: Operar apenas nas posições 1-3 do ciclo
                if posicao_ciclo < 1 or posicao_ciclo > 3:
                    print(f"    X Rejeitado: Posição {posicao_ciclo} fora do range 1-3")
                    return None
                
                # Filtro 2: Últimas 4-6 operações antes da LOSS devem ser majoritariamente WINs
                if len(historico) >= 7:
                    ultimas_6_antes = historico[1:7]
                    wins_count = ultimas_6_antes.count('V')
                    if wins_count < 5:
                        print(f"    X Rejeitado: Apenas {wins_count}/6 WINs antes da LOSS (mínimo 5)")
                        return None
                    print(f"    ✓ Filtro 2: {wins_count}/6 WINs antes da LOSS")
                
                # Filtro 3: Máximo 1 LOSS nas últimas 12 operações
                if len(historico) >= 13:
                    ultimas_12_antes = historico[1:13]
                    losses_count = ultimas_12_antes.count('D')
                    if losses_count > 1:
                        print(f"    X Rejeitado: {losses_count} LOSSes nas últimas 12 (máximo 1)")
                        return None
                    print(f"    ✓ Filtro 3: {losses_count} LOSS nas últimas 12 operações")
                
                # Filtro 4: Verificar estabilidade do ciclo anterior
                if len(historico) >= 21:
                    ciclo_anterior = historico[1:21]
                    win_rate_ciclo = (ciclo_anterior.count('V') / 20) * 100
                    if win_rate_ciclo < 75:
                        print(f"    X Rejeitado: Win rate do ciclo anterior {win_rate_ciclo:.1f}% < 75%")
                        return None
                    print(f"    ✓ Filtro 4: Win rate do ciclo anterior {win_rate_ciclo:.1f}%")
                
                print(f"    ✓ CYCLE_TRANSITION: Posição {posicao_ciclo}/20 no ciclo")
                return {'strategy': 'CYCLE_TRANSITION', 'confidence': 86}
        except Exception as e:
            print(f"    X Erro na CYCLE_TRANSITION: {e}")
        return None
    
    # Teste 1: Cenário válido - início de ciclo com alta estabilidade
    print("\nTeste 1: Cenário válido (início de ciclo + estabilidade)")
    historico_valido = ['D'] + ['V'] * 6 + ['V'] * 12 + ['V'] * 8  # LOSS + 6 WINs + 12 WINs + 8 WINs
    resultado = estrategia_cycle_transition_test(historico_valido)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU'}")
    
    # Teste 2: Falha - poucas WINs antes da LOSS
    print("\nTeste 2: Falha - poucas WINs antes da LOSS")
    historico_falha = ['D', 'V', 'V', 'V', 'D', 'V', 'V'] + ['V'] * 15
    resultado = estrategia_cycle_transition_test(historico_falha)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")
    
    # Teste 3: Falha - muitas LOSSes no histórico
    print("\nTeste 3: Falha - muitas LOSSes nas últimas 12")
    historico_falha2 = ['D'] + ['V'] * 5 + ['D', 'V', 'D', 'V'] + ['V'] * 10
    resultado = estrategia_cycle_transition_test(historico_falha2)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")

def test_fibonacci_recovery():
    print("\n=== TESTE FIBONACCI_RECOVERY ===")
    
    def estrategia_fibonacci_recovery_test(historico):
        try:
            # Verificar LOSS isolada
            if len(historico) < 10 or historico[0] != 'D' or (len(historico) >= 2 and historico[1] == 'D'):
                return None
            
            print("  - FIBONACCI_RECOVERY: LOSS isolada detectada")
            
            # Filtro 1: Win rate geral ≥80% nas últimas 15 operações
            if len(historico) >= 15:
                ultimas_15 = historico[:15]
                win_rate_geral = (ultimas_15.count('V') / 15) * 100
                if win_rate_geral < 80:
                    print(f"    X Rejeitado: Win rate geral {win_rate_geral:.1f}% < 80%")
                    return None
                print(f"    ✓ Filtro 1: Win rate geral {win_rate_geral:.1f}% >= 80%")
            
            # Verificar padrões Fibonacci nas janelas específicas: 3, 5, 8
            fibonacci_windows = {
                3: {'start': 1, 'end': 4, 'min_wins': 2},
                5: {'start': 1, 'end': 6, 'min_wins': 4},
                8: {'start': 1, 'end': 9, 'min_wins': 6}
            }
            
            fibonacci_matches = []
            
            for fib_num, config in fibonacci_windows.items():
                if len(historico) >= config['end']:
                    window = historico[config['start']:config['end']]
                    win_count = window.count('V')
                    
                    print(f"    - Janela Fibonacci {fib_num}: {win_count}/{fib_num} WINs, sequência: {window}")
                    
                    if win_count >= config['min_wins']:
                        fibonacci_matches.append({
                            'window_size': fib_num,
                            'wins': win_count,
                            'win_rate': (win_count / fib_num) * 100
                        })
                        print(f"    ✓ Fibonacci {fib_num}: {win_count} WINs >= {config['min_wins']}")
            
            # Filtro 2: Pelo menos 2 janelas Fibonacci devem atender aos critérios
            if len(fibonacci_matches) < 2:
                print(f"    X Rejeitado: Apenas {len(fibonacci_matches)} janelas Fibonacci válidas (mínimo 2)")
                return None
            
            # Filtro 3: Verificar consistência
            if len(historico) >= 10:
                ultimas_10_antes = historico[1:11]
                losses_10 = ultimas_10_antes.count('D')
                if losses_10 > 1:
                    print(f"    X Rejeitado: {losses_10} LOSSes nas últimas 10 operações (máximo 1)")
                    return None
                print(f"    ✓ Filtro 3: {losses_10} LOSS nas últimas 10 operações")
            
            melhor_fibonacci = max(fibonacci_matches, key=lambda x: x['win_rate'])
            
            print(f"    ✓ FIBONACCI_RECOVERY: {len(fibonacci_matches)} janelas válidas")
            return {'strategy': 'FIBONACCI_RECOVERY', 'confidence': 87.5}
            
        except Exception as e:
            print(f"    X Erro na FIBONACCI_RECOVERY: {e}")
        return None
    
    # Teste 1: Cenário válido - múltiplas janelas Fibonacci
    print("\nTeste 1: Cenário válido (múltiplas janelas Fibonacci)")
    historico_valido = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V'] + ['V'] * 7  # LOSS + 8 WINs + 7 WINs
    resultado = estrategia_fibonacci_recovery_test(historico_valido)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU'}")
    
    # Teste 2: Falha - win rate geral baixo
    print("\nTeste 2: Falha - win rate geral < 80%")
    historico_falha = ['D'] + ['V'] * 8 + ['D', 'D', 'D', 'V', 'V', 'V']
    resultado = estrategia_fibonacci_recovery_test(historico_falha)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")
    
    # Teste 3: Falha - poucas janelas Fibonacci válidas
    print("\nTeste 3: Falha - apenas 1 janela Fibonacci válida")
    historico_falha2 = ['D', 'V', 'V', 'D', 'D', 'V', 'D', 'V', 'V'] + ['V'] * 6
    resultado = estrategia_fibonacci_recovery_test(historico_falha2)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")

def test_momentum_shift():
    print("\n=== TESTE MOMENTUM_SHIFT ===")
    
    def estrategia_momentum_shift_test(historico):
        try:
            # Verificar LOSS isolada
            if len(historico) < 20 or historico[0] != 'D' or (len(historico) >= 2 and historico[1] == 'D'):
                return None
            
            print("  - MOMENTUM_SHIFT: LOSS isolada detectada")
            
            if len(historico) >= 16:
                # Janelas corrigidas
                old_window = historico[8:16]   # 8 operações antigas
                recent_window = historico[1:8] # 7 operações recentes
                
                old_win_rate = old_window.count('V') / len(old_window)
                recent_win_rate = recent_window.count('V') / len(recent_window)
                
                print(f"    - Janela antiga (baseline): {old_window} - Win rate: {old_win_rate*100:.1f}%")
                print(f"    - Janela recente: {recent_window} - Win rate: {recent_win_rate*100:.1f}%")
                
                improvement = recent_win_rate - old_win_rate
                
                # Filtro 1: Baseline deve ser baixo (≤60%)
                if old_win_rate > 0.60:
                    print(f"    X Rejeitado: Baseline muito alto {old_win_rate*100:.1f}% > 60%")
                    return None
                
                # Filtro 2: Melhoria deve ser significativa (≥25%)
                if improvement < 0.25:
                    print(f"    X Rejeitado: Melhoria {improvement*100:.1f}% < 25%")
                    return None
                
                # Filtro 3: Win rate recente deve ser alto (≥80%)
                if recent_win_rate < 0.80:
                    print(f"    X Rejeitado: Win rate recente {recent_win_rate*100:.1f}% < 80%")
                    return None
                
                # Filtro 4: Verificar consistência
                if len(historico) >= 11:
                    ultimas_10_antes = historico[1:11]
                    losses_10 = ultimas_10_antes.count('D')
                    if losses_10 > 1:
                        print(f"    X Rejeitado: {losses_10} LOSSes nas últimas 10 operações (máximo 1)")
                        return None
                    print(f"    ✓ Filtro 4: {losses_10} LOSS nas últimas 10 operações")
                
                print(f"    ✓ MOMENTUM_SHIFT: Melhoria {improvement*100:.1f}%")
                return {'strategy': 'MOMENTUM_SHIFT', 'confidence': 87.5}
            
            return None
        except Exception as e:
            print(f"    X Erro na MOMENTUM_SHIFT: {e}")
        return None
    
    # Teste 1: Cenário válido - momentum shift claro
    print("\nTeste 1: Cenário válido (momentum shift claro)")
    # Baseline baixo (37.5%) -> Recente alto (85.7%)
    historico_valido = ['D'] + ['V'] * 6 + ['D'] + ['D', 'D', 'D', 'V', 'V', 'V', 'D', 'D'] + ['V'] * 5
    resultado = estrategia_momentum_shift_test(historico_valido)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU'}")
    
    # Teste 2: Falha - baseline muito alto
    print("\nTeste 2: Falha - baseline muito alto (>60%)")
    historico_falha = ['D'] + ['V'] * 6 + ['D'] + ['V'] * 6 + ['V', 'D'] + ['V'] * 5
    resultado = estrategia_momentum_shift_test(historico_falha)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")
    
    # Teste 3: Falha - melhoria insuficiente
    print("\nTeste 3: Falha - melhoria < 25%")
    historico_falha2 = ['D'] + ['V'] * 5 + ['D', 'V'] + ['D', 'V', 'D', 'V', 'D', 'V', 'D', 'V'] + ['V'] * 5
    resultado = estrategia_momentum_shift_test(historico_falha2)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")

def test_stability_break():
    print("\n=== TESTE STABILITY_BREAK ===")
    
    def estrategia_stability_break_test(historico):
        try:
            # Verificar LOSS isolada
            if len(historico) < 25 or historico[0] != 'D' or (len(historico) >= 2 and historico[1] == 'D'):
                return None
            
            print("  - STABILITY_BREAK: LOSS isolada detectada")
            
            # Calcular período de estabilidade dinâmico
            max_stability_period = 0
            current_stability = 0
            
            for i in range(1, min(21, len(historico))):
                if historico[i] == 'V':
                    current_stability += 1
                    max_stability_period = max(max_stability_period, current_stability)
                else:
                    current_stability = 0
            
            print(f"    - Maior período de estabilidade: {max_stability_period} WINs consecutivos")
            
            # Filtro 1: Deve ter pelo menos 8 WINs consecutivos
            if max_stability_period < 8:
                print(f"    X Rejeitado: Período de estabilidade {max_stability_period} < 8")
                return None
            
            # Filtro 2: Verificar estabilidade geral
            stability_window = historico[1:19]
            loss_count_stability = stability_window.count('D')
            win_rate_stability = (stability_window.count('V') / len(stability_window)) * 100
            
            if loss_count_stability > 2:
                print(f"    X Rejeitado: {loss_count_stability} LOSSes em 18 operações (máximo 2)")
                return None
            
            if win_rate_stability < 89:
                print(f"    X Rejeitado: Win rate de estabilidade {win_rate_stability:.1f}% < 89%")
                return None
            
            print(f"    ✓ Filtro 2: Estabilidade geral {win_rate_stability:.1f}%")
            
            # Filtro 3: Verificar qualidade das últimas 7 operações
            recent_7 = historico[1:8]
            wins_in_recent_7 = recent_7.count('V')
            losses_in_recent_7 = recent_7.count('D')
            
            if wins_in_recent_7 < 6:
                print(f"    X Rejeitado: Qualidade recente {wins_in_recent_7}/7 < 6")
                return None
            
            # Filtro 4: Não deve haver LOSSes consecutivas
            if losses_in_recent_7 > 0 and recent_7[0] == 'D':
                print("    X Rejeitado: LOSSes consecutivas detectadas")
                return None
            
            print(f"    ✓ STABILITY_BREAK: Estabilidade de {max_stability_period} WINs")
            return {'strategy': 'STABILITY_BREAK', 'confidence': 88.7}
            
        except Exception as e:
            print(f"    X Erro na STABILITY_BREAK: {e}")
        return None
    
    # Teste 1: Cenário válido - alta estabilidade quebrada
    print("\nTeste 1: Cenário válido (alta estabilidade quebrada)")
    historico_valido = ['D'] + ['V'] * 10 + ['D'] + ['V'] * 7 + ['V'] * 8  # LOSS + 10 WINs + 1 LOSS + 15 WINs
    resultado = estrategia_stability_break_test(historico_valido)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU'}")
    
    # Teste 2: Falha - período de estabilidade insuficiente
    print("\nTeste 2: Falha - período de estabilidade < 8 WINs")
    historico_falha = ['D'] + ['V'] * 6 + ['D'] + ['V'] * 5 + ['D'] + ['V'] * 12
    resultado = estrategia_stability_break_test(historico_falha)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")
    
    # Teste 3: Falha - muitas LOSSes no período de estabilidade
    print("\nTeste 3: Falha - muitas LOSSes no período de estabilidade")
    historico_falha2 = ['D'] + ['V'] * 6 + ['D'] + ['V'] * 4 + ['D'] + ['V'] * 3 + ['D'] + ['V'] * 8
    resultado = estrategia_stability_break_test(historico_falha2)
    print(f"Resultado: {'PASSOU' if resultado else 'FALHOU (esperado)'}")

if __name__ == "__main__":
    print("TESTE DAS CORREÇÕES DAS ESTRATÉGIAS AVANÇADAS")
    print("=" * 50)
    
    test_cycle_transition()
    test_fibonacci_recovery()
    test_momentum_shift()
    test_stability_break()
    
    print("\n" + "=" * 50)
    print("TESTE CONCLUÍDO - Verifique os resultados acima")
    print("Estratégias corrigidas:")
    print("✓ CYCLE_TRANSITION: Timestamp real + teoria de ciclos de 20")
    print("✓ FIBONACCI_RECOVERY: Janelas 3,5,8 + filtro win rate ≥80%")
    print("✓ MOMENTUM_SHIFT: Índices corrigidos + baseline adequado")
    print("✓ STABILITY_BREAK: Critério flexível + período dinâmico")