import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import List, Optional
import logging

@dataclass
class SyncedTick:
    """Estrutura para tick com timestamp preciso"""
    value: float
    timestamp: float
    tick_id: str = None

class EnhancedTickBuffer:
    """Buffer thread-safe para ticks com sincronização temporal"""
    
    def __init__(self, max_size: int = 10, tolerance_seconds: float = 1.0):
        self.max_size = max_size
        self.tolerance_seconds = tolerance_seconds
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def add_tick(self, tick_value: float, custom_timestamp: float = None) -> bool:
        """Adiciona tick ao buffer com validação temporal"""
        try:
            with self.lock:
                timestamp = custom_timestamp if custom_timestamp else time.time()
                
                # Validar ordem cronológica
                if self.buffer and timestamp < self.buffer[-1].timestamp:
                    self.logger.warning(f"Tick fora de ordem temporal ignorado: {timestamp}")
                    return False
                
                # Criar tick sincronizado
                synced_tick = SyncedTick(
                    value=float(tick_value),
                    timestamp=timestamp,
                    tick_id=f"tick_{int(timestamp*1000000)}"
                )
                
                # Adicionar ao buffer
                self.buffer.append(synced_tick)
                
                # Limpeza automática de ticks obsoletos
                self._cleanup_old_ticks()
                
                return True
        
        except Exception as e:
            self.logger.error(f"Erro ao adicionar tick: {e}")
            return False
    
    def get_last_n_ticks(self, n: int = 5) -> List[float]:
        """Retorna os últimos N ticks como lista de valores"""
        try:
            with self.lock:
                if len(self.buffer) < n:
                    return []
                
                # Verificar sincronização temporal
                if not self._validate_sync_window():
                    self.logger.warning("Ticks fora da janela de sincronização")
                    return []
                
                # Retornar apenas os valores dos últimos N ticks
                return [tick.value for tick in list(self.buffer)[-n:]]
        
        except Exception as e:
            self.logger.error(f"Erro ao obter ticks: {e}")
            return []
    
    def _cleanup_old_ticks(self):
        """Remove ticks obsoletos (>5 segundos)"""
        current_time = time.time()
        while (self.buffer and
               current_time - self.buffer[0].timestamp > 5.0):
            removed_tick = self.buffer.popleft()
            self.logger.debug(f"Tick obsoleto removido: {removed_tick.timestamp}")
    
    def _validate_sync_window(self) -> bool:
        """Valida se todos os ticks estão dentro da janela de sincronização"""
        if len(self.buffer) < 2:
            return True
        
        timestamps = [tick.timestamp for tick in self.buffer]
        max_diff = max(timestamps) - min(timestamps)
        
        return max_diff <= self.tolerance_seconds
    
    def get_buffer_stats(self) -> dict:
        """Retorna estatísticas do buffer"""
        with self.lock:
            if not self.buffer:
                return {"size": 0, "time_span": 0, "synced": True}
            
            timestamps = [tick.timestamp for tick in self.buffer]
            return {
                "size": len(self.buffer),
                "time_span": max(timestamps) - min(timestamps),
                "synced": self._validate_sync_window(),
                "oldest_tick_age": time.time() - min(timestamps),
                "newest_tick_age": time.time() - max(timestamps)
            }