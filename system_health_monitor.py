import asyncio
import time
import logging
import os
import psutil
from datetime import datetime
from typing import Dict, Callable, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
import threading
import json

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERING = "recovering"

@dataclass
class HealthMetrics:
    """Métricas de saúde do sistema"""
    queue_size: int
    active_operations: int
    circuit_breaker_state: str
    last_signal_time: float
    successful_operations: int
    failed_operations: int
    connection_status: bool
    last_ping_time: float
    memory_usage_mb: float
    uptime_seconds: float

class SystemHealthMonitor:
    """Monitor de saúde do sistema com recovery automático"""
    
    def __init__(self, 
                 deadlock_threshold: float = 120.0,
                 inactivity_threshold: float = 180.0,
                 high_failure_rate: float = 0.7,
                 min_operations_for_rate_check: int = 10):
        
        self.deadlock_threshold = deadlock_threshold
        self.inactivity_threshold = inactivity_threshold
        self.high_failure_rate = high_failure_rate
        self.min_operations_for_rate_check = min_operations_for_rate_check
        
        self.start_time = time.time()
        self.last_health_check = 0
        self.health_status = HealthStatus.HEALTHY
        self.problem_start_time = None
        self.restart_in_progress = False
        
        self.logger = logging.getLogger(__name__)
        
        # Callbacks para recovery
        self.on_deadlock_detected: Optional[Callable] = None
        self.on_connection_issues: Optional[Callable] = None
        self.on_high_failure_rate: Optional[Callable] = None
        self.on_inactivity_detected: Optional[Callable] = None
        self.on_system_restart: Optional[Callable] = None
        
        # Histórico de problemas
        self.problem_history = []
        self.max_history_size = 100
        
        # Lock para thread safety
        self.lock = threading.Lock()
        
        # Estatísticas de recovery
        self.recovery_attempts = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
    
    def set_recovery_callbacks(self,
                              on_deadlock_detected: Callable = None,
                              on_connection_issues: Callable = None,
                              on_high_failure_rate: Callable = None,
                              on_inactivity_detected: Callable = None,
                              on_system_restart: Callable = None):
        """Define callbacks para diferentes tipos de problemas"""
        self.on_deadlock_detected = on_deadlock_detected
        self.on_connection_issues = on_connection_issues
        self.on_high_failure_rate = on_high_failure_rate
        self.on_inactivity_detected = on_inactivity_detected
        self.on_system_restart = on_system_restart
    
    async def collect_metrics(self, stats_provider: Callable) -> HealthMetrics:
        """Coleta métricas do sistema"""
        try:
            stats = await stats_provider()
            
            # Calcular uso de memória (aproximado)
            memory_usage = self._get_memory_usage()
            uptime = time.time() - self.start_time
            
            return HealthMetrics(
                queue_size=stats.get('queue_size', 0),
                active_operations=stats.get('active_operations', 0),
                circuit_breaker_state=stats.get('circuit_breaker_state', 'unknown'),
                last_signal_time=stats.get('last_signal_time', 0),
                successful_operations=stats.get('successful_operations', 0),
                failed_operations=stats.get('failed_operations', 0),
                connection_status=stats.get('connection_status', False),
                last_ping_time=stats.get('last_ping_time', 0),
                memory_usage_mb=memory_usage,
                uptime_seconds=uptime
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas: {e}")
            return None
    
    def analyze_health(self, metrics: HealthMetrics) -> HealthStatus:
        """Analisa métricas e determina status de saúde"""
        if not metrics:
            return HealthStatus.CRITICAL
        
        current_time = time.time()
        issues = []
        
        # 1. Verificar deadlock (queue cheia + sem operações ativas)
        is_deadlocked = (metrics.queue_size >= 3 and metrics.active_operations == 0)
        if is_deadlocked:
            issues.append("DEADLOCK")
        
        # 2. Verificar problemas de conexão
        connection_issues = (
            not metrics.connection_status or
            metrics.circuit_breaker_state == 'open' or
            (metrics.last_ping_time is not None and metrics.last_ping_time > 0 and 
             current_time - metrics.last_ping_time > 60)
        )
        if connection_issues:
            issues.append("CONNECTION")
        
        # 3. Verificar alta taxa de falhas
        total_ops = metrics.successful_operations + metrics.failed_operations
        if total_ops >= self.min_operations_for_rate_check:
            failure_rate = metrics.failed_operations / total_ops
            if failure_rate > self.high_failure_rate:
                issues.append("HIGH_FAILURE_RATE")
        
        # 4. Verificar inatividade
        if (metrics.last_signal_time is not None and metrics.last_signal_time > 0 and
            current_time - metrics.last_signal_time > self.inactivity_threshold):
            issues.append("INACTIVITY")
        
        # 5. Verificar uso excessivo de memória
        if metrics.memory_usage_mb > 500:  # 500MB limit
            issues.append("HIGH_MEMORY")
        
        # Determinar status com base nos problemas
        if not issues:
            return HealthStatus.HEALTHY
        elif len(issues) == 1 and "HIGH_MEMORY" in issues:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    async def monitor_and_recover(self, stats_provider: Callable, check_interval: float = 30.0):
        """Loop principal de monitoramento com recovery automático"""
        self.logger.info("🔍 Sistema de monitoramento de saúde iniciado")
        
        while True:
            try:
                # Coletar métricas
                metrics = await self.collect_metrics(stats_provider)
                
                if metrics:
                    # Analisar saúde
                    new_status = self.analyze_health(metrics)
                    
                    # Verificar mudança de status
                    if new_status != self.health_status:
                        await self._handle_status_change(self.health_status, new_status, metrics)
                        self.health_status = new_status
                    
                    # Executar recovery se necessário
                    if new_status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                        await self._execute_recovery(metrics)
                    
                    # Log de status periodicamente
                    if time.time() - self.last_health_check > 300:  # A cada 5 minutos
                        self._log_health_status(metrics)
                        self.last_health_check = time.time()
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
                await asyncio.sleep(check_interval)
    
    async def _handle_status_change(self, old_status: HealthStatus, new_status: HealthStatus, metrics: HealthMetrics):
        """Trata mudanças de status de saúde"""
        self.logger.info(f"🔄 Status de saúde alterado: {old_status.value} → {new_status.value}")
        
        # Registrar no histórico
        with self.lock:
            self.problem_history.append({
                "timestamp": time.time(),
                "old_status": old_status.value,
                "new_status": new_status.value,
                "metrics": metrics.__dict__.copy()
            })
            
            # Limitar tamanho do histórico
            if len(self.problem_history) > self.max_history_size:
                self.problem_history.pop(0)
        
        # Marcar início do problema
        if new_status in [HealthStatus.CRITICAL, HealthStatus.WARNING] and old_status == HealthStatus.HEALTHY:
            self.problem_start_time = time.time()
        elif new_status == HealthStatus.HEALTHY:
            self.problem_start_time = None
    
    async def _execute_recovery(self, metrics: HealthMetrics):
        """Executa procedimentos de recovery baseados nas métricas"""
        if self.restart_in_progress:
            return
        
        current_time = time.time()
        issues = self._identify_issues(metrics)
        
        self.logger.warning(f"⚠️ Problemas detectados: {issues}")
        
        # Incrementar tentativas de recovery
        self.recovery_attempts += 1
        
        try:
            # Recovery específico por tipo de problema
            recovery_success = False
            
            if "DEADLOCK" in issues:
                recovery_success = await self._recover_from_deadlock()
            
            elif "CONNECTION" in issues:
                recovery_success = await self._recover_from_connection_issues()
            
            elif "HIGH_FAILURE_RATE" in issues:
                recovery_success = await self._recover_from_high_failure_rate()
            
            elif "INACTIVITY" in issues:
                recovery_success = await self._recover_from_inactivity()
            
            # Se recovery específico falhou, tentar restart geral
            if not recovery_success and self._should_restart(current_time):
                recovery_success = await self._perform_system_restart()
            
            # Atualizar estatísticas
            if recovery_success:
                self.successful_recoveries += 1
                self.health_status = HealthStatus.RECOVERING
                self.logger.info("✅ Recovery executado com sucesso")
            else:
                self.failed_recoveries += 1
                self.logger.error("❌ Recovery falhou")
                
        except Exception as e:
            self.failed_recoveries += 1
            self.logger.error(f"❌ Erro durante recovery: {e}")
    
    def _identify_issues(self, metrics: HealthMetrics) -> List[str]:
        """Identifica problemas específicos nas métricas"""
        current_time = time.time()
        issues = []
        
        # Deadlock
        if metrics.queue_size >= 3 and metrics.active_operations == 0:
            issues.append("DEADLOCK")
        
        # Problemas de conexão
        if (not metrics.connection_status or
            metrics.circuit_breaker_state == 'open' or
            (metrics.last_ping_time is not None and metrics.last_ping_time > 0 and 
             current_time - metrics.last_ping_time > 60)):
            issues.append("CONNECTION")
        
        # Alta taxa de falhas
        total_ops = metrics.successful_operations + metrics.failed_operations
        if total_ops >= self.min_operations_for_rate_check:
            failure_rate = metrics.failed_operations / total_ops
            if failure_rate > self.high_failure_rate:
                issues.append("HIGH_FAILURE_RATE")
        
        # Inatividade
        if (metrics.last_signal_time is not None and metrics.last_signal_time > 0 and
            current_time - metrics.last_signal_time > self.inactivity_threshold):
            issues.append("INACTIVITY")
        
        # Uso excessivo de memória
        if metrics.memory_usage_mb is not None and metrics.memory_usage_mb > 500:
            issues.append("HIGH_MEMORY")
        
        return issues
    
    async def _recover_from_deadlock(self) -> bool:
        """Recovery específico para deadlock"""
        self.logger.info("🔧 Executando recovery de deadlock...")
        
        try:
            if self.on_deadlock_detected:
                await self.on_deadlock_detected()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro no recovery de deadlock: {e}")
            return False
    
    async def _recover_from_connection_issues(self) -> bool:
        """Recovery específico para problemas de conexão"""
        self.logger.info("🔧 Executando recovery de conexão...")
        
        try:
            if self.on_connection_issues:
                await self.on_connection_issues()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro no recovery de conexão: {e}")
            return False
    
    async def _recover_from_high_failure_rate(self) -> bool:
        """Recovery específico para alta taxa de falhas"""
        self.logger.info("🔧 Executando recovery de alta taxa de falhas...")
        
        try:
            if self.on_high_failure_rate:
                await self.on_high_failure_rate()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro no recovery de alta taxa de falhas: {e}")
            return False
    
    async def _recover_from_inactivity(self) -> bool:
        """Recovery específico para inatividade"""
        self.logger.info("🔧 Executando recovery de inatividade...")
        
        try:
            if self.on_inactivity_detected:
                await self.on_inactivity_detected()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro no recovery de inatividade: {e}")
            return False
    
    def _should_restart(self, current_time: float) -> bool:
        """Determina se deve fazer restart do sistema"""
        if self.problem_start_time is None:
            return False
        
        # Restart se problema persistir por mais de deadlock_threshold
        problem_duration = current_time - self.problem_start_time
        return problem_duration > self.deadlock_threshold
    
    async def _perform_system_restart(self) -> bool:
        """Executa restart completo do sistema"""
        if self.restart_in_progress:
            return False
        
        self.restart_in_progress = True
        self.logger.warning("🔄 Iniciando restart completo do sistema...")
        
        try:
            if self.on_system_restart:
                await self.on_system_restart()
                self.logger.info("✅ Restart do sistema executado")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro no restart do sistema: {e}")
            return False
        finally:
            self.restart_in_progress = False
    
    def _get_memory_usage(self) -> float:
        """Obtém uso de memória em MB"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Converter para MB
        except Exception:
            return 0.0
    
    def _log_health_status(self, metrics: HealthMetrics):
        """Log periódico do status de saúde"""
        self.logger.info(f"📊 Status de Saúde: {self.health_status.value}")
        self.logger.info(f"   • Queue: {metrics.queue_size} sinais")
        self.logger.info(f"   • Operações ativas: {metrics.active_operations}")
        self.logger.info(f"   • Circuit breaker: {metrics.circuit_breaker_state}")
        self.logger.info(f"   • Conexão: {'✅' if metrics.connection_status else '❌'}")
        self.logger.info(f"   • Memória: {metrics.memory_usage_mb:.1f} MB")
        self.logger.info(f"   • Uptime: {metrics.uptime_seconds/3600:.1f} horas")
        
        # Taxa de sucesso
        total_ops = metrics.successful_operations + metrics.failed_operations
        if total_ops > 0:
            success_rate = metrics.successful_operations / total_ops * 100
            self.logger.info(f"   • Taxa de sucesso: {success_rate:.1f}%")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Retorna relatório completo de saúde"""
        with self.lock:
            return {
                "current_status": self.health_status.value,
                "uptime_seconds": time.time() - self.start_time,
                "problem_start_time": self.problem_start_time,
                "restart_in_progress": self.restart_in_progress,
                "recovery_stats": {
                    "attempts": self.recovery_attempts,
                    "successful": self.successful_recoveries,
                    "failed": self.failed_recoveries,
                    "success_rate": self.successful_recoveries / max(1, self.recovery_attempts)
                },
                "recent_problems": self.problem_history[-10:] if self.problem_history else [],
                "thresholds": {
                    "deadlock_threshold": self.deadlock_threshold,
                    "inactivity_threshold": self.inactivity_threshold,
                    "high_failure_rate": self.high_failure_rate,
                    "min_operations_for_rate_check": self.min_operations_for_rate_check
                }
            }
    
    def reset_stats(self):
        """Reseta estatísticas de recovery"""
        with self.lock:
            self.recovery_attempts = 0
            self.successful_recoveries = 0
            self.failed_recoveries = 0
            self.problem_history.clear()
            self.problem_start_time = None
            self.health_status = HealthStatus.HEALTHY
        
        self.logger.info("📊 Estatísticas de saúde resetadas")
    
    def export_health_log(self, filename: str = None) -> str:
        """Exporta log de saúde para arquivo JSON"""
        if not filename:
            filename = f"health_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_health_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"📄 Log de saúde exportado: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Erro ao exportar log de saúde: {e}")
            return None
    
    def is_healthy(self) -> bool:
        """Verifica se o sistema está saudável"""
        return self.health_status == HealthStatus.HEALTHY
    
    def get_current_status(self) -> str:
        """Retorna status atual como string"""
        return self.health_status.value
    
    def force_health_check(self, stats_provider: Callable) -> HealthStatus:
        """Força verificação imediata de saúde (síncrona)"""
        try:
            # Para uso síncrono, criar um loop temporário se necessário
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            metrics = loop.run_until_complete(self.collect_metrics(stats_provider))
            
            if metrics:
                new_status = self.analyze_health(metrics)
                if new_status != self.health_status:
                    self.health_status = new_status
                    self.logger.info(f"🔍 Verificação forçada - Status: {new_status.value}")
                return new_status
            
            return HealthStatus.CRITICAL
            
        except Exception as e:
            self.logger.error(f"Erro na verificação forçada de saúde: {e}")
            return HealthStatus.CRITICAL

class HealthMonitorManager:
    """Gerenciador principal do sistema de monitoramento de saúde"""
    
    def __init__(self, monitor_config: Dict[str, Any] = None):
        config = monitor_config or {}
        
        self.monitor = SystemHealthMonitor(
            deadlock_threshold=config.get('deadlock_threshold', 120.0),
            inactivity_threshold=config.get('inactivity_threshold', 180.0),
            high_failure_rate=config.get('high_failure_rate', 0.7),
            min_operations_for_rate_check=config.get('min_operations_for_rate_check', 10)
        )
        
        self.running = False
        self.monitor_task = None
        self.stats_provider = None
        self.logger = logging.getLogger(__name__)
    
    def set_stats_provider(self, provider: Callable):
        """Define o provedor de estatísticas"""
        self.stats_provider = provider
    
    def set_recovery_handlers(self, handlers: Dict[str, Callable]):
        """Define handlers de recovery"""
        self.monitor.set_recovery_callbacks(
            on_deadlock_detected=handlers.get('deadlock'),
            on_connection_issues=handlers.get('connection'),
            on_high_failure_rate=handlers.get('failure_rate'),
            on_inactivity_detected=handlers.get('inactivity'),
            on_system_restart=handlers.get('restart')
        )
    
    async def start_monitoring(self, check_interval: float = 30.0):
        """Inicia monitoramento automático"""
        if self.running:
            self.logger.warning("Monitoramento já está ativo")
            return
        
        if not self.stats_provider:
            raise ValueError("Stats provider deve ser definido antes de iniciar monitoramento")
        
        self.running = True
        self.monitor_task = asyncio.create_task(
            self.monitor.monitor_and_recover(self.stats_provider, check_interval)
        )
        
        self.logger.info("🔍 Gerenciador de monitoramento de saúde iniciado")
    
    async def stop_monitoring(self):
        """Para monitoramento automático"""
        self.running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("🔍 Gerenciador de monitoramento de saúde parado")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde atual"""
        return {
            "monitor_running": self.running,
            "health_report": self.monitor.get_health_report()
        }
    
    def is_system_healthy(self) -> bool:
        """Verifica se o sistema está saudável"""
        return self.monitor.is_healthy()
    
    def export_health_report(self, filename: str = None) -> str:
        """Exporta relatório de saúde"""
        return self.monitor.export_health_log(filename)
    
    def reset_monitoring_stats(self):
        """Reseta estatísticas de monitoramento"""
        self.monitor.reset_stats()
        self.logger.info("📊 Estatísticas de monitoramento resetadas")