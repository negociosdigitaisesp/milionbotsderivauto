"""
Teste isolado do ScaleBot para verificar se a correção do erro de barrier funcionou
"""

import asyncio
import os
from deriv_api import DerivAPI
from dotenv import load_dotenv
from trading_system.bots.scale_bot import bot_scale

# Carregar variáveis de ambiente
load_dotenv()

async def test_scale_bot():
    """Testa o ScaleBot isoladamente"""
    
    # Configurar API
    app_id = os.getenv('DERIV_APP_ID')
    api_token = os.getenv('DERIV_API_TOKEN')
    
    if not app_id or not api_token:
        print("❌ Erro: DERIV_APP_ID ou DERIV_API_TOKEN não encontrados no .env")
        return
    
    print("🔧 Testando ScaleBot isoladamente...")
    print(f"📱 App ID: {app_id}")
    print(f"🔑 Token: {api_token[:10]}...")
    
    try:
        # Conectar à API
        api = DerivAPI(app_id=app_id)
        await api.authorize(api_token)
        
        print("✅ Conectado à API Deriv com sucesso!")
        print("🚀 Iniciando ScaleBot...")
        
        # Executar ScaleBot por um tempo limitado para teste
        scale_task = asyncio.create_task(bot_scale(api))
        
        # Aguardar 30 segundos para ver se há erros
        try:
            await asyncio.wait_for(scale_task, timeout=30.0)
        except asyncio.TimeoutError:
            print("⏰ Teste concluído após 30 segundos")
            scale_task.cancel()
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
    
    print("🏁 Teste finalizado")

if __name__ == "__main__":
    asyncio.run(test_scale_bot())