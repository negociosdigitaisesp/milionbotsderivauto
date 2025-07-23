"""
Teste para validação das correções do erro de stake máximo no BK Bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_system.utils.helpers import validar_e_ajustar_stake, calcular_martingale
from trading_system.config.settings import BotSpecificConfig

def test_validacao_stake():
    """Testa a função de validação de stake"""
    print("🧪 Testando validação de stake...")
    
    # Teste 1: Stake normal
    stake_normal = 5.0
    resultado = validar_e_ajustar_stake(stake_normal, "TEST_BOT")
    print(f"✅ Stake normal: ${stake_normal} -> ${resultado}")
    assert resultado == stake_normal, "Stake normal deve permanecer inalterado"
    
    # Teste 2: Stake muito alto
    stake_alto = 25.0
    resultado = validar_e_ajustar_stake(stake_alto, "TEST_BOT")
    print(f"⚠️ Stake alto: ${stake_alto} -> ${resultado}")
    assert resultado < stake_alto, "Stake alto deve ser reduzido"
    assert resultado <= 19.0, "Stake não deve exceder 19 USD"
    
    # Teste 3: Stake muito baixo
    stake_baixo = 0.1
    resultado = validar_e_ajustar_stake(stake_baixo, "TEST_BOT")
    print(f"⚠️ Stake baixo: ${stake_baixo} -> ${resultado}")
    assert resultado >= 1.0, "Stake deve ser pelo menos 1.0"
    
    print("✅ Todos os testes de validação passaram!")

def test_martingale_com_limite():
    """Testa o cálculo de martingale com os novos limites"""
    print("\n🧪 Testando martingale com limites...")
    
    config = BotSpecificConfig.BK_BOT_CONFIG
    stake_inicial = config['stake_inicial']
    stake_maximo = config['stake_maximo']
    
    print(f"📊 Configuração BK Bot:")
    print(f"   Stake inicial: ${stake_inicial}")
    print(f"   Stake máximo: ${stake_maximo}")
    
    # Simular sequência de perdas
    stake_atual = stake_inicial
    print(f"\n🔄 Simulando sequência de perdas:")
    
    for i in range(8):  # Testar 8 perdas seguidas
        lucro = -stake_atual  # Simular perda
        novo_stake = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, "BK_BOT_TEST")
        print(f"   Perda {i+1}: ${stake_atual:.2f} -> ${novo_stake:.2f}")
        
        # Verificar se não excede o máximo
        assert novo_stake <= stake_maximo, f"Stake não deve exceder ${stake_maximo}"
        
        stake_atual = novo_stake
        
        # Se chegou no máximo, deve parar de crescer
        if stake_atual == stake_maximo:
            print(f"   ⚠️ Limite máximo atingido: ${stake_maximo}")
            break
    
    # Testar vitória (reset)
    lucro = stake_atual * 0.8  # Simular vitória
    stake_reset = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, "BK_BOT_TEST")
    print(f"   ✅ Vitória: ${stake_atual:.2f} -> ${stake_reset:.2f} (reset)")
    assert stake_reset == stake_inicial, "Vitória deve resetar para stake inicial"
    
    print("✅ Todos os testes de martingale passaram!")

def test_configuracao_bk_bot():
    """Testa se a configuração do BK Bot está correta"""
    print("\n🧪 Testando configuração do BK Bot...")
    
    config = BotSpecificConfig.BK_BOT_CONFIG
    
    # Verificar valores essenciais
    assert config['stake_inicial'] == 1.0, "Stake inicial deve ser 1.0"
    assert config['stake_maximo'] <= 20.0, "Stake máximo deve ser <= 20.0 para segurança"
    assert config['stake_maximo'] > config['stake_inicial'], "Stake máximo deve ser maior que inicial"
    
    print(f"✅ Configuração válida:")
    print(f"   Stake inicial: ${config['stake_inicial']}")
    print(f"   Stake máximo: ${config['stake_maximo']}")
    print(f"   Stop Loss: ${config['stop_loss']}")
    print(f"   Stop Win: ${config['stop_win']}")
    print(f"   Símbolo: {config['symbol']}")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes de correção do erro de stake máximo\n")
    
    try:
        test_validacao_stake()
        test_martingale_com_limite()
        test_configuracao_bk_bot()
        
        print("\n🎉 Todos os testes passaram com sucesso!")
        print("✅ As correções do erro de stake máximo estão funcionando corretamente.")
        print("\n📋 Resumo das correções implementadas:")
        print("   1. ✅ Função validar_e_ajustar_stake() criada")
        print("   2. ✅ Validação automática na função executar_compra()")
        print("   3. ✅ Tentativa de compra de emergência em caso de erro")
        print("   4. ✅ Stake máximo do BK Bot ajustado para valor mais seguro")
        print("   5. ✅ Validação adicional no código do BK Bot")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()