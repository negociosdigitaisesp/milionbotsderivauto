#!/usr/bin/env python3
"""
Sistema Robusto de Tratamento de Erros
Para gerenciamento centralizado de exceções e recuperação automática
"""

import logging
import asyncio
import time
import traceback
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from enum import Enum
from dataclasses import dataclass

class ErrorSeverity(Enum):
    """Níveis de severidade de erro"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorType(Enum):
    """Tipos de erro categorizados"""
    CONNECTION = "CONNECTION"
    AUTHENTICATION = "AUTHENTICATION"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    WEBSOCKET = "WEBSOCKET"
    TRADING = "TRADING"
    DATA_PROCESSING = "DATA_PROCESSING"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"

@dataclass
class ErrorInfo:
    """Informações detalhadas do erro"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    timestamp: datetime
    traceback_info: str
    retry_count: int = 0
    max_retries: int = 3
    recovery_action: Optional[str] = None

class CircuitBreaker:
    """Implementação de Circuit Breaker para prevenção de falhas em cascata"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Executa função com proteção de circuit breaker"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
    
    async def async_call(self, func: Callable, *args, **kwargs):
        """Versão assíncrona do circuit breaker"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e

class RobustErrorHandler:
    """Sistema robusto de tratamento de erros com recuperação automática"""
    
    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.logger = logging.getLogger(f"{bot_name}_error_handler")
        self.error_history: Dict[str, ErrorInfo] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_strategies: Dict[ErrorType, Callable] = {}
        
        # Configurar circuit breakers para diferentes operações
        self.circuit_breakers["websocket"] = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        self.circuit_breakers["api_calls"] = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.circuit_breakers["trading"] = CircuitBreaker(failure_threshold=2, recovery_timeout=120)
        
        # Configurar estratégias de recuperação
        self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self):
        """Configura estratégias de recuperação para diferentes tipos de erro"""
        self.recovery_strategies = {
            ErrorType.CONNECTION: self._recover_connection,
            ErrorType.WEBSOCKET: self._recover_websocket,
            ErrorType.AUTHENTICATION: self._recover_authentication,
            ErrorType.API_RATE_LIMIT: self._recover_rate_limit,
            ErrorType.TRADING: self._recover_trading,
        }
    
    def classify_error(self, exception: Exception) -> ErrorInfo:
        """Classifica o erro e determina severidade"""
        error_msg = str(exception)
        error_type = ErrorType.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        
        # Classificação por tipo de exceção
        if isinstance(exception, ConnectionError) or "connection" in error_msg.lower():
            error_type = ErrorType.CONNECTION
            severity = ErrorSeverity.HIGH
        elif "websocket" in error_msg.lower() or "ws" in error_msg.lower():
            error_type = ErrorType.WEBSOCKET
            severity = ErrorSeverity.HIGH
        elif "auth" in error_msg.lower() or "token" in error_msg.lower():
            error_type = ErrorType.AUTHENTICATION
            severity = ErrorSeverity.CRITICAL
        elif "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            error_type = ErrorType.API_RATE_LIMIT
            severity = ErrorSeverity.MEDIUM
        elif "buy" in error_msg.lower() or "trade" in error_msg.lower():
            error_type = ErrorType.TRADING
            severity = ErrorSeverity.HIGH
        elif "json" in error_msg.lower() or "decode" in error_msg.lower():
            error_type = ErrorType.DATA_PROCESSING
            severity = ErrorSeverity.LOW
        
        return ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=error_msg,
            timestamp=datetime.now(),
            traceback_info=traceback.format_exc()
        )
    
    async def handle_error(self, exception: Exception, context: str = "") -> bool:
        """Manipula erro com recuperação automática"""
        error_info = self.classify_error(exception)
        error_key = f"{error_info.error_type.value}_{context}"
        
        # Atualizar histórico de erros
        if error_key in self.error_history:
            self.error_history[error_key].retry_count += 1
        else:
            self.error_history[error_key] = error_info
        
        # Log detalhado do erro
        self.logger.error(
            f"🚨 ERRO DETECTADO [{self.bot_name}] - {error_info.error_type.value}\n"
            f"   Contexto: {context}\n"
            f"   Severidade: {error_info.severity.value}\n"
            f"   Mensagem: {error_info.message}\n"
            f"   Tentativa: {error_info.retry_count + 1}/{error_info.max_retries}"
        )
        
        # Verificar se deve tentar recuperação
        if error_info.retry_count >= error_info.max_retries:
            self.logger.critical(
                f"💀 ERRO CRÍTICO [{self.bot_name}] - Máximo de tentativas excedido para {error_info.error_type.value}"
            )
            return False
        
        # Tentar recuperação automática
        if error_info.error_type in self.recovery_strategies:
            try:
                recovery_success = await self.recovery_strategies[error_info.error_type](error_info, context)
                if recovery_success:
                    self.logger.info(f"✅ RECUPERAÇÃO AUTOMÁTICA SUCESSO [{self.bot_name}] - {error_info.error_type.value}")
                    # Reset do contador de erros em caso de sucesso
                    if error_key in self.error_history:
                        self.error_history[error_key].retry_count = 0
                    return True
                else:
                    self.logger.warning(f"⚠️ RECUPERAÇÃO FALHOU [{self.bot_name}] - {error_info.error_type.value}")
            except Exception as recovery_error:
                self.logger.error(f"❌ ERRO NA RECUPERAÇÃO [{self.bot_name}]: {recovery_error}")
        
        return False
    
    async def _recover_connection(self, error_info: ErrorInfo, context: str) -> bool:
        """Estratégia de recuperação para erros de conexão"""
        self.logger.info(f"🔄 Tentando recuperar conexão [{self.bot_name}]...")
        await asyncio.sleep(5 * (error_info.retry_count + 1))  # Backoff exponencial
        return True  # Será implementado pelo bot específico
    
    async def _recover_websocket(self, error_info: ErrorInfo, context: str) -> bool:
        """Estratégia de recuperação para erros de WebSocket"""
        self.logger.info(f"🔄 Tentando recuperar WebSocket [{self.bot_name}]...")
        await asyncio.sleep(3 * (error_info.retry_count + 1))
        return True  # Será implementado pelo bot específico
    
    async def _recover_authentication(self, error_info: ErrorInfo, context: str) -> bool:
        """Estratégia de recuperação para erros de autenticação"""
        self.logger.info(f"🔄 Tentando reautenticar [{self.bot_name}]...")
        await asyncio.sleep(10)
        return True  # Será implementado pelo bot específico
    
    async def _recover_rate_limit(self, error_info: ErrorInfo, context: str) -> bool:
        """Estratégia de recuperação para rate limiting"""
        wait_time = 60 * (error_info.retry_count + 1)  # Aumenta tempo de espera
        self.logger.info(f"⏳ Rate limit detectado [{self.bot_name}] - Aguardando {wait_time}s...")
        await asyncio.sleep(wait_time)
        return True
    
    async def _recover_trading(self, error_info: ErrorInfo, context: str) -> bool:
        """Estratégia de recuperação para erros de trading"""
        self.logger.info(f"🔄 Tentando recuperar sistema de trading [{self.bot_name}]...")
        await asyncio.sleep(15)
        return True  # Será implementado pelo bot específico
    
    def get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """Obtém circuit breaker para operação específica"""
        return self.circuit_breakers.get(operation, self.circuit_breakers["api_calls"])
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de erros"""
        stats = {
            "total_errors": len(self.error_history),
            "error_types": {},
            "circuit_breaker_states": {}
        }
        
        for error_info in self.error_history.values():
            error_type = error_info.error_type.value
            if error_type not in stats["error_types"]:
                stats["error_types"][error_type] = 0
            stats["error_types"][error_type] += 1
        
        for name, cb in self.circuit_breakers.items():
            stats["circuit_breaker_states"][name] = cb.state
        
        return stats

# Decorator para tratamento automático de erros
def with_error_handling(error_type: ErrorType, severity: ErrorSeverity):
    """Decorator para aplicar tratamento de erros automático"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Tentar obter error_handler da instância (self)
                if args and hasattr(args[0], 'error_handler'):
                    error_handler = args[0].error_handler
                    recovery_success = await error_handler.handle_error(e, error_type, severity)
                    if not recovery_success:
                        raise e
                    # Tentar novamente após recuperação
                    return await func(*args, **kwargs)
                else:
                    # Se não há error_handler, apenas re-raise
                    raise e
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Para funções síncronas, tentar usar error_handler se disponível
                if args and hasattr(args[0], 'error_handler'):
                    error_handler = args[0].error_handler
                    error_handler.logger.error(f"Erro em função síncrona [{error_type.value}]: {e}")
                raise e
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator