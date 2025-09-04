#!/usr/bin/env python3
"""
Sistema de Sincronização Aprimorado para Bot Accumulator
Inclui queue thread-safe, processamento paralelo e monitoramento em tempo real
"""

import asyncio
import threading
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from queue import Queue, Empty
from collections import deque
from threading import Lock
from aiohttp import web
import aiohttp_cors

# Configuração de logging com timestamps precisos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler('enhanced_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SignalData:
    """Estrutura de dados para sinais detectados"""
    timestamp: float
    ticks: List[float]
    pattern_detected: bool
    signal_id: str
    processing_started: Optional[float] = None
    processing_completed: Optional[float] = None
    operation_result: Optional[str] = None

@dataclass
class SystemStats:
    """Estatísticas do sistema em tempo real"""
    active_operations: int = 0
    queue_size: int = 0
    total_signals_processed: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    last_signal_time: Optional[float] = None
    circuit_breaker_state: str = "CLOSED"
    average_processing_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

class ProposalCache:
    """Cache para propostas válidas com TTL de 5 segundos"""
    
    def __init__(self, ttl: float = 5.0):
        self.cache = {}
        self.ttl = ttl
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtém item do cache se ainda válido"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return data
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, value: Dict[str, Any]):
        """Armazena item no cache"""
        with self.lock:
            self.cache[key] = (value, time.time())
    
    def clear_expired(self):
        """Remove itens expirados do cache"""
        current_time = time.time()
        with self.lock:
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp >= self.ttl
            ]
            for key in expired_keys:
                del self.cache[key]

