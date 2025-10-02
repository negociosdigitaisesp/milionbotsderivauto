#!/usr/bin/env python3
"""
Tunder Bot - Modo Standalone
Bot de trading automatizado com estratégia Accumulator
Com lógica de entrada otimizada e sistema de sinais integrado
"""

import os
import sys
import asyncio
import time
import logging
import json
import threading
import websockets
import uuid
import signal
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client
from robust_order_system import RobustOrderSystem, OperationType
from enhanced_sync_system import EnhancedSyncSystem
from aiohttp import web
from error_handler import RobustErrorHandler, with_error_handling, ErrorType, ErrorSeverity

# NOVOS IMPORTS - Sistema de Sincronia Aprimorado
from enhanced_tick_buffer import EnhancedTickBuffer
from websocket_recovery import WebSocketRecoveryManager
from signal_queue_system import ThreadSafeSignalQueue
from system_health_monitor import SystemHealthMonitor

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tunderbot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# PARÂMETROS DE GESTÃO (CONFORME XML ORIGINAL)
# ============================================================================
NOME_BOT = "Tunder Bot"
STAKE_INICIAL = 5.0  # initial stake - alterado para 5
STAKE_MAXIMO_DERIV = 1000.0  # Limite máximo de stake permitido pela Deriv API
TAKE_PROFIT_PERCENTUAL = 0.45  # 45% (Return%) - Alterado conforme solicitado
ATIVO = 'R_75'
GROWTH_RATE = 0.02  # 2% - Valor alterado para Tunder Bot
WIN_STOP = 1000.0  # Meta de ganho diário
LOSS_LIMIT = 1000.0  # Limite de perda diária
KHIZZBOT = 50  # Valor khizzbot conforme XML original

# ============================================================================
# CLASSE DE GERENCIAMENTO DA API - WEBSOCKET NATIVO
# ============================================================================
class DerivWebSocketNativo:
    """Gerenciador de API WebSocket nativo com APP_ID 85515"""
    
    def __init__(self):
        # WebSocket connection
        self.ws = None
        self.connected = False
        
        # Request management
        self.req_id_counter = 0
        self.req_id_lock = threading.Lock()
        self.pending_requests = {}
        self.request_timeout = 15  # Otimizado para menor latência
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 2 requests per second max
        
        # Credentials from environment
        self.app_id = "85515"  # APP_ID específico conforme especificação
        self.api_token = os.getenv('DERIV_API_TOKEN')
        
        if not self.api_token:
            raise ValueError("❌ DERIV_API_TOKEN deve estar definido no arquivo .env")
        
        # Connection state
        self.session_id = None
        self.authorized = False
        
        logger.info(f"🔧 DerivWebSocketNativo inicializado - App ID: {self.app_id}")
    
    async def _check_network_connectivity(self):
        """Verifica conectividade de rede antes de tentar conectar"""
        try:
            import socket
            # Tenta conectar ao DNS do Google para verificar conectividade
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            return result == 0
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar conectividade de rede: {e}")
            return True  # Assume conectividade se não conseguir verificar
    
    async def connect(self):
        """Conecta ao WebSocket da Deriv com autenticação e logs detalhados"""
        max_retries = 5  # Aumentado de 3 para 5
        connection_start_time = time.time()
        
        logger.info(f"🔗 Iniciando processo de conexão WebSocket...")
        logger.debug(f"📊 Estado atual: connected={getattr(self, 'connected', False)}, "
                    f"authorized={getattr(self, 'authorized', False)}, "
                    f"session_id={getattr(self, 'session_id', None)}")
        
        # Verificar conectividade de rede antes de tentar conectar
        logger.debug("🌐 Verificando conectividade de rede...")
        if not await self._check_network_connectivity():
            logger.error("❌ Sem conectividade de rede. Aguardando 10 segundos...")
            await asyncio.sleep(10)
            if not await self._check_network_connectivity():
                logger.error("❌ Ainda sem conectividade de rede após 10 segundos")
                return False
        logger.debug("✅ Conectividade de rede confirmada")
        
        for attempt in range(max_retries):
            attempt_start_time = time.time()
            try:
                logger.info(f"🔗 Tentativa {attempt + 1}/{max_retries} - Conectando WebSocket...")
                
                # Fechar conexão anterior se existir
                if self.ws:
                    try:
                        logger.debug("🔄 Fechando conexão WebSocket anterior...")
                        await asyncio.wait_for(self.ws.close(), timeout=5.0)
                        logger.debug("✅ Conexão anterior fechada com sucesso")
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Timeout ao fechar conexão anterior")
                    except Exception as close_error:
                        logger.warning(f"⚠️ Erro ao fechar conexão anterior: {close_error}")
                
                # URL WebSocket conforme especificação
                ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
                logger.debug(f"🌐 URL de conexão: {ws_url}")
                
                # Conectar WebSocket com timeout
                logger.debug("🔗 Estabelecendo conexão WebSocket...")
                connect_start = time.time()
                self.ws = await asyncio.wait_for(
                    websockets.connect(ws_url, ping_interval=20, ping_timeout=10), 
                    timeout=30.0
                )
                connect_time = time.time() - connect_start
                logger.info(f"🔗 WebSocket conectado em {connect_time:.2f}s: {ws_url}")
                
                # Verificar estado da conexão
                try:
                    # Diferentes versões do websockets podem ter atributos diferentes
                    is_closed = getattr(self.ws, 'closed', False) or getattr(self.ws, 'close_code', None) is not None
                    if is_closed:
                        logger.error("❌ WebSocket foi fechado imediatamente após conexão")
                        continue
                except AttributeError:
                    # Se não conseguir verificar o estado, continua
                    logger.debug("⚠️ Não foi possível verificar estado do WebSocket, continuando...")
                    pass
                    
                # Log do estado do WebSocket (compatível com diferentes versões)
                try:
                    is_open = not (getattr(self.ws, 'closed', False) or getattr(self.ws, 'close_code', None) is not None)
                    logger.debug(f"📊 Estado WebSocket: open={is_open}, "
                               f"local_address={getattr(self.ws, 'local_address', 'N/A')}, "
                               f"remote_address={getattr(self.ws, 'remote_address', 'N/A')}")
                except AttributeError:
                    logger.debug("📊 Estado WebSocket: conectado (verificação de estado não disponível)")
                
                # Iniciar task para processar mensagens
                logger.debug("🔄 Iniciando handler de mensagens...")
                message_task = asyncio.create_task(self._handle_messages())
                
                # Aguardar um pouco para garantir que o handler está ativo
                await asyncio.sleep(0.1)
                
                # Autenticar
                logger.debug("🔐 Iniciando processo de autenticação...")
                auth_start = time.time()
                auth_success = await self._authenticate()
                auth_time = time.time() - auth_start
                
                if auth_success:
                    self.connected = True
                    total_time = time.time() - connection_start_time
                    logger.info(f"✅ Conexão WebSocket estabelecida em {total_time:.2f}s - "
                              f"Session: {self.session_id} (auth: {auth_time:.2f}s)")
                    
                    # Iniciar keepalive
                    logger.debug("💓 Iniciando sistema de keepalive...")
                    keepalive_task = asyncio.create_task(self._keepalive_loop())
                    
                    # Reset contador de falhas de reconexão em caso de sucesso
                    if hasattr(self, 'consecutive_reconnect_failures'):
                        self.consecutive_reconnect_failures = 0
                        logger.debug("🔄 Reset contador de falhas de reconexão")
                    
                    return True
                else:
                    logger.error(f"❌ Falha na autenticação após {auth_time:.2f}s")
                    
            except asyncio.TimeoutError:
                attempt_time = time.time() - attempt_start_time
                logger.error(f"❌ Timeout na tentativa {attempt + 1} após {attempt_time:.2f}s")
                # Verificar conectividade novamente após timeout
                if not await self._check_network_connectivity():
                    logger.warning("⚠️ Conectividade de rede perdida após timeout")
            except websockets.exceptions.InvalidURI as e:
                logger.error(f"❌ URL WebSocket inválida na tentativa {attempt + 1}: {e}")
                # Erro de URL é crítico, não vale a pena tentar novamente
                break
            except websockets.exceptions.ConnectionClosed as e:
                attempt_time = time.time() - attempt_start_time
                logger.error(f"❌ Conexão fechada na tentativa {attempt + 1} após {attempt_time:.2f}s: {e}")
            except websockets.exceptions.WebSocketException as e:
                attempt_time = time.time() - attempt_start_time
                logger.error(f"❌ Erro WebSocket na tentativa {attempt + 1} após {attempt_time:.2f}s: {e}")
            except OSError as e:
                attempt_time = time.time() - attempt_start_time
                logger.error(f"❌ Erro de rede na tentativa {attempt + 1} após {attempt_time:.2f}s: {e}")
                # Verificar conectividade após erro de rede
                if not await self._check_network_connectivity():
                    logger.warning("⚠️ Conectividade de rede perdida após erro de rede")
            except Exception as e:
                attempt_time = time.time() - attempt_start_time
                logger.error(f"❌ Erro inesperado na tentativa {attempt + 1} após {attempt_time:.2f}s: {type(e).__name__}: {e}")
                import traceback
                logger.debug(f"📋 Stack trace: {traceback.format_exc()}")
                
            if attempt < max_retries - 1:
                # Backoff exponencial com jitter
                base_wait = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
                jitter = base_wait * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)  # ±10% jitter
                wait_time = min(base_wait + jitter, 30)  # Máximo 30 segundos
                logger.warning(f"⏳ Aguardando {wait_time:.1f}s antes da próxima tentativa (backoff exponencial)...")
                await asyncio.sleep(wait_time)
                    
        total_failed_time = time.time() - connection_start_time
        logger.error(f"❌ Falha ao estabelecer conexão WebSocket após {total_failed_time:.2f}s e {max_retries} tentativas")
        return False
    
    def _get_next_req_id(self):
        """Gera próximo request ID thread-safe"""
        with self.req_id_lock:
            self.req_id_counter += 1
            return self.req_id_counter
    
    async def _authenticate(self):
        """Autentica com a API da Deriv"""
        try:
            req_id = self._get_next_req_id()
            auth_message = {
                "authorize": self.api_token,
                "req_id": req_id
            }
            
            logger.info(f"🔐 Enviando autenticação - req_id: {req_id}")
            response = await self._send_request(auth_message)
            
            if 'error' in response:
                logger.error(f"❌ Erro de autenticação: {response['error']['message']}")
                return False
            
            if 'authorize' in response:
                self.authorized = True
                self.session_id = response['authorize'].get('loginid')
                logger.info(f"✅ Autenticado com sucesso - LoginID: {self.session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {e}")
            return False
    
    async def _handle_messages(self):
        """Processa mensagens recebidas do WebSocket"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    req_id = data.get('req_id')
                    
                    logger.debug(f"📥 Mensagem recebida - req_id: {req_id}, data: {data}")
                    
                    # NOVO: Processar ticks em tempo real
                    if 'tick' in data:
                        await self._process_tick(data['tick'])
                    
                    if req_id and req_id in self.pending_requests:
                        future = self.pending_requests.pop(req_id)
                        if not future.done():
                            future.set_result(data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Erro ao decodificar JSON: {e}")
                except Exception as e:
                    logger.error(f"❌ Erro ao processar mensagem: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ Conexão WebSocket fechada")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Erro no handler de mensagens: {e}")
            self.connected = False
    
    async def _keepalive_loop(self):
        """Loop de ping/pong aprimorado para manter conexão ativa"""
        consecutive_ping_failures = 0
        max_ping_failures = 3
        ping_timeout = 10.0  # 10 segundos timeout para ping
        last_successful_ping = time.time()
        
        while self.connected and self.ws:
            try:
                await asyncio.sleep(20)  # Ping a cada 20 segundos (mais frequente)
                
                if self.connected and self.ws:
                    req_id = self._get_next_req_id()
                    ping_message = {"ping": 1, "req_id": req_id}
                    
                    try:
                        # Enviar ping com timeout
                        ping_start = time.time()
                        response = await asyncio.wait_for(
                            self._send_request(ping_message), 
                            timeout=ping_timeout
                        )
                        
                        if 'ping' in response:
                            ping_duration = time.time() - ping_start
                            last_successful_ping = time.time()
                            consecutive_ping_failures = 0
                            
                            logger.debug(f"💓 Ping OK - req_id: {req_id}, latência: {ping_duration*1000:.1f}ms")
                            
                            # Alertar sobre latência alta
                            if ping_duration > 5.0:
                                logger.warning(f"⚠️ Latência alta no ping: {ping_duration*1000:.1f}ms")
                        else:
                            consecutive_ping_failures += 1
                            logger.warning(f"⚠️ Ping falhou ({consecutive_ping_failures}/{max_ping_failures}) - Resposta inválida")
                            
                    except asyncio.TimeoutError:
                        consecutive_ping_failures += 1
                        logger.warning(f"⚠️ Timeout no ping ({consecutive_ping_failures}/{max_ping_failures}) - {ping_timeout}s")
                        
                    except Exception as ping_error:
                        consecutive_ping_failures += 1
                        logger.error(f"❌ Erro no ping ({consecutive_ping_failures}/{max_ping_failures}): {ping_error}")
                    
                    # Verificar se muitas falhas consecutivas
                    if consecutive_ping_failures >= max_ping_failures:
                        time_since_last_success = time.time() - last_successful_ping
                        logger.error(f"❌ Muitas falhas de ping consecutivas ({consecutive_ping_failures}), "
                                   f"última resposta há {time_since_last_success:.1f}s - Forçando reconexão")
                        await self._reconnect()
                        consecutive_ping_failures = 0
                        last_successful_ping = time.time()
                        
            except Exception as e:
                logger.error(f"❌ Erro no keepalive: {e} - Reconectando...")
                await self._reconnect()
                consecutive_ping_failures = 0
                last_successful_ping = time.time()
    
    async def _reconnect(self):
        """Reconecta automaticamente com circuit breaker inteligente"""
        # Verificar se não estamos em loop de reconexão
        if hasattr(self, '_reconnecting') and self._reconnecting:
            logger.warning("⚠️ Reconexão já em andamento, ignorando nova tentativa")
            return
            
        self._reconnecting = True
        
        try:
            # Incrementar contador de falhas consecutivas
            if not hasattr(self, 'consecutive_reconnect_failures'):
                self.consecutive_reconnect_failures = 0
            if not hasattr(self, 'last_reconnect_attempt'):
                self.last_reconnect_attempt = 0
                
            self.consecutive_reconnect_failures += 1
            current_time = time.time()
            
            # Implementar backoff exponencial
            if self.consecutive_reconnect_failures > 1:
                backoff_time = min(30 * (2 ** (self.consecutive_reconnect_failures - 1)), 300)  # Máximo 5 minutos
                time_since_last_attempt = current_time - self.last_reconnect_attempt
                
                if time_since_last_attempt < backoff_time:
                    wait_time = backoff_time - time_since_last_attempt
                    logger.warning(f"⏳ Aguardando {wait_time:.1f}s antes da próxima tentativa de reconexão "
                                 f"(tentativa {self.consecutive_reconnect_failures})")
                    await asyncio.sleep(wait_time)
            
            # Circuit breaker - parar tentativas se muitas falhas
            if self.consecutive_reconnect_failures > 10:
                logger.critical(f"❌ Muitas falhas de reconexão consecutivas ({self.consecutive_reconnect_failures}), "
                              f"pausando por 10 minutos")
                await asyncio.sleep(600)  # 10 minutos
                self.consecutive_reconnect_failures = 5  # Reset parcial
            
            logger.info(f"🔄 Iniciando reconexão (tentativa {self.consecutive_reconnect_failures})...")
            self.connected = False
            self.last_reconnect_attempt = current_time
            
            # Tentar reconectar com timeout
            try:
                await asyncio.wait_for(self.connect(), timeout=60.0)  # 1 minuto timeout
                
                # Se chegou até aqui, reconexão foi bem-sucedida
                logger.info(f"✅ Reconexão bem-sucedida após {self.consecutive_reconnect_failures} tentativas")
                self.consecutive_reconnect_failures = 0
                
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout na reconexão (tentativa {self.consecutive_reconnect_failures})")
                raise
            except Exception as reconnect_error:
                logger.error(f"❌ Erro na reconexão (tentativa {self.consecutive_reconnect_failures}): {reconnect_error}")
                raise
                
        except Exception as e:
            logger.error(f"❌ Falha crítica na reconexão: {e}")
        finally:
            self._reconnecting = False
    
    async def _send_request(self, message):
        """Envia request e aguarda response"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
            
            req_id = message.get('req_id')
            if not req_id:
                req_id = self._get_next_req_id()
                message['req_id'] = req_id
            
            # Criar Future para aguardar response
            future = asyncio.Future()
            self.pending_requests[req_id] = future
            
            # Enviar mensagem
            message_str = json.dumps(message)
            logger.debug(f"📤 Enviando: {message_str}")
            
            await self.ws.send(message_str)
            self.last_request_time = time.time()
            
            # Aguardar response com timeout
            try:
                response = await asyncio.wait_for(future, timeout=self.request_timeout)
                return response  # Retorne a resposta em caso de sucesso
            except asyncio.TimeoutError:
                logger.warning(f"A requisição {req_id} expirou (timeout).")
                # Remover a future do dicionário para evitar vazamento de memória
                if req_id in self.pending_requests:
                    del self.pending_requests[req_id]
                return None  # Retornar None para indicar falha por timeout
            except asyncio.CancelledError:
                logger.warning(f"A requisição {req_id} foi cancelada.")
                # Remover a future também em caso de cancelamento
                if req_id in self.pending_requests:
                    del self.pending_requests[req_id]
                # Propagar o erro para que a tarefa que o cancelou saiba disso
                raise
            except Exception as e:
                logger.error(f"Erro inesperado ao enviar requisição {req_id}: {e}")
                if req_id in self.pending_requests:
                    del self.pending_requests[req_id]
                return None
                
        except Exception as e:
            # Cleanup em caso de erro
            self.pending_requests.pop(req_id, None)
            raise e
    
    async def ensure_connection(self):
        """Garante que a conexão WebSocket está ativa"""
        if not self.connected or not self.ws or not self.authorized:
            await self.connect()
    
    async def buy(self, params):
        """Executa compra usando WebSocket nativo"""
        await self.ensure_connection()
        
        try:
            # Estrutura de compra conforme documentação Deriv
            buy_message = {
                "buy": str(params["buy"]),
                "price": float(params["price"])
            }
            
            logger.info(f"🔄 Executando compra via WebSocket - Session: {self.session_id}")
            logger.info(f"📋 Parâmetros: {buy_message}")
            
            response = await self._send_request(buy_message)
            
            if 'error' in response:
                raise Exception(f"Deriv API Error: {response['error']['message']}")
            
            logger.info(f"✅ Compra executada com sucesso via WebSocket")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na compra via WebSocket: {e}")
            raise e
    
    async def ticks_history(self, symbol: str, count: int = 5):
        """Obtém histórico de ticks usando WebSocket nativo"""
        await self.ensure_connection()
        
        try:
            # Estrutura de ticks_history conforme documentação Deriv
            ticks_message = {
                "ticks_history": symbol,
                "count": count,
                "end": "latest"
            }
            
            logger.debug(f"📊 Solicitando histórico de ticks: {ticks_message}")
            
            response = await self._send_request(ticks_message)
            
            if 'error' in response:
                raise Exception(f"Deriv API Error: {response['error']['message']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter ticks via WebSocket: {e}")
            raise e
    
    async def proposal_open_contract(self, contract_id: str):
        """Obtém informações do contrato usando WebSocket nativo"""
        await self.ensure_connection()
        
        try:
            # Estrutura de proposal_open_contract conforme documentação Deriv
            contract_message = {
                "proposal_open_contract": 1,
                "contract_id": contract_id
            }
            
            logger.debug(f"📋 Solicitando informações do contrato: {contract_message}")
            
            response = await self._send_request(contract_message)
            
            if 'error' in response:
                raise Exception(f"Deriv API Error: {response['error']['message']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter contrato via WebSocket: {e}")
            raise e
    
    async def proposal(self, params):
        """Executa proposta usando WebSocket nativo"""
        await self.ensure_connection()
        
        try:
            # Estrutura de proposta conforme documentação Deriv
            proposal_message = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": str(params["symbol"]),
                "amount": float(params["amount"]),
                "basis": "stake",
                "currency": "USD",
                "growth_rate": float(params["growth_rate"])
            }
            
            # Adicionar limit_order se presente
            if "limit_order" in params:
                proposal_message["limit_order"] = params["limit_order"]
            
            logger.info(f"🔄 Executando proposta via WebSocket - Session: {self.session_id}")
            logger.info(f"📋 Parâmetros: {proposal_message}")
            
            response = await self._send_request(proposal_message)
            
            if 'error' in response:
                raise Exception(f"Deriv API Error: {response['error']['message']}")
            
            logger.info(f"✅ Proposta executada com sucesso via WebSocket")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na proposta via WebSocket: {e}")
            raise e
    
    async def _process_tick(self, tick_data):
        """Processa tick recebido em tempo real"""
        try:
            if hasattr(self, 'bot_instance') and self.bot_instance:
                await self.bot_instance._handle_new_tick(tick_data)
        except Exception as e:
            await self.error_handler.handle_error(e, "tick_processing")
            logger.error(f"❌ Erro ao processar tick: {e}")
    
    async def subscribe_ticks(self, symbol: str):
        """Inicia subscription de ticks em tempo real"""
        await self.ensure_connection()
        
        try:
            # Estrutura de subscription conforme documentação Deriv
            tick_message = {
                "ticks": symbol,
                "subscribe": 1
            }
            
            logger.info(f"📊 Iniciando subscription de ticks para {symbol}")
            
            response = await self._send_request(tick_message)
            
            if 'error' in response:
                raise Exception(f"Deriv API Error: {response['error']['message']}")
            
            logger.info(f"✅ Subscription de ticks ativa para {symbol}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar subscription de ticks: {e}")
            raise e
    
    def set_bot_instance(self, bot_instance):
        """Define a instância do bot para callback de ticks"""
        self.bot_instance = bot_instance
    
    async def portfolio(self, params=None):
        """Obtém portfolio de contratos ativos usando WebSocket nativo"""
        await self.ensure_connection()
        
        try:
            # Estrutura de portfolio conforme documentação Deriv
            portfolio_message = {
                "portfolio": 1
            }
            
            logger.debug(f"📊 Solicitando portfolio: {portfolio_message}")
            
            response = await self._send_request(portfolio_message)
            
            if 'error' in response:
                raise Exception(f"Deriv API Error: {response['error']['message']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter portfolio via WebSocket: {e}")
            raise e
    
    async def disconnect(self):
        """Desconecta adequadamente o WebSocket"""
        logger.info("🔌 Desconectando WebSocket...")
        
        self.connected = False
        self.authorized = False
        
        # Limpar requests pendentes
        for req_id, future in self.pending_requests.items():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
        
        if self.ws:
            try:
                await self.ws.close()
                logger.info("✅ WebSocket desconectado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao desconectar WebSocket: {e}")
        
        self.ws = None
        self.session_id = None

