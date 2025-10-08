#!/usr/bin/env python3
"""
Script para testar a validade do token da Deriv API
"""

import os
import asyncio
import websockets
import json
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def test_deriv_token():
    """Testa se o token da Deriv API está válido"""
    
    # Obter credenciais
    app_id = "85515"
    api_token = os.getenv('DERIV_API_TOKEN')
    
    print("🔍 Testando token da Deriv API...")
    print(f"📱 APP_ID: {app_id}")
    print(f"🔑 Token: {api_token[:10]}...{api_token[-5:] if len(api_token) > 15 else api_token}")
    print(f"📏 Comprimento do token: {len(api_token)} caracteres")
    
    # Validações básicas
    if not api_token:
        print("❌ ERRO: DERIV_API_TOKEN não está definido no arquivo .env")
        return False
    
    if len(api_token) < 30:
        print(f"❌ ERRO: Token muito curto ({len(api_token)} caracteres)")
        print("   Tokens válidos da Deriv têm pelo menos 30 caracteres")
        print("   Obtenha um token válido em: https://app.deriv.com/account/api-token")
        return False
    
    if "EXEMPLO" in api_token or "AQUI" in api_token:
        print("❌ ERRO: Token ainda está com valor de exemplo")
        print("   Configure seu token real da Deriv API")
        return False
    
    print("✅ Validações básicas do token passaram")
    
    # Teste de conectividade
    ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
    
    try:
        print(f"🔗 Conectando ao WebSocket: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("✅ Conexão WebSocket estabelecida")
            
            # Teste de autenticação
            auth_message = {
                "authorize": api_token,
                "req_id": 1
            }
            
            print("🔐 Testando autenticação...")
            await websocket.send(json.dumps(auth_message))
            
            # Aguardar resposta com timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                response_data = json.loads(response)
                
                print(f"📨 Resposta recebida: {json.dumps(response_data, indent=2)}")
                
                if "authorize" in response_data:
                    print("✅ SUCESSO: Token válido e autenticação bem-sucedida!")
                    print(f"👤 Usuário: {response_data['authorize'].get('loginid', 'N/A')}")
                    print(f"💰 Moeda: {response_data['authorize'].get('currency', 'N/A')}")
                    return True
                elif "error" in response_data:
                    error = response_data["error"]
                    print(f"❌ ERRO na autenticação: {error.get('message', 'Erro desconhecido')}")
                    print(f"   Código: {error.get('code', 'N/A')}")
                    return False
                else:
                    print("⚠️ Resposta inesperada do servidor")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ TIMEOUT: Servidor não respondeu em 30 segundos")
                print("   Isso pode indicar:")
                print("   - Token inválido")
                print("   - Problemas de conectividade")
                print("   - Servidor sobrecarregado")
                return False
                
    except Exception as e:
        print(f"❌ ERRO na conexão: {e}")
        return False

async def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 TESTE DE VALIDADE DO TOKEN DA DERIV API")
    print("=" * 60)
    
    start_time = time.time()
    success = await test_deriv_token()
    end_time = time.time()
    
    print("\n" + "=" * 60)
    print(f"⏱️ Tempo total: {end_time - start_time:.2f} segundos")
    
    if success:
        print("🎉 RESULTADO: Token válido e funcionando!")
        print("✅ Você pode executar o bot principal agora")
    else:
        print("💥 RESULTADO: Token inválido ou com problemas")
        print("❌ Corrija o token antes de executar o bot principal")
        print("\n📋 INSTRUÇÕES:")
        print("1. Acesse: https://app.deriv.com/account/api-token")
        print("2. Gere um novo token de API")
        print("3. Atualize o arquivo .env com o token correto")
        print("4. Execute este teste novamente")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        exit(1)