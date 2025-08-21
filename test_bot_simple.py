#!/usr/bin/env python3
"""
Simple test bot without Unicode characters to verify basic functionality
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def test_environment():
    """Test if environment variables are properly loaded"""
    print("=== TESTING ENVIRONMENT SETUP ===")
    print(f"Deriv App ID: {'OK' if DERIV_APP_ID else 'MISSING'}")
    print(f"Deriv API Token: {'OK' if DERIV_API_TOKEN else 'MISSING'}")
    print(f"Supabase URL: {'OK' if SUPABASE_URL else 'MISSING'}")
    print(f"Supabase Key: {'OK' if SUPABASE_KEY else 'MISSING'}")
    
    if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("ERROR: Missing environment variables. Check .env file")
        return False
    
    print("Environment variables loaded successfully!")
    return True

async def test_deriv_connection():
    """Test connection to Deriv API"""
    try:
        from deriv_api import DerivAPI
        
        print("\n=== TESTING DERIV CONNECTION ===")
        print("Connecting to Deriv API...")
        
        api = DerivAPI(app_id=DERIV_APP_ID)
        await api.authorize(DERIV_API_TOKEN)
        
        print("Deriv API connection successful!")
        
        # Test getting account balance
        balance_response = await api.balance()
        if 'error' not in balance_response:
            balance = balance_response['balance']['balance']
            currency = balance_response['balance']['currency']
            print(f"Account balance: {balance} {currency}")
        
        await api.disconnect()
        return True
        
    except Exception as e:
        print(f"Deriv connection failed: {e}")
        return False

async def test_supabase_connection():
    """Test connection to Supabase"""
    try:
        from supabase import create_client
        
        print("\n=== TESTING SUPABASE CONNECTION ===")
        print("Connecting to Supabase...")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test connection by trying to select from operacoes table
        result = supabase.table('operacoes').select('*').limit(1).execute()
        print("Supabase connection successful!")
        print(f"Found {len(result.data)} records in test query")
        
        return True
        
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return False

async def main():
    """Main test function"""
    print("SIMPLE BOT TEST - ENVIRONMENT AND CONNECTIONS")
    print("=" * 50)
    
    # Test environment
    env_ok = await test_environment()
    if not env_ok:
        return
    
    # Test Deriv connection
    deriv_ok = await test_deriv_connection()
    
    # Test Supabase connection
    supabase_ok = await test_supabase_connection()
    
    print("\n=== FINAL RESULTS ===")
    print(f"Environment: {'OK' if env_ok else 'FAILED'}")
    print(f"Deriv API: {'OK' if deriv_ok else 'FAILED'}")
    print(f"Supabase: {'OK' if supabase_ok else 'FAILED'}")
    
    if all([env_ok, deriv_ok, supabase_ok]):
        print("\nALL TESTS PASSED - Bot system ready!")
    else:
        print("\nSome tests failed - Check configuration")

if __name__ == "__main__":
    asyncio.run(main())