#!/usr/bin/env python3
"""
Sistema Robusto de Execução de Ordens para Deriv API
Inclui timeout, retry, gestão de contratos, circuit breaker e logging estruturado
"""

import asyncio
import time
import logging
import json
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('robust_order_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Tipos de operação suportados"""
    BUY = "buy"
    PROPOSAL = "proposal"
    PORTFOLIO = "portfolio"
    CONTRACT_INFO = "contract_info"

@dataclass
class RetryConfig:
    """Configuração de retry com delay exponencial"""
    max_attempts: int = 3
    base_delay: float = 1.0  # Delay inicial em segundos
    max_delay: float = 8.0   # Delay máximo em segundos
    timeout: float = 15.0    # Timeout por tentativa (otimizado)

@dataclass
class CircuitBreakerConfig:
    """Configuração do circuit breaker"""
    failure_threshold: int = 5  # Número de falhas consecutivas
    recovery_timeout: float = 120.0  # 2 minutos em segundos (otimizado)
    half_open_max_calls: int = 3  # Máximo de chamadas no estado half-open

class CircuitBreakerState(Enum):
    """Estados do circuit breaker"""
    CLOSED = "closed"      # Funcionamento normal
    OPEN = "open"          # Bloqueado devido a falhas
    HALF_OPEN = "half_open" # Testando recuperação

@dataclass
class OperationResult:
    """Resultado de uma operação"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0
    total_time: float = 0.0
    circuit_breaker_triggered: bool = False

class RobustOrderSystem:
    """Sistema robusto de execução de ordens com timeout, retry e circuit breaker"""
    
    def __init__(self, api_manager, retry_config: RetryConfig = None, circuit_config: CircuitBreakerConfig = None):
        self.api_manager = api_manager
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        
        # Logger instance
        self.logger = logger
        
        # Circuit breaker state
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
        # Request ID management
        self.req_id_counter = 0
        self.pending_futures = {}
        
        # Connection monitoring
        self.last_ping_time = 0
        self.ping_interval = 25.0  # 25 segundos
        self.max_latency = 2.0     # 2 segundos
        
        # Portfolio management
        self.max_positions_per_type = 5
        self.current_positions = {}
        
        # Statistics
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'timeouts': 0,
            'circuit_breaker_activations': 0,
            'retries_performed': 0
        }
        
        self.logger.info("🔧 Sistema Robusto de Ordens inicializado")
        self.logger.info(f"⚙️ Configurações: timeout={self.retry_config.timeout}s, max_attempts={self.retry_config.max_attempts}")
        self.logger.info(f"🔒 Circuit Breaker: threshold={self.circuit_config.failure_threshold}, recovery={self.circuit_config.recovery_timeout}s")
    
    @property
    def circuit_breaker_state(self):
        """Retorna o estado atual do circuit breaker como string"""
        return self.circuit_state.value
    
    def _generate_unique_req_id(self) -> str:
        """Gera um req_id único baseado em timestamp + valor aleatório"""
        timestamp = int(time.time() * 1000)  # Milliseconds
        random_part = random.randint(1000, 9999)
        self.req_id_counter += 1
        return f"{timestamp}_{random_part}_{self.req_id_counter}"
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calcula delay exponencial para retry"""
        delay = self.retry_config.base_delay * (2 ** (attempt - 1))
        return min(delay, self.retry_config.max_delay)
    
    async def _check_circuit_breaker(self) -> bool:
        """Verifica estado do circuit breaker"""
        current_time = time.time()
        
        if self.circuit_state == CircuitBreakerState.OPEN:
            # Verificar se é hora de tentar recuperação
            if (self.last_failure_time and 
                current_time - self.last_failure_time >= self.circuit_config.recovery_timeout):
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("🔄 Circuit Breaker: Tentando recuperação (HALF_OPEN)")
                return True
            else:
                remaining = self.circuit_config.recovery_timeout - (current_time - self.last_failure_time)
                logger.warning(f"🚫 Circuit Breaker ATIVO - Aguardando {remaining:.1f}s para recuperação")
                return False
        
        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Limitar chamadas no estado half-open
            if self.half_open_calls >= self.circuit_config.half_open_max_calls:
                logger.warning("🚫 Circuit Breaker: Limite de chamadas HALF_OPEN atingido")
                return False
        
        return True
    
    def _record_success(self):
        """Registra sucesso e atualiza circuit breaker"""
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Recuperação bem-sucedida
            self.circuit_state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
            logger.info("✅ Circuit Breaker: Recuperação bem-sucedida (CLOSED)")
        else:
            # Reset contador de falhas em operação normal
            self.failure_count = 0
        
        self.stats['successful_operations'] += 1
    
    def _record_failure(self):
        """Registra falha e atualiza circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Falha durante recuperação - voltar para OPEN
            self.circuit_state = CircuitBreakerState.OPEN
            logger.error("❌ Circuit Breaker: Falha durante recuperação (OPEN)")
        elif (self.circuit_state == CircuitBreakerState.CLOSED and 
              self.failure_count >= self.circuit_config.failure_threshold):
            # Ativar circuit breaker
            self.circuit_state = CircuitBreakerState.OPEN
            self.stats['circuit_breaker_activations'] += 1
            logger.error(f"🚨 CIRCUIT BREAKER ATIVADO após {self.failure_count} falhas consecutivas")
            logger.error(f"⏰ Sistema pausado por {self.circuit_config.recovery_timeout}s")
        
        self.stats['failed_operations'] += 1
    
    async def _check_portfolio_limits(self, contract_type: str) -> bool:
        """Verifica se o limite de posições foi atingido"""
        try:
            portfolio_response = await self.api_manager.portfolio()
            
            # CORREÇÃO CRÍTICA: Validar resposta NULL antes de processar
            if portfolio_response is None:
                self.logger.error("Falha na comunicação WebSocket: resposta NULL do portfolio (timeout ou erro de conexão)")
                return False  # Tratar como erro de conexão
            
            if 'error' in portfolio_response:
                 self.logger.error(f"Erro ao consultar portfolio: {portfolio_response['error']}")
                 return False
            
            # Conta contratos ativos do tipo especificado
            # A estrutura do portfolio da Deriv pode variar, vamos verificar ambas as possibilidades
            contracts = []
            if 'portfolio' in portfolio_response:
                if 'contracts' in portfolio_response['portfolio']:
                    contracts = portfolio_response['portfolio']['contracts']
                else:
                    # Às vezes os contratos vêm diretamente no portfolio
                    contracts = portfolio_response['portfolio']
            
            # Filtra contratos ativos (não vendidos) do tipo especificado
            same_type_count = 0
            for contract in contracts:
                # Verifica se é do tipo correto e ainda está ativo
                if (contract.get('contract_type') == contract_type and 
                    contract.get('is_sold', 1) == 0):  # is_sold = 0 significa ativo
                    same_type_count += 1
            
            self.logger.info(f"Contratos ativos do tipo {contract_type}: {same_type_count}/5")
            
            return same_type_count < 5
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar limites do portfolio: {e}")
            return False
    
    async def _execute_with_retry(self, operation_func: Callable, params: Dict[str, Any], 
                                 operation_type: OperationType) -> OperationResult:
        """Executa operação com retry e timeout"""
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                # Gerar req_id único para esta tentativa
                req_id = self._generate_unique_req_id()
                if 'req_id' not in params:
                    params['req_id'] = req_id
                
                logger.info(f"🔄 {operation_type.value.upper()} - Tentativa {attempt}/{self.retry_config.max_attempts} (req_id: {req_id})")
                
                # Executar com timeout
                result = await asyncio.wait_for(
                    operation_func(params),
                    timeout=self.retry_config.timeout
                )
                
                # Verificar se há erro na resposta
                if isinstance(result, dict) and 'error' in result:
                    raise Exception(f"API Error: {result['error'].get('message', 'Unknown error')}")
                
                # Sucesso
                total_time = time.time() - start_time
                logger.info(f"✅ {operation_type.value.upper()} bem-sucedida em {total_time:.2f}s (tentativa {attempt})")
                
                return OperationResult(
                    success=True,
                    data=result,
                    attempts=attempt,
                    total_time=total_time
                )
                
            except asyncio.TimeoutError:
                self.stats['timeouts'] += 1
                last_error = f"Timeout após {self.retry_config.timeout}s"
                logger.warning(f"⏰ {operation_type.value.upper()} - Timeout na tentativa {attempt}")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ {operation_type.value.upper()} - Erro na tentativa {attempt}: {e}")
            
            # Delay antes da próxima tentativa (exceto na última)
            if attempt < self.retry_config.max_attempts:
                delay = self._calculate_delay(attempt)
                logger.info(f"⏳ Aguardando {delay:.1f}s antes da próxima tentativa...")
                await asyncio.sleep(delay)
                self.stats['retries_performed'] += 1
        
        # Todas as tentativas falharam
        total_time = time.time() - start_time
        logger.error(f"❌ {operation_type.value.upper()} falhou após {self.retry_config.max_attempts} tentativas em {total_time:.2f}s")
        logger.error(f"❌ Último erro: {last_error}")
        
        return OperationResult(
            success=False,
            error=last_error,
            attempts=self.retry_config.max_attempts,
            total_time=total_time
        )
    
    async def execute_buy(self, params: Dict[str, Any]) -> OperationResult:
        """Executa compra com sistema robusto"""
        self.stats['total_operations'] += 1
        
        # Verificar circuit breaker
        if not await self._check_circuit_breaker():
            return OperationResult(
                success=False,
                error="Circuit breaker ativo",
                circuit_breaker_triggered=True
            )
        
        # Verificar limites de portfolio
        contract_type = params.get('contract_type', 'ACCU')
        if not await self._check_portfolio_limits(contract_type):
            return OperationResult(
                success=False,
                error=f"Limite de posições atingido para {contract_type}"
            )
        
        # Executar compra
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
        
        result = await self._execute_with_retry(
            self.api_manager.buy,
            params,
            OperationType.BUY
        )
        
        # Atualizar circuit breaker
        if result.success:
            self._record_success()
        else:
            self._record_failure()
        
        return result
    
    async def execute_proposal(self, params: Dict[str, Any]) -> OperationResult:
        """Executa proposta com sistema robusto"""
        self.stats['total_operations'] += 1
        
        # Verificar circuit breaker
        if not await self._check_circuit_breaker():
            return OperationResult(
                success=False,
                error="Circuit breaker ativo",
                circuit_breaker_triggered=True
            )
        
        # Executar proposta
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
        
        result = await self._execute_with_retry(
            self.api_manager.proposal,
            params,
            OperationType.PROPOSAL
        )
        
        # Atualizar circuit breaker
        if result.success:
            self._record_success()
        else:
            self._record_failure()
        
        return result
    
    async def monitor_connection(self):
        """Monitora conexão com ping/pong automático"""
        while True:
            try:
                current_time = time.time()
                
                # Verificar se é hora de fazer ping
                if current_time - self.last_ping_time >= self.ping_interval:
                    start_ping = time.time()
                    
                    # Executar ping
                    ping_params = {"ping": 1}
                    result = await self._execute_with_retry(
                        self.api_manager._send_request,
                        ping_params,
                        OperationType.PORTFOLIO  # Usar tipo genérico
                    )
                    
                    if result.success:
                        latency = time.time() - start_ping
                        self.last_ping_time = current_time
                        
                        if latency > self.max_latency:
                            logger.warning(f"⚠️ Alta latência detectada: {latency:.2f}s > {self.max_latency}s")
                            # Reconectar se latência muito alta
                            await self.api_manager._reconnect()
                        else:
                            logger.debug(f"💓 Ping OK - Latência: {latency:.2f}s")
                    else:
                        logger.warning("⚠️ Ping falhou - Tentando reconexão...")
                        await self.api_manager._reconnect()
                
                await asyncio.sleep(5)  # Verificar a cada 5 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento de conexão: {e}")
                await asyncio.sleep(10)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        total_ops = self.stats['total_operations']
        success_rate = (self.stats['successful_operations'] / total_ops * 100) if total_ops > 0 else 0
        
        return {
            'total_operations': total_ops,
            'successful_operations': self.stats['successful_operations'],
            'failed_operations': self.stats['failed_operations'],
            'success_rate': f"{success_rate:.1f}%",
            'timeouts': self.stats['timeouts'],
            'retries_performed': self.stats['retries_performed'],
            'circuit_breaker_activations': self.stats['circuit_breaker_activations'],
            'circuit_breaker_state': self.circuit_state.value,
            'current_failure_count': self.failure_count,
            'current_positions': self.current_positions
        }
    
    def log_statistics(self):
        """Registra estatísticas no log"""
        stats = self.get_statistics()
        logger.info("📊 ESTATÍSTICAS DO SISTEMA ROBUSTO:")
        for key, value in stats.items():
            logger.info(f"   • {key}: {value}")
    
    def reset_circuit_breaker(self):
        """Força reset do circuit breaker para estado CLOSED"""
        try:
            old_state = self.circuit_state.value
            self.circuit_state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.half_open_calls = 0
            
            logger.info(f"🔄 Circuit Breaker resetado: {old_state} → CLOSED")
            logger.info("✅ Contadores de falha zerados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao resetar circuit breaker: {e}")