#!/usr/bin/env python3
"""
Teste específico para verificar as correções nos filtros da estratégia PREMIUM_RECOVERY
"""

def test_premium_recovery_filters():
    """
    Testa os filtros corrigidos da estratégia PREMIUM_RECOVERY
    """
    
    def estrategia_premium_recovery_test(historico):
        """Versão de teste da estratégia PREMIUM_RECOVERY com logs detalhados"""
        try:
            print(f"\n=== TESTANDO PREMIUM_RECOVERY ===")
            print(f"Histórico: {' '.join(historico[:15])}...")
            
            # Detectar dupla LOSS consecutiva
            if len(historico) >= 2 and historico[0] == 'D' and historico[1] == 'D':
                print("✓ PREMIUM_RECOVERY: Dupla LOSS detectada")
                
                # Filtro 1: Rejeitar se 7+ WINs TOTAIS antes da primeira LOSS (não consecutivos)
                if len(historico) >= 9:
                    # Contar TOTAL de WINs nas 7 operações antes da primeira LOSS (índices 2-8)
                    wins_antes_total = 0
                    for i in range(2, min(9, len(historico))):
                        if historico[i] == 'V':
                            wins_antes_total += 1
                    if wins_antes_total > 6:
                        print(f"    X Rejeitado: {wins_antes_total} WINs totais antes da primeira LOSS (>6)")
                        return None
                    print(f"    ✓ Filtro 1: {wins_antes_total} WINs totais antes da primeira LOSS (<=6)")
                
                # Filtro 2: Rejeitar se densidade de LOSSes > 15% nas últimas 20 operações
                if len(historico) >= 20:
                    losses_20 = historico[:20].count('D')
                    densidade_losses = (losses_20 / 20) * 100
                    if densidade_losses > 15.0:
                        print(f"    X Rejeitado: Densidade de LOSSes {densidade_losses:.1f}% > 15%")
                        return None
                    print(f"    ✓ Filtro 2: Densidade de LOSSes {densidade_losses:.1f}% <= 15%")
                
                # Filtro 3: Rejeitar se LOSS nas 5 operações antes da dupla (índices 2-6)
                if len(historico) >= 7:
                    losses_antes_dupla = 0
                    for i in range(2, 7):  # Índices 2, 3, 4, 5, 6 (5 operações antes da dupla)
                        if historico[i] == 'D':
                            losses_antes_dupla += 1
                    if losses_antes_dupla > 0:
                        print(f"    X Rejeitado: {losses_antes_dupla} LOSS(es) nas 5 operações antes da dupla")
                        return None
                    print("    ✓ Filtro 3: Nenhuma LOSS nas 5 operações antes da dupla")
                
                print("    ✅ PREMIUM_RECOVERY: Todos os filtros passaram - ESTRATÉGIA ATIVADA!")
                return {'strategy': 'PREMIUM_RECOVERY', 'confidence': 97}
            else:
                print("    - Não há dupla LOSS consecutiva")
                return None
        except Exception as e:
            print(f"    X Erro na PREMIUM_RECOVERY: {e}")
        return None
    
    # Casos de teste
    test_cases = [
        {
            'name': 'Caso 1: Dupla LOSS com 6 WINs antes (deve PASSAR)',
            # Índices: 0=D, 1=D, 2-7=6WINs, resto=WINs (densidade baixa)
            'historico': ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
        },
        {
            'name': 'Caso 2: Dupla LOSS com 7 WINs antes (deve FALHAR - Filtro 1)',
            # Índices: 0=D, 1=D, 2-8=7WINs (deve falhar no filtro 1)
            'historico': ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
        },
        {
            'name': 'Caso 3: Dupla LOSS com densidade LOSSes > 15% (deve FALHAR - Filtro 2)',
            # 4 LOSSes em 20 operações = 20% > 15%
            'historico': ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V']
        },
        {
            'name': 'Caso 4: Dupla LOSS com LOSS antes da dupla (deve FALHAR - Filtro 3)',
            # LOSS no índice 4 (dentro do range 2-6)
            'historico': ['D', 'D', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
        },
        {
            'name': 'Caso 5: Cenário ideal (deve PASSAR todos os filtros)',
            # Índices: 0=D, 1=D, 2-7=6WINs, sem LOSSes nas 5 antes da dupla, densidade baixa
            'historico': ['D', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
        }
    ]
    
    print("\n" + "="*80)
    print("TESTE DOS FILTROS CORRIGIDOS DA PREMIUM_RECOVERY")
    print("="*80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'-'*60}")
        print(f"TESTE {i}: {case['name']}")
        print(f"{'-'*60}")
        
        resultado = estrategia_premium_recovery_test(case['historico'])
        
        if resultado:
            print(f"\n🎯 RESULTADO: ESTRATÉGIA ATIVADA - {resultado['strategy']} ({resultado['confidence']}%)")
        else:
            print(f"\n❌ RESULTADO: ESTRATÉGIA NÃO ATIVADA")
    
    print(f"\n{'='*80}")
    print("TESTE CONCLUÍDO")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_premium_recovery_filters()