import asyncio
import time
import threading
from dataclasses import dataclass
from typing import Optional, List, Any, Callable
from enum import Enum
import logging
from collections import deque
import uuid

class CircuitBreakerState(Enum):
    CLOSED = "closed"    # Funcionando normalmente
    OPEN = "open"        # Bloqueado por falhas
    HALF_OPEN = "half_open"  # Testando recuperação

@dataclass
class QueuedSignal:
    """Estrutura para sinal enfileirado"""
    ticks_data: List[float]
    pattern_detected: bool
    timestamp: float
    signal_id: str
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3

class CircuitBreaker:
    """Circuit breaker para proteção contra falhas consecutivas"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitBreakerState.CLOSED
        self.logger = logging.getLogger(__name__)
    
    def record_success(self):
        """Registra operação bem-sucedida"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.logger.info("Circuit breaker: Recuperação confirmada")
            self.reset()
        elif self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Registra falha de operação"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold and self.state == CircuitBreakerState.CLOSED:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker ABERTO após {self.failure_count} falhas")
    
    def can_execute(self) -> bool:
        """Verifica se pode executar operação"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker: Tentando recuperação")
                return True
            return False
        
        # HALF_OPEN: permitir uma tentativa
        return True
    
    def reset(self):
        """Reseta o circuit breaker"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = 0
        self.logger.info("Circuit breaker resetado")
    
    def get_state(self) -> str:
        return self.state.value
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do circuit breaker"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_age": time.time() - self.last_failure_time if self.last_failure_time > 0 else None,
            "recovery_timeout": self.recovery_timeout
        }

