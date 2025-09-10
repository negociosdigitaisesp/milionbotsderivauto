import asyncio
import time
import logging
from typing import Callable, Optional
from enum import Enum

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

class WebSocketRecoveryManager:
    """Gerenciador de reconexão WebSocket com backoff exponencial"""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 2.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_retries = 0
        self.state = ConnectionState.DISCONNECTED
        self.last_ping_time = 0
        self.ping_interval = 30.0  # 30 segundos
        self.ping_timeout = 10.0   # 10 segundos
        self.logger = logging.getLogger(__name__)
        
        # Callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_reconnect_failed: Optional[Callable] = None
    
    def set_callbacks(self, on_connected: Callable = None,
                     on_disconnected: Callable = None,
                     on_reconnect_failed: Callable = None):
        """Define callbacks para eventos de conexão"""
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        self.on_reconnect_failed = on_reconnect_failed
    
    async def attempt_connection(self, connect_func: Callable) -> bool:
        """Tenta estabelecer conexão com backoff exponencial"""
        self.state = ConnectionState.CONNECTING
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Tentativa de conexão {attempt + 1}/{self.max_retries}")
                
                # Tentar conectar
                success = await asyncio.wait_for(connect_func(), timeout=15.0)
                
                if success:
                    self.state = ConnectionState.CONNECTED
                    self.current_retries = 0
                    self.last_ping_time = time.time()
                    
                    if self.on_connected:
                        await self.on_connected()
                    
                    self.logger.info("Conexão estabelecida com sucesso")
                    return True
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout na tentativa {attempt + 1}")
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}: {e}")
            
            # Calcular delay com backoff exponencial
            if attempt < self.max_retries - 1:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                self.logger.info(f"Aguardando {delay:.1f}s antes da próxima tentativa")
                await asyncio.sleep(delay)
        
        # Todas as tentativas falharam
        self.state = ConnectionState.FAILED
        self.current_retries = self.max_retries
        
        if self.on_reconnect_failed:
            await self.on_reconnect_failed()
        
        self.logger.error("Falha em todas as tentativas de conexão")
        return False
    
    async def start_keepalive(self, ping_func: Callable, websocket_check: Callable):
        """Inicia loop de keepalive com ping/pong"""
        while self.state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(self.ping_interval)
                
                if self.state != ConnectionState.CONNECTED:
                    break
                
                # Verificar se WebSocket ainda está ativo
                if not await websocket_check():
                    self.logger.warning("WebSocket inativo detectado")
                    await self._handle_disconnection()
                    break
                
                # Enviar ping
                ping_start = time.time()
                pong_received = await asyncio.wait_for(ping_func(), timeout=self.ping_timeout)
                
                if pong_received:
                    latency = (time.time() - ping_start) * 1000
                    self.last_ping_time = time.time()
                    self.logger.debug(f"Ping OK - Latência: {latency:.2f}ms")
                else:
                    self.logger.warning("Pong não recebido")
                    await self._handle_disconnection()
                    break
                    
            except asyncio.TimeoutError:
                self.logger.warning("Timeout no ping - conexão pode estar morta")
                await self._handle_disconnection()
                break
            except Exception as e:
                self.logger.error(f"Erro no keepalive: {e}")
                await self._handle_disconnection()
                break
    
    async def _handle_disconnection(self):
        """Trata desconexão detectada"""
        if self.state == ConnectionState.CONNECTED:
            self.state = ConnectionState.DISCONNECTED
            
            if self.on_disconnected:
                await self.on_disconnected()
            
            self.logger.warning("Desconexão detectada")
    
    def get_connection_stats(self) -> dict:
        """Retorna estatísticas da conexão"""
        return {
            "state": self.state.value,
            "current_retries": self.current_retries,
            "max_retries": self.max_retries,
            "last_ping_age": time.time() - self.last_ping_time if self.last_ping_time > 0 else None,
            "ping_interval": self.ping_interval,
            "ping_timeout": self.ping_timeout
        }
    
    def reset_retries(self):
        """Reseta contador de tentativas"""
        self.current_retries = 0
        self.logger.info("Contador de tentativas resetado")
    
    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self.state == ConnectionState.CONNECTED
    
    def is_connecting(self) -> bool:
        """Verifica se está tentando conectar"""
        return self.state in [ConnectionState.CONNECTING, ConnectionState.RECONNECTING]
    
    def should_retry(self) -> bool:
        """Verifica se deve tentar reconectar"""
        return self.current_retries < self.max_retries and self.state != ConnectionState.FAILED
    
    async def force_reconnect(self, connect_func: Callable) -> bool:
        """Força uma nova tentativa de reconexão"""
        self.logger.info("Forçando reconexão...")
        self.state = ConnectionState.RECONNECTING
        self.current_retries = 0
        return await self.attempt_connection(connect_func)
    
    def update_ping_settings(self, interval: float = None, timeout: float = None):
        """Atualiza configurações de ping"""
        if interval is not None:
            self.ping_interval = interval
            self.logger.info(f"Intervalo de ping atualizado para {interval}s")
        
        if timeout is not None:
            self.ping_timeout = timeout
            self.logger.info(f"Timeout de ping atualizado para {timeout}s")
    
    def get_health_status(self) -> dict:
        """Retorna status de saúde da conexão"""
        current_time = time.time()
        last_ping_age = current_time - self.last_ping_time if self.last_ping_time > 0 else None
        
        # Determinar status de saúde
        if self.state == ConnectionState.CONNECTED:
            if last_ping_age is None:
                health = "unknown"
            elif last_ping_age < self.ping_interval * 1.5:
                health = "healthy"
            elif last_ping_age < self.ping_interval * 3:
                health = "warning"
            else:
                health = "critical"
        else:
            health = "disconnected"
        
        return {
            "health": health,
            "state": self.state.value,
            "last_ping_age": last_ping_age,
            "retry_count": self.current_retries,
            "can_retry": self.should_retry(),
            "uptime": current_time - self.last_ping_time if self.last_ping_time > 0 else 0
        }