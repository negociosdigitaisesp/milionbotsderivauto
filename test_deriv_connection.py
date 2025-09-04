#!/usr/bin/env python3
"""
Teste de conexão com a API da Deriv
"""

import os
import sys
import asyncio
import logging
import websockets
import json
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DerivTest')

load_dotenv()

class DerivAPITest:
    def __init__(self):
        self.app_id = os.getenv('DERIV_APP_ID', '85515')
        self.api_token = os.getenv('DERIV_API_TOKEN')
        self.websocket = None
        self.connected = False
        
    async def connect(self):
        """Testa conexão com a API da Deriv"""
        try:
            logger.info(f"🔗 Conectando à API da Deriv (App ID: {self.app_id})...")
            
            # URL da API da Deriv
            url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
            
            # Conectar ao WebSocket
            self.websocket = await websockets.connect(
                url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info("✅ Conexão WebSocket estabelecida")
            self.connected = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            logger.error(f"📋 Tipo: {type(e).__name__}")
            return False
    
    async def test_ping(self):
        """Testa ping básico"""
        try:
            if not self.connected:
                logger.error("❌ Não conectado")
                return False
                
            logger.info("🏓 Enviando ping...")
            
            ping_message = {
                "ping": 1,
                "req_id": 1
            }
            
            await self.websocket.send(json.dumps(ping_message))
            
            # Aguardar resposta
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=10
            )
            
            data = json.loads(response)
            logger.info(f"📨 Resposta recebida: {data}")
            
            if 'ping' in data and data['ping'] == 'pong':
                logger.info("✅ Ping/Pong funcionando")
                return True
            else:
                logger.warning("⚠️ Resposta inesperada ao ping")
                return False
                
        except asyncio.TimeoutError:
            logger.error("❌ Timeout no ping")
            return False
        except Exception as e:
            logger.error(f"❌ Erro no ping: {e}")
            return False
    
    async def test_authorize(self):
        """Testa autorização com token"""
        try:
            if not self.api_token:
                logger.warning("⚠️ Token não configurado, pulando teste de autorização")
                return True
                
            logger.info("🔐 Testando autorização...")
            
            auth_message = {
                "authorize": self.api_token,
                "req_id": 2
            }
            
            await self.websocket.send(json.dumps(auth_message))
            
            # Aguardar resposta
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=15
            )
            
            data = json.loads(response)
            logger.info(f"📨 Resposta de autorização: {data}")
            
            if 'authorize' in data and data.get('authorize'):
                logger.info("✅ Autorização bem-sucedida")
                return True
            elif 'error' in data:
                logger.error(f"❌ Erro na autorização: {data['error']}")
                return False
            else:
                logger.warning("⚠️ Resposta inesperada na autorização")
                return False
                
        except asyncio.TimeoutError:
            logger.error("❌ Timeout na autorização")
            return False
        except Exception as e:
            logger.error(f"❌ Erro na autorização: {e}")
            return False
    
    async def test_ticks_subscription(self):
        """Testa subscrição a ticks"""
        try:
            logger.info("📊 Testando subscrição a ticks...")
            
            # Subscrever a ticks do Volatility 75 Index
            ticks_message = {
                "ticks": "R_75",
                "subscribe": 1,
                "req_id": 3
            }
            
            await self.websocket.send(json.dumps(ticks_message))
            
            # Aguardar algumas respostas de tick
            tick_count = 0
            max_ticks = 3
            
            while tick_count < max_ticks:
                response = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=30
                )
                
                data = json.loads(response)
                
                if 'tick' in data:
                    tick_count += 1
                    tick_data = data['tick']
                    logger.info(f"📈 Tick {tick_count}: {tick_data['symbol']} = {tick_data['quote']}")
                elif 'error' in data:
                    logger.error(f"❌ Erro nos ticks: {data['error']}")
                    return False
                else:
                    logger.info(f"📨 Outra resposta: {data}")
            
            logger.info("✅ Subscrição a ticks funcionando")
            return True
            
        except asyncio.TimeoutError:
            logger.error("❌ Timeout na subscrição de ticks")
            return False
        except Exception as e:
            logger.error(f"❌ Erro na subscrição de ticks: {e}")
            return False
    
    async def disconnect(self):
        """Desconecta do WebSocket"""
        try:
            if self.websocket and hasattr(self.websocket, 'close'):
                await self.websocket.close()
                logger.info("🔌 Desconectado")
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar: {e}")

async def main():
    """Função principal de teste"""
    deriv_test = DerivAPITest()
    
    try:
        logger.info("🧪 INICIANDO TESTE DE CONEXÃO DERIV")
        logger.info("="*50)
        
        # Teste 1: Conexão
        if not await deriv_test.connect():
            logger.error("❌ Falha na conexão")
            return False
        
        # Teste 2: Ping
        if not await deriv_test.test_ping():
            logger.error("❌ Falha no ping")
            return False
        
        # Teste 3: Autorização
        if not await deriv_test.test_authorize():
            logger.error("❌ Falha na autorização")
            return False
        
        # Teste 4: Ticks
        if not await deriv_test.test_ticks_subscription():
            logger.error("❌ Falha na subscrição de ticks")
            return False
        
        logger.info("✅ TODOS OS TESTES DE CONEXÃO PASSARAM")
        return True
        
    except KeyboardInterrupt:
        logger.info("🛑 Teste interrompido pelo usuário")
        return True
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO: {e}")
        logger.error(f"📋 Tipo: {type(e).__name__}")
        return False
    finally:
        await deriv_test.disconnect()

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            logger.info("🎉 Teste de conexão concluído com sucesso")
        else:
            logger.error("💥 Teste de conexão falhou")
    except Exception as e:
        logger.error(f"❌ ERRO FATAL: {e}")
        logger.info("🔄 Verificar credenciais e conectividade")