class EnhancedSyncSystem:
    """Sistema de sincronização aprimorado com queue thread-safe e processamento paralelo"""
    
    def __init__(self, max_concurrent_operations: int = 2, max_queue_size: int = 3):
        # Sistema de queue thread-safe
        self.signal_queue = Queue(maxsize=max_queue_size)
        self.max_queue_size = max_queue_size
        
        # Controle de concorrência
        self.max_concurrent_operations = max_concurrent_operations
        self.operation_semaphore = asyncio.Semaphore(max_concurrent_operations)
        self.active_operations = 0
        self.operations_lock = Lock()
        
        # Cache de propostas
        self.proposal_cache = ProposalCache()
        
        # Histórico de sinais (últimos 100)
        self.signal_history = deque(maxlen=100)
        self.history_lock = Lock()
        
        # Estatísticas
        self.stats = SystemStats()
        self.stats_lock = Lock()
        
        # Controle de threads
        self.running = False
        self.processor_thread = None
        self.monitor_thread = None
        self.stats_thread = None
        
        # Servidor HTTP para endpoint /status
        self.app = None
        self.runner = None
        self.site = None
        
        logger.info(f"🔧 Sistema de Sincronização Aprimorado inicializado")
        logger.info(f"⚙️ Configurações: max_operations={max_concurrent_operations}, max_queue={max_queue_size}")
    
    def _generate_signal_id(self) -> str:
        """Gera ID único para sinal"""
        timestamp = int(time.time() * 1000000)  # Microsegundos
        return f"signal_{timestamp}"
    
    def queue_signal(self, ticks: List[float], pattern_detected: bool) -> bool:
        """Adiciona sinal à queue thread-safe"""
        try:
            signal_id = self._generate_signal_id()
            signal_data = SignalData(
                timestamp=time.time(),
                ticks=ticks.copy(),
                pattern_detected=pattern_detected,
                signal_id=signal_id
            )
            
            # Tentar adicionar à queue (não bloqueante)
            self.signal_queue.put_nowait(signal_data)
            
            # Atualizar estatísticas
            with self.stats_lock:
                self.stats.queue_size = self.signal_queue.qsize()
                self.stats.last_signal_time = signal_data.timestamp
            
            logger.info(f"📥 SINAL ENFILEIRADO: {signal_id} | Queue: {self.signal_queue.qsize()}/{self.max_queue_size}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Queue cheia - descartando sinal mais antigo: {e}")
            try:
                # Remover sinal mais antigo e adicionar novo
                old_signal = self.signal_queue.get_nowait()
                logger.warning(f"🗑️ Sinal descartado: {old_signal.signal_id}")
                
                self.signal_queue.put_nowait(signal_data)
                logger.info(f"📥 SINAL ENFILEIRADO (substituição): {signal_id}")
                return True
            except Exception as e2:
                logger.error(f"❌ Erro ao gerenciar queue: {e2}")
                return False
    
    def _increment_active_operations(self):
        """Incrementa contador de operações ativas"""
        with self.operations_lock:
            self.active_operations += 1
            with self.stats_lock:
                self.stats.active_operations = self.active_operations
    
    def _decrement_active_operations(self):
        """Decrementa contador de operações ativas"""
        with self.operations_lock:
            self.active_operations = max(0, self.active_operations - 1)
            with self.stats_lock:
                self.stats.active_operations = self.active_operations
    
    async def _process_signal_queue(self):
        """Processa sinais da queue em loop contínuo"""
        logger.info("🔄 Iniciando processador de sinais")
        
        while self.running:
            try:
                # Tentar obter sinal da queue (timeout de 1s)
                try:
                    signal_data = self.signal_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Verificar se há slots disponíveis para processamento
                if self.operation_semaphore.acquire(blocking=False):
                    # Criar task para processar sinal
                    asyncio.create_task(self._process_single_signal(signal_data))
                else:
                    # Sem slots disponíveis - recolocar na queue
                    logger.warning(f"⏳ Sem slots disponíveis - reagendando sinal {signal_data.signal_id}")
                    self.signal_queue.put(signal_data)
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Erro no processador de sinais: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_single_signal(self, signal_data: SignalData):
        """Processa um único sinal"""
        start_time = time.time()
        signal_data.processing_started = start_time
        
        try:
            self._increment_active_operations()
            
            logger.info(f"🔄 PROCESSANDO SINAL: {signal_data.signal_id} | Operações ativas: {self.active_operations}")
            
            # Adicionar ao histórico
            with self.history_lock:
                self.signal_history.append(signal_data)
            
            # Simular processamento (substituir pela lógica real do bot)
            if signal_data.pattern_detected:
                # Verificar cache de propostas
                cache_key = f"proposal_{hash(tuple(signal_data.ticks))}"
                cached_proposal = self.proposal_cache.get(cache_key)
                
                if cached_proposal:
                    logger.info(f"💾 Cache HIT para proposta: {signal_data.signal_id}")
                    with self.stats_lock:
                        self.stats.cache_hits += 1
                else:
                    logger.info(f"🔍 Cache MISS - gerando nova proposta: {signal_data.signal_id}")
                    with self.stats_lock:
                        self.stats.cache_misses += 1
                    
                    # Simular geração de proposta
                    await asyncio.sleep(0.5)  # Simular latência
                    cached_proposal = {"proposal_id": f"prop_{signal_data.signal_id}", "ask_price": 1.0}
                    self.proposal_cache.set(cache_key, cached_proposal)
                
                # Simular execução de compra
                await asyncio.sleep(0.3)  # Simular latência de compra
                
                signal_data.operation_result = "SUCCESS"
                with self.stats_lock:
                    self.stats.successful_operations += 1
                
                logger.info(f"✅ OPERAÇÃO CONCLUÍDA: {signal_data.signal_id}")
            else:
                signal_data.operation_result = "NO_PATTERN"
                logger.debug(f"📊 Sinal sem padrão: {signal_data.signal_id}")
            
        except Exception as e:
            signal_data.operation_result = f"ERROR: {str(e)}"
            with self.stats_lock:
                self.stats.failed_operations += 1
            logger.error(f"❌ Erro ao processar sinal {signal_data.signal_id}: {e}")
        
        finally:
            # Finalizar processamento
            signal_data.processing_completed = time.time()
            processing_time = signal_data.processing_completed - start_time
            
            # Atualizar estatísticas
            with self.stats_lock:
                self.stats.total_signals_processed += 1
                # Calcular média móvel do tempo de processamento
                if self.stats.average_processing_time == 0:
                    self.stats.average_processing_time = processing_time
                else:
                    self.stats.average_processing_time = (
                        self.stats.average_processing_time * 0.9 + processing_time * 0.1
                    )
            
            self._decrement_active_operations()
            self.operation_semaphore.release()
            
            logger.info(f"⏱️ Sinal {signal_data.signal_id} processado em {processing_time:.3f}s")
    
    def _save_signal_history(self):
        """Salva histórico de sinais em arquivo JSON"""
        try:
            with self.history_lock:
                history_data = [
                    {
                        "signal_id": signal.signal_id,
                        "timestamp": signal.timestamp,
                        "pattern_detected": signal.pattern_detected,
                        "processing_time": (
                            signal.processing_completed - signal.processing_started
                            if signal.processing_started and signal.processing_completed
                            else None
                        ),
                        "operation_result": signal.operation_result,
                        "ticks_count": len(signal.ticks)
                    }
                    for signal in self.signal_history
                ]
            
            with open('signal_history.json', 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar histórico: {e}")
    
    async def _periodic_stats_logger(self):
        """Log estruturado de estatísticas a cada 30 segundos"""
        while self.running:
            try:
                await asyncio.sleep(30.0)
                
                with self.stats_lock:
                    stats_copy = SystemStats(**asdict(self.stats))
                
                logger.info("📊 ESTATÍSTICAS DO SISTEMA:")
                logger.info(f"   • Operações ativas: {stats_copy.active_operations}/{self.max_concurrent_operations}")
                logger.info(f"   • Queue: {stats_copy.queue_size}/{self.max_queue_size}")
                logger.info(f"   • Sinais processados: {stats_copy.total_signals_processed}")
                logger.info(f"   • Sucessos: {stats_copy.successful_operations}")
                logger.info(f"   • Falhas: {stats_copy.failed_operations}")
                logger.info(f"   • Tempo médio: {stats_copy.average_processing_time:.3f}s")
                logger.info(f"   • Cache: {stats_copy.cache_hits} hits, {stats_copy.cache_misses} misses")
                logger.info(f"   • Circuit Breaker: {stats_copy.circuit_breaker_state}")
                
                # Salvar histórico
                self._save_signal_history()
                
                # Limpar cache expirado
                self.proposal_cache.clear_expired()
                
            except Exception as e:
                logger.error(f"❌ Erro no log de estatísticas: {e}")
    
    async def _status_handler(self, request):
        """Handler para endpoint /status"""
        try:
            with self.stats_lock:
                stats_dict = asdict(self.stats)
            
            # Adicionar informações extras
            status_data = {
                **stats_dict,
                "timestamp": time.time(),
                "uptime_seconds": time.time() - getattr(self, 'start_time', time.time()),
                "max_concurrent_operations": self.max_concurrent_operations,
                "max_queue_size": self.max_queue_size,
                "cache_size": len(self.proposal_cache.cache)
            }
            
            return web.json_response(status_data)
            
        except Exception as e:
            logger.error(f"❌ Erro no endpoint /status: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def start(self, port: int = 8080):
        """Inicia o sistema de sincronização"""
        self.running = True
        self.start_time = time.time()
        
        # Configurar servidor HTTP
        self.app = web.Application()
        
        # Configurar CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Adicionar rotas
        status_resource = self.app.router.add_get('/status', self._status_handler)
        cors.add(status_resource)
        
        # Iniciar servidor
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', port)
        await self.site.start()
        
        logger.info(f"🌐 Servidor de status iniciado em http://localhost:{port}/status")
        
        # Iniciar processador de sinais
        asyncio.create_task(self._process_signal_queue())
        
        # Iniciar logger de estatísticas
        asyncio.create_task(self._periodic_stats_logger())
        
        logger.info("✅ Sistema de Sincronização Aprimorado iniciado")
    
    async def stop(self):
        """Para o sistema de sincronização"""
        logger.info("🛑 Parando Sistema de Sincronização Aprimorado...")
        
        self.running = False
        
        # Parar servidor HTTP
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        # Salvar histórico final
        self._save_signal_history()
        
        logger.info("✅ Sistema de Sincronização Aprimorado parado")
    
    def get_stats(self) -> SystemStats:
        """Retorna estatísticas atuais"""
        with self.stats_lock:
            return SystemStats(**asdict(self.stats))
    
    def update_circuit_breaker_state(self, state: str):
        """Atualiza estado do circuit breaker"""
        with self.stats_lock:
            self.stats.circuit_breaker_state = state
        logger.info(f"🔒 Circuit Breaker: {state}")
    
    def get_next_signal(self) -> Optional[SignalData]:
        """Obtém próximo sinal da queue (não bloqueante)"""
        try:
            return self.signal_queue.get_nowait()
        except Empty:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas como dicionário"""
        with self.stats_lock:
            return asdict(self.stats)
    
    def can_execute_operation(self) -> bool:
        """Verifica se há slots disponíveis para executar operação"""
        return self.operation_semaphore._value > 0
    
    def record_operation_failure(self, error_message: str = None):
        """Registra uma falha de operação nas estatísticas"""
        with self.stats_lock:
            self.stats.failed_operations += 1
        
        if error_message:
            logger.error(f"❌ Falha de operação registrada: {error_message}")
        else:
            logger.error("❌ Falha de operação registrada")
    
    def record_operation_success(self):
        """Registra uma operação bem-sucedida nas estatísticas"""
        with self.stats_lock:
            self.stats.successful_operations += 1
        logger.info("✅ Operação bem-sucedida registrada")
    
    async def clear_signal_queue(self):
        """Limpa completamente a queue de sinais"""
        try:
            # Limpar todos os sinais da queue
            cleared_count = 0
            while not self.signal_queue.empty():
                try:
                    self.signal_queue.get_nowait()
                    cleared_count += 1
                except:
                    break
            
            # Atualizar estatísticas
            with self.stats_lock:
                self.stats.queue_size = 0
            
            logger.info(f"🧹 Queue de sinais limpa: {cleared_count} sinais removidos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar queue de sinais: {e}")