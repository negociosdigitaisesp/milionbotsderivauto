import asyncio
import os
from deriv_api import DerivAPI
from dotenv import load_dotenv
from trading_system.bots.accumulator_bot.bot_accumulator_scalping import bot_accumulator_scalping

load_dotenv()

class ApiManager:
    def __init__(self, api):
        self.api = api
        self.lock = asyncio.Lock()
    
    async def buy(self, params):
        async with self.lock:
            return await self.api.buy(params)
    
    async def ticks_history(self, params):
        async with self.lock:
            return await self.api.ticks_history(params)
    
    async def proposal_open_contract(self, params):
        async with self.lock:
            return await self.api.proposal_open_contract(params)
    
    async def proposal(self, params):
        async with self.lock:
            return await self.api.proposal(params)

async def delayed_bot(func, delay, manager, bot_name):
    print(f"⏰ Bot {bot_name} aguardando {delay}s para iniciar...")
    await asyncio.sleep(delay)
    print(f"🚀 Iniciando {bot_name}...")
    try:
        await func(manager)
    except Exception as e:
        print(f"❌ Erro no {bot_name}: {e}")
        import traceback
        traceback.print_exc()

async def test_delayed_accumulator():
    try:
        print("🔌 Conectando à API da Deriv...")
        api = DerivAPI(app_id=int(os.getenv("DERIV_APP_ID")))
        await api.authorize(os.getenv("DERIV_API_TOKEN"))
        print("✅ Conexão estabelecida")
        
        print("🛡️ Criando ApiManager...")
        api_manager = ApiManager(api)
        print("✅ ApiManager criado")
        
        print("🧪 Testando delayed_bot com bot_accumulator_scalping...")
        
        # Simular exatamente como o sistema principal chama o bot
        task = asyncio.create_task(delayed_bot(bot_accumulator_scalping, 4, api_manager, "bot_accumulator_scalping"))
        
        # Aguardar 30 segundos para ver se há logs
        await asyncio.sleep(30)
        
        print("⏹️ Cancelando bot após 30 segundos...")
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            print("✅ Bot cancelado com sucesso")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await api.disconnect()
            print("🔌 Desconectado da API")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_delayed_accumulator())