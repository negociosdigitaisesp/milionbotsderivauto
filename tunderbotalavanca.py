#!/usr/bin/env python3
"""
Tunder Bot Avalancs
Refatorado para seguir fielmente a estratégia do Scalping Bot.xml
Com lógica de entrada corrigida e resiliência a falhas
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
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client
from robust_order_system import RobustOrderSystem, OperationType
from enhanced_sync_system import EnhancedSyncSystem
from aiohttp import web
from error_handler import RobustErrorHandler, with_error_handling, ErrorType, ErrorSeverity
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
        logging.FileHandler('accumulator_standalone.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# PARÂMETROS DE GESTÃO (ACCUMULATOR STRATEGY)
# ============================================================================
NOME_BOT = "Tunder Bot Alavancs"
STAKE_INICIAL = 5.0  # initial stake - alterado para 5
STAKE_MAXIMO_DERIV = 1000.0  # Limite máximo de stake permitido pela Deriv API
TAKE_PROFIT_PERCENTUAL = 0.26  # 26% (Return%) - Conforme solicitação
ATIVO = 'R_10'
GROWTH_RATE = 0.05  # 5% - Valor alterado conforme solicitação
WIN_STOP = 1000.0  # Meta de ganho diário
LOSS_LIMIT = 1000.0  # Limite de perda diária
KHIZZBOT = 50  # Valor khizzbot conforme XML original

# ============================================================================
# CONFIGURAÇÃO DE MÚLTIPLAS CONTAS DERIV
# ============================================================================
ACCOUNTS = [
    {
        "name": "Bot_Principal",
        "token": "5iD3wgrYUz39kzS",
        "app_id": "105327"
    },
    {
        "name": "Bot_Secundario",
        "token": "SEU_TOKEN_2_AQUI",  # Usuário adicionará depois
        "app_id": "105327"
    },
    {
        "name": "Bot_Terciario",
        "token": "SEU_TOKEN_3_AQUI",  # Usuário adicionará depois
        "app_id": "105327"
    }
]

# Configuração para usar apenas a conta principal inicialmente
ACTIVE_ACCOUNTS = [ACCOUNTS[0]]  # Apenas Bot_Principal ativo

# ============================================================================
# CLASSE DE GERENCIAMENTO DA API - WEBSOCKET NATIVO
# ============================================================================
class DerivWebSocketNativo:
    """Gerenciador de API WebSocket nativo com suporte a múltiplas contas"""
    
    def __init__(self, account_config=None):
        # WebSocket connection
        self.ws = None
        self.connected = False
        
        # Request management
        self.req_id_counter = 0
        self.req_id_lock = threading.Lock()
        self.pending_requests = {}
        self.request_timeout = 30  # Aumentado de 15 para 30 segundos para resolver timeouts
        self.portfolio_timeout = 45  # Timeout específico para portfolio (operação mais lenta)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 2 requests per second max
        
        # Credentials - usar configuração da conta ou fallback para variáveis de ambiente
        if account_config:
            self.account_name = account_config.get('name', 'Unknown')
            self.app_id = account_config.get('app_id', '105327')
            self.api_token = account_config.get('token')
            
            if not self.api_token or self.api_token.startswith('SEU_TOKEN_'):
                raise ValueError(f"❌ Token inválido para a conta {self.account_name}")
        else:
            # Fallback para variáveis de ambiente (compatibilidade)
            self.account_name = "Default"
            self.app_id = "85515"
            self.api_token = os.getenv('DERIV_API_TOKEN')
            
            if not self.api_token:
                raise ValueError("❌ DERIV_API_TOKEN deve estar definido no arquivo .env")
        
        # Connection state
        self.session_id = None
        self.authorized = False
        
        # Error handler
        self.error_handler = RobustErrorHandler(f"DerivWebSocket_{self.account_name}")
        
        logger.info(f"🔧 DerivWebSocketNativo inicializado - Conta: {self.account_name}, App ID: {self.app_id}")
    
    async def connect(self):
        """Conecta ao WebSocket da Deriv com autenticação"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"🔗 Tentativa {attempt + 1}/{max_retries} - Conectando WebSocket...")
                
                # Fechar conexão anterior se existir
                if self.ws:
                    try:
                        await self.ws.close()
                    except:
                        pass
                
                # URL WebSocket conforme especificação
                ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
                
                # Conectar WebSocket
                self.ws = await websockets.connect(ws_url)
                logger.info(f"🔗 WebSocket conectado: {ws_url}")
                
                # Iniciar task para processar mensagens
                asyncio.create_task(self._handle_messages())
                
                # Autenticar
                auth_success = await self._authenticate()
                if auth_success:
                    self.connected = True
                    logger.info(f"✅ Conexão WebSocket estabelecida - Session: {self.session_id}")
                    
                    # Iniciar keepalive
                    asyncio.create_task(self._keepalive_loop())
                    
                    return True
                else:
                    logger.error("❌ Falha na autenticação")
                    
            except Exception as e:
                logger.error(f"❌ Erro na tentativa {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                    
        logger.error("❌ Falha ao estabelecer conexão WebSocket")
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
        """Loop de ping/pong para manter conexão ativa"""
        while self.connected and self.ws:
            try:
                await asyncio.sleep(30)  # Ping a cada 30 segundos
                if self.connected and self.ws:
                    req_id = self._get_next_req_id()
                    ping_message = {"ping": 1, "req_id": req_id}
                    
                    response = await self._send_request(ping_message)
                    if 'ping' in response:
                        logger.debug(f"💓 Ping OK - req_id: {req_id}")
                    else:
                        logger.warning("⚠️ Ping falhou - Reconectando...")
                        await self._reconnect()
                        
            except Exception as e:
                logger.error(f"❌ Erro no keepalive: {e} - Reconectando...")
                await self._reconnect()
    
    async def _reconnect(self):
        """Reconecta automaticamente"""
        logger.info("🔄 Iniciando reconexão...")
        self.connected = False
        await self.connect()
    
    async def _send_request(self, message):
        """Envia request e aguarda response com logging detalhado"""
        start_time = time.time()
        req_id = None
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.debug(f"⏱️ Rate limiting: aguardando {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            
            req_id = message.get('req_id')
            if not req_id:
                req_id = self._get_next_req_id()
                message['req_id'] = req_id
            
            # Criar Future para aguardar response
            future = asyncio.Future()
            self.pending_requests[req_id] = future
            
            # Enviar mensagem
            message_str = json.dumps(message)
            logger.debug(f"📤 Enviando req_id {req_id} (timeout {self.request_timeout}s): {message_str}")
            
            send_start = time.time()
            await self.ws.send(message_str)
            send_time = time.time() - send_start
            self.last_request_time = time.time()
            
            logger.debug(f"📤 Mensagem enviada em {send_time:.3f}s, aguardando response...")
            
            # Aguardar response com timeout
            try:
                wait_start = time.time()
                response = await asyncio.wait_for(future, timeout=self.request_timeout)
                wait_time = time.time() - wait_start
                total_time = time.time() - start_time
                
                logger.debug(f"📥 Response recebido para req_id {req_id} em {wait_time:.3f}s (total: {total_time:.3f}s)")
                return response
                
            except asyncio.TimeoutError:
                # Cleanup em caso de timeout
                self.pending_requests.pop(req_id, None)
                total_time = time.time() - start_time
                logger.error(f"⏰ Timeout para req_id {req_id} após {total_time:.3f}s (limite: {self.request_timeout}s)")
                raise Exception(f"Timeout aguardando response para req_id {req_id}")
                
        except Exception as e:
            # Cleanup em caso de erro
            if req_id:
                self.pending_requests.pop(req_id, None)
            total_time = time.time() - start_time
            logger.error(f"❌ Erro no request req_id {req_id} após {total_time:.3f}s: {e}")
            raise e
    
    async def _send_request_with_timeout(self, message, custom_timeout):
        """Envia request e aguarda response com timeout customizado e logging detalhado"""
        start_time = time.time()
        req_id = None
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.debug(f"⏱️ Rate limiting: aguardando {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            
            req_id = message.get('req_id')
            if not req_id:
                req_id = self._get_next_req_id()
                message['req_id'] = req_id
            
            # Criar Future para aguardar response
            future = asyncio.Future()
            self.pending_requests[req_id] = future
            
            # Enviar mensagem
            message_str = json.dumps(message)
            logger.debug(f"📤 Enviando req_id {req_id} (timeout customizado {custom_timeout}s): {message_str}")
            
            send_start = time.time()
            await self.ws.send(message_str)
            send_time = time.time() - send_start
            self.last_request_time = time.time()
            
            logger.debug(f"📤 Mensagem enviada em {send_time:.3f}s, aguardando response com timeout {custom_timeout}s...")
            
            # Aguardar response com timeout customizado
            try:
                wait_start = time.time()
                response = await asyncio.wait_for(future, timeout=custom_timeout)
                wait_time = time.time() - wait_start
                total_time = time.time() - start_time
                
                logger.debug(f"📥 Response recebido para req_id {req_id} em {wait_time:.3f}s (total: {total_time:.3f}s)")
                return response
                
            except asyncio.TimeoutError:
                # Cleanup em caso de timeout
                self.pending_requests.pop(req_id, None)
                total_time = time.time() - start_time
                logger.error(f"⏰ Timeout customizado para req_id {req_id} após {total_time:.3f}s (limite: {custom_timeout}s)")
                raise asyncio.TimeoutError(f"Timeout aguardando response para req_id {req_id} após {custom_timeout}s")
                
        except Exception as e:
            # Cleanup em caso de erro
            if req_id:
                self.pending_requests.pop(req_id, None)
            total_time = time.time() - start_time
            logger.error(f"❌ Erro no request customizado req_id {req_id} após {total_time:.3f}s: {e}")
            raise e
    
    async def ensure_connection(self):
        """Garante que a conexão WebSocket está ativa com verificação de saúde"""
        # Verificação básica de estado
        if not self.connected or not self.ws or not self.authorized:
            logger.info("🔄 Conexão não estabelecida, conectando...")
            await self.connect()
            return
        
        # Verificação de saúde da conexão
        try:
            # Verificar se o WebSocket ainda está aberto
            if hasattr(self.ws, 'closed') and self.ws.closed:
                logger.warning("⚠️ WebSocket fechado detectado, reconectando...")
                await self.connect()
                return
            elif hasattr(self.ws, 'close_code') and self.ws.close_code is not None:
                logger.warning("⚠️ WebSocket com close_code detectado, reconectando...")
                await self.connect()
                return
            
            # Teste de ping para verificar se a conexão está responsiva
            ping_message = {"ping": 1}
            logger.debug("🏓 Testando conexão com ping...")
            
            # Usar timeout menor para ping (5 segundos)
            try:
                await self._send_request_with_timeout(ping_message, 5)
                logger.debug("✅ Ping bem-sucedido, conexão saudável")
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"⚠️ Ping falhou ({e}), reconectando...")
                await self.connect()
                
        except Exception as e:
            logger.warning(f"⚠️ Erro na verificação de saúde da conexão: {e}, reconectando...")
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
            # Log para verificação do growth_rate dinâmico
            growth_rate_recebido = params.get("growth_rate", "AUSENTE")
            logger.info(f"🔍 VERIFICAÇÃO GROWTH_RATE: Recebido={growth_rate_recebido}")
            
            # Estrutura de proposta conforme documentação Deriv para ACCUMULATOR
            proposal_message = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": str(params["symbol"]),
                "amount": float(params["amount"]),
                "basis": "stake",
                "currency": "USD",
                "growth_rate": float(params.get("growth_rate", GROWTH_RATE))  # ✅ CORRIGIDO - usar growth_rate para ACCUMULATOR
            }
            
            logger.info(f"🔍 VERIFICAÇÃO ENVIO: Enviando growth_rate={proposal_message['growth_rate']}")
            
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
            self.error_handler.handle_error(e, ErrorType.TICK_PROCESSING, ErrorSeverity.HIGH)
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
        """Obtém portfolio de contratos ativos usando WebSocket nativo com retry logic"""
        max_retries = 3
        retry_delay = 2  # segundos
        
        for attempt in range(max_retries):
            try:
                await self.ensure_connection()
                
                # Estrutura de portfolio conforme documentação Deriv
                portfolio_message = {
                    "portfolio": 1
                }
                
                logger.info(f"📊 Solicitando portfolio (tentativa {attempt + 1}/{max_retries}): {portfolio_message}")
                start_time = time.time()
                
                # Usar timeout específico para portfolio
                response = await self._send_request_with_timeout(portfolio_message, self.portfolio_timeout)
                
                elapsed_time = time.time() - start_time
                logger.info(f"✅ Portfolio obtido com sucesso em {elapsed_time:.2f}s")
                
                if 'error' in response:
                    raise Exception(f"Deriv API Error: {response['error']['message']}")
                
                return response
                
            except asyncio.TimeoutError as e:
                logger.warning(f"⏰ Timeout na tentativa {attempt + 1}/{max_retries} para portfolio (>{self.portfolio_timeout}s)")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Todas as tentativas de portfolio falharam por timeout")
                    raise Exception(f"Portfolio timeout após {max_retries} tentativas")
                await asyncio.sleep(retry_delay)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro na tentativa {attempt + 1}/{max_retries} para portfolio: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Todas as tentativas de portfolio falharam: {e}")
                    raise e
                await asyncio.sleep(retry_delay)
    
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
    
    def __init__(self, account_config=None):
        # Sistema de tratamento de erros
        self.error_handler = RobustErrorHandler(NOME_BOT)
        
        # Configuração da conta
        self.account_config = account_config
        self.account_name = account_config.get('name', 'Default') if account_config else 'Default'
        self.token = account_config.get('token', '') if account_config else ''
        self.app_id = account_config.get('app_id', '') if account_config else ''
        
        self.api_manager = DerivWebSocketNativo(account_config)
        self.ativo = ATIVO
        
        # VARIÁVEIS PARA ESTRATÉGIA ALAVANCS PRO 2.0
        self.nome_bot = NOME_BOT  # Nome do bot
        self.stake = STAKE_INICIAL  # Stake inicial
        self.initial_stake = STAKE_INICIAL  # Stake inicial (constante)
        
        # Controles de parada
        self.win_stop = WIN_STOP
        self.loss_limit = LOSS_LIMIT
        self.total_profit = 0.0  # Lucro total acumulado
        
        # VARIÁVEIS CONFORME XML ORIGINAL ACCUMULATOR
        self.stake = STAKE_INICIAL  # Stake (variável)
        self.initial_stake = STAKE_INICIAL  # initial stake (constante)
        self.total_lost = 0.0  # total lost
        self.khizzbot = KHIZZBOT  # khizzbot = 50
        self.account_initial_take_profit = STAKE_INICIAL * TAKE_PROFIT_PERCENTUAL  # DT inicial
        self.dt = self.account_initial_take_profit  # DT (take profit dinâmico)
        
        # VARIÁVEIS DE ESTADO PARA ACCUMULATOR
        self.consecutive_losses = 0  # Contador de perdas consecutivas
        self.is_trading_locked = False  # Controle de bloqueio para prevenir condições de corrida
        
        self.ticks_history = []
        self.ciclo = 0
        
        # NOVO: Sistema de tick stream em tempo real
        self.tick_buffer = []  # Buffer para manter últimos 4 ticks
        self.tick_subscription_active = False  # Flag para controlar subscription
        
        # NOVO: Sistema robusto de execução de ordens
        self.robust_order_system = RobustOrderSystem(self.api_manager)
        
        # NOVO: Sistema de sincronização aprimorado
        self.sync_system = EnhancedSyncSystem(max_concurrent_operations=2, max_queue_size=3)
        
        # NOVO: Sistemas Avançados Integrados
        self.enhanced_tick_buffer = EnhancedTickBuffer(max_size=10, tolerance_seconds=1.0)
        self.websocket_recovery = WebSocketRecoveryManager(max_retries=5, base_delay=2.0)
        self.signal_queue = ThreadSafeSignalQueue(max_size=10, max_concurrent=2)
        self.health_monitor = SystemHealthMonitor(
            deadlock_threshold=120.0,
            inactivity_threshold=180.0,
            high_failure_rate=0.7,
            min_operations_for_rate_check=10
        )
        
        # Cache de parâmetros pré-validados
        self._cached_params = None
        self._params_cache_time = 0
        self._params_cache_ttl = 5.0  # 5 segundos
        
        # Sistema de debugging avançado
        self._signal_history = []
        self._max_signal_history = 100
        self._debug_log_file = f"debug_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Sistema de monitoramento de inatividade
        self._last_operation_time = time.time()  # Timestamp da última operação
        self._inactivity_timeout = 120  # 2 minutos em segundos
        self._restart_in_progress = False  # Flag para evitar múltiplos restarts
        self._operation_count = 0  # Contador de operações executadas
        
        # SISTEMA DE CONFIRMAÇÃO FIEL AO XML
        self.aguardando_confirmacao = False  # Variável AguardandoConfirmacao do XML
        
        # Configurar callbacks de recuperação do health monitor
        self.health_monitor.set_recovery_callbacks(
            on_system_restart=self._force_restart_bot
        )
        
        logger.info(f"🤖 {NOME_BOT} inicializado")
        logger.info(f"📊 Configuração ACCUMULATOR:")
        logger.info(f"   • Ativo: {ATIVO}")
        logger.info(f"   • Stake Inicial: ${self.stake}")
        logger.info(f"   • Take Profit: {TAKE_PROFIT_PERCENTUAL*100}%")
        logger.info(f"   • Growth Rate: {GROWTH_RATE*100}%")
        logger.info(f"   • Win Stop: ${self.win_stop}")
        logger.info(f"   • Loss Limit: ${self.loss_limit}")
        
        # NOVO: Buffer de ticks para análise reativa ALAVANCS PRO 2.0
        self.tick_buffer_alavancs = []  # Buffer específico para análise de padrões
        self.max_buffer_size = 10  # Máximo de 10 ticks no buffer
        self.pattern_detection_active = False  # Flag para detecção de padrões
        self.last_tick_time = 0  # Timestamp do último tick recebido

    # ============================================================================
    # SISTEMA DE ANÁLISE DE TICKS REATIVO - ALAVANCS PRO 2.0 (SIMPLIFICADO)
    # ============================================================================
    
    async def _handle_new_tick(self, tick_data):
        """Processa novo tick para análise de padrão ACCUMULATOR (Red-Red-Red-Blue)"""
        try:
            # Extrair valor do tick
            tick_value = float(tick_data.get('quote', 0))
            
            if tick_value <= 0:
                return
            
            # Adicionar ao buffer
            self.tick_buffer.append(tick_value)
            
            # Manter apenas os últimos 5 ticks
            if len(self.tick_buffer) > 5:
                self.tick_buffer.pop(0)
            
            # Executar análise quando tiver 5 ticks
            if len(self.tick_buffer) == 5:
                pattern_detected = self.analisar_padrao_entrada_accumulator(self.tick_buffer.copy())
                
                if pattern_detected and not self.is_trading_locked:
                    # Bloquear operações simultâneas
                    self.is_trading_locked = True
                    logger.info(f"🎯 PADRÃO ACCUMULATOR DETECTADO - EXECUTANDO COMPRA")
                    # Executar ciclo completo da operação
                    asyncio.create_task(self._execute_trade_lifecycle_accumulator())
                    
        except Exception as e:
            logger.error(f"❌ Erro em _handle_new_tick: {e}")

    def analisar_padrao_entrada_accumulator(self, ticks: List[float]) -> bool:
        """ 
        Lógica de Padrão ACCUMULATOR: Red-Red-Red-Blue (3 subidas + 1 queda) 
        """ 
        if len(ticks) < 5: 
            return False 
     
        # Atribuições de tick (indexação FROM_END) 
        tick4 = ticks[-5]  # FROM_END 5 (mais antigo) 
        tick3 = ticks[-4]  # FROM_END 4  
        tick2 = ticks[-3]  # FROM_END 3 
        tick1 = ticks[-2]  # FROM_END 2 
        tick_atual = ticks[-1]  # FROM_END 1 (atual/mais novo) 
     
        # Cálculos de sinal ACCUMULATOR 
        single4 = "Red" if tick4 > tick3 else "Blue" 
        single3 = "Red" if tick3 > tick2 else "Blue"  
        single2 = "Red" if tick2 > tick1 else "Blue" 
        single1 = "Red" if tick1 > tick_atual else "Blue" 
     
        # Condição ACCUMULATOR: single1=Red E single2=Red E single3=Red E single4=Blue 
        entrada_accumulator = (single1 == "Red" and 
                              single2 == "Red" and 
                              single3 == "Red" and 
                              single4 == "Blue") 
     
        # Log detalhado 
        logger.info(f"📊 VERIFICAÇÃO DE PADRÃO ACCUMULATOR:") 
        logger.info(f"   • single1: {single1}, single2: {single2}, single3: {single3}, single4: {single4}") 
        logger.info(f"   • Padrão esperado: Red-Red-Red-Blue") 
        logger.info(f"   • Entrada detectada: {entrada_accumulator}") 
     
        if entrada_accumulator: 
            logger.info("🎯 PADRÃO ACCUMULATOR DETECTADO! (Red-Red-Red-Blue)") 
            
        return entrada_accumulator

    async def _execute_trade_lifecycle_accumulator(self):
        """Ciclo de vida completo para operação ACCUMULATOR"""
        try:
            logger.info("--- Iniciando Novo Ciclo ACCUMULATOR ---")
            contract_id = await self.executar_compra_accumulator()
            
            if contract_id:
                lucro = await self.monitorar_contrato(contract_id)
                self.aplicar_gestao_risco_accumulator(lucro)
            else:
                logger.error("Falha na operação ACCUMULATOR")
        
        except Exception as e:
            logger.error(f"Erro no ciclo ACCUMULATOR: {e}")
        
        finally:
            self.is_trading_locked = False
            logger.info("--- Fim do Ciclo ACCUMULATOR (TRAVA LIBERADA) ---")

    async def executar_compra_accumulator(self) -> Optional[str]:
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
            
        # Take profit: baseado no percentual configurado
        take_profit_amount = self.stake * TAKE_PROFIT_PERCENTUAL
        
        try:
            # ESTRUTURA CORRETA BASEADA NA DOCUMENTAÇÃO OFICIAL DA DERIV API
            proposal_params = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": ATIVO,
                "amount": float(stake_para_usar),
                "basis": "stake",
                "currency": "USD",
                "growth_rate": GROWTH_RATE,
                "limit_order": {
                    "take_profit": float(take_profit_amount)
                }
            }
            
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
            
            logger.info(f"💰 SOLICITANDO PROPOSTA ACCU:")
            logger.info(f"   • Stake: ${stake_para_usar}")
            logger.info(f"   • Take Profit (DT): ${take_profit_amount:.2f}")
            logger.info(f"   • Growth Rate: {GROWTH_RATE*100}%")
            logger.info(f"   • Symbol: {ATIVO}")
            
            # Executar proposta
            proposal_response = await self.api_manager.proposal(proposal_params)
            
            if not proposal_response or 'proposal' not in proposal_response:
                logger.error(f"❌ Proposta inválida - campo 'proposal' ausente: {proposal_response}")
                return None
                
            proposal = proposal_response['proposal']
            proposal_id = proposal.get('id')
            ask_price = proposal.get('ask_price')
            
            if not proposal_id or not ask_price:
                logger.error(f"❌ Dados essenciais da proposta ausentes - ID: {proposal_id}, Ask Price: {ask_price}")
                return None
            
            logger.info(f"✅ Proposta aceita - ID: {proposal_id}, Ask Price: ${ask_price}")
            
            # Executar compra usando o ask_price da proposta
            buy_params = {
                "buy": proposal_id,
                "price": float(ask_price)
            }
            
            logger.info(f"🔄 Executando compra com Ask Price: ${ask_price}")
            
            buy_response = await self.api_manager.buy(buy_params)
            
            if buy_response and 'buy' in buy_response and 'contract_id' in buy_response['buy']:
                contract_id = buy_response['buy']['contract_id']
                logger.info(f"✅ COMPRA ACCU EXECUTADA COM SUCESSO!")
                logger.info(f"   • Contract ID: {contract_id}")
                logger.info(f"   • Stake: ${stake_para_usar}")
                logger.info(f"   • Take Profit: ${take_profit_amount:.2f}")
                return contract_id
            else:
                logger.error(f"❌ Falha na compra: {buy_response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro durante execução da compra ACCU: {e}")
            return None

    def aplicar_gestao_risco_accumulator(self, lucro: float):
        """Gestão de risco específica para ACCUMULATOR - stake sempre fixo"""
        logger.info(f"💼 GESTÃO DE RISCO ACCUMULATOR (STAKE FIXO) - Lucro: ${lucro:.2f}")
        
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
            if self.total_profit >= WIN_STOP:
                logger.info(f"🎯 WIN STOP ATINGIDO! Total: ${self.total_profit:.2f}")
                return "STOP_WIN"
        else:
            self.total_lost += abs(lucro)  # Acumular perdas
            logger.info(f"💸 LOSS - Stake mantido: ${self.stake:.2f}")
            
            # Verificar Loss Limit
            if self.total_lost >= LOSS_LIMIT:
                logger.info(f"🛑 LOSS LIMIT ATINGIDO! Total perdido: ${self.total_lost:.2f}")
                return "STOP_LOSS"
        
        logger.info(f"📊 Estado atual: Stake=${self.stake:.2f} (FIXO), Total Profit=${self.total_profit:.2f}, Total Lost=${self.total_lost:.2f}")

    async def _execute_trade_lifecycle(self):
        """
        Encapsula o ciclo de vida completo de uma única operação:
        comprar, monitorar o resultado e aplicar a gestão de risco.
        """
        try:
            logger.info("--- Iniciando Novo Ciclo de Operação ---")
            contract_id = await self.executar_compra_accumulator()
            
            if contract_id:
                lucro = await self.monitorar_contrato(contract_id)
                self.aplicar_gestao_risco_accumulator(lucro)
            else:
                logger.error("Falha ao iniciar a operação. Nenhuma ação de gestão de risco aplicada.")
        
        except Exception as e:
            logger.error(f"Erro inesperado no ciclo de vida da operação: {e}")
        
        finally:
            # Libera a trava para permitir que novas operações sejam iniciadas
            self.is_trading_locked = False
            logger.info("--- Fim do Ciclo de Operação (TRAVA LIBERADA) ---")

    def _pre_validate_params(self):
        """Pré-valida parâmetros para otimização de latência - ACCUMULATOR"""
        current_time = time.time()
        
        # Verificar se cache ainda é válido
        if (self._cached_params and 
            current_time - self._params_cache_time < self._params_cache_ttl):
            return self._cached_params
        
        try:
            # Validar parâmetros ACCUMULATOR
            params = {
                'contract_type': 'ACCU',
                'symbol': ATIVO,
                'currency': 'USD',
                'amount': float(STAKE_INICIAL),
                'growth_rate': GROWTH_RATE
            }
            
            # Validações básicas
            if params['amount'] <= 0:
                raise ValueError(f"Stake inválido: {params['amount']}")
            
            if not (0.01 <= params['growth_rate'] <= 0.05):
                raise ValueError(f"Growth rate inválido: {params['growth_rate']}")
            
            # Atualizar cache
            self._cached_params = params
            self._params_cache_time = current_time
            
            logger.debug(f"✅ Parâmetros ACCUMULATOR pré-validados e cacheados")
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
        """Inicia servidor HTTP para endpoint /status"""
        try:
            app = web.Application()
            app.router.add_get('/status', self._status_handler)
            
            runner = web.AppRunner(app)
            await runner.setup()
            
            site = web.TCPSite(runner, 'localhost', 8080)
            await site.start()
            
            logger.info("🌐 Servidor HTTP iniciado em http://localhost:8080/status")
            
        except Exception as e:
             logger.error(f"❌ Erro ao iniciar servidor HTTP: {e}")
    
    async def _force_restart_bot(self):
        """Força reinicialização completa do bot em caso de deadlock crítico"""
        try:
            logger.error("🔄 INICIANDO REINICIALIZAÇÃO FORÇADA DO BOT...")
            
            # 1. Parar processamento de sinais
            self.running = False
            logger.info("✅ Processamento de sinais interrompido")
            
            # 2. Limpar queue de sinais
            await self.sync_system.clear_signal_queue()
            logger.info("✅ Queue de sinais limpa")
            
            # 3. Reset do circuit breaker
            self.robust_order_system.reset_circuit_breaker()
            logger.info("✅ Circuit breaker resetado")
            
            # 4. Desconectar WebSocket com timeout
            if hasattr(self, 'api_manager') and self.api_manager:
                try:
                    await asyncio.wait_for(self.api_manager.disconnect(), timeout=10.0)
                    logger.info("✅ WebSocket desconectado")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Timeout na desconexão WebSocket - continuando...")
                except Exception as e:
                    logger.warning(f"⚠️ Erro na desconexão WebSocket: {e} - continuando...")
            
            # 5. Aguardar limpeza completa
            await asyncio.sleep(8)
            
            # 6. Reinicializar componentes
            self.api_manager = DerivWebSocketNativo()
            self.api_manager.set_bot_instance(self)
            logger.info("✅ API Manager reinicializado")
            
            # 7. Reconectar com retry e timeout
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔗 Tentativa {attempt + 1}/{max_retries} de reconexão...")
                    await asyncio.wait_for(self.api_manager.connect(), timeout=15.0)
                    await asyncio.sleep(2)  # Aguardar estabilização
                    
                    await asyncio.wait_for(self.api_manager.subscribe_ticks(ATIVO), timeout=10.0)
                    logger.info("✅ Reconectado e resubscrito aos ticks")
                    break
                    
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ Timeout na tentativa {attempt + 1} - tentando novamente...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                    else:
                        raise Exception("Falha na reconexão após múltiplas tentativas")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro na tentativa {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                    else:
                        raise
            
            # 8. Reiniciar processamento
            self.running = True
            logger.info("✅ Processamento de sinais reiniciado")
            
            # 9. Reiniciar tarefas assíncronas
            asyncio.create_task(self._process_signals_from_queue())
            asyncio.create_task(self._real_time_monitoring())
            
            logger.error("🔄 REINICIALIZAÇÃO FORÇADA CONCLUÍDA COM SUCESSO")
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na reinicialização forçada: {e}")
            # Em caso de falha crítica, encerrar o processo
            logger.error("💀 ENCERRANDO PROCESSO - Falha na recuperação automática")
            os._exit(1)
    
    async def _check_inactivity_and_restart(self):
        """Verifica inatividade e reinicia o bot se necessário"""
        try:
            current_time = time.time()
            time_since_last_operation = current_time - self._last_operation_time
            
            # Log de monitoramento a cada 30 segundos
            if int(time_since_last_operation) % 30 == 0 and int(time_since_last_operation) > 0:
                logger.info(f"⏱️ Tempo desde última operação: {int(time_since_last_operation)}s (limite: {self._inactivity_timeout}s)")
            
            # Verificar se excedeu o timeout de inatividade
            if time_since_last_operation > self._inactivity_timeout and not self._restart_in_progress:
                logger.warning(f"⚠️ INATIVIDADE DETECTADA: {int(time_since_last_operation)}s sem operações")
                logger.warning(f"🔄 Iniciando reinício automático do bot...")
                
                self._restart_in_progress = True
                
                # Executar restart
                restart_success = await self._force_restart_bot()
                
                if restart_success:
                    # Resetar timestamp e contador
                    self._last_operation_time = time.time()
                    self._operation_count = 0
                    logger.info("✅ Bot reiniciado com sucesso após inatividade")
                else:
                    logger.error("❌ Falha no reinício automático")
                
                self._restart_in_progress = False
                
        except Exception as e:
            logger.error(f"❌ Erro no monitoramento de inatividade: {e}")
            self._restart_in_progress = False
    
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
    
    def _get_enhanced_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas de todos os sistemas integrados"""
        try:
            # Stats do Enhanced Tick Buffer
            buffer_stats = self.enhanced_tick_buffer.get_buffer_stats()
            
            # Stats do WebSocket Recovery
            recovery_stats = self.websocket_recovery.get_connection_stats()
            
            # Stats da Signal Queue
            queue_stats = self.signal_queue.get_queue_stats()
            
            # Stats do Health Monitor
            health_summary = self.health_monitor.get_health_report()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'bot_name': NOME_BOT,
                'operation_count': self._operation_count,
                'total_profit': self.total_profit,
                'current_stake': self.stake,
                'buffer_size': buffer_stats.get('current_size', 0),
                'buffer_capacity': buffer_stats.get('max_size', 0),
                'buffer_hit_rate': buffer_stats.get('hit_rate', 0.0),
                'recovery_attempts': recovery_stats.get('total_attempts', 0),
                'recovery_successes': recovery_stats.get('successful_recoveries', 0),
                'queue_size': queue_stats.get('current_size', 0),
                'queue_processed': queue_stats.get('total_processed', 0),
                'queue_errors': queue_stats.get('total_errors', 0),
                'health_score': health_summary.get('overall_health_score', 0.0),
                'system_uptime': health_summary.get('uptime_seconds', 0),
                'last_check': health_summary.get('last_check_time', 'N/A'),
                'active_alerts': len(health_summary.get('active_alerts', []))
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def test_enhanced_systems(self) -> Dict[str, Any]:
        """Testa todos os sistemas avançados integrados"""
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'bot_name': NOME_BOT,
            'tests': {}
        }
        
        try:
            # Teste Enhanced Tick Buffer
            test_tick_value = 1.23456
            self.enhanced_tick_buffer.add_tick(test_tick_value)
            buffer_test = self.enhanced_tick_buffer.get_last_n_ticks(1)
            buffer_stats = self.enhanced_tick_buffer.get_buffer_stats()
            test_results['tests']['enhanced_tick_buffer'] = {
                'status': 'PASS' if len(buffer_test) > 0 else 'FAIL',
                'details': f'Buffer size: {len(buffer_test)}, Stats: {buffer_stats}'
            }
            
            # Teste Signal Queue
            test_ticks = [1.23456, 1.23457, 1.23458]
            queue_added = self.signal_queue.queue_signal(test_ticks, True)
            queue_stats = self.signal_queue.get_queue_stats()
            test_results['tests']['signal_queue'] = {
                'status': 'PASS' if queue_added else 'FAIL',
                'details': f'Queue size: {queue_stats["current_size"]}, Stats: {queue_stats}'
            }
            
            # Teste WebSocket Recovery
            recovery_stats = self.websocket_recovery.get_connection_stats()
            test_results['tests']['websocket_recovery'] = {
                'status': 'PASS',
                'details': f'Recovery manager initialized, state: {recovery_stats.get("state", "unknown")}'
            }
            
            # Teste Health Monitor
            health_report = self.health_monitor.get_health_report()
            test_results['tests']['health_monitor'] = {
                'status': 'PASS',
                'details': f'Health status: {health_report.get("current_status", "unknown")}'
            }
            
            # Teste Enhanced Stats
            enhanced_stats = self._get_enhanced_stats()
            test_results['tests']['enhanced_stats'] = {
                'status': 'PASS' if 'error' not in enhanced_stats else 'FAIL',
                'details': f'Stats fields: {len(enhanced_stats)}'
            }
            
            # Resumo geral
            passed_tests = sum(1 for test in test_results['tests'].values() if test['status'] == 'PASS')
            total_tests = len(test_results['tests'])
            test_results['summary'] = {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': f'{(passed_tests/total_tests)*100:.1f}%'
            }
            
            logger.info(f"🧪 Teste dos sistemas avançados: {passed_tests}/{total_tests} PASS")
            
        except Exception as e:
            test_results['error'] = str(e)
            logger.error(f"❌ Erro durante teste dos sistemas: {e}")
        
        return test_results
    
    def _validar_configuracao_inicial(self):
        """Valida a configuração inicial do bot - Digits Over/Under"""
        logger.info("🔍 VALIDANDO CONFIGURAÇÃO INICIAL...")
        
        # Validar ATIVO
        if not ATIVO or not isinstance(ATIVO, str):
            raise ValueError(f"❌ ATIVO inválido: {ATIVO}")
        
        # Validar STAKE_INICIAL
        if STAKE_INICIAL < 0.35 or STAKE_INICIAL > 50000:
            raise ValueError(f"❌ STAKE_INICIAL inválido: ${STAKE_INICIAL} (deve ser $0.35-$50,000)")
        
        logger.info("✅ Configuração inicial validada com sucesso!")
    

    

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
                'account_name': self.account_name,
                'bot_name': NOME_BOT,
                'created_at': current_time
            }
            
            result = supabase.table('tunder_bot_logs').insert(data).execute()
            logger.info(f"✅ Log salvo no Supabase [{self.account_name}]: {operation_result} - Profit: {profit_percentage:.2f}% - Stake: ${stake_value}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar log para Supabase [{self.account_name}]: {e}")
    


    @with_error_handling(ErrorType.TRADING, ErrorSeverity.CRITICAL)
    async def executar_compra_accumulator(self) -> Optional[str]:
        """Executa compra do contrato ACCUMULATOR com parâmetros corretos"""
        
        # VALIDAÇÃO E LIMITAÇÃO DE STAKE
        stake_para_usar = min(self.stake, STAKE_MAXIMO_DERIV)
        
        if stake_para_usar < self.stake:
            logger.warning(f"⚠️ Stake limitado: ${self.stake:.2f} -> ${stake_para_usar:.2f}")
        
        # Take profit: 45% do stake atual
        take_profit_amount = self.stake * TAKE_PROFIT_PERCENTUAL
        
        try:
            # PARÂMETROS PARA PROPOSTA ACCUMULATOR
            proposal_params = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": ATIVO,
                "amount": float(stake_para_usar),
                "basis": "stake",
                "currency": "USD",
                "growth_rate": GROWTH_RATE,
                "limit_order": {
                    "take_profit": float(take_profit_amount)
                }
            }
            
            logger.info(f"💰 SOLICITANDO PROPOSTA ACCUMULATOR:")
            logger.info(f"   • Stake: ${stake_para_usar}")
            logger.info(f"   • Take Profit: ${take_profit_amount:.2f} (45%)")
            logger.info(f"   • Growth Rate: {GROWTH_RATE*100}%")
            logger.info(f"   • Symbol: {ATIVO}")
            
            # Executar proposta com sistema robusto
            proposal_result = await self.robust_order_system._execute_with_retry(
                self.api_manager.proposal,
                proposal_params,
                OperationType.PROPOSAL
            )
            
            if not proposal_result.success:
                logger.error(f"❌ Falha na proposta: {proposal_result.error}")
                return None
                
            proposal_response = proposal_result.data
            
            if 'proposal' not in proposal_response:
                logger.error(f"❌ Proposta inválida: {proposal_response}")
                return None
                
            proposal = proposal_response['proposal']
            proposal_id = proposal.get('id')
            ask_price = proposal.get('ask_price')
            
            if not proposal_id or not ask_price:
                logger.error(f"❌ Dados da proposta inválidos")
                return None
                
            # COMPRA IMEDIATA
            buy_params = {
                "buy": proposal_id,
                "price": float(ask_price)
            }
            
            buy_result = await self.robust_order_system._execute_with_retry(
                self.api_manager.buy,
                buy_params,
                OperationType.BUY
            )
            
            if buy_result.success:
                response = buy_result.data
                if 'buy' in response and 'contract_id' in response['buy']:
                    contract_id = response['buy']['contract_id']
                    logger.info(f"✅ Compra ACCUMULATOR executada - Contract ID: {contract_id}")
                    self._update_operation_timestamp()
                    return contract_id
                    
            logger.error(f"❌ Falha na compra: {buy_result.error if not buy_result.success else 'Resposta inválida'}")
            return None
            
        except Exception as e:
            logger.error(f"❌ ERRO na execução da compra ACCUMULATOR: {e}")
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
    
    def aplicar_gestao_risco_alavancs_pro(self, lucro: float):
        """Gestão de Risco ALAVANCS PRO 2.0 - Com pausa de segurança após perdas consecutivas"""
        logger.info(f"💼 GESTÃO DE RISCO ALAVANCS PRO 2.0 - Lucro: ${lucro:.2f}")
        
        # Calcular percentual para log
        profit_percentage = (lucro / self.stake) * 100 if self.stake > 0 else 0
        operation_result = "WIN" if lucro > 0 else "LOSS"
        
        # Enviar para Supabase
        asyncio.create_task(self.log_to_supabase(operation_result, profit_percentage, self.stake))
        
        # Atualizar total_profit ANTES de resetar o stake
        self.total_profit += lucro
        
        # SEMPRE resetar stake para valor fixo (SEM Martingale)
        self.stake = STAKE_INICIAL  # Sempre fixo
        
        if lucro > 0:
            # WIN: Resetar contador de perdas consecutivas
            self.consecutive_losses = 0
            logger.info(f"🎉 WIN - Perdas consecutivas resetadas. Stake: ${self.stake:.2f}")
            
            # Verificar Win Stop
            if self.total_profit >= WIN_STOP:
                logger.info(f"🎯 WIN STOP ATINGIDO! Total: ${self.total_profit:.2f}")
                return "STOP_WIN"
        else:
            # LOSS: Incrementar contador de perdas consecutivas
            self.consecutive_losses += 1
            logger.info(f"💸 LOSS #{self.consecutive_losses} - Stake resetado para: ${self.stake:.2f}")
            
            # Verificar Loss Limit (total de perdas acumuladas)
            if self.total_profit <= -LOSS_LIMIT:
                logger.info(f"🛑 LOSS LIMIT ATINGIDO! Total: ${self.total_profit:.2f}")
                return "STOP_LOSS"
        
        logger.info(f"📊 Estado: Stake=${self.stake:.2f}, Total=${self.total_profit:.2f}, Perdas consecutivas={self.consecutive_losses}")
        return None  # Continuar operando
    

    def aplicar_gestao_risco(self, lucro: float):
        """Mantém compatibilidade com código legado - redireciona para versão ALAVANCS PRO"""
        return self.aplicar_gestao_risco_alavancs_pro(lucro)
    

    


    async def start(self):
        """Inicia o bot ALAVANCS PRO 2.0 - Sistema reativo baseado em ticks"""
        logger.info("\n" + "="*70)
        logger.info(f"🚀 INICIANDO {NOME_BOT}")
        logger.info("="*70)
        logger.info(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info(f"🎯 Estratégia: ACCUMULATOR - Sistema Reativo")
        logger.info(f"💰 Stake inicial: ${STAKE_INICIAL}")
        logger.info(f"📊 Ativo: {ATIVO}")
        logger.info(f"📈 Take Profit: {TAKE_PROFIT_PERCENTUAL*100}%")
        logger.info(f"📊 Growth Rate: {GROWTH_RATE*100}%")
        logger.info(f"🔴 Padrão: Red-Red-Red-Blue")
        logger.info(f"🎯 Meta de lucro: ${WIN_STOP}")
        logger.info(f"🛑 Limite de perda: ${LOSS_LIMIT}")
        logger.info(f"⚖️ Gestão: Dinâmica com barreiras adaptáveis")
        logger.info("="*70)
        
        # Conectar à API
        if not await self.api_manager.connect():
            logger.error("❌ Falha na conexão inicial. Encerrando.")
            return
        
        # Configurar callback de ticks
        self.api_manager.set_bot_instance(self)
        
        try:
            # Pré-validar parâmetros
            if not self._pre_validate_params():
                logger.error("❌ Falha na pré-validação de parâmetros")
                return
            
            # ATIVAR SUBSCRIPTION DE TICKS PARA ANÁLISE EM TEMPO REAL
            logger.info(f"📊 Ativando subscription de ticks para {ATIVO}...")
            await self.api_manager.subscribe_ticks(ATIVO)
            logger.info("✅ Subscription de ticks ativa - Bot reagirá a cada tick recebido")
            logger.info("🤖 Sistema reativo iniciado - _handle_new_tick processará todos os ticks")
            
            # Loop principal simples para manter o programa ativo
            logger.info("🔄 Entrando em loop de monitoramento...")
            while True:
                try:
                    # Verificar condições de parada
                    if self.total_profit >= WIN_STOP:
                        logger.info(f"🎯 META DE LUCRO ATINGIDA! Lucro total: ${self.total_profit:.2f}")
                        await self.api_manager.disconnect()
                        break
                    
                    if self.total_profit <= -LOSS_LIMIT:
                        logger.info(f"🛑 LIMITE DE PERDA ATINGIDO! Perda total: ${self.total_profit:.2f}")
                        await self.api_manager.disconnect()
                        break
                    
                    # Verificar saúde da conexão
                    if not self.api_manager.connected:
                        logger.warning("⚠️ Conexão perdida - tentando reconectar...")
                        if not await self.api_manager.connect():
                            logger.error("❌ Falha na reconexão. Tentando novamente em 10 segundos...")
                            await asyncio.sleep(10)
                            continue
                        else:
                            # Reativar subscription após reconexão
                            logger.info("🔄 Reativando subscription de ticks após reconexão...")
                            await self.api_manager.subscribe_ticks(ATIVO)
                            self.api_manager.set_bot_instance(self)
                    
                    # Sleep para evitar consumo desnecessário de CPU
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ ERRO NO LOOP DE MONITORAMENTO: {e}")
                    logger.error(f"📋 Tipo do erro: {type(e).__name__}")
                    logger.error("⏸️ Pausando por 10 segundos para recuperação...")
                    await asyncio.sleep(10)
                    
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO NO SISTEMA: {e}")
            logger.error("🔄 Encerrando bot...")
        
        finally:
            logger.info("🏁 Bot finalizado.")
            if self.api_manager.connected:
                await self.api_manager.disconnect()
    


# ============================================================================
# GERENCIADOR DE MÚLTIPLAS CONTAS
# ============================================================================
class MultiAccountManager:
    """Gerenciador para múltiplas instâncias do bot em contas diferentes"""
    
    def __init__(self, accounts_config):
        self.accounts_config = accounts_config
        self.bot_instances = {}
        self.active_bots = []
        self.operation_queue = asyncio.Queue()
        self.current_account_index = 0
        
        logger.info(f"🏦 MultiAccountManager inicializado com {len(accounts_config)} contas")
    
    async def initialize_bots(self):
        """Inicializa todas as instâncias do bot para as contas ativas"""
        for account in self.accounts_config:
            try:
                # Verificar se o token é válido
                if account['token'].startswith('SEU_TOKEN_'):
                    logger.warning(f"⚠️ Conta {account['name']} tem token placeholder - pulando")
                    continue
                
                logger.info(f"🤖 Inicializando bot para conta: {account['name']}")
                bot = AccumulatorScalpingBot(account)
                
                self.bot_instances[account['name']] = bot
                self.active_bots.append(bot)
                
                logger.info(f"✅ Bot inicializado para conta {account['name']}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar bot para conta {account['name']}: {e}")
        
        logger.info(f"🎯 Total de bots ativos: {len(self.active_bots)}")
    
    async def start_all_bots(self):
        """Inicia todos os bots simultaneamente"""
        if not self.active_bots:
            logger.error("❌ Nenhum bot ativo para iniciar")
            return
        
        logger.info(f"🚀 Iniciando {len(self.active_bots)} bots simultaneamente...")
        
        # Criar tasks para todos os bots
        tasks = []
        for bot in self.active_bots:
            task = asyncio.create_task(self._run_bot_with_monitoring(bot))
            tasks.append(task)
        
        # Executar todos os bots simultaneamente
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"❌ Erro na execução dos bots: {e}")
    
    async def _run_bot_with_monitoring(self, bot):
        """Executa um bot individual com monitoramento"""
        try:
            logger.info(f"🤖 Iniciando bot para conta: {bot.account_name}")
            await bot.start()
        except Exception as e:
            logger.error(f"❌ Erro no bot da conta {bot.account_name}: {e}")
            # Tentar reiniciar o bot após erro
            await asyncio.sleep(30)
            logger.info(f"🔄 Tentando reiniciar bot da conta {bot.account_name}")
            await self._run_bot_with_monitoring(bot)
    
    def get_next_available_bot(self):
        """Retorna o próximo bot disponível para operação (round-robin)"""
        if not self.active_bots:
            return None
        
        bot = self.active_bots[self.current_account_index]
        self.current_account_index = (self.current_account_index + 1) % len(self.active_bots)
        
        return bot
    
    async def distribute_operation(self, operation_data):
        """Distribui uma operação para o próximo bot disponível"""
        bot = self.get_next_available_bot()
        if bot:
            logger.info(f"📊 Distribuindo operação para conta: {bot.account_name}")
            await self.operation_queue.put((bot, operation_data))
        else:
            logger.warning("⚠️ Nenhum bot disponível para operação")
    
    async def get_combined_statistics(self):
        """Retorna estatísticas combinadas de todos os bots"""
        total_profit = 0.0
        total_operations = 0
        
        for bot in self.active_bots:
            total_profit += bot.total_profit
            total_operations += bot.ciclo
        
        return {
            'total_profit': total_profit,
            'total_operations': total_operations,
            'active_accounts': len(self.active_bots),
            'accounts': [bot.account_name for bot in self.active_bots]
        }

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
@with_error_handling(ErrorType.SYSTEM, ErrorSeverity.CRITICAL)
async def main():
    """Função principal do bot com suporte a múltiplas contas"""
    try:
        print("\n[INICIO] Iniciando ACCUMULATOR Bot - Modo Multi-Conta")
        print("[CONFIG] Configuracao:")
        print(f"   • Ativo: {ATIVO}")
        print(f"   • Stake Inicial: ${STAKE_INICIAL}")
        print(f"   • Take Profit: {TAKE_PROFIT_PERCENTUAL*100}%")
        print(f"   • Growth Rate: {GROWTH_RATE*100}%")
        print(f"   • Estratégia: ACCUMULATOR")
        print(f"   • Padrão: Red-Red-Red-Blue")
        print("="*60)
        
        # Verificar se há contas ativas configuradas
        if not ACTIVE_ACCOUNTS:
            logger.error("❌ Nenhuma conta ativa configurada")
            return
        
        print(f"[CONTAS] Contas configuradas:")
        for account in ACTIVE_ACCOUNTS:
            status = "✅ ATIVA" if not account['token'].startswith('SEU_TOKEN_') else "⚠️ TOKEN PLACEHOLDER"
            print(f"   • {account['name']}: {status}")
        print("="*60)
        
        # Criar e inicializar o gerenciador de múltiplas contas
        manager = MultiAccountManager(ACTIVE_ACCOUNTS)
        await manager.initialize_bots()
        
        # Verificar se há bots ativos
        if not manager.active_bots:
            logger.error("❌ Nenhum bot foi inicializado com sucesso")
            return
        
        # Iniciar todos os bots
        logger.info(f"🚀 Iniciando {len(manager.active_bots)} bots simultaneamente...")
        await manager.start_all_bots()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO na função main: {e}")
        logger.error(f"📋 Tipo do erro: {type(e).__name__}")
        # Não fazer sys.exit() para evitar exit code 1
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Accumulator Bot finalizado pelo usuário")
    except Exception as e:
        logger.error(f"❌ ERRO FATAL: {e}")
        # Log do erro mas não fazer exit com código 1
        logger.info("🔄 Bot será reiniciado pelo gerenciador")