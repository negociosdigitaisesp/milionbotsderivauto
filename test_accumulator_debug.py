#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para debug do Accumulator_Scalping_Bot
"""

import asyncio
import logging
from deriv_api import DerivAPI
from trading_system.bots.accumulator_bot.bot_accumulator_scalping import bot_accumulator_scalping

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

class SimpleApiManager:
    """ApiManager simplificado para teste"""
    
    def __init__(self, api):
        self.api = api
        self.lock = asyncio.Lock()
    
    async def ticks_history(self, params):
        async with self.lock:
            return await self.api.ticks_history(params)
    
    async def buy(self, params):
        async with self.lock:
            return await self.api.buy(params)
    
    async def proposal_open_contract(self, params):
        async with self.lock:
            return await self.api.proposal_open_contract(params)

async def test_accumulator_bot():
    """Teste isolado do Accumulator bot"""
    api = None
    
    try:
        print("🔌 Conectando à API da Deriv...")
        api = DerivAPI(app_id=1089)
        await api.authorize('YOUR_TOKEN_HERE')  # Substitua pelo token real
        
        print("✅ Conexão estabelecida")
        
        # Criar ApiManager
        api_manager = SimpleApiManager(api)
        
        print("🤖 Iniciando teste do Accumulator_Scalping_Bot...")
        
        # Executar bot por 60 segundos
        bot_task = asyncio.create_task(bot_accumulator_scalping(api_manager))
        
        # Aguardar 60 segundos
        await asyncio.sleep(60)
        
        # Cancelar bot
        bot_task.cancel()
        
        try:
            await bot_task
        except asyncio.CancelledError:
            print("🛑 Bot cancelado após 60 segundos")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if api:
            await api.disconnect()
            print("🔌 Desconectado da API")

if __name__ == "__main__":
    asyncio.run(test_accumulator_bot())