"""
Sistema de Retry para operações Supabase
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuração do sistema de retry"""
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0
    DEFAULT_MAX_DELAY = 10.0
    DEFAULT_BACKOFF_MULTIPLIER = 2.0

class RetryError(Exception):
    """Erro após esgotar todas as tentativas"""
    
    def __init__(self, message: str, last_exception: Exception, attempts: int):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts

def retry_operation(
    max_retries: int = RetryConfig.DEFAULT_MAX_RETRIES,
    base_delay: float = RetryConfig.DEFAULT_BASE_DELAY,
    max_delay: float = RetryConfig.DEFAULT_MAX_DELAY,
    backoff_multiplier: float = RetryConfig.DEFAULT_BACKOFF_MULTIPLIER,
    retry_on_exceptions: tuple = (Exception,)
):
    """
    Decorator para retry automático com backoff exponencial
    
    Args:
        max_retries: Número máximo de tentativas
        base_delay: Delay inicial em segundos
        max_delay: Delay máximo em segundos
        backoff_multiplier: Multiplicador para backoff exponencial
        retry_on_exceptions: Tupla de exceções que devem causar retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 para incluir tentativa inicial
                try:
                    logger.debug(f"[RETRY] {func.__name__} - Tentativa {attempt + 1}/{max_retries + 1}")
                    
                    result = func(*args, **kwargs)
                    
                    # Sucesso na primeira tentativa
                    if attempt == 0:
                        logger.debug(f"[RETRY] {func.__name__} - Sucesso na primeira tentativa")
                    else:
                        logger.info(f"[RETRY] {func.__name__} - Sucesso após {attempt + 1} tentativas")
                    
                    return result
                    
                except retry_on_exceptions as e:
                    last_exception = e
                    
                    # Se é a última tentativa, não fazer retry
                    if attempt == max_retries:
                        break
                    
                    # Calcular delay com backoff exponencial
                    delay = min(base_delay * (backoff_multiplier ** attempt), max_delay)
                    
                    logger.warning(
                        f"[RETRY] {func.__name__} - Tentativa {attempt + 1} falhou: {e}. "
                        f"Tentando novamente em {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
                
                except Exception as e:
                    # Exceções não listadas em retry_on_exceptions não fazem retry
                    logger.error(f"[RETRY] {func.__name__} - Erro não recuperável: {e}")
                    raise e
            
            # Se chegou aqui, todas as tentativas falharam
            error_message = f"Falha após {max_retries + 1} tentativas em {func.__name__}"
            logger.error(f"[RETRY] {error_message}. Última exceção: {last_exception}")
            
            raise RetryError(error_message, last_exception, max_retries + 1)
        
        return wrapper
    return decorator

class SupabaseRetryMixin:
    """Mixin com métodos específicos para retry de operações Supabase"""
    
    @staticmethod
    @retry_operation(
        max_retries=3,
        base_delay=1.0,
        retry_on_exceptions=(ConnectionError, TimeoutError, OSError)
    )
    def safe_insert(supabase_client, table_name: str, data: dict):
        """Inserção segura com retry"""
        response = supabase_client.table(table_name).insert(data).execute()
        
        if not response.data:
            raise ValueError(f"Inserção retornou dados vazios para tabela {table_name}")
        
        return response
    
    @staticmethod
    @retry_operation(
        max_retries=3,
        base_delay=1.0,
        retry_on_exceptions=(ConnectionError, TimeoutError, OSError)
    )
    def safe_update(supabase_client, table_name: str, data: dict, filter_col: str, filter_val: Any):
        """Atualização segura com retry"""
        response = supabase_client.table(table_name).update(data).eq(filter_col, filter_val).execute()
        
        if not response.data:
            raise ValueError(f"Atualização retornou dados vazios para {filter_col}={filter_val}")
        
        return response
    
    @staticmethod
    @retry_operation(
        max_retries=2,
        base_delay=0.5,
        retry_on_exceptions=(ConnectionError, TimeoutError, OSError)
    )
    def safe_select(supabase_client, table_name: str, select_fields: str = "*", filters: Optional[dict] = None):
        """Seleção segura com retry"""
        query = supabase_client.table(table_name).select(select_fields)
        
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        
        response = query.execute()
        return response

def test_retry_system():
    """Teste do sistema de retry"""
    print("=== TESTE DO SISTEMA DE RETRY ===")
    
    # Teste 1: Função que falha nas primeiras tentativas
    call_count = 0
    
    @retry_operation(max_retries=3, base_delay=0.1)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Falha simulada {call_count}")
        return f"Sucesso na tentativa {call_count}"
    
    try:
        result = flaky_function()
        print(f"✅ Teste 1 passou: {result}")
    except RetryError as e:
        print(f"❌ Teste 1 falhou: {e}")
    
    # Teste 2: Função que sempre falha
    @retry_operation(max_retries=2, base_delay=0.1)
    def always_fails():
        raise ValueError("Sempre falha")
    
    try:
        always_fails()
        print("❌ Teste 2 deveria ter falhado")
    except RetryError as e:
        print(f"✅ Teste 2 passou: Falhou como esperado após {e.attempts} tentativas")
    
    # Teste 3: Função que falha com exceção não recuperável
    @retry_operation(max_retries=3, base_delay=0.1, retry_on_exceptions=(ConnectionError,))
    def non_recoverable_error():
        raise ValueError("Erro não recuperável")
    
    try:
        non_recoverable_error()
        print("❌ Teste 3 deveria ter falhado")
    except ValueError as e:
        print(f"✅ Teste 3 passou: Erro não recuperável capturado: {e}")
    
    # Teste 4: Função que funciona na primeira tentativa
    @retry_operation(max_retries=3, base_delay=0.1)
    def works_immediately():
        return "Sucesso imediato"
    
    try:
        result = works_immediately()
        print(f"✅ Teste 4 passou: {result}")
    except Exception as e:
        print(f"❌ Teste 4 falhou: {e}")
    
    print("\n=== TESTE DE BACKOFF EXPONENCIAL ===")
    
    # Teste 5: Verificar backoff exponencial
    attempt_times = []
    
    @retry_operation(max_retries=3, base_delay=0.5, backoff_multiplier=2.0)
    def test_backoff():
        attempt_times.append(time.time())
        if len(attempt_times) < 4:
            raise ConnectionError(f"Tentativa {len(attempt_times)}")
        return "Sucesso após backoff"
    
    start_time = time.time()
    try:
        result = test_backoff()
        print(f"✅ Teste 5 passou: {result}")
        
        # Verificar intervalos
        if len(attempt_times) >= 2:
            for i in range(1, len(attempt_times)):
                interval = attempt_times[i] - attempt_times[i-1]
                expected_min = 0.5 * (2.0 ** (i-1)) * 0.8  # 20% de tolerância
                print(f"   Intervalo {i}: {interval:.2f}s (esperado: ~{0.5 * (2.0 ** (i-1)):.2f}s)")
    except RetryError as e:
        print(f"❌ Teste 5 falhou: {e}")
    
    print("\n=== TESTES CONCLUÍDOS ===")

if __name__ == "__main__":
    # Configurar logging para os testes
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_retry_system()