# ============================================================================
# CLASSE PRINCIPAL DO BOT ACCUMULATOR
# ============================================================================
class AccumulatorScalpingBot:
    """Bot Accumulator Scalping com lógica fiel ao XML e resiliência a falhas"""
    
    def __init__(self):
        # Sistema de tratamento de erros
        self.error_handler = RobustErrorHandler(NOME_BOT)
        
        self.api_manager = DerivWebSocketNativo()
        self.ativo = ATIVO
        
        # VARIÁVEIS CONFORME XML ORIGINAL
        self.stake = STAKE_INICIAL  # Stake (variável)
        self.initial_stake = STAKE_INICIAL  # initial stake (constante)
        self.total_lost = 0.0  # total lost
        self.khizzbot = KHIZZBOT  # khizzbot = 50
        self.account_initial_take_profit = STAKE_INICIAL * TAKE_PROFIT_PERCENTUAL  # DT inicial
        self.dt = self.account_initial_take_profit  # DT (take profit dinâmico)
        
        # Controles de parada
        self.win_stop = WIN_STOP
        self.loss_limit = LOSS_LIMIT
        self.total_profit = 0.0  # Lucro total acumulado
        
        self.ticks_history = []
        self.ciclo = 0
        
        # NOVO: Sistema de tick stream em tempo real
        self.tick_buffer = []  # Buffer para manter últimos 5 ticks
        self.tick_subscription_active = False  # Flag para controlar subscription
        
        # NOVO: Sistema robusto de execução de ordens
        self.robust_order_system = RobustOrderSystem(self.api_manager)
        
        # SISTEMA ORIGINAL (mantido para compatibilidade)
        self.sync_system = EnhancedSyncSystem(max_concurrent_operations=2, max_queue_size=3)
        
        # NOVOS SISTEMAS APRIMORADOS
        self.enhanced_tick_buffer = EnhancedTickBuffer(max_size=10, tolerance_seconds=1.0)
        self.websocket_recovery = WebSocketRecoveryManager(max_retries=5, base_delay=2.0)
        self.signal_queue = ThreadSafeSignalQueue(max_size=10, max_concurrent=2)
        self.health_monitor = SystemHealthMonitor(
            deadlock_threshold=120.0,
            inactivity_threshold=180.0,
            high_failure_rate=0.7
        )
        
        # Configurar callbacks de recovery
        self._setup_recovery_callbacks()
        
        # Cache de parâmetros pré-validados
        self._cached_params = None
        self._params_cache_time = 0
        self._params_cache_ttl = 5.0  # 5 segundos
        
        # Sistema de debugging avançado
        self._signal_history = []
        self._max_signal_history = 100
        
        # NOVO: Sistema de tracking de tasks assíncronas e graceful shutdown
        self._running_tasks = set()  # Conjunto de tasks ativas
        self._shutdown_event = asyncio.Event()  # Evento para sinalizar shutdown
        self._is_shutting_down = False  # Flag para indicar se está em processo de shutdown
        self._task_lock = asyncio.Lock()  # Lock para operações thread-safe com tasks
        self._restart_requested = False  # Flag para indicar se restart foi solicitado
        self._debug_log_file = f"debug_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    async def create_tracked_task(self, coro, name: str = None):
        """Método centralizado para criação de tasks com tracking automático"""
        if self._is_shutting_down:
            logger.warning(f"⚠️ Tentativa de criar task '{name}' durante shutdown - ignorando")
            return None
            
        async with self._task_lock:
            task = asyncio.create_task(coro, name=name)
            self._running_tasks.add(task)
            
            # Callback para remover task quando completar
            def task_done_callback(completed_task):
                self._running_tasks.discard(completed_task)
                if completed_task.cancelled():
                    logger.debug(f"🔄 Task '{name or 'unnamed'}' foi cancelada")
                elif completed_task.exception():
                    logger.error(f"❌ Task '{name or 'unnamed'}' falhou: {completed_task.exception()}")
                else:
                    logger.debug(f"✅ Task '{name or 'unnamed'}' completada com sucesso")
            
            task.add_done_callback(task_done_callback)
            logger.debug(f"📝 Task '{name or 'unnamed'}' criada e rastreada ({len(self._running_tasks)} tasks ativas)")
            return task
    
    async def shutdown_gracefully(self, timeout: float = 30.0):
        """Implementa shutdown graceful cancelando todas as tasks ativas"""
        if self._is_shutting_down:
            logger.warning("⚠️ Shutdown já em andamento")
            return
            
        logger.info("🛑 Iniciando shutdown graceful...")
        self._is_shutting_down = True
        self._shutdown_event.set()
        
        # Copiar conjunto de tasks para evitar modificação durante iteração
        async with self._task_lock:
            tasks_to_cancel = self._running_tasks.copy()
        
        if not tasks_to_cancel:
            logger.info("✅ Nenhuma task ativa para cancelar")
            return
            
        logger.info(f"🔄 Cancelando {len(tasks_to_cancel)} tasks ativas...")
        
        # Cancelar todas as tasks
        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()
        
        # Aguardar cancelamento com timeout
        if tasks_to_cancel:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                    timeout=timeout
                )
                logger.info("✅ Todas as tasks foram canceladas com sucesso")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout de {timeout}s atingido - algumas tasks podem não ter sido canceladas")
                # Forçar cancelamento das tasks restantes
                for task in tasks_to_cancel:
                    if not task.done():
                        logger.warning(f"⚠️ Forçando cancelamento da task: {task.get_name()}")
                        task.cancel()
        
        # Limpar conjunto de tasks
        async with self._task_lock:
            self._running_tasks.clear()
        
        logger.info("🧹 Shutdown graceful concluído")
    
    def request_restart(self):
        """Solicita restart do bot de forma segura"""
        logger.info("🔄 Restart solicitado")
        self._restart_requested = True
        self._shutdown_event.set()
    
    def setup_signal_handlers(self):
        """Configura signal handlers para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Signal {signum} recebido - iniciando shutdown graceful")
            self.request_restart()
        
        # Configurar handlers apenas se estivermos no thread principal
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGTERM, signal_handler)
                signal.signal(signal.SIGINT, signal_handler)
                logger.info("✅ Signal handlers configurados (SIGTERM, SIGINT)")
            else:
                logger.warning("⚠️ Signal handlers não configurados - não estamos no thread principal")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao configurar signal handlers: {e}")
    
    async def wait_for_shutdown_signal(self):
        """Aguarda sinal de shutdown"""
        await self._shutdown_event.wait()
        return self._restart_requested
        
        # Sistema de monitoramento de inatividade
        self._last_operation_time = time.time()  # Timestamp da última operação
        self._inactivity_timeout = 120  # 2 minutos em segundos
        self._restart_in_progress = False  # Flag para evitar múltiplos restarts
        self._operation_count = 0  # Contador de operações executadas
        
        # Lock global para evitar deadlock no sistema de recovery
        self._global_restart_lock = asyncio.Lock()
        
        logger.info(f"🤖 {NOME_BOT} inicializado")
        logger.info(f"📊 Configuração do Bot:")
        logger.info(f"   • Ativo: {ATIVO}")
        logger.info(f"   • Initial Stake: ${self.initial_stake}")
        logger.info(f"   • Stake Atual: ${self.stake}")
        logger.info(f"   • Take Profit %: {TAKE_PROFIT_PERCENTUAL*100}%")
        logger.info(f"   • Growth Rate: {GROWTH_RATE*100}%")
        logger.info(f"   • Khizzbot: {self.khizzbot}")
        logger.info(f"   • Win Stop: ${self.win_stop}")
        logger.info(f"   • Loss Limit: ${self.loss_limit}")
        logger.info(f"   • Sistema de Sinais: Integrado com radar_de_apalancamiento_signals")
    
    def _setup_recovery_callbacks(self):
        """Configura callbacks para recovery automático"""
        try:
            # Callbacks do WebSocket Recovery
            self.websocket_recovery.set_callbacks(
                on_connected=self._on_websocket_connected,
                on_disconnected=self._on_websocket_disconnected,
                on_reconnect_failed=self._on_websocket_failed
            )
            
            # Callbacks do Health Monitor
            self.health_monitor.set_recovery_callbacks(
                on_deadlock_detected=self._on_deadlock_detected,
                on_connection_issues=self._on_connection_issues,
                on_high_failure_rate=self._on_high_failure_rate,
                on_inactivity_detected=self._on_inactivity_detected,
                on_system_restart=self._force_restart_bot
            )
            
            logger.info("✅ Callbacks de recovery configurados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar callbacks: {e}")
    
    async def _on_websocket_connected(self):
        """Callback chamado quando WebSocket conecta"""
        logger.info("🔗 WebSocket conectado via recovery manager")
    
    async def _on_websocket_disconnected(self):
        """Callback chamado quando WebSocket desconecta"""
        logger.warning("⚠️ WebSocket desconectado - recovery será iniciado")
    
    async def _on_websocket_failed(self):
        """Callback chamado quando recovery do WebSocket falha"""
        logger.error("❌ Recovery do WebSocket falhou - intervenção manual necessária")
    
    async def cleanup_resources(self):
        """Limpa recursos e conexões antes de reiniciar o bot"""
        logger.info("🧹 Iniciando limpeza de recursos para reinicialização...")
        
        try:
            # Cancelar qualquer subscription ativa
            if self.tick_subscription_active:
                try:
                    await self.api_manager.unsubscribe_ticks(ATIVO)
                    logger.info("📡 Subscription de ticks cancelada")
                except Exception as e:
                    logger.error(f"❌ Erro ao cancelar subscription: {e}")
            
            # Limpar buffers e filas
            self.tick_buffer.clear()
            self.enhanced_tick_buffer.clear()
            self.signal_queue.clear()
            logger.info("🧹 Buffers e filas limpos")
            
            # Resetar circuit breaker
            self.robust_order_system.reset_circuit_breaker()
            logger.info("🔄 Circuit breaker resetado")
            
            # Desconectar API
            if self.api_manager.connected:
                try:
                    await self.api_manager.disconnect()
                    logger.info("🔌 API desconectada")
                except Exception as e:
                    logger.error(f"❌ Erro ao desconectar API: {e}")
            
            # Resetar flags
            self.tick_subscription_active = False
            self._restart_in_progress = False
            
            # Salvar histórico antes de limpar
            self._save_history_to_file()
            
            logger.info("✅ Limpeza de recursos concluída com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante limpeza de recursos: {e}")
            return False
    
    async def _on_deadlock_detected(self):
        """Callback chamado quando deadlock é detectado"""
        logger.error("🔄 Deadlock detectado - limpando queue de sinais")
        await self.signal_queue.clear_queue()
    
    async def _on_connection_issues(self):
        """Callback chamado para problemas de conexão"""
        logger.error("🔄 Problemas de conexão detectados - reconectando")
        await self._reconnect_and_resubscribe()
    
    async def _on_high_failure_rate(self):
        """Callback chamado para alta taxa de falhas"""
        logger.error("🔄 Alta taxa de falhas detectada - resetando circuit breaker")
        self.signal_queue.circuit_breaker.reset()
    
    async def _on_inactivity_detected(self):
        """Callback chamado para inatividade detectada"""
        logger.error("🔄 Inatividade detectada - reiniciando subscription")
        await self.api_manager.subscribe_ticks(ATIVO)
    
    @with_error_handling(ErrorType.DATA_PROCESSING, ErrorSeverity.MEDIUM)
    async def _handle_new_tick(self, tick_data):
        """Processa novo tick recebido em tempo real com sistema de queue"""
        try:
            # Timestamp preciso para debugging
            tick_timestamp = time.time()
            
            # Extrair valor do tick
            tick_value = float(tick_data.get('quote', 0))
            
            if tick_value <= 0:
                logger.warning(f"⚠️ Tick inválido recebido: {tick_data}")
                return
            
            # Log detalhado com timestamp preciso
            logger.debug(f"📥 TICK_RECEIVED: {tick_value:.5f} at {tick_timestamp:.6f}")
            
            # Adicionar ao buffer
            self.tick_buffer.append(tick_value)
            
            # Manter apenas os últimos 5 ticks
            if len(self.tick_buffer) > 5:
                self.tick_buffer.pop(0)  # Remove o mais antigo
            
            # Executar análise quando tiver 5 ticks
            if len(self.tick_buffer) == 5:
                pattern_detected = self.analisar_padrao_entrada(self.tick_buffer.copy())
                
                if pattern_detected:
                    logger.info(f"🎯 PATTERN_DETECTED at {tick_timestamp:.6f}")
                
                # Salvar sinal no histórico de debugging
                self._save_signal_to_history(self.tick_buffer.copy(), pattern_detected)
                
                # Enviar sinal para queue (sempre, mesmo sem padrão para estatísticas)
                success = self.sync_system.queue_signal(self.tick_buffer.copy(), pattern_detected)
                
                if success:
                    logger.debug(f"📤 SIGNAL_QUEUED: pattern={pattern_detected} at {tick_timestamp:.6f}")
                else:
                    logger.warning(f"⚠️ Falha ao enfileirar sinal at {tick_timestamp:.6f}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar tick: {e}")
    
    async def _process_signals_from_queue(self):
        """Processa sinais da queue de forma assíncrona"""
        while True:
            try:
                # Obter próximo sinal da queue (não bloqueante)
                signal = self.sync_system.get_next_signal()
                
                if signal and signal.pattern_detected:
                    operation_timestamp = time.time()
                    logger.info(f"🚀 OPERATION_QUEUED at {operation_timestamp:.6f}")
                    
                    # Verificar se pode executar operação
                    if self.sync_system.can_execute_operation():
                        # Adquirir semáforo para operação
                        async with self.sync_system.operation_semaphore:
                            try:
                                logger.info(f"⚡ OPERATION_EXECUTING at {time.time():.6f}")
                                
                                # Executar compra
                                contract_id = await self.executar_compra_accu()
                                
                                if contract_id:
                                    logger.info(f"✅ OPERATION_SUCCESS at {time.time():.6f}")
                                    self.sync_system.record_operation_success()
                                    
                                    # Monitorar contrato
                                    lucro = await self.monitorar_contrato(contract_id)
                                    
                                    # Aplicar gestão de risco
                                    self.aplicar_gestao_risco(lucro)
                                else:
                                    logger.error(f"❌ OPERATION_FAILED at {time.time():.6f}")
                                    self.sync_system.record_operation_failure()
                                    
                            except Exception as e:
                                logger.error(f"❌ Erro durante execução da compra: {e}")
                                self.sync_system.record_operation_failure()
                    else:
                        logger.warning(f"⚠️ Operação rejeitada - limite de operações simultâneas atingido")
                
                # Pequeno delay para evitar loop intensivo
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento de sinais: {e}")
                await asyncio.sleep(1)
        
        # Validar configuração inicial
        self._validar_configuracao_inicial()
    
    def _pre_validate_params(self):
        """Pré-valida parâmetros para otimização de latência"""
        current_time = time.time()
        
        # Verificar se cache ainda é válido
        if (self._cached_params and 
            current_time - self._params_cache_time < self._params_cache_ttl):
            return self._cached_params
        
        try:
            # Validar parâmetros ACCU
            params = {
                'contract_type': 'ACCU',
                'symbol': ATIVO,
                'currency': 'USD',
                'amount': float(STAKE_INICIAL),
                'growth_rate': float(GROWTH_RATE),
                'take_profit': float(TAKE_PROFIT_PERCENTUAL)
            }
            
            # Validações básicas
            if params['amount'] <= 0:
                raise ValueError(f"Stake inválido: {params['amount']}")
            
            if not (0.01 <= params['growth_rate'] <= 0.05):
                raise ValueError(f"Growth rate inválido: {params['growth_rate']}")
            
            if not (0.01 <= params['take_profit'] <= 1.0):
                raise ValueError(f"Take profit inválido: {params['take_profit']}")
            
            # Atualizar cache
            self._cached_params = params
            self._params_cache_time = current_time
            
            logger.debug(f"✅ Parâmetros pré-validados e cacheados")
            return params
            
        except Exception as e:
            logger.error(f"❌ Erro na pré-validação de parâmetros: {e}")
            return None
    
    async def _real_time_monitoring(self):
        """Monitoramento em tempo real com logs estruturados e detecção de problemas"""
        deadlock_start_time = None
        connection_error_start_time = None
        last_successful_operation_time = time.time()
        error_threshold = 120  # 2 minutos em segundos
        
        while True:
            try:
                # Log estruturado a cada 30 segundos
                stats = self.sync_system.get_statistics()
                current_time = time.time()
                
                last_signal_str = f"{stats['last_signal_time']:.6f}" if stats['last_signal_time'] else "None"
                
                logger.info(f"📊 STATUS_REPORT: "
                          f"queue_size={stats['queue_size']}, "
                          f"active_operations={stats['active_operations']}, "
                          f"circuit_breaker={stats['circuit_breaker_state']}, "
                          f"last_signal={last_signal_str}, "
                          f"total_signals={stats['total_signals_processed']}, "
                          f"successful_operations={stats['successful_operations']}, "
                          f"failed_operations={stats['failed_operations']}")
                
                # Atualizar tempo da última operação bem-sucedida
                if stats['successful_operations'] > 0:
                    last_successful_operation_time = current_time
                
                # 1. Detecção de deadlock: queue cheia + sem operações ativas
                is_deadlocked = (stats['queue_size'] >= 3 and stats['active_operations'] == 0)
                
                # 2. Detecção de problemas de conexão/operação
                total_operations = stats['successful_operations'] + stats['failed_operations']
                failure_rate = stats['failed_operations'] / max(total_operations, 1)
                
                connection_issues = (
                    # WebSocket realmente desconectado
                    (hasattr(self.api_manager, 'websocket') and 
                     self.api_manager.websocket is not None and 
                     self.api_manager.websocket.closed) or
                    # Circuit breaker aberto por muito tempo
                    stats['circuit_breaker_state'] == 'OPEN' or
                    # Taxa de falha muito alta (>70%) com pelo menos 10 operações
                    (total_operations >= 10 and failure_rate > 0.7) or
                    # Sem operações bem-sucedidas há muito tempo (apenas se já houve operações)
                    (total_operations > 0 and (current_time - last_successful_operation_time) > 600)  # 10 minutos
                )
                
                # 3. Verificar latência da conexão
                high_latency = False
                if hasattr(self.api_manager, 'last_ping_time'):
                    latency = current_time - self.api_manager.last_ping_time
                    if latency > 2.0:  # Latência > 2s
                        high_latency = True
                        logger.warning(f"⚠️ Alta latência detectada: {latency:.3f}s")
                
                # Detectar qualquer problema crítico
                critical_issue = is_deadlocked or connection_issues or high_latency
                
                if critical_issue:
                    # Identificar tipo de problema
                    problem_type = []
                    if is_deadlocked:
                        problem_type.append("DEADLOCK")
                    if connection_issues:
                        problem_type.append("CONNECTION_ISSUES")
                    if high_latency:
                        problem_type.append("HIGH_LATENCY")
                    
                    if deadlock_start_time is None:
                        deadlock_start_time = current_time
                        logger.warning(f"⚠️ PROBLEMA CRÍTICO DETECTADO: {', '.join(problem_type)} - iniciando contagem de {error_threshold}s")
                        logger.warning(f"   Detalhes: queue_size={stats['queue_size']}, active_operations={stats['active_operations']}, "
                                     f"circuit_breaker={stats['circuit_breaker_state']}, failed_ops={stats['failed_operations']}")
                    else:
                        problem_duration = current_time - deadlock_start_time
                        logger.warning(f"⚠️ PROBLEMA ATIVO há {problem_duration:.1f}s - limite: {error_threshold}s - Tipos: {', '.join(problem_type)}")
                        
                        if problem_duration >= error_threshold:
                            logger.error(f"🔄 PROBLEMA CRÍTICO: Reiniciando bot após {problem_duration:.1f}s - Tipos: {', '.join(problem_type)}")
                            # Forçar reinicialização do sistema
                            await self._force_restart_bot()
                            return  # Sair do loop de monitoramento
                else:
                    # Reset do contador se a situação foi resolvida
                    if deadlock_start_time is not None:
                        logger.info(f"✅ PROBLEMAS RESOLVIDOS: queue_size={stats['queue_size']}, active_operations={stats['active_operations']}, "
                                  f"circuit_breaker={stats['circuit_breaker_state']}")
                        deadlock_start_time = None
                
                await asyncio.sleep(30)  # Log a cada 30 segundos
                
            except Exception as e:
                 logger.error(f"❌ Erro no monitoramento em tempo real: {e}")
                 # Se houver erro no próprio monitoramento, também considerar reiniciar
                 if connection_error_start_time is None:
                     connection_error_start_time = time.time()
                 elif (time.time() - connection_error_start_time) > 180:  # 3 minutos de erros
                     logger.error(f"🔄 ERRO PERSISTENTE NO MONITORAMENTO: Reiniciando bot")
                     await self._force_restart_bot()
                     return
                 await asyncio.sleep(30)
    
    async def _status_handler(self, request):
        """Handler para endpoint /status"""
        try:
            stats = self.sync_system.get_statistics()
            
            status_data = {
                'timestamp': time.time(),
                'bot_name': NOME_BOT,
                'active': True,
                'circuit_breaker_state': stats['circuit_breaker_state'],
                'active_operations': stats['active_operations'],
                'queue_size': stats['queue_size'],
                'last_signal_time': stats['last_signal_time'],
                'total_signals': stats['total_signals'],
                'successful_operations': stats['successful_operations'],
                'failed_operations': stats['failed_operations'],
                'tick_buffer_size': len(self.tick_buffer),
                'connection_status': self.api_manager.connected if hasattr(self, 'api_manager') else False,
                'subscription_active': self.tick_subscription_active,
                'cached_params_valid': (time.time() - self._params_cache_time) < self._params_cache_ttl if self._cached_params else False
            }
            
            return web.json_response(status_data)
            
        except Exception as e:
            logger.error(f"❌ Erro no endpoint /status: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def _start_http_server(self):
        """Inicia servidor HTTP para endpoint /status com fallback de portas"""
        try:
            app = web.Application()
            app.router.add_get('/status', self._status_handler)
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            # Tentar portas sequencialmente
            ports_to_try = [8080, 8081, 8082, 8083, 8084]
            server_started = False
            
            for port in ports_to_try:
                try:
                    site = web.TCPSite(runner, 'localhost', port)
                    await site.start()
                    logger.info(f"🌐 Servidor HTTP iniciado em http://localhost:{port}/status")
                    server_started = True
                    break
                except OSError as port_error:
                    logger.warning(f"⚠️ Porta {port} já está em uso, tentando próxima porta...")
                    continue
            
            if not server_started:
                logger.error("❌ Não foi possível iniciar servidor HTTP - todas as portas estão ocupadas")
                # Desabilitar servidor HTTP se não conseguir iniciar
                logger.info("ℹ️ Continuando sem servidor HTTP de status")
            
        except Exception as e:
             logger.error(f"❌ Erro ao iniciar servidor HTTP: {e}")
             logger.info("ℹ️ Continuando sem servidor HTTP de status")
    
    async def _force_restart_bot(self):
        """Força reinicialização completa do bot em caso de deadlock crítico"""
        # Verificar se já existe um restart em andamento
        if self._global_restart_lock.locked():
            logger.warning("🔄 Restart já em andamento, ignorando nova solicitação")
            return False
            
        async with self._global_restart_lock:
            logger.info("🔄 Forçando o reinício do bot devido a inatividade ou erro...")
            restart_start_time = time.time()
            
            try:
                # 1. Marcar estado de reinicialização
                if hasattr(self, 'is_restarting'):
                    self.is_restarting = True
                
                # 2. Parar subscription de ticks primeiro
                logger.info("📡 Parando subscription de ticks...")
                if hasattr(self, 'tick_subscription_active'):
                    self.tick_subscription_active = False
                
                # 3. Desconectar de forma limpa com timeout
                logger.info("🔌 Fechando conexão existente...")
                if self.api_manager and hasattr(self.api_manager, 'connected') and self.api_manager.connected:
                    try:
                        await asyncio.wait_for(self.api_manager.disconnect(), timeout=10.0)
                        logger.info("✅ Desconexão realizada com sucesso")
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Timeout na desconexão, forçando fechamento")
                    except Exception as disconnect_error:
                        logger.warning(f"⚠️ Erro na desconexão: {disconnect_error}")
                
                # 4. Limpar buffers e resetar estados
                logger.info("🧹 Limpando buffers e resetando estados...")
                if hasattr(self, 'tick_buffer'):
                    self.tick_buffer.clear()
                if hasattr(self, 'enhanced_tick_buffer'):
                    try:
                        self.enhanced_tick_buffer.clear_buffer()
                    except:
                        pass
                if hasattr(self, 'signal_queue'):
                    try:
                        self.signal_queue.clear_queue()
                    except:
                        pass
                
                # 5. Aguardar estabilização
                await asyncio.sleep(3)

                # 6. Reconectar com retry
                logger.info("🔌 Estabelecendo nova conexão...")
                connection_attempts = 0
                max_connection_attempts = 3
                
                while connection_attempts < max_connection_attempts:
                    try:
                        connection_attempts += 1
                        logger.info(f"🔌 Tentativa de conexão {connection_attempts}/{max_connection_attempts}")
                        
                        # Timeout para conexão
                        connect_success = await asyncio.wait_for(
                            self.api_manager.connect(), 
                            timeout=15.0
                        )
                        
                        if connect_success:
                            logger.info("✅ Nova conexão estabelecida com sucesso")
                            break
                        else:
                            logger.warning(f"⚠️ Falha na tentativa {connection_attempts}")
                            if connection_attempts < max_connection_attempts:
                                await asyncio.sleep(5)
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"⚠️ Timeout na tentativa de conexão {connection_attempts}")
                        if connection_attempts < max_connection_attempts:
                            await asyncio.sleep(5)
                    except Exception as conn_error:
                        logger.error(f"❌ Erro na tentativa de conexão {connection_attempts}: {conn_error}")
                        if connection_attempts < max_connection_attempts:
                            await asyncio.sleep(5)
                else:
                    logger.error("❌ Falha em todas as tentativas de conexão")
                    return False

                # 7. Reconfigurar callback do bot
                logger.info("🔧 Reconfigurando callback do bot...")
                if hasattr(self.api_manager, 'set_bot_instance'):
                    self.api_manager.set_bot_instance(self)

                # 8. Tentar se reinscrever com tratamento de erro robusto
                logger.info(f"📡 Reinscrevendo nos ticks para o ativo {ATIVO}...")
                subscription_attempts = 0
                max_subscription_attempts = 3
                
                while subscription_attempts < max_subscription_attempts:
                    try:
                        subscription_attempts += 1
                        logger.info(f"📡 Tentativa de subscription {subscription_attempts}/{max_subscription_attempts}")
                        
                        await asyncio.wait_for(
                            self.api_manager.subscribe_ticks(ATIVO), 
                            timeout=15.0
                        )
                        
                        self.tick_subscription_active = True
                        logger.info("✅ Reinscrição nos ticks realizada com sucesso")
                        break
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"⚠️ Timeout na subscription {subscription_attempts}")
                        if subscription_attempts < max_subscription_attempts:
                            await asyncio.sleep(3)
                    except asyncio.CancelledError:
                        logger.warning("⚠️ Subscription cancelada durante o reinício")
                        raise
                    except Exception as sub_error:
                        logger.error(f"❌ Erro na subscription {subscription_attempts}: {sub_error}")
                        if subscription_attempts < max_subscription_attempts:
                            await asyncio.sleep(3)
                else:
                    logger.error("❌ Falha em todas as tentativas de subscription")
                    return False
                
                # 9. Validar estado final
                await asyncio.sleep(2)  # Aguardar estabilização
                
                final_validation = (
                    hasattr(self, 'api_manager') and
                    self.api_manager and
                    hasattr(self.api_manager, 'connected') and
                    self.api_manager.connected and
                    hasattr(self, 'tick_subscription_active') and
                    self.tick_subscription_active
                )
                
                if final_validation:
                    restart_duration = time.time() - restart_start_time
                    logger.info(f"✅ Reinício completo bem-sucedido em {restart_duration:.1f}s")
                    
                    # Atualizar timestamps
                    if hasattr(self, 'last_activity_time'):
                        self.last_activity_time = time.time()
                    if hasattr(self, '_last_operation_time'):
                        self._last_operation_time = time.time()
                        
                    return True
                else:
                    logger.error("❌ Falha na validação final do reinício")
                    return False

            except Exception as e:
                restart_duration = time.time() - restart_start_time
                logger.critical(f"❌ Erro crítico durante o processo de reinício forçado ({restart_duration:.1f}s): {e}")
                import traceback
                logger.critical(f"Stack trace: {traceback.format_exc()}")
                return False
            finally:
                # O bloco finally garante que, mesmo com erros, o estado é atualizado
                if hasattr(self, 'is_restarting'):
                    self.is_restarting = False
                restart_duration = time.time() - restart_start_time
                logger.info(f"🏁 Processo de reinício finalizado em {restart_duration:.1f}s")
    
    async def _check_inactivity_and_restart(self):
        """Monitora inatividade continuamente e reinicia o bot se necessário"""
        logger.info("🔍 Sistema de monitoramento de inatividade iniciado")
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                await asyncio.sleep(30)  # Verifica a cada 30 segundos
                
                if self._restart_in_progress:
                    logger.debug("⏸️ Reinicialização em progresso, pulando verificação")
                    continue
                
                current_time = time.time()
                time_since_last_operation = current_time - self._last_operation_time
                
                # Verificar múltiplos indicadores de problemas
                connection_healthy = (
                    hasattr(self, 'api_manager') and 
                    self.api_manager and 
                    self.api_manager.connected and
                    not (hasattr(self.api_manager, 'websocket') and 
                         self.api_manager.websocket and 
                         self.api_manager.websocket.closed)
                )
                
                subscription_healthy = (
                    hasattr(self, 'tick_subscription_active') and 
                    self.tick_subscription_active
                )
                
                # Log de monitoramento detalhado
                logger.info(f"🔍 HEALTH_CHECK: inatividade={time_since_last_operation:.1f}s/{self._inactivity_timeout}s, "
                          f"conexão={'✅' if connection_healthy else '❌'}, "
                          f"subscription={'✅' if subscription_healthy else '❌'}, "
                          f"operações={self._operation_count}")
                
                # Condições para reinício
                needs_restart = (
                    # Inatividade prolongada
                    time_since_last_operation > self._inactivity_timeout or
                    # Conexão perdida
                    not connection_healthy or
                    # Subscription inativa
                    not subscription_healthy
                )
                
                if needs_restart:
                    reason = []
                    if time_since_last_operation > self._inactivity_timeout:
                        reason.append(f"inatividade {int(time_since_last_operation)}s")
                    if not connection_healthy:
                        reason.append("conexão perdida")
                    if not subscription_healthy:
                        reason.append("subscription inativa")
                    
                    logger.warning(f"⚠️ PROBLEMA DETECTADO: {', '.join(reason)}")
                    logger.warning(f"🔄 Iniciando reinício automático do bot...")
                    
                    self._restart_in_progress = True
                    
                    # Executar restart com timeout
                    try:
                        restart_success = await asyncio.wait_for(
                            self._force_restart_bot(), 
                            timeout=60.0  # Timeout de 60s para restart
                        )
                        
                        if restart_success:
                            # Resetar timestamp e contador
                            self._last_operation_time = time.time()
                            self._operation_count = 0
                            consecutive_errors = 0  # Reset contador de erros
                            logger.info("✅ Bot reiniciado com sucesso")
                        else:
                            logger.error("❌ Falha no reinício automático")
                            consecutive_errors += 1
                            
                    except asyncio.TimeoutError:
                        logger.error("❌ Timeout no reinício automático (60s)")
                        consecutive_errors += 1
                    except Exception as restart_error:
                        logger.error(f"❌ Erro durante reinício: {restart_error}")
                        consecutive_errors += 1
                    
                    self._restart_in_progress = False
                    
                    # Se muitos erros consecutivos, aguardar mais tempo
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"❌ Muitos erros consecutivos ({consecutive_errors}), aguardando 5 minutos")
                        await asyncio.sleep(300)  # 5 minutos
                        consecutive_errors = 0
                else:
                    # Reset contador de erros se tudo está funcionando
                    consecutive_errors = 0
                    
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Erro no monitoramento de inatividade ({consecutive_errors}/{max_consecutive_errors}): {e}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
                self._restart_in_progress = False
                
                # Aguardar mais tempo se muitos erros
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"❌ Muitos erros no monitoramento, aguardando 5 minutos")
                    await asyncio.sleep(300)  # 5 minutos
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(30)  # Aguarda antes de tentar novamente
    
    def _update_operation_timestamp(self):
        """Atualiza o timestamp da última operação"""
        self._last_operation_time = time.time()
        self._operation_count += 1
        logger.debug(f"📊 Operação #{self._operation_count} registrada às {datetime.now().strftime('%H:%M:%S')}")
    
    def _save_signal_to_history(self, signal_data, pattern_detected, operation_result=None):
        """Salva sinal no histórico para debugging"""
        try:
            timestamp_precise = time.time()
            
            signal_record = {
                'timestamp': timestamp_precise,
                'timestamp_readable': datetime.fromtimestamp(timestamp_precise).strftime('%Y-%m-%d %H:%M:%S.%f'),
                'ticks': signal_data.copy() if signal_data else [],
                'pattern_detected': pattern_detected,
                'operation_result': operation_result,
                'queue_size_at_time': self.sync_system.get_statistics()['queue_size'],
                'active_operations_at_time': self.sync_system.get_statistics()['active_operations']
            }
            
            # Adicionar ao histórico
            self._signal_history.append(signal_record)
            
            # Manter apenas os últimos 100 sinais
            if len(self._signal_history) > self._max_signal_history:
                self._signal_history.pop(0)
            
            # Salvar em arquivo JSON a cada 10 sinais
            if len(self._signal_history) % 10 == 0:
                self._save_history_to_file()
            
            # Log detalhado com timestamp preciso
            logger.debug(f"🔍 SIGNAL_SAVED: timestamp={timestamp_precise:.6f}, "
                        f"pattern={pattern_detected}, ticks={len(signal_data) if signal_data else 0}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sinal no histórico: {e}")
    
    def _save_history_to_file(self):
        """Salva histórico de sinais em arquivo JSON"""
        try:
            with open(self._debug_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'bot_name': NOME_BOT,
                    'created_at': datetime.now().isoformat(),
                    'total_signals': len(self._signal_history),
                    'signals': self._signal_history
                }, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Histórico salvo: {len(self._signal_history)} sinais em {self._debug_log_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar histórico em arquivo: {e}")
    
    def _validar_configuracao_inicial(self):
        """Valida a configuração inicial do bot"""
        logger.info("🔍 VALIDANDO CONFIGURAÇÃO INICIAL...")
        
        # Validar GROWTH_RATE
        if GROWTH_RATE < 0.01 or GROWTH_RATE > 0.05:
            raise ValueError(f"❌ GROWTH_RATE inválido: {GROWTH_RATE*100}% (deve ser 1-5%)")
        
        # Validar ATIVO
        if not ATIVO or not isinstance(ATIVO, str):
            raise ValueError(f"❌ ATIVO inválido: {ATIVO}")
        
        # Validar STAKE_INICIAL
        if STAKE_INICIAL < 0.35 or STAKE_INICIAL > 50000:
            raise ValueError(f"❌ STAKE_INICIAL inválido: ${STAKE_INICIAL} (deve ser $0.35-$50,000)")
        
        # Validar TAKE_PROFIT_PERCENTUAL
        if TAKE_PROFIT_PERCENTUAL <= 0 or TAKE_PROFIT_PERCENTUAL > 1:
            raise ValueError(f"❌ TAKE_PROFIT_PERCENTUAL inválido: {TAKE_PROFIT_PERCENTUAL*100}%")
        
        logger.info("✅ Configuração inicial validada com sucesso!")
    
    def _validar_parametros_accu(self, params: Dict[str, Any]) -> bool:
        """Valida se os parâmetros do contrato ACCU estão corretos"""
        required_keys = ["proposal", "contract_type", "symbol", "amount", "basis", "currency", "growth_rate"]
        
        # Verificar se todas as chaves obrigatórias estão presentes
        if not all(key in params for key in required_keys):
            missing_keys = [key for key in required_keys if key not in params]
            logger.error(f"❌ Chaves obrigatórias ausentes: {missing_keys}")
            return False
        
        # Verificar valores específicos
        if params.get("contract_type") != "ACCU":
            logger.error(f"❌ Contract type deve ser 'ACCU', recebido: {params.get('contract_type')}")
            return False
        
        if params.get("basis") != "stake":
            logger.error(f"❌ Basis deve ser 'stake', recebido: {params.get('basis')}")
            return False
        
        # CORREÇÃO CRÍTICA: Aceitar tanto float quanto string para growth_rate
        growth_rate = params.get("growth_rate")
        if growth_rate is None:
            logger.error(f"❌ Growth rate ausente")
            return False
            
        # Converter para float se for string
        try:
            if isinstance(growth_rate, str):
                growth_rate_float = float(growth_rate)
            else:
                growth_rate_float = float(growth_rate)
                
            if growth_rate_float < 0.01 or growth_rate_float > 0.05:
                logger.error(f"❌ Growth rate deve ser entre 0.01 e 0.05, recebido: {growth_rate}")
                return False
        except (ValueError, TypeError):
            logger.error(f"❌ Growth rate inválido: {growth_rate}")
            return False
        
        if not isinstance(params.get("amount"), (int, float)) or params.get("amount") < 0.35:
            logger.error(f"❌ Amount deve ser >= 0.35, recebido: {params.get('amount')}")
            return False
        
        logger.info("✅ Parâmetros ACCU validados com sucesso!")
        return True
    
    async def obter_ultimos_5_ticks(self) -> List[float]:
        """Obtém os últimos 5 ticks do ativo com tratamento robusto de erros"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.api_manager.ticks_history(self.ativo, count=5)
                
                # A API retorna os dados em 'history' ao invés de 'ticks_history'
                if 'history' in response and 'prices' in response['history']:
                    prices = response['history']['prices']
                    self.ticks_history = prices[-5:] if len(prices) >= 5 else prices
                    return self.ticks_history
                elif 'ticks_history' in response and 'prices' in response['ticks_history']:
                    prices = response['ticks_history']['prices']
                    self.ticks_history = prices[-5:] if len(prices) >= 5 else prices
                    return self.ticks_history
                else:
                    raise Exception(f"Resposta inválida da API: {response}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao obter ticks (tentativa {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise Exception(f"Falha ao obter ticks após {max_retries} tentativas: {e}")
    
    def debug_comparacao_xml_python(self, ticks: List[float]) -> Dict[str, Any]:
        """Função de debug para comparar resultados XML vs Python"""
        if len(ticks) < 5:
            return {"erro": "Ticks insuficientes"}
            
        # SIMULAÇÃO DA LÓGICA XML EXATA
        tick4 = ticks[-5]  # FROM_END 5 (mais antigo)
        tick3 = ticks[-4]  # FROM_END 4
        tick2 = ticks[-3]  # FROM_END 3
        tick1 = ticks[-2]  # FROM_END 2
        tick_atual = ticks[-1]  # Tick atual (mais recente)
        
        # Cálculo dos sinais XML
        single4_xml = "Red" if tick4 > tick3 else "Blue"
        single3_xml = "Red" if tick3 > tick2 else "Blue"
        single2_xml = "Red" if tick2 > tick1 else "Blue"
        single1_xml = "Red" if tick1 > tick_atual else "Blue"
        
        # CORREÇÃO CRÍTICA: Usar verificação individual das condições com operador AND
        # Condição de entrada XML: single1=Red E single2=Red E single3=Red E single4=Blue
        entrada_xml = (single1_xml == "Red" and 
                      single2_xml == "Red" and 
                      single3_xml == "Red" and 
                      single4_xml == "Blue")
        
        debug_info = {
            "ticks_raw": ticks,
            "tick_positions": {
                "tick4 (FROM_END 5)": tick4,
                "tick3 (FROM_END 4)": tick3,
                "tick2 (FROM_END 3)": tick2,
                "tick1 (FROM_END 2)": tick1,
                "tick_atual": tick_atual
            },
            "comparacoes": {
                "tick4 > tick3": f"{tick4:.5f} > {tick3:.5f} = {tick4 > tick3}",
                "tick3 > tick2": f"{tick3:.5f} > {tick2:.5f} = {tick3 > tick2}",
                "tick2 > tick1": f"{tick2:.5f} > {tick1:.5f} = {tick2 > tick1}",
                "tick1 > tick_atual": f"{tick1:.5f} > {tick_atual:.5f} = {tick1 > tick_atual}"
            },
            "sinais_xml": {
                "single1": single1_xml,
                "single2": single2_xml,
                "single3": single3_xml,
                "single4": single4_xml
            },
            "padrao_completo": [single1_xml, single2_xml, single3_xml, single4_xml],
            "padrao_esperado": "single1=Red E single2=Red E single3=Red E single4=Blue",
            "entrada_detectada": entrada_xml,
            "timestamp": datetime.now().strftime('%H:%M:%S.%f')[:-3]
        }
        
        return debug_info
    
    def analisar_padrao_entrada(self, ticks: List[float]) -> bool:
        """ 
        Lógica de Padrão XML: single1=Red E single2=Red E single3=Red E single4=Blue 
        Onde os sinais são atribuídos em ordem cronológica reversa mas verificados individualmente 
        """ 
        if len(ticks) < 5: 
            return False 
     
        # Atribuições de tick do XML (indexação FROM_END) 
        tick4 = ticks[-5]  # FROM_END 5 (mais antigo) 
        tick3 = ticks[-4]  # FROM_END 4  
        tick2 = ticks[-3]  # FROM_END 3 
        tick1 = ticks[-2]  # FROM_END 2 
        tick_atual = ticks[-1]  # FROM_END 1 (atual/mais novo) 
     
        # Cálculos de sinal do XML 
        single4 = "Red" if tick4 > tick3 else "Blue" 
        single3 = "Red" if tick3 > tick2 else "Blue"  
        single2 = "Red" if tick2 > tick1 else "Blue" 
        single1 = "Red" if tick1 > tick_atual else "Blue" 
     
        # Condição de entrada XML: todas as quatro condições devem ser True simultaneamente 
        entrada_xml = (single1 == "Red" and 
                       single2 == "Red" and 
                       single3 == "Red" and 
                       single4 == "Blue") 
     
        # Log detalhado para debug 
        logger.info(f"📊 VERIFICAÇÃO DE PADRÃO XML:") 
        logger.info(f"   • single1 (tick1 > atual): {single1} ({tick1:.5f} > {tick_atual:.5f})") 
        logger.info(f"   • single2 (tick2 > tick1): {single2} ({tick2:.5f} > {tick1:.5f})") 
        logger.info(f"   • single3 (tick3 > tick2): {single3} ({tick3:.5f} > {tick2:.5f})") 
        logger.info(f"   • single4 (tick4 > tick3): {single4} ({tick4:.5f} > {tick3:.5f})") 
        logger.info(f"   • Padrão esperado: single1=Red E single2=Red E single3=Red E single4=Blue") 
        logger.info(f"   • Entrada detectada: {entrada_xml}") 
     
        if entrada_xml:
            logger.info("🎯 PADRÃO DE ENTRADA DETECTADO! (XML MATCH)")
            logger.info("🚀 EXECUTANDO COMPRA DO CONTRATO ACCUMULATOR...")
        else:
            logger.info("⏳ Aguardando padrão correto...")
            
        return entrada_xml
    
    async def log_to_supabase(self, operation_result: str, profit_percentage: float, stake_value: float):
        """Envia log de operação para Supabase"""
        try:
            supabase: Client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
            
            # Adicionar timestamp fields obrigatórios
            current_time = datetime.now().isoformat()
            
            data = {
                'operation_result': operation_result,
                'profit_percentage': profit_percentage,
                'stake_value': stake_value,
                'created_at': current_time
            }
            
            result = supabase.table('tunder_bot_logs').insert(data).execute()
            logger.info(f"📊 Log enviado para Supabase: {operation_result} - {profit_percentage:.2f}% - ${stake_value}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar log para Supabase: {e}")
    
    async def executar_compra_accu(self) -> Optional[str]:
        """Executa compra do contrato ACCU com parâmetros corretos e validação"""
        
        # VALIDAÇÃO E LIMITAÇÃO DE STAKE (CORREÇÃO CRÍTICA)
        # Validar e limitar stake conforme limite da Deriv API
        stake_para_usar = min(self.stake, STAKE_MAXIMO_DERIV)
        
        if stake_para_usar < self.stake:
            logger.warning(f"⚠️ Stake limitado: ${self.stake:.2f} -> ${stake_para_usar:.2f}")
        
        # VALIDAÇÃO DOS PARÂMETROS ANTES DO ENVIO
        # 1. Validar stake mínimo/máximo
        if stake_para_usar < 0.35:
            logger.error(f"❌ Stake muito baixo: ${stake_para_usar} (mínimo: $0.35)")
            return None
        if stake_para_usar > STAKE_MAXIMO_DERIV:
            logger.error(f"❌ Stake muito alto: ${stake_para_usar} (máximo: ${STAKE_MAXIMO_DERIV})")
            return None
            
        # 2. Validar growth rate (1-5%)
        if GROWTH_RATE < 0.01 or GROWTH_RATE > 0.05:
            logger.error(f"❌ Growth rate inválido: {GROWTH_RATE*100}% (deve ser 1-5%)")
            return None
            
        # 3. Validar parâmetros obrigatórios para ACCU
        if not ATIVO or not isinstance(ATIVO, str):
            logger.error(f"❌ Símbolo inválido: {ATIVO}")
            return None
            
        # 4. Validar take profit
        if self.dt <= 0:
            logger.error(f"❌ Take profit inválido: ${self.dt}")
            return None
            
        # 3. Take profit: 10% do stake atual ($0.50 se stake=$5)
        take_profit_amount = self.stake * TAKE_PROFIT_PERCENTUAL
        
        # ESTRUTURA CORRETA BASEADA NA DOCUMENTAÇÃO OFICIAL DA DERIV API
        # Primeiro fazer proposal para obter o ID
        try:
            # VALIDAÇÃO FINAL DOS PARÂMETROS ANTES DO ENVIO
            # ESTRUTURA CORRIGIDA CONFORME DOCUMENTAÇÃO OFICIAL DA DERIV
            required_params = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": ATIVO,
                "amount": float(stake_para_usar),  # USAR STAKE LIMITADO
                "basis": "stake",
                "currency": "USD",
                "growth_rate": GROWTH_RATE,
                "limit_order": {
                    "take_profit": float(take_profit_amount)  # CORREÇÃO: 10% do stake
                }
            }
            
            # CORREÇÃO CRÍTICA: Manter growth_rate como float
            # A API da Deriv espera growth_rate como float entre 0.01 e 0.05
            
            # CORREÇÃO FINAL: Estrutura conforme documentação mais recente da Deriv
            # A API espera growth_rate como float entre 0.01 e 0.05
            required_params_final = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": ATIVO,
                "amount": float(stake_para_usar),  # USAR STAKE LIMITADO
                "basis": "stake",
                "currency": "USD",
                "growth_rate": GROWTH_RATE  # CORREÇÃO: Usar GROWTH_RATE (0.02)
            }
            
            # TENTATIVA ALTERNATIVA: Estrutura mais simples sem limit_order
            # Algumas versões da API têm problemas com limit_order em ACCU
            required_params_simple = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": ATIVO,
                "amount": float(stake_para_usar),  # USAR STAKE LIMITADO
                "basis": "stake",
                "currency": "USD",
                "growth_rate": GROWTH_RATE  # CORREÇÃO: Usar GROWTH_RATE (0.02)
            }
            
            # Validar parâmetros usando função especializada
            if not self._validar_parametros_accu(required_params):
                logger.error(f"❌ Validação dos parâmetros ACCU falhou")
                return None
                
            # Usar a estrutura validada
            proposal_params = required_params
                
            # Log detalhado dos parâmetros para debug
            logger.info(f"📋 PARÂMETROS DA PROPOSTA ACCU:")
            logger.info(f"   • proposal: 1")
            logger.info(f"   • contract_type: ACCU")
            logger.info(f"   • symbol: {ATIVO}")
            logger.info(f"   • amount: {stake_para_usar}")
            logger.info(f"   • basis: stake")
            logger.info(f"   • currency: USD")
            logger.info(f"   • growth_rate: {GROWTH_RATE}")
            logger.info(f"   • limit_order.take_profit: {take_profit_amount}")
            
            logger.info(f"💰 SOLICITANDO PROPOSTA ACCU (CONFORME XML):")
            logger.info(f"   • Stake: ${stake_para_usar}")
            logger.info(f"   • Take Profit (DT): ${take_profit_amount:.2f}")
            logger.info(f"   • Growth Rate: {GROWTH_RATE*100}%")
            logger.info(f"   • Symbol: {ATIVO}")
            logger.info(f"   • Currency: USD")
            logger.info(f"   • Basis: stake")
            logger.info(f"   • Total Lost: ${self.total_lost}")
            logger.info(f"   • Khizzbot: {self.khizzbot}")
            
            # EXECUÇÃO OTIMIZADA COM POOLING PERSISTENTE
            # Medição de latência para otimização
            start_time = time.time()
            
            # VALIDAÇÃO FINAL ANTES DO ENVIO
            logger.info(f"🔍 VALIDAÇÃO FINAL DOS PARÂMETROS:")
            logger.info(f"   • Estrutura: {proposal_params}")
            logger.info(f"   • Growth Rate: {proposal_params.get('growth_rate')}")
            logger.info(f"   • Basis: {proposal_params.get('basis')}")
            logger.info(f"   • Contract Type: {proposal_params.get('contract_type')}")
            
            # USAR SISTEMA ROBUSTO DE EXECUÇÃO DE ORDENS
            logger.info(f"🔄 Executando proposta via sistema robusto...")
            
            # Verificar limites de portfolio antes da proposta
            if not await self.robust_order_system._check_portfolio_limits("ACCU"):
                logger.warning(f"🚫 Limite de posições ACCU atingido - operação cancelada")
                return None
            
            # Executar proposta com retry e timeout
            proposal_result = await self.robust_order_system._execute_with_retry(
                self.api_manager.proposal,
                proposal_params,
                OperationType.PROPOSAL
            )
            
            if not proposal_result.success:
                logger.error(f"❌ Falha na proposta após retries: {proposal_result.error}")
                return None
                
            proposal_response = proposal_result.data
            
            proposal_latency = (time.time() - start_time) * 1000
            logger.info(f"📥 Resposta da proposta (latência: {proposal_latency:.2f}ms): {proposal_response}")
            
            # VALIDAÇÃO CRÍTICA DA PROPOSTA
            if 'proposal' not in proposal_response:
                logger.error(f"❌ Proposta inválida - campo 'proposal' ausente: {proposal_response}")
                return None
                
            proposal = proposal_response['proposal']
            proposal_id = proposal.get('id')
            ask_price = proposal.get('ask_price')
            
            # VALIDAR DADOS ESSENCIAIS DA PROPOSTA
            if not proposal_id:
                logger.error(f"❌ Proposal ID ausente: {proposal}")
                return None
                
            if not ask_price:
                logger.error(f"❌ Ask price ausente: {proposal}")
                return None
                
            logger.info(f"✅ Proposta válida - ID: {proposal_id}, Ask Price: ${ask_price}")
            
            # COMPRA IMEDIATA NA MESMA SESSÃO WEBSOCKET
            # ESTRUTURA CORRETA CONFORME DOCUMENTAÇÃO OFICIAL DA DERIV API
            parametros_da_compra = {
                "buy": proposal_id,
                "price": float(ask_price)  # USAR ASK_PRICE DA PROPOSTA
            }
            
            logger.info(f"🚀 EXECUTANDO COMPRA IMEDIATA (MESMA SESSÃO):")
            logger.info(f"   • Proposal ID: {proposal_id}")
            logger.info(f"   • Ask Price (CORRETO): ${ask_price}")
            logger.info(f"   • Session ID: {self.api_manager.session_id}")
            
            # COMPRA VIA SISTEMA ROBUSTO
            buy_start_time = time.time()
            
            # Executar compra com retry e timeout
            buy_result = await self.robust_order_system._execute_with_retry(
                self.api_manager.buy,
                parametros_da_compra,
                OperationType.BUY
            )
            
            buy_latency = (time.time() - buy_start_time) * 1000
            total_latency = (time.time() - start_time) * 1000
            
            logger.info(f"⚡ Latências - Compra: {buy_latency:.2f}ms, Total: {total_latency:.2f}ms")
            
            # VALIDAR RESPOSTA DA COMPRA
            if buy_result.success:
                response = buy_result.data
                if 'buy' in response and 'contract_id' in response['buy']:
                    contract_id = response['buy']['contract_id']
                    logger.info(f"✅ Compra executada via sistema robusto - Contract ID: {contract_id}")
                    # Atualizar timestamp da última operação
                    self._update_operation_timestamp()
                    return contract_id
                else:
                    logger.error(f"❌ Resposta de compra inválida: {response}")
                    return None
            else:
                logger.error(f"❌ Falha na compra após retries: {buy_result.error}")
                return None
                
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na execução da compra: {e}")
            logger.error(f"📋 Tipo do erro: {type(e).__name__}")
            
            # FALLBACK: Tentar compra simplificada sem take_profit
            try:
                logger.info("🔄 TENTANDO FALLBACK - Compra sem take_profit...")
                
                # ESTRUTURA FALLBACK VALIDADA (sem take_profit)
                fallback_proposal = {
                    "proposal": 1,
                    "contract_type": "ACCU",
                    "symbol": ATIVO,
                    "amount": self.stake,
                    "basis": "stake",
                    "currency": "USD",
                    "growth_rate": GROWTH_RATE
                    # Sem limit_order para fallback
                }
                
                # CORREÇÃO FINAL: Usar growth_rate correto (0.02) como float
                fallback_proposal["growth_rate"] = GROWTH_RATE
                
                # Validar parâmetros do fallback usando função especializada
                if not self._validar_parametros_accu(fallback_proposal):
                    logger.error(f"❌ Validação dos parâmetros ACCU do fallback falhou")
                    return None
                
                logger.info(f"🔄 Enviando proposta fallback via sistema robusto...")
                
                # Executar proposta fallback com retry e timeout
                fallback_result = await self.robust_order_system._execute_with_retry(
                    self.api_manager.proposal,
                    fallback_proposal,
                    OperationType.PROPOSAL
                )
                
                if not fallback_result.success:
                    logger.error(f"❌ Falha na proposta fallback: {fallback_result.error}")
                    return None
                    
                fallback_response = fallback_result.data
                logger.info(f"📥 Resposta da proposta fallback: {fallback_response}")
                
                if 'proposal' in fallback_response and 'id' in fallback_response['proposal']:
                    fallback_id = fallback_response['proposal']['id']
                    logger.info(f"✅ Proposta fallback aceita - ID: {fallback_id}")
                    
                    # FALLBACK TAMBÉM PRECISA USAR ASK_PRICE
                    fallback_ask_price = fallback_response['proposal'].get('ask_price')
                    
                    if not fallback_ask_price:
                        logger.error(f"❌ Fallback ask_price ausente: {fallback_response['proposal']}")
                        return None
                    
                    fallback_buy = {
                        "buy": fallback_id,
                        "price": float(fallback_ask_price)  # USAR ASK_PRICE DO FALLBACK
                    }
                    
                    logger.info(f"🔄 Fallback usando Ask Price: ${fallback_ask_price}")
                    
                    # Executar compra fallback via sistema robusto
                    fallback_buy_result = await self.robust_order_system._execute_with_retry(
                        self.api_manager.buy,
                        fallback_buy,
                        OperationType.BUY
                    )
                    
                    if fallback_buy_result.success:
                        fallback_buy_response = fallback_buy_result.data
                        if 'buy' in fallback_buy_response and 'contract_id' in fallback_buy_response['buy']:
                            contract_id = fallback_buy_response['buy']['contract_id']
                            logger.info(f"✅ Compra fallback executada via sistema robusto - Contract ID: {contract_id}")
                            # Atualizar timestamp da última operação
                            self._update_operation_timestamp()
                            return contract_id
                    else:
                        logger.error(f"❌ Falha na compra fallback: {fallback_buy_result.error}")
                        return None
                        
            except Exception as fallback_error:
                logger.error(f"❌ FALLBACK também falhou: {fallback_error}")
                
            return None
    
    async def monitorar_contrato(self, contract_id: str) -> float:
        """Monitora o contrato até o final e retorna o lucro/prejuízo"""
        logger.info(f"👁️ Monitorando contrato {contract_id}...")
        
        while True:
            try:
                response = await self.api_manager.proposal_open_contract(contract_id)
                
                if 'proposal_open_contract' in response:
                    contract = response['proposal_open_contract']
                    status = contract.get('status', 'open')
                    
                    if status in ['won', 'lost']:
                        profit = float(contract.get('profit', 0))
                        logger.info(f"🏁 Contrato finalizado - Status: {status}, Lucro: ${profit:.2f}")
                        return profit
                    
                    # Log de progresso
                    current_spot = contract.get('current_spot', 0)
                    logger.info(f"📈 Contrato ativo - Spot atual: {current_spot}")
                
                await asyncio.sleep(2)  # Verificar a cada 2 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro ao monitorar contrato: {e}")
                await asyncio.sleep(5)
    
    def aplicar_gestao_risco(self, lucro: float):
        """Gestão SEM Martingale - stake sempre fixo"""
        logger.info(f"💼 GESTÃO DE RISCO (STAKE FIXO) - Lucro: ${lucro:.2f}")
        
        # Calcular percentual para log
        profit_percentage = (lucro / self.stake) * 100 if self.stake > 0 else 0
        operation_result = "WIN" if lucro > 0 else "LOSS"
        
        # Enviar para Supabase
        asyncio.create_task(self.log_to_supabase(operation_result, profit_percentage, self.stake))
        
        # SEMPRE manter stake fixo (SEM Martingale)
        self.stake = STAKE_INICIAL  # Sempre fixo
        
        if lucro > 0:
            self.total_profit += lucro  # Acumular lucro total
            logger.info(f"🎉 WIN - Stake mantido: ${self.stake:.2f}")
            
            # Verificar Win Stop
            if self.total_profit >= self.win_stop:
                logger.info(f"🎯 WIN STOP ATINGIDO! Total: ${self.total_profit:.2f}")
                return "STOP_WIN"
        else:
            logger.info(f"💸 LOSS - Stake mantido: ${self.stake:.2f}")
            
            # Verificar Loss Limit (baseado em número de perdas consecutivas)
            if abs(lucro) * 200 >= self.loss_limit:  # Exemplo: 200 perdas de $5 = $1000
                logger.info(f"🛑 LOSS LIMIT ATINGIDO!")
                return "STOP_LOSS"
        
        logger.info(f"📊 Estado atual: Stake=${self.stake:.2f} (FIXO), Total Profit=${self.total_profit:.2f}")
    
    async def executar_ciclo_trading(self):
        """Executa um ciclo completo de trading"""
        self.ciclo += 1
        logger.info(f"\n🔄 CICLO {self.ciclo} - {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. Obter últimos 5 ticks
        ticks = await self.obter_ultimos_5_ticks()
        if len(ticks) < 4:
            logger.warning("⚠️ Ticks insuficientes para análise")
            return
        
        # 2. Analisar padrão de entrada
        if not self.analisar_padrao_entrada(ticks):
            logger.info("⏳ Aguardando padrão de entrada...")
            return
        
        # 3. Executar compra
        contract_id = await self.executar_compra_accu()
        if not contract_id:
            logger.error("❌ Falha na execução da compra")
            return
        
        # 4. Monitorar contrato
        lucro = await self.monitorar_contrato(contract_id)
        
        # 5. Aplicar gestão de risco
        self.aplicar_gestao_risco(lucro)
    
    async def start(self):
        """Inicia o bot com tick stream subscription em tempo real"""
        logger.info("\n" + "="*70)
        logger.info(f"🚀 INICIANDO {NOME_BOT} - MODO TEMPO REAL")
        logger.info("="*70)
        logger.info(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info(f"🎯 Estratégia: Padrão Red-Red-Red-Blue (3 subidas + 1 queda)")
        logger.info(f"💰 Stake inicial: ${STAKE_INICIAL}")
        logger.info(f"📈 Take Profit: {TAKE_PROFIT_PERCENTUAL*100}%")
        logger.info(f"📊 Ativo: {ATIVO}")
        logger.info(f"🔄 Growth Rate: {GROWTH_RATE*100}%")
        logger.info(f"⚖️ Gestão: Stake fixo (sem martingale)")
        logger.info(f"⚡ NOVO: Análise em tempo real via tick stream")
        logger.info("="*70)
        
        # Conectar à API
        if not await self.api_manager.connect():
            logger.error("❌ Falha na conexão inicial. Encerrando.")
            return
        
        # Configurar callback do bot na API
        self.api_manager.set_bot_instance(self)
        
        try:
            # Pré-validar parâmetros
            if not self._pre_validate_params():
                logger.error("❌ Falha na pré-validação de parâmetros")
                return
            
            # Iniciar subscription de ticks em tempo real
            logger.info(f"📡 Iniciando subscription de ticks para {ATIVO}...")
            await self.api_manager.subscribe_ticks(ATIVO)
            self.tick_subscription_active = True
            
            # Iniciar processamento de sinais da queue
            logger.info("🚀 Iniciando processamento de sinais da queue...")
            signal_processor_task = asyncio.create_task(self._process_signals_from_queue())
            
            # Iniciar monitoramento em tempo real (sistema antigo como backup)
            logger.info("📊 Iniciando monitoramento em tempo real...")
            monitoring_task = asyncio.create_task(self._real_time_monitoring())
            
            # NOVO: Iniciar sistema de monitoramento de saúde aprimorado
            logger.info("🏥 Iniciando monitoramento de saúde aprimorado...")
            health_monitor_task = asyncio.create_task(
                self.health_monitor.monitor_and_recover(
                    stats_provider=self._get_enhanced_stats,
                    check_interval=30.0
                )
            )
            
            # Iniciar servidor HTTP para endpoint /status
            logger.info("🌐 Iniciando servidor HTTP...")
            http_server_task = asyncio.create_task(self._start_http_server())
            
            # Inicializar sinal no radar (bot seguro para operar inicialmente)
            logger.info("📊 Inicializando sinal no sistema radar...")
            await self.save_signal_to_radar(
                is_safe_to_operate=True,
                reason="Bot inicializado e pronto para operar",
                last_pattern_found="Aguardando primeiro padrão",
                losses_in_last_10_ops=0,
                wins_in_last_5_ops=0,
                historical_accuracy=0.0,
                pattern_found_at=datetime.now().isoformat(),
                operations_after_pattern=0,
                auto_disable_after_ops=3
            )
            
            logger.info("✅ Bot em modo tempo real - aguardando ticks...")
            logger.info("🏥 Sistema de monitoramento de saúde ativo")
            logger.info("📊 Buffer de ticks sincronizado ativo")
            logger.info("🔄 Sistema de recovery automático ativo")
            logger.info("⚡ Queue de sinais thread-safe ativa")
            logger.info("🎯 Padrão será analisado automaticamente a cada tick recebido")
            logger.info("⚡ Sistema de sincronização aprimorado ativo")
            logger.info("📊 Sistema de sinais integrado com radar_de_apalancamiento_signals")
            logger.info("🌐 Endpoint de status disponível em http://localhost:8080/status")
            
            # Loop de monitoramento principal com tratamento robusto de erros
            consecutive_main_loop_errors = 0
            max_main_loop_errors = 10
            main_loop_start_time = time.time()
            
            while True:
                try:
                    loop_iteration_start = time.time()
                    
                    # Verificar se subscription ainda está ativa
                    if not self.api_manager.connected:
                        logger.warning("⚠️ Conexão perdida - tentando reconectar...")
                        try:
                            await asyncio.wait_for(
                                self._reconnect_and_resubscribe(), 
                                timeout=120.0  # Timeout de 2 minutos para reconexão
                            )
                        except asyncio.TimeoutError:
                            logger.error("❌ Timeout na reconexão (2 minutos)")
                            consecutive_main_loop_errors += 1
                        except Exception as reconnect_error:
                            logger.error(f"❌ Erro na reconexão: {reconnect_error}")
                            consecutive_main_loop_errors += 1
                    
                    # Verificar se o loop principal está rodando há muito tempo sem restart
                    main_loop_duration = time.time() - main_loop_start_time
                    if main_loop_duration > 86400:  # 24 horas
                        logger.info(f"🔄 Loop principal rodando há {main_loop_duration/3600:.1f}h, reiniciando preventivamente")
                        await self._force_restart_bot()
                        main_loop_start_time = time.time()
                    
                    # Reset contador de erros se chegou até aqui sem problemas
                    consecutive_main_loop_errors = 0
                    
                    # Aguardar antes da próxima verificação com timeout
                    try:
                        await asyncio.wait_for(
                            asyncio.sleep(15), 
                            timeout=20.0  # Timeout de 20s para o sleep
                        )
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Timeout no sleep do loop principal")
                    
                    # Log de saúde do loop principal a cada 5 minutos
                    if int(time.time()) % 300 == 0:  # A cada 5 minutos
                        loop_iteration_duration = time.time() - loop_iteration_start
                        logger.info(f"💓 MAIN_LOOP_HEALTH: duração_iteração={loop_iteration_duration:.3f}s, "
                                  f"tempo_total={main_loop_duration/3600:.1f}h, "
                                  f"erros_consecutivos={consecutive_main_loop_errors}")
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Loop principal cancelado")
                    break
                except Exception as e:
                    consecutive_main_loop_errors += 1
                    logger.error(f"❌ ERRO NO MONITORAMENTO ({consecutive_main_loop_errors}/{max_main_loop_errors}): {e}")
                    logger.error(f"📋 Tipo do erro: {type(e).__name__}")
                    
                    # Log stack trace para erros críticos
                    if consecutive_main_loop_errors >= 3:
                        import traceback
                        logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Se muitos erros consecutivos, tentar restart completo
                    if consecutive_main_loop_errors >= max_main_loop_errors:
                        logger.critical(f"❌ Muitos erros consecutivos no loop principal ({consecutive_main_loop_errors}), "
                                      f"tentando restart completo")
                        try:
                            await asyncio.wait_for(
                                self._force_restart_bot(), 
                                timeout=180.0  # 3 minutos para restart
                            )
                            consecutive_main_loop_errors = 0
                            main_loop_start_time = time.time()
                        except Exception as restart_error:
                            logger.critical(f"❌ Falha crítica no restart: {restart_error}")
                            # Aguardar mais tempo antes de tentar novamente
                            await asyncio.sleep(300)  # 5 minutos
                            consecutive_main_loop_errors = 0
                    else:
                        # Aguardar tempo progressivo baseado no número de erros
                        sleep_time = min(15 * consecutive_main_loop_errors, 120)  # Máximo 2 minutos
                        logger.error(f"⏸️ Pausando por {sleep_time} segundos para recuperação...")
                        await asyncio.sleep(sleep_time)
                        
                        # Tentar reconectar após erro
                        try:
                            await asyncio.wait_for(
                                self._reconnect_and_resubscribe(), 
                                timeout=60.0
                            )
                        except Exception as reconnect_after_error:
                            logger.error(f"❌ Erro na reconexão pós-erro: {reconnect_after_error}")
                    
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO NO SISTEMA DE TEMPO REAL: {e}")
            logger.error("🔄 Tentando reiniciar sistema...")
            await self._reconnect_and_resubscribe()
    
    async def _get_enhanced_stats(self) -> dict:
        """Fornece estatísticas aprimoradas para o monitor de saúde"""
        try:
            # Obter estatísticas dos sistemas novos
            queue_stats = self.signal_queue.get_queue_stats()
            buffer_stats = self.enhanced_tick_buffer.get_buffer_stats()
            websocket_stats = self.websocket_recovery.get_connection_stats()
            
            # Combinar com estatísticas antigas para compatibilidade
            old_stats = self.sync_system.get_statistics()
            
            # Retornar estatísticas consolidadas
            enhanced_stats = {
                # Stats do novo sistema
                'queue_size': queue_stats.get('queue_size', 0),
                'active_operations': queue_stats.get('processing_count', 0),
                'circuit_breaker_state': queue_stats.get('circuit_breaker_state', 'unknown'),
                'last_signal_time': queue_stats.get('last_signal_time', 0),
                'successful_operations': queue_stats.get('successful_operations', 0),
                'failed_operations': queue_stats.get('failed_operations', 0),
                'total_signals': queue_stats.get('total_signals', 0),
                
                # Stats de conexão
                'connection_status': (
                    self.api_manager.connected if hasattr(self, 'api_manager') else False
                ),
                'websocket_healthy': websocket_stats.get('connection_healthy', False),
                'last_ping_time': websocket_stats.get('last_ping_age', 0),
                
                # Stats do buffer
                'buffer_synced': buffer_stats.get('synced', True),
                'buffer_size': buffer_stats.get('size', 0),
                'tick_buffer_size': len(self.tick_buffer),
                
                # Stats de compatibilidade (sistema antigo)
                'old_system_queue_size': old_stats.get('queue_size', 0),
                'old_system_operations': old_stats.get('active_operations', 0),
                
                # Flags adicionais
                'subscription_active': self.tick_subscription_active,
                'cached_params_valid': (
                    (time.time() - self._params_cache_time) < self._params_cache_ttl
                    if self._cached_params else False
                )
            }
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas aprimoradas: {e}")
            # Fallback para estatísticas básicas
            return {
                'queue_size': len(self.tick_buffer),
                'active_operations': 0,
                'circuit_breaker_state': 'unknown',
                'last_signal_time': time.time(),
                'successful_operations': 0,
                'failed_operations': 0,
                'connection_status': False
            }
    
    async def test_enhanced_systems(self):
        """Testa os sistemas aprimorados (método de debug)"""
        try:
            logger.info("🧪 TESTANDO SISTEMAS APRIMORADOS...")
            
            # Teste do buffer sincronizado
            test_ticks = [1.23456, 1.23457, 1.23458, 1.23459, 1.23460]
            for i, tick in enumerate(test_ticks):
                success = self.enhanced_tick_buffer.add_tick(tick, time.time() + i)
                logger.info(f"Buffer test {i+1}: {'✅' if success else '❌'}")
            
            synced_ticks = self.enhanced_tick_buffer.get_last_n_ticks(5)
            logger.info(f"Ticks sincronizados obtidos: {len(synced_ticks)}")
            
            # Teste da queue de sinais
            queue_success = self.signal_queue.queue_signal(synced_ticks, True)
            logger.info(f"Queue test: {'✅' if queue_success else '❌'}")
            
            # Teste das estatísticas
            stats = await self._get_enhanced_stats()
            logger.info(f"Stats test: {len(stats)} campos obtidos")
            
            # Teste do monitor de saúde
            health_summary = self.health_monitor.get_health_summary()
            logger.info(f"Health monitor: Status {health_summary['status']}")
            
            logger.info("🧪 TESTE DOS SISTEMAS APRIMORADOS CONCLUÍDO")
            
        except Exception as e:
            logger.error(f"❌ Erro no teste dos sistemas aprimorados: {e}")
    
    async def _reconnect_and_resubscribe(self):
        """Reconecta e reinicia subscription de ticks com recuperação automática"""
        # Verificar se já existe um restart em andamento
        if self._global_restart_lock.locked():
            logger.warning("🔄 Reconexão já em andamento, ignorando nova solicitação")
            return False
            
        async with self._global_restart_lock:
            try:
                logger.info("🔄 Iniciando recuperação automática...")
                
                # Verificar conectividade de rede primeiro
                if not await self.api_manager._check_network_connectivity():
                    logger.error("❌ Sem conectividade de rede. Aguardando 30s antes de tentar novamente...")
                    await asyncio.sleep(30)
                    if not await self.api_manager._check_network_connectivity():
                        logger.error("❌ Conectividade de rede ainda indisponível")
                        return False
                
                # Resetar flags
                self.tick_subscription_active = False
                
                # Auto-reset do circuit breaker se necessário
                circuit_state = self.robust_order_system.circuit_breaker_state
                if circuit_state != 'CLOSED':
                    logger.info(f"🔧 Auto-reset do circuit breaker (estado: {circuit_state})")
                    self.robust_order_system.reset_circuit_breaker()
                
                # Limpar buffer de ticks para evitar dados obsoletos
                self.tick_buffer.clear()
                logger.debug("🧹 Buffer de ticks limpo")
                
                # Reconectar com retry melhorado
                max_retries = 5  # Aumentado para 5 tentativas
                for attempt in range(max_retries):
                    try:
                        logger.info(f"🔌 Tentativa de reconexão {attempt + 1}/{max_retries}")
                        
                        # Verificar conectividade antes de cada tentativa
                        if attempt > 0 and not await self.api_manager._check_network_connectivity():
                            logger.warning(f"⚠️ Conectividade perdida na tentativa {attempt + 1}")
                            await asyncio.sleep(15)  # Aguardar mais tempo se não há conectividade
                            continue
                        
                        if await self.api_manager.connect():
                            logger.info("✅ Reconexão bem-sucedida")
                            break
                        else:
                            logger.warning(f"⚠️ Falha na tentativa {attempt + 1}")
                            if attempt < max_retries - 1:
                                # Backoff exponencial com máximo de 60s
                                wait_time = min(2 ** attempt * 5, 60)
                                logger.info(f"⏳ Aguardando {wait_time}s antes da próxima tentativa...")
                                await asyncio.sleep(wait_time)
                    except Exception as conn_error:
                        logger.error(f"❌ Erro na tentativa {attempt + 1}: {type(conn_error).__name__}: {conn_error}")
                        if attempt < max_retries - 1:
                            wait_time = min(2 ** attempt * 5, 60)
                            await asyncio.sleep(wait_time)
                else:
                    logger.error("❌ Falha em todas as tentativas de reconexão")
                    return False
                
                # Reconfigurar callback
                self.api_manager.set_bot_instance(self)
                
                # Reiniciar subscription com validação
                try:
                    await self.api_manager.subscribe_ticks(ATIVO)
                    self.tick_subscription_active = True
                    logger.info("📡 Subscription de ticks reestabelecida")
                except Exception as sub_error:
                    logger.error(f"❌ Erro ao reestabelecer subscription: {sub_error}")
                    return False
                
                # Validar conectividade
                await asyncio.sleep(2)  # Aguardar estabilização
                if self.api_manager.connected and self.tick_subscription_active:
                    logger.info("✅ Recuperação automática concluída com sucesso")
                    return True
                else:
                    logger.error("❌ Falha na validação pós-recuperação")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Erro crítico na recuperação automática: {e}")
                await asyncio.sleep(10)
                return False
    
    async def save_signal_to_radar(self, is_safe_to_operate: bool, reason: str = None, 
                                  last_pattern_found: str = None, losses_in_last_10_ops: int = None,
                                  wins_in_last_5_ops: int = None, historical_accuracy: float = None,
                                  pattern_found_at: str = None, operations_after_pattern: int = 0,
                                  auto_disable_after_ops: int = 3):
        """Salva ou atualiza sinal na tabela radar_de_apalancamiento_signals usando UPSERT"""
        try:
            supabase: Client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
            
            # Primeiro, verificar se já existe um registro para o Tunder Bot
            existing_signal = supabase.table('radar_de_apalancamiento_signals') \
                .select('*') \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            # Preparar dados do sinal
            signal_data = {
                'bot_name': NOME_BOT,
                'is_safe_to_operate': is_safe_to_operate,
                'reason': reason,
                'last_pattern_found': last_pattern_found,
                'losses_in_last_10_ops': losses_in_last_10_ops,
                'wins_in_last_5_ops': wins_in_last_5_ops,
                'historical_accuracy': historical_accuracy,
                'pattern_found_at': pattern_found_at,
                'operations_after_pattern': operations_after_pattern,
                'auto_disable_after_ops': auto_disable_after_ops
            }
            
            if existing_signal.data:
                # Atualizar registro existente
                result = supabase.table('radar_de_apalancamiento_signals') \
                    .update(signal_data) \
                    .eq('bot_name', NOME_BOT) \
                    .execute()
                logger.info(f"📊 Sinal atualizado para {NOME_BOT}: safe_to_operate={is_safe_to_operate}")
            else:
                # Inserir novo registro
                result = supabase.table('radar_de_apalancamiento_signals') \
                    .insert(signal_data) \
                    .execute()
                logger.info(f"📊 Novo sinal criado para {NOME_BOT}: safe_to_operate={is_safe_to_operate}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sinal no radar: {e}")
            return None
    
    async def get_signal_from_radar(self):
        """Obtém o sinal atual do Tunder Bot da tabela radar_de_apalancamiento_signals"""
        try:
            supabase: Client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
            
            result = supabase.table('radar_de_apalancamiento_signals') \
                .select('*') \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            if result.data:
                signal = result.data[0]
                logger.info(f"📊 Sinal obtido para {NOME_BOT}: safe_to_operate={signal.get('is_safe_to_operate')}")
                return signal
            else:
                logger.warning(f"⚠️ Nenhum sinal encontrado para {NOME_BOT}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter sinal do radar: {e}")
            return None
    
    async def update_signal_status(self, is_safe_to_operate: bool, reason: str = None):
        """Atualiza rapidamente apenas o status de segurança do sinal"""
        try:
            supabase: Client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_KEY')
            )
            
            update_data = {
                'is_safe_to_operate': is_safe_to_operate,
                'reason': reason
            }
            
            result = supabase.table('radar_de_apalancamiento_signals') \
                .update(update_data) \
                .eq('bot_name', NOME_BOT) \
                .execute()
            
            logger.info(f"📊 Status do sinal atualizado para {NOME_BOT}: {is_safe_to_operate}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar status do sinal: {e}")
            return None

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
@with_error_handling(ErrorType.SYSTEM, ErrorSeverity.CRITICAL)
async def main():
    """Função principal do bot"""
    try:
        print("\n[INICIO] Iniciando Tunder Bot - Modo Standalone")
        print("[CONFIG] Configuracao:")
        print(f"   • Ativo: {ATIVO}")
        print(f"   • Stake Inicial: ${STAKE_INICIAL}")
        print(f"   • Take Profit: {TAKE_PROFIT_PERCENTUAL*100}%")
        print(f"   • Growth Rate: {GROWTH_RATE*100}%")
        print(f"   • Padrao: Red-Red-Red-Blue (3 subidas + 1 queda)")
        print(f"   • Gestao: Stake fixo (sem martingale)")
        print(f"   • Sistema de Sinais: Integrado")
        print(f"   • Sistema de Reinicialização Automática: Ativado")
        print("="*60)
        
        # Criar e iniciar o bot com tratamento de erros interno
        bot = AccumulatorScalpingBot()
        
        # Configurar sistema de recuperação de erros internos
        max_retries_internal = 3
        retry_count = 0
        
        while retry_count < max_retries_internal:
            try:
                # Iniciar o bot com timeout de segurança
                await asyncio.wait_for(bot.start(), timeout=3600)  # 1 hora de timeout
                # Se chegou aqui, o bot foi finalizado normalmente
                logger.info("✅ Bot finalizado normalmente dentro do método main")
                break
                
            except asyncio.TimeoutError:
                # Timeout de segurança atingido
                retry_count += 1
                logger.warning(f"⚠️ Timeout de segurança atingido. Reiniciando internamente. (Tentativa {retry_count}/{max_retries_internal})")
                # Tentar limpar recursos antes de reiniciar
                try:
                    await bot.cleanup_resources()
                except Exception as cleanup_error:
                    logger.error(f"❌ Erro ao limpar recursos: {cleanup_error}")
                continue
                
            except Exception as e:
                # Erro durante a execução do bot
                retry_count += 1
                error_type = type(e).__name__
                logger.error(f"❌ Erro durante execução do bot: {e}")
                logger.error(f"📋 Tipo do erro: {error_type}")
                
                # Tratamento específico para erros de conexão WebSocket
                if "websocket" in str(e).lower() or "connection" in str(e).lower():
                    logger.warning("🔌 Erro de conexão detectado. Implementando estratégia de recuperação...")
                    # Aguardar mais tempo para erros de conexão
                    retry_delay = min(30 * retry_count, 120)  # Máximo 2 minutos
                    logger.info(f"⏱️ Aguardando {retry_delay}s para recuperação de conexão...")
                    await asyncio.sleep(retry_delay)
                elif "timeout" in str(e).lower():
                    logger.warning("⏰ Timeout detectado. Aguardando antes de reiniciar...")
                    retry_delay = 15 * retry_count
                    await asyncio.sleep(retry_delay)
                else:
                    # Outros tipos de erro
                    retry_delay = 5 * retry_count
                    logger.info(f"⏱️ Aguardando {retry_delay} segundos antes de tentar novamente...")
                    await asyncio.sleep(retry_delay)
                
                # Tentar limpar recursos antes de reiniciar
                try:
                    await bot.cleanup_resources()
                except Exception as cleanup_error:
                    logger.error(f"❌ Erro ao limpar recursos: {cleanup_error}")
                
                continue
        
        # Se atingiu o número máximo de tentativas internas
        if retry_count >= max_retries_internal:
            logger.error(f"❌ Número máximo de tentativas internas ({max_retries_internal}) atingido. Reiniciando o bot completamente.")
            raise Exception("Número máximo de tentativas internas atingido")
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO na função main: {e}")
        logger.error(f"📋 Tipo do erro: {type(e).__name__}")
        # Não fazer sys.exit() para evitar exit code 1
        raise

# Função para reiniciar o bot automaticamente
async def force_cleanup_and_restart():
    """Força limpeza completa de recursos e prepara para restart"""
    logger.info("🧹 Iniciando cleanup forçado...")
    
    try:
        # 1. Cancelar todas as tasks pendentes
        current_task = asyncio.current_task()
        all_tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]
        
        if all_tasks:
            logger.info(f"🔄 Cancelando {len(all_tasks)} tasks pendentes...")
            for task in all_tasks:
                task.cancel()
            
            # Aguardar cancelamento com timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*all_tasks, return_exceptions=True),
                    timeout=10.0
                )
                logger.info("✅ Tasks canceladas com sucesso")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout no cancelamento de tasks - forçando finalização")
        
        # 2. Limpeza de memória
        import gc
        gc.collect()
        logger.info("🧹 Garbage collection executado")
        
        # 3. Delay para estabilização
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"❌ Erro durante cleanup forçado: {e}")

