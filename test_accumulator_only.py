#!/usr/bin/env python3
"""
Teste específico do Accumulator_Scalping_Bot
Para verificar se há algum erro na execução do bot
"""

import asyncio
import os
from dotenv import load_dotenv
from deriv_api import DerivAPI
from trading_system.bots.accumulator_bot.bot_accumulator_scalping import bot_accumulator_scalping

load_dotenv()

class ApiManager:
    """Classe ApiManager simplificada para teste"""
    def __init__(self, api):
        self.api = api
        self.lock = asyncio.Lock()
    
    async def buy(self, params):
        async with self.lock:
            await asyncio.sleep(0.1)  # Rate limiting básico
            return await self.api.buy(params)
    
    async def ticks_history(self, params):
        async with self.lock:
            await asyncio.sleep(0.1)  # Rate limiting básico
            return await self.api.ticks_history(params)
    
    async def proposal_open_contract(self, params):
        async with self.lock:
            await asyncio.sleep(0.1)  # Rate limiting básico
            return await self.api.proposal_open_contract(params)

async def test_accumulator_bot():
    """Teste específico do Accumulator_Scalping_Bot"""
    print("🧪 TESTE ESPECÍFICO DO ACCUMULATOR_SCALPING_BOT")
    print("=" * 60)
    
    try:
        # Conectar à API
        print("📊 Conectando à API da Deriv...")
        app_id = os.getenv("DERIV_APP_ID")
        token = os.getenv("DERIV_API_TOKEN")
        
        if not app_id or not token:
            raise ValueError("❌ Variáveis de ambiente DERIV_APP_ID ou DERIV_API_TOKEN não encontradas")
        
        api = DerivAPI(app_id=app_id)
        await api.authorize(token)
        print("✅ Conexão com Deriv API estabelecida")
        
        # Criar ApiManager
        api_manager = ApiManager(api)
        print("✅ ApiManager criado")
        
        # Executar bot por 60 segundos
        print("🚀 Iniciando Accumulator_Scalping_Bot por 60 segundos...")
        print("📊 Monitorando logs do bot...")
        print("-" * 60)
        
        # Executar com timeout
        await asyncio.wait_for(bot_accumulator_scalping(api_manager), timeout=60)
        
    except asyncio.TimeoutError:
        print("\n⏰ Teste de 60 segundos concluído")
        print("✅ Bot executou sem erros críticos")
        
    except Exception as e:
        print(f"\n❌ ERRO DETECTADO: {e}")
        print(f"📋 Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"📋 Traceback completo:")
        traceback.print_exc()
        
    finally:
        print("\n🔚 Finalizando teste...")
        try:
            await api.disconnect()
            print("✅ Desconectado da API")
        except:
            pass

if __name__ == "__main__":
    print("🧪 INICIANDO TESTE DO ACCUMULATOR_SCALPING_BOT")
    asyncio.run(test_accumulator_bot())
    print("🏁 TESTE FINALIZADO")