class ThreadSafeSignalQueue:
    """Fila thread-safe para processamento de sinais de trading"""
    
    def __init__(self, max_size: int = 10, max_concurrent: int = 2):
        self.max_size = max_size
        self.max_concurrent = max_concurrent
        self.queue = deque(maxlen=max_size)
        self.processing_count = 0
        self.lock = threading.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.circuit_breaker = CircuitBreaker()
        self.logger = logging.getLogger(__name__)
        
        # Estatísticas
        self.total_signals = 0
        self.processed_signals = 0
        self.failed_signals = 0
        self.last_signal_time = 0
        self.successful_operations = 0
        self.failed_operations = 0
        
        # Callbacks
        self.on_signal_processed: Optional[Callable] = None
        self.on_signal_failed: Optional[Callable] = None
        self.on_queue_full: Optional[Callable] = None
    
    def set_callbacks(self, on_signal_processed: Callable = None,
                     on_signal_failed: Callable = None,
                     on_queue_full: Callable = None):
        """Define callbacks para eventos da fila"""
        self.on_signal_processed = on_signal_processed
        self.on_signal_failed = on_signal_failed
        self.on_queue_full = on_queue_full
    
    def queue_signal(self, ticks_data: List[float], pattern_detected: bool) -> bool:
        """Adiciona sinal à fila com controle de fluxo"""
        try:
            with self.lock:
                # Verificar circuit breaker
                if not self.circuit_breaker.can_execute():
                    self.logger.warning("Sinal rejeitado - Circuit breaker aberto")
                    return False
                
                # Verificar tamanho da fila
                if len(self.queue) >= self.max_size:
                    self.logger.warning("Sinal rejeitado - Fila cheia")
                    if self.on_queue_full:
                        try:
                            self.on_queue_full(len(self.queue))
                        except Exception as e:
                            self.logger.error(f"Erro no callback queue_full: {e}")
                    return False
                
                # Criar sinal
                signal = QueuedSignal(
                    ticks_data=ticks_data.copy(),
                    pattern_detected=pattern_detected,
                    timestamp=time.time(),
                    signal_id=f"signal_{uuid.uuid4().hex[:8]}",
                    priority=1 if pattern_detected else 0
                )
                
                # Adicionar à fila (prioridade para padrões detectados)
                if pattern_detected:
                    # Inserir no início para prioridade
                    self.queue.appendleft(signal)
                else:
                    self.queue.append(signal)
                
                self.total_signals += 1
                self.last_signal_time = time.time()
                
                self.logger.debug(f"Sinal enfileirado: {signal.signal_id}, pattern={pattern_detected}")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao enfileirar sinal: {e}")
            return False
    
    def get_next_signal(self) -> Optional[QueuedSignal]:
        """Obtém próximo sinal da fila (não bloqueante)"""
        try:
            with self.lock:
                if not self.queue:
                    return None
                
                signal = self.queue.popleft()
                self.processed_signals += 1
                
                self.logger.debug(f"Sinal desenfileirado: {signal.signal_id}")
                return signal
                
        except Exception as e:
            self.logger.error(f"Erro ao obter sinal: {e}")
            return None
    
    async def process_signal_async(self, signal: QueuedSignal, processor_func: Callable) -> bool:
        """Processa sinal de forma assíncrona com controle de concorrência"""
        async with self.semaphore:
            try:
                with self.lock:
                    self.processing_count += 1
                
                self.logger.info(f"Processando sinal: {signal.signal_id}")
                
                # Executar processamento
                result = await processor_func(signal)
                
                if result:
                    self.successful_operations += 1
                    self.circuit_breaker.record_success()
                    
                    if self.on_signal_processed:
                        try:
                            await self.on_signal_processed(signal, result)
                        except Exception as e:
                            self.logger.error(f"Erro no callback signal_processed: {e}")
                    
                    self.logger.info(f"Sinal processado com sucesso: {signal.signal_id}")
                    return True
                else:
                    self.failed_operations += 1
                    self.circuit_breaker.record_failure()
                    
                    if self.on_signal_failed:
                        try:
                            await self.on_signal_failed(signal, "Processing failed")
                        except Exception as e:
                            self.logger.error(f"Erro no callback signal_failed: {e}")
                    
                    self.logger.warning(f"Falha no processamento do sinal: {signal.signal_id}")
                    return False
                    
            except Exception as e:
                self.failed_operations += 1
                self.circuit_breaker.record_failure()
                
                if self.on_signal_failed:
                    try:
                        await self.on_signal_failed(signal, str(e))
                    except Exception as callback_error:
                        self.logger.error(f"Erro no callback signal_failed: {callback_error}")
                
                self.logger.error(f"Erro ao processar sinal {signal.signal_id}: {e}")
                return False
                
            finally:
                with self.lock:
                    self.processing_count -= 1
    
    def retry_signal(self, signal: QueuedSignal) -> bool:
        """Recoloca sinal na fila para retry"""
        if signal.retry_count >= signal.max_retries:
            self.logger.warning(f"Sinal {signal.signal_id} excedeu máximo de tentativas")
            return False
        
        signal.retry_count += 1
        signal.timestamp = time.time()  # Atualizar timestamp
        
        with self.lock:
            # Adicionar no final da fila para retry
            self.queue.append(signal)
            
        self.logger.info(f"Sinal {signal.signal_id} recolocado na fila (tentativa {signal.retry_count})")
        return True
    
    def clear_queue(self):
        """Limpa toda a fila"""
        with self.lock:
            cleared_count = len(self.queue)
            self.queue.clear()
            
        self.logger.info(f"Fila limpa - {cleared_count} sinais removidos")
    
    def get_queue_stats(self) -> dict:
        """Retorna estatísticas da fila"""
        with self.lock:
            current_size = len(self.queue)
            
        return {
            "current_size": current_size,
            "max_size": self.max_size,
            "processing_count": self.processing_count,
            "max_concurrent": self.max_concurrent,
            "total_signals": self.total_signals,
            "processed_signals": self.processed_signals,
            "failed_signals": self.failed_signals,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "last_signal_age": time.time() - self.last_signal_time if self.last_signal_time > 0 else None,
            "circuit_breaker": self.circuit_breaker.get_stats()
        }
    
    def get_health_status(self) -> dict:
        """Retorna status de saúde da fila"""
        stats = self.get_queue_stats()
        
        # Calcular taxa de sucesso
        total_ops = stats["successful_operations"] + stats["failed_operations"]
        success_rate = stats["successful_operations"] / total_ops if total_ops > 0 else 1.0
        
        # Determinar status de saúde
        if stats["circuit_breaker"]["state"] == "open":
            health = "critical"
        elif success_rate < 0.5:
            health = "warning"
        elif stats["current_size"] >= stats["max_size"] * 0.8:
            health = "warning"
        else:
            health = "healthy"
        
        return {
            "health": health,
            "success_rate": success_rate,
            "queue_utilization": stats["current_size"] / stats["max_size"],
            "processing_utilization": stats["processing_count"] / stats["max_concurrent"],
            "circuit_breaker_state": stats["circuit_breaker"]["state"],
            "last_signal_age": stats["last_signal_age"]
        }
    
    def is_healthy(self) -> bool:
        """Verifica se a fila está saudável"""
        return self.get_health_status()["health"] == "healthy"
    
    def reset_stats(self):
        """Reseta estatísticas da fila"""
        with self.lock:
            self.total_signals = 0
            self.processed_signals = 0
            self.failed_signals = 0
            self.successful_operations = 0
            self.failed_operations = 0
            
        self.circuit_breaker.reset()
        self.logger.info("Estatísticas da fila resetadas")
    
    def get_pending_signals(self) -> List[dict]:
        """Retorna lista de sinais pendentes na fila"""
        with self.lock:
            return [
                {
                    "signal_id": signal.signal_id,
                    "pattern_detected": signal.pattern_detected,
                    "timestamp": signal.timestamp,
                    "priority": signal.priority,
                    "retry_count": signal.retry_count,
                    "age": time.time() - signal.timestamp
                }
                for signal in self.queue
            ]
    
    def remove_old_signals(self, max_age: float = 300.0) -> int:
        """Remove sinais antigos da fila (mais de max_age segundos)"""
        current_time = time.time()
        removed_count = 0
        
        with self.lock:
            # Criar nova deque sem sinais antigos
            new_queue = deque(maxlen=self.max_size)
            
            for signal in self.queue:
                if current_time - signal.timestamp <= max_age:
                    new_queue.append(signal)
                else:
                    removed_count += 1
            
            self.queue = new_queue
        
        if removed_count > 0:
            self.logger.info(f"Removidos {removed_count} sinais antigos da fila")
        
        return removed_count

