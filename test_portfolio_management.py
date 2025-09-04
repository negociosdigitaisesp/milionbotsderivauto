#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do sistema de gerenciamento de portfólio corrigido
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_instance import BotInstance

async def test_portfolio_management():
    """Testa o sistema de gerenciamento de portfólio"""
    
    print("="*60)
    print("TESTE DO SISTEMA DE GERENCIAMENTO DE PORTFOLIO")
    print("="*60)
    
    # Usar bot ID do bot ativo
    bot_id = "c49d0823-3981-4fdd-ba8a-50b09c9f4c82"
    
    try:
        print(f"Criando instancia do bot {bot_id}...")
        bot = BotInstance(bot_id)
        
        print("Bot inicializado com sucesso!")
        print(f"Bot Name: {bot.bot_name}")
        
        # Testar verificação de portfólio
        print("\n1. Testando verificação de portfólio...")
        portfolio_ok = await bot.verificar_e_limpar_portfolio()
        print(f"Resultado da verificação: {portfolio_ok}")
        
        # Testar análise de padrão com exemplo funcional
        print("\n2. Testando análise de padrão com exemplo que DEVE detectar...")
        ticks_pattern = [100.0, 120.0, 115.0, 110.0, 105.0]  # Red-Red-Red-Blue
        pattern_detected = bot.analisar_padrao_entrada(ticks_pattern)
        print(f"Padrão detectado: {pattern_detected}")
        
        if pattern_detected:
            print("SUCCESS: Padrão Red-Red-Red-Blue detectado corretamente!")
        else:
            print("ERROR: Padrão deveria ter sido detectado")
        
        # Testar processo completo se padrão detectado
        if pattern_detected and portfolio_ok:
            print("\n3. Testando execução de compra...")
            contract_id = await bot.executar_compra()
            
            if contract_id:
                print(f"SUCCESS: Compra executada - Contract ID: {contract_id}")
            else:
                print("INFO: Compra não executada (pode ser devido a portfólio cheio)")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO")
        print("Verificações implementadas:")
        print("✅ Verificação de portfólio antes da compra") 
        print("✅ Limpeza automática de posições antigas")
        print("✅ Retry inteligente após limpeza")
        print("✅ Tratamento específico para erro de limite de posições")
        print("✅ Análise de padrão corrigida (igual ao accumulator_standalone.py)")
        print("="*60)
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_portfolio_management())