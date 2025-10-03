#!/usr/bin/env python3
"""
Teste de validação do token API da Deriv
"""

import asyncio
import websockets
import json
import os
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def test_deriv_token():
    """Testa se o token API da Deriv é válido"""
    
    # Obter token do ambiente
    api_token = os.getenv('DERIV_API_TOKEN')
    app_id = "85515"
    
    print(f"🔍 Testando token API: {api_token}")
    print(f"📱 App ID: {app_id}")
    print(f"🔗 URL: wss://ws.binaryws.com/websockets/v3?app_id={app_id}")
    
    if not api_token:
        print("❌ DERIV_API_TOKEN não encontrado no arquivo .env")
        return False
    
    if len(api_token) < 15:
        print(f"⚠️ Token parece muito curto ({len(api_token)} caracteres). Tokens válidos geralmente têm 20+ caracteres.")
    
    try:
        # Conectar ao WebSocket
        uri = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
        print(f"\n🔗 Conectando ao WebSocket...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket conectado com sucesso")
            
            # Enviar mensagem de autenticação
            auth_message = {
                "authorize": api_token,
                "req_id": 1
            }
            
            print(f"🔐 Enviando autenticação...")
            await websocket.send(json.dumps(auth_message))
            
            # Aguardar resposta com timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                print(f"📨 Resposta recebida: {json.dumps(data, indent=2)}")
                
                if 'error' in data:
                    error = data['error']
                    print(f"❌ Erro de autenticação:")
                    print(f"   Código: {error.get('code', 'N/A')}")
                    print(f"   Mensagem: {error.get('message', 'N/A')}")
                    print(f"   Detalhes: {error.get('details', 'N/A')}")
                    return False
                
                elif 'authorize' in data:
                    auth_data = data['authorize']
                    print(f"✅ Autenticação bem-sucedida!")
                    print(f"   Login ID: {auth_data.get('loginid', 'N/A')}")
                    print(f"   Email: {auth_data.get('email', 'N/A')}")
                    print(f"   País: {auth_data.get('country', 'N/A')}")
                    print(f"   Moeda: {auth_data.get('currency', 'N/A')}")
                    return True
                
                else:
                    print(f"⚠️ Resposta inesperada: {data}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout aguardando resposta de autenticação (10s)")
                return False
                
    except websockets.exceptions.InvalidURI:
        print("❌ URI do WebSocket inválida")
        return False
    except websockets.exceptions.ConnectionClosed:
        print("❌ Conexão WebSocket fechada inesperadamente")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

async def test_ping():
    """Testa conectividade básica com ping"""
    app_id = "85515"
    uri = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
    
    try:
        print(f"\n🏓 Testando ping básico...")
        async with websockets.connect(uri) as websocket:
            ping_message = {
                "ping": 1,
                "req_id": 999
            }
            
            await websocket.send(json.dumps(ping_message))
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            if 'ping' in data and data['ping'] == 'pong':
                print("✅ Ping/Pong funcionando - conectividade OK")
                return True
            else:
                print(f"⚠️ Resposta inesperada ao ping: {data}")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste de ping: {e}")
        return False

async def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 TESTE DE VALIDAÇÃO DO TOKEN API DERIV")
    print("=" * 60)
    
    # Teste de ping primeiro
    ping_ok = await test_ping()
    
    if ping_ok:
        print("\n" + "=" * 60)
        print("🔐 TESTE DE AUTENTICAÇÃO")
        print("=" * 60)
        
        # Teste de autenticação
        auth_ok = await test_deriv_token()
        
        if auth_ok:
            print("\n🎉 Todos os testes passaram! Token é válido.")
        else:
            print("\n❌ Falha na autenticação. Verifique o token API.")
            print("\n💡 Dicas:")
            print("   1. Verifique se o token está correto no arquivo .env")
            print("   2. Confirme se o token não expirou")
            print("   3. Verifique se a conta Deriv está ativa")
            print("   4. Gere um novo token em: https://app.deriv.com/account/api-token")
    else:
        print("\n❌ Falha no teste de conectividade básica.")

if __name__ == "__main__":
    asyncio.run(main())