#!/usr/bin/env python3
"""
Test all bots execution - runs for 90 seconds only
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

async def bot_scale(api_manager):
    """Scale Bot - Simple strategy"""
    bot_name = "ScaleBot"
    print(f"[{bot_name}] Starting...")
    
    for i in range(3):  # Only 3 attempts for testing
        try:
            print(f"[{bot_name}] Running cycle {i+1}/3")
            
            # Get current tick for R_100
            tick_response = await api_manager.ticks_history({
                "ticks_history": "R_100",
                "count": 2,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"[{bot_name}] Error getting ticks: {tick_response['error']['message']}")
                await asyncio.sleep(5)
                continue
            
            prices = tick_response['history']['prices']
            direction = 'CALL' if prices[-1] > prices[0] else 'PUT'
            
            print(f"[{bot_name}] Strategy: {direction} (Price: {prices[0]:.5f} -> {prices[-1]:.5f})")
            
            # Wait between operations
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"[{bot_name}] Error: {e}")
            await asyncio.sleep(5)

async def bot_gold(api_manager):
    """Gold Bot - DIGITDIFF strategy"""
    bot_name = "GoldBot"
    print(f"[{bot_name}] Starting...")
    
    for i in range(2):  # Only 2 attempts for testing
        try:
            print(f"[{bot_name}] Running cycle {i+1}/2")
            
            # Get current tick for R_100
            tick_response = await api_manager.ticks_history({
                "ticks_history": "R_100",
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"[{bot_name}] Error getting ticks: {tick_response['error']['message']}")
                await asyncio.sleep(5)
                continue
            
            # Extract last digit
            ultimo_tick = tick_response['history']['prices'][-1]
            predicao = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"[{bot_name}] Last digit R_100: {predicao} (Price: {ultimo_tick:.5f})")
            print(f"[{bot_name}] Would use DIGITDIFF strategy with prediction: {predicao}")
            
            # Wait between operations  
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"[{bot_name}] Error: {e}")
            await asyncio.sleep(5)

async def bot_double_cuentas(api_manager):
    """DoubleCuentas Bot - Digit trigger strategy"""
    bot_name = "DoubleCuentas"
    print(f"[{bot_name}] Starting...")
    
    for i in range(5):  # Check 5 times for digit trigger
        try:
            print(f"[{bot_name}] Running cycle {i+1}/5")
            
            # Get current tick for R_75
            tick_response = await api_manager.ticks_history({
                "ticks_history": "R_75",
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"[{bot_name}] Error getting ticks: {tick_response['error']['message']}")
                await asyncio.sleep(5)
                continue
            
            # Extract last digit
            ultimo_tick = tick_response['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"[{bot_name}] Price R_75: {ultimo_tick:.5f} | Last Digit: {ultimo_digito}")
            
            if ultimo_digito == 0:
                print(f"[{bot_name}] TRIGGER ACTIVATED! Last digit = 0. Would execute DIGITOVER...")
            else:
                print(f"[{bot_name}] Waiting for trigger (digit = 0). Current: {ultimo_digito}")
            
            # Wait between checks
            await asyncio.sleep(8)
            
        except Exception as e:
            print(f"[{bot_name}] Error: {e}")
            await asyncio.sleep(5)

async def main():
    """Main test function"""
    print("=== TEST ALL BOTS EXECUTION (90 seconds) ===")
    
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
        
        print("[SYSTEM] Starting all 3 bots in parallel...")
        
        # Create bot tasks with delays
        tasks = [
            asyncio.create_task(asyncio.wait_for(bot_scale(api_manager), timeout=90)),
            asyncio.create_task(asyncio.wait_for(bot_gold(api_manager), timeout=90)),  
            asyncio.create_task(asyncio.wait_for(bot_double_cuentas(api_manager), timeout=90))
        ]
        
        print(f"[SYSTEM] {len(tasks)} bots configured for parallel execution")
        
        # Run all bots
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                bot_names = ["ScaleBot", "GoldBot", "DoubleCuentas"]
                if isinstance(result, Exception):
                    print(f"[SYSTEM] {bot_names[i]} finished with error: {result}")
                else:
                    print(f"[SYSTEM] {bot_names[i]} completed successfully")
                    
        except Exception as e:
            print(f"[SYSTEM] Error in parallel execution: {e}")
        
        # Disconnect
        await api.disconnect()
        print("[SYSTEM] All bots test completed!")
        
    except Exception as e:
        print(f"[SYSTEM] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())