def reiniciar_bot_automaticamente():
    """Função que reinicia o bot automaticamente com cleanup forçado"""
    max_tentativas = 10
    tentativa_atual = 0
    delay_base = 5
    timeout_reinicio = 30 * 60  # 30 minutos
    
    while tentativa_atual < max_tentativas:
        loop = None
        try:
            tentativa_atual += 1
            logger.info(f"🔄 REINICIANDO BOT (Tentativa {tentativa_atual}/{max_tentativas})")
            
            # Delay progressivo entre tentativas
            if tentativa_atual > 1:
                delay = min(delay_base * (2 ** (tentativa_atual - 2)), 300)
                logger.info(f"⏱️ Aguardando {delay}s antes de reiniciar...")
                time.sleep(delay)
            
            # NOVO: Forçar fechamento de event loop anterior se existir
            try:
                current_loop = asyncio.get_event_loop()
                if current_loop and not current_loop.is_closed():
                    logger.info("🔄 Fechando event loop anterior...")
                    current_loop.close()
            except RuntimeError:
                pass  # Não há loop ativo
            
            # Criar novo event loop limpo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("✅ Novo event loop criado")
            
            # Executar bot com timeout e cleanup automático
            logger.info(f"⏰ Bot executará por {timeout_reinicio//60} minutos")
            
            try:
                # Executar main com timeout
                loop.run_until_complete(
                    asyncio.wait_for(main(), timeout=timeout_reinicio)
                )
                logger.info("✅ Bot finalizado normalmente")
                break
                
            except asyncio.TimeoutError:
                logger.info("⏰ Timeout de 30 minutos - reiniciando automaticamente")
                print("🔄 Bot reiniciado automaticamente após 30 minutos")
                
                # NOVO: Cleanup forçado antes de reiniciar
                try:
                    loop.run_until_complete(force_cleanup_and_restart())
                except Exception as cleanup_error:
                    logger.error(f"❌ Erro no cleanup: {cleanup_error}")
                
                continue
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrupção manual detectada")
            print("\n🛑 Bot interrompido pelo usuário")
            break
            
        except asyncio.CancelledError:
            logger.info("🔄 Execução cancelada - reiniciando")
            continue
            
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                logger.info("🔄 Event loop fechado - criando novo")
                continue
            else:
                logger.error(f"❌ RuntimeError: {e}")
                continue
                
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"❌ Erro: {e}")
            continue
            
        finally:
            # NOVO: Cleanup forçado do event loop
            if loop and not loop.is_closed():
                try:
                    # Cancelar tasks restantes
                    pending_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                    if pending_tasks:
                        logger.info(f"🧹 Limpando {len(pending_tasks)} tasks restantes...")
                        for task in pending_tasks:
                            task.cancel()
                    
                    # Fechar loop
                    loop.close()
                    logger.info("🧹 Event loop fechado e limpo")
                except Exception as cleanup_error:
                    logger.error(f"❌ Erro no cleanup final: {cleanup_error}")
            
            # Delay adicional para estabilização
            if tentativa_atual < max_tentativas:
                time.sleep(3)
    
    # Verificar se atingiu limite de tentativas
    if tentativa_atual >= max_tentativas:
        logger.critical(f"❌ Limite de {max_tentativas} tentativas atingido!")
        print(f"❌ Sistema falhou após {max_tentativas} tentativas")
    
    logger.info("🏁 Sistema de restart finalizado")
    print("🏁 Sistema finalizado")

if __name__ == "__main__":
    try:
        # Iniciar o sistema de reinicialização automática
        reiniciar_bot_automaticamente()
    except KeyboardInterrupt:
        print("\nSistema interrompido pelo usuário.")
        logger.info("🛑 Sistema finalizado pelo usuário")
    finally:
        print("Programa finalizado.")
        logger.info("🏁 Programa finalizado")