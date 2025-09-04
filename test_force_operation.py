#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para forçar uma operação e verificar se o logging funciona
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

async def test_force_operation():
    """Testa forçar uma operação"""
    
    print("="*60)
    print("TESTE DE OPERACAO FORCADA")
    print("="*60)
    
    # Usar bot ID do bot ativo
    bot_id = "c49d0823-3981-4fdd-ba8a-50b09c9f4c82"
    
    try:
        print(f"Criando instancia do bot {bot_id}...")
        bot = BotInstance(bot_id)
        
        print("Bot inicializado com sucesso!")
        print(f"Bot Name: {bot.bot_name}")
        print(f"Stake: ${bot.stake}")
        print(f"Take Profit: {bot.take_profit_percentual*100}%")
        
        # Testar logging direto
        print("\nTestando log_operation diretamente...")
        
        # Simular uma operação WIN
        result = await bot.log_operation(
            operation_result="WIN",
            profit_percentage=5.5,
            stake_value=50.0
        )
        
        if result:
            print("SUCCESS: Operacao WIN registrada!")
        else:
            print("FAIL: Falha ao registrar operacao WIN")
        
        # Simular uma operação LOSS
        result2 = await bot.log_operation(
            operation_result="LOSS", 
            profit_percentage=-100.0,
            stake_value=25.0
        )
        
        if result2:
            print("SUCCESS: Operacao LOSS registrada!")
        else:
            print("FAIL: Falha ao registrar operacao LOSS")
        
        # Testar gestão de risco
        print("\nTestando aplicar_gestao_risco...")
        
        # Simular lucro
        bot._last_operation_stake = 30.0
        await bot.aplicar_gestao_risco(15.0)  # Lucro de $15
        
        # Simular perda  
        bot._last_operation_stake = 40.0
        await bot.aplicar_gestao_risco(-40.0)  # Perda total
        
        print("\n" + "="*60)
        print("TESTE CONCLUIDO")
        print("Verifique a tabela bot_operation_logs no Supabase")
        print("="*60)
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_force_operation())