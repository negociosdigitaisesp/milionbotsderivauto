#!/usr/bin/env python3
"""
Quick test version - runs for 60 seconds only
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from deriv_api import DerivAPI
from supabase import create_client

# Load environment variables
load_dotenv()

# Get environment variables  
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class ApiManager:
    def __init__(self, api):
        self.api = api
        self.api_lock = asyncio.Lock()
    
    async def buy(self, params):
        async with self.api_lock:
            result = await self.api.buy(params)
            await asyncio.sleep(0.5)  # Rate limiting
            return result
    
    async def ticks_history(self, params):
        async with self.api_lock:
            result = await self.api.ticks_history(params)
            await asyncio.sleep(0.3)  # Rate limiting
            return result
    
    async def proposal_open_contract(self, params):
        async with self.api_lock:
            result = await self.api.proposal_open_contract(params)
            await asyncio.sleep(0.3)  # Rate limiting
            return result

def salvar_operacao(nome_bot, lucro):
    """Save operation to Supabase"""
    try:
        data = {
            'nome_bot': nome_bot,
            'lucro': lucro,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        result = supabase.table('operacoes').insert(data).execute()
        print(f"[DB] Operation saved - Bot: {nome_bot}, Profit: ${lucro:.2f}")
    except Exception as e:
        print(f"[DB] Error saving to Supabase: {e}")

async def test_bot(api_manager):
    """Simple test bot that makes one trade"""
    bot_name = "TestBot"
    print(f"[{bot_name}] Starting quick test bot...")
    
    try:
        # Get current tick for R_100
        tick_response = await api_manager.ticks_history({
            "ticks_history": "R_100",
            "count": 2,
            "end": "latest"
        })
        
        if 'error' in tick_response:
            print(f"[{bot_name}] Error getting ticks: {tick_response['error']['message']}")
            return
        
        # Simple strategy: CALL if price went up, PUT if down
        prices = tick_response['history']['prices']
        direction = 'CALL' if prices[-1] > prices[0] else 'PUT'
        
        print(f"[{bot_name}] Price trend: {prices[0]:.5f} -> {prices[-1]:.5f}")
        print(f"[{bot_name}] Strategy: {direction}")
        
        # Make a small trade
        buy_params = {
            'buy': '1',
            'price': 1.0,  # $1 stake
            'parameters': {
                'amount': 1.0,
                'basis': 'stake',
                'contract_type': direction,
                'currency': 'USD',
                'duration': 1,
                'duration_unit': 't',
                'symbol': 'R_100'
            }
        }
        
        print(f"[{bot_name}] Placing {direction} trade with $1 stake...")
        
        buy_response = await api_manager.buy(buy_params)
        
        if 'error' in buy_response:
            print(f"[{bot_name}] Trade error: {buy_response['error']['message']}")
            return
        
        if 'buy' in buy_response and 'contract_id' in buy_response['buy']:
            contract_id = buy_response['buy']['contract_id']
            print(f"[{bot_name}] Trade placed successfully! Contract ID: {contract_id}")
            
            # Wait for result (max 15 seconds)
            for attempt in range(15):
                await asyncio.sleep(1)
                
                try:
                    status = await api_manager.proposal_open_contract({
                        "proposal_open_contract": 1,
                        "contract_id": contract_id
                    })
                    
                    if 'proposal_open_contract' in status:
                        contract = status['proposal_open_contract']
                        
                        if contract.get('is_sold') == 1:
                            payout = float(contract.get('payout', 0))
                            buy_price = float(contract.get('buy_price', 0))
                            profit = payout - buy_price
                            
                            result = "WIN" if profit > 0 else "LOSS"
                            print(f"[{bot_name}] RESULT: {result}! Profit: ${profit:.2f}")
                            
                            # Save to database
                            salvar_operacao(bot_name, profit)
                            return
                        
                except Exception as e:
                    print(f"[{bot_name}] Waiting for result... ({attempt + 1}s)")
            
            print(f"[{bot_name}] Timeout waiting for result")
        else:
            print(f"[{bot_name}] Failed to get contract ID")
            
    except Exception as e:
        print(f"[{bot_name}] Error: {e}")

async def main():
    """Main test function"""
    print("=== QUICK BOT TEST (60 seconds) ===")
    
    try:
        # Connect to Deriv API
        print("[SYSTEM] Connecting to Deriv API...")
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        api_manager = ApiManager(api)
        print("[SYSTEM] Connected successfully!")
        
        # Test Supabase connection
        try:
            result = supabase.table('operacoes').select('*').limit(1).execute()
            print(f"[SYSTEM] Supabase connected - Found {len(result.data)} test records")
        except Exception as e:
            print(f"[SYSTEM] Supabase warning: {e}")
        
        # Run test bot for 60 seconds
        print("[SYSTEM] Starting test bot...")
        
        try:
            await asyncio.wait_for(test_bot(api_manager), timeout=60)
        except asyncio.TimeoutError:
            print("[SYSTEM] Test completed (60 second timeout)")
        
        # Disconnect
        await api.disconnect()
        print("[SYSTEM] Test finished successfully!")
        
    except Exception as e:
        print(f"[SYSTEM] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())