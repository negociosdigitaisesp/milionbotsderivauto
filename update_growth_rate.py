#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar o growth_rate dos bots para o valor correto (2%)
"""

import os
import json
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
        # Buscar todos os bots
        response = supabase.table('bot_configurations') \
            .select('*') \
            .execute()
        
        if not response.data:
            print("❌ Nenhum bot encontrado")
            return
        
        print("\n📊 ATUALIZANDO GROWTH RATE DOS BOTS:")
        print("=" * 60)
        
        for bot in response.data:
            bot_id = bot['id']
            bot_name = bot['bot_name']
            current_overrides = bot.get('param_overrides', {})
            
            print(f"\n🤖 {bot_name} (ID: {bot_id[:8]}...)")
            print(f"   • param_overrides atual: {current_overrides}")
            
            # Preparar novos overrides com growth_rate correto
            if isinstance(current_overrides, str):
                try:
                    overrides = json.loads(current_overrides)
                except:
                    overrides = {}
            else:
                overrides = current_overrides.copy() if current_overrides else {}
            
            # Definir growth_rate como 2% (valor do accumulator_standalone.py)
            overrides['growth_rate'] = 2.0  # Será dividido por 100 no código = 0.02
            
            print(f"   • Novos param_overrides: {overrides}")
            
            # Atualizar no banco
            update_response = supabase.table('bot_configurations') \
                .update({'param_overrides': overrides}) \
                .eq('id', bot_id) \
                .execute()
            
            if update_response.data:
                print(f"   • ✅ Growth rate atualizado para 2%")
            else:
                print(f"   • ❌ Erro ao atualizar")
                
        print("\n🎉 Atualização concluída! Reinicie os bots para aplicar as mudanças.")
                
    except Exception as e:
        print(f"❌ Erro ao atualizar configurações: {e}")

if __name__ == "__main__":
    main()