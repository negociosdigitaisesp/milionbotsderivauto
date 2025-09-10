#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from tunderbot import AccumulatorScalpingBot

async def test_enhanced_stats():
    """Testa o método _get_enhanced_stats"""
    try:
        print("🧪 Testando método _get_enhanced_stats...")
        
        # Criar instância do bot
        bot = AccumulatorScalpingBot()
        print("✅ Bot inicializado")
        
        # Testar método de estatísticas aprimoradas
        stats = await bot._get_enhanced_stats()
        print("✅ Enhanced stats method working")
        print(f"📊 Stats keys: {list(stats.keys())}")
        print(f"📈 Total stats fields: {len(stats)}")
        
        # Mostrar algumas estatísticas importantes
        print("\n📋 Estatísticas importantes:")
        print(f"   • Queue size: {stats.get('queue_size', 'N/A')}")
        print(f"   • Active operations: {stats.get('active_operations', 'N/A')}")
        print(f"   • Connection status: {stats.get('connection_status', 'N/A')}")
        print(f"   • Buffer synced: {stats.get('buffer_synced', 'N/A')}")
        print(f"   • Subscription active: {stats.get('subscription_active', 'N/A')}")
        
        print("\n✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_enhanced_stats())