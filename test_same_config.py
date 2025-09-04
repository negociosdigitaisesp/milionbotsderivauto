#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste usando exatamente a mesma configuração do bot_trading_system.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env (mesmo que bot_trading_system.py)
load_dotenv()

async def test_connection():
    """Testa conexão usando a mesma configuração do bot_trading_system.py"""
    try:
        from deriv_api import DerivAPI
        
        # Usar exatamente as mesmas variáveis que bot_trading_system.py
        DERIV_APP_ID = os.getenv("DERIV_APP_ID")
        DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
        
        print(f"=== TESTE DE CONEXÃO ===")
        print(f"DERIV_APP_ID: {DERIV_APP_ID}")
        print(f"DERIV_API_TOKEN: {DERIV_API_TOKEN[:10]}...{DERIV_API_TOKEN[-4:] if DERIV_API_TOKEN else 'None'}")
        
        if not all([DERIV_APP_ID, DERIV_API_TOKEN]):
            print("❌ Erro: Variáveis de ambiente não encontradas")
            return False
        
        print("🔗 Conectando à API da Deriv...")
        api = DerivAPI(app_id=DERIV_APP_ID)
        response = await api.authorize(DERIV_API_TOKEN)
        
        if 'authorize' in response:
            account_info = response['authorize']
            print("✅ Conexão bem-sucedida!")
            print(f"👤 Usuário: {account_info.get('loginid', 'N/A')}")
            print(f"💰 Moeda: {account_info.get('currency', 'N/A')}")
            print(f"🏦 Saldo: {account_info.get('balance', 'N/A')}")
            
            await api.disconnect()
            return True
        else:
            print(f"❌ Erro na autorização: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())