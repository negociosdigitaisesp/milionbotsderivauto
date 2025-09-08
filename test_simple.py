#!/usr/bin/env python3
"""
Teste Simples para o Scalping Bot
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from radar_analisis_scalping_bot import (
        analisar_micro_burst,
        analisar_precision_surge,
        analisar_quantum_matrix
    )
    print("✅ Importações realizadas com sucesso")
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    sys.exit(1)

def teste_micro_burst():
    """Teste básico da estratégia MICRO_BURST"""
    print("\n🧪 Testando MICRO_BURST...")
    
    # Cenário ideal: 2 WINs consecutivos, 1 LOSS isolado
    historico_ideal = ['V', 'V', 'D', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    resultado = analisar_micro_burst(historico_ideal)
    print(f"   Cenário ideal: {resultado['should_operate']} - {resultado['reason']}")
    
    # Cenário com muitos WINs (deve falhar)
    historico_muitos_wins = ['V'] * 10
    resultado = analisar_micro_burst(historico_muitos_wins)
    print(f"   Muitos WINs: {resultado['should_operate']} - {resultado['reason']}")
    
    return True

def teste_precision_surge():
    """Teste básico da estratégia PRECISION_SURGE"""
    print("\n🧪 Testando PRECISION_SURGE...")
    
    # Cenário ideal: 4 WINs consecutivos
    historico_ideal = ['V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V', 'V']
    resultado = analisar_precision_surge(historico_ideal)
    print(f"   Cenário ideal: {resultado['should_operate']} - {resultado['reason']}")
    
    return True

def teste_quantum_matrix():
    """Teste básico da estratégia QUANTUM_MATRIX"""
    print("\n🧪 Testando QUANTUM_MATRIX...")
    
    # Cenário ideal: 6+ WINs consecutivos
    historico_ideal = ['V'] * 15
    resultado = analisar_quantum_matrix(historico_ideal)
    print(f"   Cenário ideal: {resultado['should_operate']} - {resultado['reason']}")
    
    return True

def main():
    """Função principal"""
    print("🧪 TESTE SIMPLES DO SCALPING BOT")
    print(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*50)
    
    try:
        teste_micro_burst()
        teste_precision_surge()
        teste_quantum_matrix()
        
        print("\n✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)