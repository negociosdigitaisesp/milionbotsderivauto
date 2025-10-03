#!/usr/bin/env python3
"""
Diagnóstico avançado de conectividade com a API Deriv
"""

import asyncio
import websockets
import json
import os
import time
import aiohttp
import socket
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

class DerivConnectionDiagnostic:
    def __init__(self):
        self.api_token = os.getenv('DERIV_API_TOKEN')
        self.app_id = "85515"
        self.base_url = "wss://ws.binaryws.com/websockets/v3"
        self.results = {}
    
    async def test_dns_resolution(self):
        """Testa resolução DNS"""
        print("🔍 Testando resolução DNS...")
        try:
            import socket
            start_time = time.time()
            ip = socket.gethostbyname('ws.binaryws.com')
            dns_time = (time.time() - start_time) * 1000
            print(f"✅ DNS resolvido: ws.binaryws.com → {ip} ({dns_time:.2f}ms)")
            self.results['dns'] = {'success': True, 'ip': ip, 'time_ms': dns_time}
            return True
        except Exception as e:
            print(f"❌ Erro na resolução DNS: {e}")
            self.results['dns'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_tcp_connection(self):
        """Testa conexão TCP básica"""
        print("🔗 Testando conexão TCP...")
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex(('ws.binaryws.com', 443))
            tcp_time = (time.time() - start_time) * 1000
            sock.close()
            
            if result == 0:
                print(f"✅ Conexão TCP estabelecida ({tcp_time:.2f}ms)")
                self.results['tcp'] = {'success': True, 'time_ms': tcp_time}
                return True
            else:
                print(f"❌ Falha na conexão TCP: código {result}")
                self.results['tcp'] = {'success': False, 'error_code': result}
                return False
        except Exception as e:
            print(f"❌ Erro na conexão TCP: {e}")
            self.results['tcp'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_websocket_connection(self):
        """Testa conexão WebSocket"""
        print("🌐 Testando conexão WebSocket...")
        try:
            uri = f"{self.base_url}?app_id={self.app_id}"
            start_time = time.time()
            
            async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
                connect_time = (time.time() - start_time) * 1000
                print(f"✅ WebSocket conectado ({connect_time:.2f}ms)")
                
                # Testar ping/pong
                ping_start = time.time()
                ping_message = {"ping": 1, "req_id": 999}
                await websocket.send(json.dumps(ping_message))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                ping_time = (time.time() - ping_start) * 1000
                data = json.loads(response)
                
                if 'ping' in data and data['ping'] == 'pong':
                    print(f"✅ Ping/Pong funcionando ({ping_time:.2f}ms)")
                    self.results['websocket'] = {
                        'success': True, 
                        'connect_time_ms': connect_time,
                        'ping_time_ms': ping_time
                    }
                    return True
                else:
                    print(f"⚠️ Resposta inesperada ao ping: {data}")
                    self.results['websocket'] = {'success': False, 'error': 'Invalid ping response'}
                    return False
                    
        except Exception as e:
            print(f"❌ Erro na conexão WebSocket: {e}")
            self.results['websocket'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_authentication_detailed(self):
        """Testa autenticação com detalhes"""
        print("🔐 Testando autenticação detalhada...")
        
        if not self.api_token:
            print("❌ Token API não encontrado")
            self.results['auth'] = {'success': False, 'error': 'No API token'}
            return False
        
        try:
            uri = f"{self.base_url}?app_id={self.app_id}"
            
            async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
                print("📡 WebSocket conectado para autenticação")
                
                # Enviar autenticação
                auth_message = {
                    "authorize": self.api_token,
                    "req_id": 1
                }
                
                print(f"📤 Enviando autenticação...")
                send_start = time.time()
                await websocket.send(json.dumps(auth_message))
                send_time = (time.time() - send_start) * 1000
                
                print(f"📤 Mensagem enviada ({send_time:.2f}ms)")
                print("⏳ Aguardando resposta...")
                
                # Aguardar resposta com timeout longo
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60)
                    auth_time = (time.time() - send_start) * 1000
                    data = json.loads(response)
                    
                    print(f"📨 Resposta recebida ({auth_time:.2f}ms)")
                    print(f"📄 Dados: {json.dumps(data, indent=2)}")
                    
                    if 'error' in data:
                        error = data['error']
                        print(f"❌ Erro de autenticação:")
                        print(f"   Código: {error.get('code', 'N/A')}")
                        print(f"   Mensagem: {error.get('message', 'N/A')}")
                        self.results['auth'] = {
                            'success': False, 
                            'error': error,
                            'response_time_ms': auth_time
                        }
                        return False
                    
                    elif 'authorize' in data:
                        auth_data = data['authorize']
                        print(f"✅ Autenticação bem-sucedida!")
                        print(f"   Login ID: {auth_data.get('loginid', 'N/A')}")
                        print(f"   Email: {auth_data.get('email', 'N/A')}")
                        self.results['auth'] = {
                            'success': True,
                            'response_time_ms': auth_time,
                            'loginid': auth_data.get('loginid'),
                            'email': auth_data.get('email')
                        }
                        return True
                    
                    else:
                        print(f"⚠️ Resposta inesperada: {data}")
                        self.results['auth'] = {
                            'success': False, 
                            'error': 'Unexpected response',
                            'response': data
                        }
                        return False
                        
                except asyncio.TimeoutError:
                    print("❌ Timeout na autenticação (60s)")
                    self.results['auth'] = {'success': False, 'error': 'Timeout after 60s'}
                    return False
                    
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            self.results['auth'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_network_latency(self):
        """Testa latência de rede"""
        print("⚡ Testando latência de rede...")
        try:
            uri = f"{self.base_url}?app_id={self.app_id}"
            latencies = []
            
            for i in range(5):
                try:
                    start_time = time.time()
                    async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
                        connect_time = (time.time() - start_time) * 1000
                        latencies.append(connect_time)
                        print(f"   Teste {i+1}/5: {connect_time:.2f}ms")
                except Exception as e:
                    print(f"   Teste {i+1}/5: FALHOU - {e}")
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                
                print(f"📊 Latência média: {avg_latency:.2f}ms")
                print(f"📊 Latência mínima: {min_latency:.2f}ms")
                print(f"📊 Latência máxima: {max_latency:.2f}ms")
                
                self.results['latency'] = {
                    'success': True,
                    'avg_ms': avg_latency,
                    'min_ms': min_latency,
                    'max_ms': max_latency,
                    'samples': latencies
                }
                return True
            else:
                print("❌ Nenhum teste de latência bem-sucedido")
                self.results['latency'] = {'success': False, 'error': 'All tests failed'}
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de latência: {e}")
            self.results['latency'] = {'success': False, 'error': str(e)}
            return False
    
    async def run_full_diagnostic(self):
        """Executa diagnóstico completo"""
        print("=" * 70)
        print("🧪 DIAGNÓSTICO COMPLETO DE CONECTIVIDADE DERIV API")
        print("=" * 70)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔑 Token: {self.api_token[:10]}..." if self.api_token else "❌ Token não encontrado")
        print(f"📱 App ID: {self.app_id}")
        print(f"🌐 URL: {self.base_url}")
        print()
        
        tests = [
            ("DNS Resolution", self.test_dns_resolution),
            ("TCP Connection", self.test_tcp_connection),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Network Latency", self.test_network_latency),
            ("Authentication", self.test_authentication_detailed),
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*50}")
            print(f"🧪 {test_name}")
            print(f"{'='*50}")
            
            try:
                await test_func()
            except Exception as e:
                print(f"❌ Erro inesperado no teste {test_name}: {e}")
                self.results[test_name.lower().replace(' ', '_')] = {
                    'success': False, 
                    'error': f'Unexpected error: {e}'
                }
        
        print(f"\n{'='*70}")
        print("📋 RESUMO DO DIAGNÓSTICO")
        print(f"{'='*70}")
        
        for test_name, result in self.results.items():
            status = "✅ PASSOU" if result.get('success') else "❌ FALHOU"
            print(f"{test_name.upper()}: {status}")
            if not result.get('success') and 'error' in result:
                print(f"   Erro: {result['error']}")
        
        print(f"\n🕐 Diagnóstico concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Salvar resultados
        with open('diagnostic_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print("💾 Resultados salvos em: diagnostic_results.json")

async def main():
    diagnostic = DerivConnectionDiagnostic()
    await diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())