class SignalQueueManager:
    """Gerenciador principal do sistema de fila de sinais"""
    
    def __init__(self, max_size: int = 10, max_concurrent: int = 2):
        self.queue = ThreadSafeSignalQueue(max_size, max_concurrent)
        self.running = False
        self.processor_task = None
        self.cleanup_task = None
        self.logger = logging.getLogger(__name__)
        
        # Configurar callbacks padrão
        self.queue.set_callbacks(
            on_signal_processed=self._on_signal_processed,
            on_signal_failed=self._on_signal_failed,
            on_queue_full=self._on_queue_full
        )
    
    async def _on_signal_processed(self, signal: QueuedSignal, result: Any):
        """Callback padrão para sinal processado"""
        self.logger.info(f"✅ Sinal {signal.signal_id} processado com sucesso")
    
    async def _on_signal_failed(self, signal: QueuedSignal, error: str):
        """Callback padrão para falha no sinal"""
        self.logger.warning(f"❌ Falha no sinal {signal.signal_id}: {error}")
        
        # Tentar retry se possível
        if signal.retry_count < signal.max_retries:
            self.queue.retry_signal(signal)
    
    async def _on_queue_full(self, queue_size: int):
        """Callback padrão para fila cheia"""
        self.logger.warning(f"⚠️ Fila cheia ({queue_size} sinais) - removendo sinais antigos")
        self.queue.remove_old_signals(max_age=60.0)  # Remove sinais com mais de 1 minuto
    
    async def start_processing(self, processor_func: Callable):
        """Inicia processamento automático da fila"""
        if self.running:
            self.logger.warning("Processamento já está ativo")
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._process_loop(processor_func))
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Sistema de processamento de sinais iniciado")
    
    async def stop_processing(self):
        """Para processamento automático da fila"""
        self.running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Sistema de processamento de sinais parado")
    
    async def _process_loop(self, processor_func: Callable):
        """Loop principal de processamento"""
        while self.running:
            try:
                signal = self.queue.get_next_signal()
                
                if signal:
                    await self.queue.process_signal_async(signal, processor_func)
                else:
                    # Aguardar um pouco se não há sinais
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de processamento: {e}")
                await asyncio.sleep(1.0)  # Aguardar antes de tentar novamente
    
    async def _cleanup_loop(self):
        """Loop de limpeza automática"""
        while self.running:
            try:
                # Limpeza a cada 5 minutos
                await asyncio.sleep(300)
                
                if self.running:
                    # Remover sinais antigos (mais de 10 minutos)
                    removed = self.queue.remove_old_signals(max_age=600.0)
                    
                    if removed > 0:
                        self.logger.info(f"Limpeza automática: {removed} sinais antigos removidos")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erro no loop de limpeza: {e}")
    
    def add_signal(self, ticks_data: List[float], pattern_detected: bool) -> bool:
        """Adiciona sinal à fila"""
        return self.queue.queue_signal(ticks_data, pattern_detected)
    
    def get_stats(self) -> dict:
        """Retorna estatísticas completas do sistema"""
        return {
            "queue_stats": self.queue.get_queue_stats(),
            "health_status": self.queue.get_health_status(),
            "running": self.running,
            "pending_signals": len(self.queue.get_pending_signals())
        }
    
    def is_healthy(self) -> bool:
        """Verifica se o sistema está saudável"""
        return self.queue.is_healthy() and self.running