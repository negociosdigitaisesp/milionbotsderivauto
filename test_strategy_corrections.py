#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste das correções implementadas nas estratégias:
- MOMENTUM_CONTINUATION
- VOLATILITY_BREAK  
- PATTERN_REVERSAL
"""

def test_momentum_continuation_corrected():
    """
    Testa as correções na estratégia MOMENTUM_CONTINUATION:
    - Filtro 2: Permite 1 LOSS não consecutiva
    - Filtro 3: Slice correto e edge cases
    """
    
    def estrategia_momentum_continuation_test(historico):
        try:
            # Detectar LOSS isolada
            if len(historico) >= 2 and historico[0] == 'D' and historico[1] != 'D':
                print(f"  - MOMENTUM_CONTINUATION: LOSS isolada detectada em {historico[:2]}")
                
                # Contar WINs consecutivos antes da LOSS
                wins_consecutivos = 0
                for i in range(1, len(historico)):
                    if historico[i] == 'V':
                        wins_consecutivos += 1
                    else:
                        break
                
                # Filtro 1: Aceitar apenas se 4-6 WINs antes da LOSS
                if wins_consecutivos < 4 or wins_consecutivos > 6:
                    print(f"    X Rejeitado: {wins_consecutivos} WINs (precisa 4-6)")
                    return None
                
                # Filtro 2 CORRIGIDO: Permitir máximo 1 LOSS não consecutiva nas últimas 8 operações
                if len(historico) >= 9:
                    ultimas_8_antes = historico[1:9]
                    losses_count = ultimas_8_antes.count('D')
                    
                    if losses_count > 1:
                        print(f"    X Rejeitado: {losses_count} LOSSes nas últimas 8 operações (máximo 1)")
                        return None
                    
                    # Se há 1 LOSS, verificar se não é consecutiva com a atual
                    if losses_count == 1 and ultimas_8_antes[0] == 'D':
                        print("    X Rejeitado: LOSS consecutiva detectada")
                        return None
                
                # Filtro 3 CORRIGIDO: Win rate com validação de edge cases
                if len(historico) >= 12:
                    ultimas_12 = historico[:12]
                    win_rate = (ultimas_12.count('V') / 12) * 100
                    if win_rate < 85:
                        print(f"    X Rejeitado: Win rate {win_rate:.1f}% < 85%")
                        return None
                    print(f"    ✓ Filtro 3: Win rate {win_rate:.1f}% >= 85%")
                else:
                    # Para histórico < 12, usar win rate mais flexível
                    total_ops = len(historico)
                    win_rate = (historico.count('V') / total_ops) * 100
                    if win_rate < 80:  # Critério mais flexível para amostras menores
                        print(f"    X Rejeitado: Win rate {win_rate:.1f}% < 80% (histórico pequeno)")
                        return None
                    print(f"    ✓ Filtro 3: Win rate {win_rate:.1f}% >= 80% (histórico: {total_ops} ops)")
                
                print(f"    ✓ MOMENTUM_CONTINUATION: {wins_consecutivos} WINs consecutivos")
                return {'strategy': 'MOMENTUM_CONTINUATION', 'confidence': 89}
        except Exception as e:
            print(f"    X Erro na MOMENTUM_CONTINUATION: {e}")
        return None
    
    print("\n=== TESTE MOMENTUM_CONTINUATION CORRIGIDA ===")
    
    # Caso 1: Deve PASSAR - 5 WINs, sem LOSS nas últimas 8, win rate alto
    caso1 = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 1 - Deve PASSAR: {caso1}")
    resultado1 = estrategia_momentum_continuation_test(caso1)
    print(f"Resultado: {'ATIVADO' if resultado1 else 'NÃO ATIVADO'}")
    
    # Caso 2: Deve FALHAR - 1 LOSS não consecutiva permitida
    caso2 = ['D', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 2 - Deve PASSAR (1 LOSS não consecutiva): {caso2}")
    resultado2 = estrategia_momentum_continuation_test(caso2)
    print(f"Resultado: {'ATIVADO' if resultado2 else 'NÃO ATIVADO'}")
    
    # Caso 3: Deve FALHAR - 2 LOSSes nas últimas 8
    caso3 = ['D', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'D', 'V', 'V', 'V', 'V']
    print(f"\nCaso 3 - Deve FALHAR (2 LOSSes): {caso3}")
    resultado3 = estrategia_momentum_continuation_test(caso3)
    print(f"Resultado: {'ATIVADO' if resultado3 else 'NÃO ATIVADO'}")
    
    # Caso 4: Deve FALHAR - LOSS consecutiva
    caso4 = ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 4 - Deve FALHAR (LOSS consecutiva): {caso4}")
    resultado4 = estrategia_momentum_continuation_test(caso4)
    print(f"Resultado: {'ATIVADO' if resultado4 else 'NÃO ATIVADO'}")
    
    # Caso 5: Edge case - histórico pequeno
    caso5 = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 5 - Edge case (histórico < 12): {caso5}")
    resultado5 = estrategia_momentum_continuation_test(caso5)
    print(f"Resultado: {'ATIVADO' if resultado5 else 'NÃO ATIVADO'}")

def test_volatility_break_corrected():
    """
    Testa as correções na estratégia VOLATILITY_BREAK:
    - Algoritmo de alternações corrigido
    - Conflito de LOSSes resolvido
    """
    
    def estrategia_volatility_break_test(historico):
        try:
            # Detectar LOSS isolada
            if len(historico) >= 2 and historico[0] == 'D' and historico[1] != 'D':
                print(f"  - VOLATILITY_BREAK: LOSS isolada detectada em {historico[:2]}")
                
                # Filtro 1: Operação anterior deve ser WIN
                if historico[1] != 'V':
                    print("    X Rejeitado: Operação anterior não é WIN")
                    return None
                
                # Analisar últimas 8 operações antes da LOSS para detectar volatilidade
                if len(historico) >= 9:
                    ultimas_8 = historico[1:9]  # Excluir a LOSS atual
                    
                    # Contar alternações WIN-LOSS (mudanças de estado)
                    alternacoes = 0
                    for i in range(len(ultimas_8) - 1):
                        if ultimas_8[i] != ultimas_8[i + 1]:
                            alternacoes += 1
                    
                    print(f"    - Sequência analisada: {ultimas_8}")
                    print(f"    - Alternações detectadas: {alternacoes}")
                    
                    # Filtro 2: Aceitar apenas se 3+ alternações em 8 operações (ajustado)
                    if alternacoes < 3:
                        print(f"    X Rejeitado: {alternacoes} alternações < 3")
                        return None
                    
                    # Filtro 3 CORRIGIDO: Máximo 1 LOSS adicional nas últimas 10 operações
                    if len(historico) >= 11:
                        ultimas_10_antes = historico[1:11]  # Excluir a LOSS atual
                        losses_10_antes = ultimas_10_antes.count('D')
                        if losses_10_antes > 1:
                            print(f"    X Rejeitado: {losses_10_antes} LOSSes adicionais > 1 nas últimas 10")
                            return None
                        print(f"    ✓ Filtro 3: {losses_10_antes} LOSS adicional nas últimas 10 operações")
                    else:
                        # Para histórico menor, verificar se não há LOSSes consecutivas
                        if len(historico) >= 2 and historico[1] == 'D':
                            print("    X Rejeitado: LOSSes consecutivas detectadas")
                            return None
                    
                    print(f"    ✓ VOLATILITY_BREAK: {alternacoes} alternações detectadas")
                    return {'strategy': 'VOLATILITY_BREAK', 'confidence': 84}
        except Exception as e:
            print(f"    X Erro na VOLATILITY_BREAK: {e}")
        return None
    
    print("\n=== TESTE VOLATILITY_BREAK CORRIGIDA ===")
    
    # Caso 1: Deve PASSAR - Alta volatilidade com alternações
    caso1 = ['D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'V']
    print(f"\nCaso 1 - Deve PASSAR (alta volatilidade): {caso1}")
    resultado1 = estrategia_volatility_break_test(caso1)
    print(f"Resultado: {'ATIVADO' if resultado1 else 'NÃO ATIVADO'}")
    
    # Caso 2: Deve FALHAR - Poucas alternações
    caso2 = ['D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 2 - Deve FALHAR (poucas alternações): {caso2}")
    resultado2 = estrategia_volatility_break_test(caso2)
    print(f"Resultado: {'ATIVADO' if resultado2 else 'NÃO ATIVADO'}")
    
    # Caso 3: Deve FALHAR - Muitas LOSSes adicionais
    caso3 = ['D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V', 'D', 'V']
    print(f"\nCaso 3 - Deve FALHAR (muitas LOSSes): {caso3}")
    resultado3 = estrategia_volatility_break_test(caso3)
    print(f"Resultado: {'ATIVADO' if resultado3 else 'NÃO ATIVADO'}")

def test_pattern_reversal_corrected():
    """
    Testa as correções na estratégia PATTERN_REVERSAL:
    - Sequência corrigida
    - Filtros alinhados com documentação
    """
    
    def estrategia_pattern_reversal_test(historico):
        try:
            # Detectar padrão específico: LOSS atual seguindo padrão WIN-WIN-LOSS-WIN-WIN
            if len(historico) >= 6:
                # Padrão esperado: LOSS(atual)-WIN-WIN-LOSS-WIN-WIN (do mais recente para mais antigo)
                padrao_esperado = ['D', 'V', 'V', 'D', 'V', 'V']
                padrao_atual = historico[:6]
                
                print(f"    - Sequência atual: {padrao_atual}")
                print(f"    - Padrão esperado: {padrao_esperado}")
                
                if padrao_atual == padrao_esperado:
                    print("  - PATTERN_REVERSAL: Padrão D-V-V-D-V-V detectado")
                    
                    # Filtro 1: Contexto temporal - máximo 3 LOSSes nas últimas 12 operações
                    if len(historico) >= 12:
                        ultimas_12 = historico[:12]
                        losses_12 = ultimas_12.count('D')
                        if losses_12 > 3:
                            print(f"    X Rejeitado: {losses_12} LOSSes > 3 nas últimas 12 operações")
                            return None
                        print(f"    ✓ Filtro 1: {losses_12} LOSSes <= 3 nas últimas 12 operações")
                    
                    # Filtro 2: Win rate nas últimas 10 operações >= 65% (ajustado)
                    if len(historico) >= 10:
                        ultimas_10 = historico[:10]
                        win_rate = (ultimas_10.count('V') / 10) * 100
                        if win_rate < 65:
                            print(f"    X Rejeitado: Win rate {win_rate:.1f}% < 65%")
                            return None
                        print(f"    ✓ Filtro 2: Win rate {win_rate:.1f}% >= 65%")
                    
                    # Filtro 3: Validação de contexto - não mais de 2 LOSSes consecutivas no histórico
                    consecutivas = 0
                    max_consecutivas = 0
                    for op in historico:
                        if op == 'D':
                            consecutivas += 1
                            max_consecutivas = max(max_consecutivas, consecutivas)
                        else:
                            consecutivas = 0
                    
                    if max_consecutivas > 2:
                        print(f"    X Rejeitado: {max_consecutivas} LOSSes consecutivas > 2")
                        return None
                    
                    print("    ✓ PATTERN_REVERSAL: Padrão específico confirmado com contexto válido")
                    return {'strategy': 'PATTERN_REVERSAL', 'confidence': 91}
        except Exception as e:
            print(f"    X Erro na PATTERN_REVERSAL: {e}")
        return None
    
    print("\n=== TESTE PATTERN_REVERSAL CORRIGIDA ===")
    
    # Caso 1: Deve PASSAR - Padrão exato
    caso1 = ['D', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 1 - Deve PASSAR (padrão exato): {caso1}")
    resultado1 = estrategia_pattern_reversal_test(caso1)
    print(f"Resultado: {'ATIVADO' if resultado1 else 'NÃO ATIVADO'}")
    
    # Caso 2: Deve FALHAR - Padrão incorreto
    caso2 = ['D', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    print(f"\nCaso 2 - Deve FALHAR (padrão incorreto): {caso2}")
    resultado2 = estrategia_pattern_reversal_test(caso2)
    print(f"Resultado: {'ATIVADO' if resultado2 else 'NÃO ATIVADO'}")
    
    # Caso 3: Deve FALHAR - Muitas LOSSes consecutivas
    caso3 = ['D', 'V', 'V', 'D', 'V', 'V', 'D', 'D', 'D', 'V', 'V', 'V']
    print(f"\nCaso 3 - Deve FALHAR (LOSSes consecutivas): {caso3}")
    resultado3 = estrategia_pattern_reversal_test(caso3)
    print(f"Resultado: {'ATIVADO' if resultado3 else 'NÃO ATIVADO'}")

if __name__ == "__main__":
    print("TESTE DAS CORREÇÕES IMPLEMENTADAS NAS ESTRATÉGIAS")
    print("=" * 60)
    
    test_momentum_continuation_corrected()
    test_volatility_break_corrected()
    test_pattern_reversal_corrected()
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO - Verifique os resultados acima")