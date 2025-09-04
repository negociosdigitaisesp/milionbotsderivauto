#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste de conexão com a API da Deriv
Use este script para verificar se suas credenciais estão funcionando
"""

import os
import asyncio
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def test_deriv_connection():
    """Testa a conexão com a API da Deriv"""
    try:
        # Importar a API da Deriv
        from deriv_api import DerivAPI
        
        # Obter credenciais do .env
        api_token = os.getenv('DERIV_TOKEN') or os.getenv('DERIV_API_TOKEN')
        app_id = os.getenv('DERIV_APP_ID', '1089')
        
        print("🔍 Testando conexão com a API da Deriv...")
        print(f"📋 App ID: {app_id}")
        print(f"🔑 Token: {api_token[:10]}...{api_token[-4:] if api_token and len(api_token) > 14 else 'INVÁLIDO'}")
        
        if not api_token:
            print("❌ Token não encontrado no arquivo .env")
            print("\n📝 Para obter um token válido:")
            print("   1. Acesse: https://app.deriv.com/account/api-token")
            print("   2. Faça login na sua conta Deriv")
            print("   3. Crie um novo token de API")
            print("   4. Copie o token e cole no arquivo .env")
            return False
        
        # Tentar conectar
        api = DerivAPI(app_id=int(app_id))
        response = await api.authorize(api_token)
        
        if 'authorize' in response:
            account_info = response['authorize']
            print("✅ Conexão bem-sucedida!")
            print(f"👤 Usuário: {account_info.get('loginid', 'N/A')}")
            print(f"💰 Moeda: {account_info.get('currency', 'N/A')}")
            print(f"🏦 Saldo: {account_info.get('balance', 'N/A')}")
            print(f"🌍 País: {account_info.get('country', 'N/A')}")
            
            # Testar obtenção de ticks
            print("\n🔍 Testando obtenção de ticks do R_75...")
            ticks_response = await api.ticks_history('R_75', count=5)
            
            if 'ticks_history' in ticks_response:
                prices = ticks_response['ticks_history']['prices']
                print(f"📊 Últimos 5 ticks: {prices}")
                print("✅ Teste de ticks bem-sucedido!")
            else:
                print("⚠️ Erro ao obter ticks")
            
            await api.disconnect()
            return True
        else:
            print(f"❌ Erro na autorização: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print("\n🔧 Possíveis soluções:")
        print("   1. Verifique se o token está correto")
        print("   2. Verifique sua conexão com a internet")
        print("   3. Certifique-se de que o token não expirou")
        print("   4. Tente gerar um novo token")
        return False

async def test_supabase_connection():
    """Testa a conexão com o Supabase (opcional)"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        print("\n🔍 Testando conexão com Supabase...")
        
        if not supabase_url or not supabase_key or 'exemplo' in supabase_url:
            print("⚠️ Credenciais do Supabase não configuradas (opcional)")
            return True
        
        print(f"🌐 URL: {supabase_url}")
        print(f"🔑 Key: {supabase_key[:10]}...{supabase_key[-4:]}")
        
        # Aqui você pode adicionar teste real do Supabase se necessário
        print("ℹ️ Teste do Supabase não implementado (opcional)")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro no teste do Supabase: {e}")
        return True  # Supabase é opcional

async def main():
    """Função principal de teste"""
    print("🚀 TESTE DE CONEXÃO - ACCUMULATOR BOT")
    print("=" * 50)
    
    # Testar Deriv API
    deriv_ok = await test_deriv_connection()
    
    # Testar Supabase (opcional)
    supabase_ok = await test_supabase_connection()
    
    print("\n" + "=" * 50)
    print("📊 RESULTADO DOS TESTES:")
    print(f"   🎯 Deriv API: {'✅ OK' if deriv_ok else '❌ FALHOU'}")
    print(f"   🗄️ Supabase: {'✅ OK' if supabase_ok else '⚠️ OPCIONAL'}")
    
    if deriv_ok:
        print("\n🎉 Tudo pronto! Você pode executar o bot com:")
        print("   python accumulator_standalone.py")
    else:
        print("\n🔧 Configure suas credenciais antes de executar o bot.")

if __name__ == "__main__":
    asyncio.run(main())