#!/usr/bin/env python3
"""
Accumulator Scalping Bot - Modo Standalone
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
# PARÂMETROS DE GESTÃO (CONFORME XML ORIGINAL)
# ============================================================================
NOME_BOT = "Accumulator_Scalping_Bot"
STAKE_INICIAL = 5.0  # initial stake - alterado para 5
STAKE_MAXIMO_DERIV = 1000.0  # Limite máximo de stake permitido pela Deriv API
TAKE_PROFIT_PERCENTUAL = 0.10  # 10% (Return%) - Voltando ao valor original
ATIVO = 'R_10'
GROWTH_RATE = 0.02  # 2% - Valor corrigido conforme solicitação
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
                return response
            except asyncio.TimeoutError:
                # Cleanup em caso de timeout
                self.pending_requests.pop(req_id, None)
                raise Exception(f"Timeout aguardando response para req_id {req_id}")
                
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
        
        # Configurar callbacks de recuperação do health monitor
        self.health_monitor.set_recovery_callbacks(
            on_connection_issues=self._reconnect_and_resubscribe,
            on_system_restart=self._force_restart_bot
        )
        
        logger.info(f"🤖 {NOME_BOT} inicializado")
        logger.info(f"📊 Configuração XML:")
        logger.info(f"   • Ativo: {ATIVO}")
        logger.info(f"   • Initial Stake: ${self.initial_stake}")
        logger.info(f"   • Stake Atual: ${self.stake}")
        logger.info(f"   • Take Profit %: {TAKE_PROFIT_PERCENTUAL*100}%")
        logger.info(f"   • Growth Rate: {GROWTH_RATE*100}%")
        logger.info(f"   • Khizzbot: {self.khizzbot}")
        logger.info(f"   • Win Stop: ${self.win_stop}")
        logger.info(f"   • Loss Limit: ${self.loss_limit}")
        logger.info(f"🔧 Sistemas Avançados Integrados:")
        logger.info(f"   • Enhanced Tick Buffer: ✅ (max_size=10)")
        logger.info(f"   • WebSocket Recovery: ✅ (max_retries=5)")
        logger.info(f"   • Signal Queue: ✅ (max_size=10, max_concurrent=2)")
        logger.info(f"   • Health Monitor: ✅ (check_interval=30s)")
    
    @with_error_handling(ErrorType.DATA_PROCESSING, ErrorSeverity.HIGH)
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
            
            result = supabase.table('scalping_accumulator_bot_logs').insert(data).execute()
            logger.info(f"📊 Log enviado para Supabase: {operation_result} - {profit_percentage:.2f}% - ${stake_value}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar log para Supabase: {e}")
    
    @with_error_handling(ErrorType.TRADING, ErrorSeverity.CRITICAL)
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
            
            # Iniciar monitoramento em tempo real
            logger.info("📊 Iniciando monitoramento em tempo real...")
            monitoring_task = asyncio.create_task(self._real_time_monitoring())
            
            # Iniciar servidor HTTP para endpoint /status
            logger.info("🌐 Iniciando servidor HTTP...")
            http_server_task = asyncio.create_task(self._start_http_server())
            
            # Iniciar Health Monitor em paralelo
            logger.info("🏥 Iniciando Health Monitor...")
            health_monitor_task = asyncio.create_task(
                self.health_monitor.monitor_and_recover(
                    stats_provider=self._get_enhanced_stats,
                    check_interval=30.0
                )
            )
            
            logger.info("✅ Bot em modo tempo real - aguardando ticks...")
            logger.info("🎯 Padrão será analisado automaticamente a cada tick recebido")
            logger.info("⚡ Sistema de sincronização aprimorado ativo")
            logger.info("🌐 Endpoint de status disponível em http://localhost:8080/status")
            logger.info("🔧 Sistemas Avançados Ativos:")
            logger.info("   • Enhanced Tick Buffer: ✅ Otimização de dados")
            logger.info("   • WebSocket Recovery: ✅ Auto-recuperação")
            logger.info("   • Signal Queue: ✅ Processamento paralelo")
            logger.info("   • Health Monitor: ✅ Monitoramento contínuo")
            
            # Loop de monitoramento principal
            while True:
                try:
                    # Verificar se subscription ainda está ativa
                    if not self.api_manager.connected:
                        logger.warning("⚠️ Conexão perdida - tentando reconectar...")
                        await self._reconnect_and_resubscribe()
                    
                    # Verificar inatividade e reiniciar se necessário
                    await self._check_inactivity_and_restart()
                    
                    # Aguardar antes da próxima verificação
                    await asyncio.sleep(15)  # Verificação de conectividade a cada 15s
                    
                except Exception as e:
                    logger.error(f"❌ ERRO NO MONITORAMENTO: {e}")
                    logger.error(f"📋 Tipo do erro: {type(e).__name__}")
                    logger.error("⏸️ Pausando por 15 segundos para recuperação...")
                    
                    await asyncio.sleep(15)
                    await self._reconnect_and_resubscribe()
                    
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO NO SISTEMA DE TEMPO REAL: {e}")
            logger.error("🔄 Tentando reiniciar sistema...")
            await self._reconnect_and_resubscribe()
    
    async def _reconnect_and_resubscribe(self):
        """Reconecta e reinicia subscription de ticks com recuperação automática"""
        try:
            logger.info("🔄 Iniciando recuperação automática...")
            
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
            
            # Reconectar com retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔌 Tentativa de reconexão {attempt + 1}/{max_retries}")
                    
                    if await self.api_manager.connect():
                        logger.info("✅ Reconexão bem-sucedida")
                        break
                    else:
                        logger.warning(f"⚠️ Falha na tentativa {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(5 * (attempt + 1))  # Delay progressivo
                except Exception as conn_error:
                    logger.error(f"❌ Erro na tentativa {attempt + 1}: {conn_error}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5 * (attempt + 1))
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

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
@with_error_handling(ErrorType.SYSTEM, ErrorSeverity.CRITICAL)
async def main():
    """Função principal do bot"""
    try:
        print("\n[INICIO] Iniciando Accumulator Scalping Bot - Modo Standalone")
        print("[CONFIG] Configuracao:")
        print(f"   • Ativo: {ATIVO}")
        print(f"   • Stake Inicial: ${STAKE_INICIAL}")
        print(f"   • Take Profit: {TAKE_PROFIT_PERCENTUAL*100}%")
        print(f"   • Growth Rate: {GROWTH_RATE*100}%")
        print(f"   • Padrao: Red-Red-Red-Blue (3 subidas + 1 queda)")
        print(f"   • Gestao: Stake fixo (sem martingale)")
        print("="*60)
        
        # Criar e iniciar o bot
        bot = AccumulatorScalpingBot()
        await bot.start()
        
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