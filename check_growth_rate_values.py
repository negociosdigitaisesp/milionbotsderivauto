#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar os valores de growth_rate dos bots no banco de dados
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def main():
    # Conectar ao Supabase
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Variáveis de ambiente SUPABASE_URL ou SUPABASE_ANON_KEY não encontradas")
        return
    
    supabase: Client = create_client(url, key)
    print("✅ Conexão com Supabase estabelecida")
    
    try:
        # Buscar configurações dos bots
        response = supabase.table('bot_configurations') \
            .select('id, bot_name, param_growth_rate, param_overrides') \
            .execute()
        
        if not response.data:
            print("❌ Nenhum bot encontrado")
            return
        
        print("\n📊 VALORES DE GROWTH RATE DOS BOTS:")
        print("=" * 60)
        
        for bot in response.data:
            print(f"\n🤖 {bot['bot_name']} (ID: {bot['id'][:8]}...)")
            print(f"   • param_growth_rate: {bot.get('param_growth_rate', 'N/A')}")
            print(f"   • param_overrides: {bot.get('param_overrides', 'N/A')}")
            
            # Calcular valor final do growth_rate
            growth_rate = float(bot.get('param_growth_rate', 2.0)) / 100.0
            print(f"   • Growth Rate Final: {growth_rate*100}% ({growth_rate})")
            
            # Verificar se está no intervalo correto
            if 0.01 <= growth_rate <= 0.05:
                print(f"   • Status: ✅ VÁLIDO")
            else:
                print(f"   • Status: ❌ FORA DO PADRÃO (deve ser 1-5%)")
                
    except Exception as e:
        print(f"❌ Erro ao buscar configurações: {e}")

if __name__ == "__main__":
    main()