"""
Logger Principal de Estratégias - Core do sistema de logging
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from bot_name_validator import BotNameValidator
from strategy_execution import StrategyExecution
from retry_system import SupabaseRetryMixin, RetryError

logger = logging.getLogger(__name__)

class StrategyLogger(SupabaseRetryMixin):
    """Logger principal para estratégias de trading"""
    
    def __init__(self, supabase_client, bot_name: str):
        """
        Inicializa o logger com validação rigorosa
        
        Args:
            supabase_client: Cliente Supabase inicializado
            bot_name: Nome único do bot (obrigatório)
        """
        # Validação crítica do bot_name
        is_valid, error_msg = BotNameValidator.validate(bot_name)
        if not is_valid:
            raise ValueError(f"Bot name inválido: {error_msg}")
        
        self.supabase = supabase_client
        self.bot_name = bot_name.strip()
        self.table_name = "strategy_execution_logs"
        self.current_execution: Optional[StrategyExecution] = None
        
        logger.info(f"[STRATEGY_LOGGER] Inicializado para bot: '{self.bot_name}'")
        
        # Teste de conectividade crítico
        self._test_connectivity()
        
        # Limpeza de execuções órfãs
        self._cleanup_orphaned_executions()
    
    def _test_connectivity(self):
        """Testa conectividade com a tabela"""
        try:
            response = self.safe_select(
                self.supabase,
                self.table_name,
                "id",
                {"bot_name": self.bot_name}
            )
            logger.info(f"[CONNECTIVITY] Teste OK - Tabela '{self.table_name}' acessível")
            
        except Exception as e:
            error_msg = f"Falha na conectividade com tabela '{self.table_name}': {e}"
            logger.error(f"[CONNECTIVITY] {error_msg}")
            raise RuntimeError(error_msg)
    
    def _cleanup_orphaned_executions(self):
        """Limpa execuções órfãs (WAITING/MONITORING há mais de 1 hora)"""
        try:
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            # Buscar execuções órfãs
            response = self.safe_select(
                self.supabase,
                self.table_name,
                "id, status, created_at",
                {"bot_name": self.bot_name}
            )
            
            orphaned_count = 0
            if response.data:
                for record in response.data:
                    if record['status'] in ['WAITING', 'MONITORING']:
                        # Converter string para datetime com timezone
                        created_at_str = record.get('created_at', '')
                        if created_at_str:
                            # Parse datetime com timezone awareness
                            if '+' in created_at_str or 'Z' in created_at_str:
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            else:
                                created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)
                            
                            if created_at < cutoff_time:
                                # Marcar como timeout
                                self.safe_update(
                                    self.supabase,
                                    self.table_name,
                                    {
                                        'status': 'TIMEOUT',
                                        'completed_at': datetime.now(timezone.utc).isoformat(),
                                        'updated_at': datetime.now(timezone.utc).isoformat()
                                    },
                                    'id',
                                    record['id']
                                )
                                orphaned_count += 1
            
            if orphaned_count > 0:
                logger.warning(f"[CLEANUP] {orphaned_count} execuções órfãs limpas")
            else:
                logger.debug(f"[CLEANUP] Nenhuma execução órfã encontrada")
                
        except Exception as e:
            # Não interromper o sistema por erro de limpeza
            logger.warning(f"[CLEANUP] Erro na limpeza (não crítico): {e}")
    
    def start_pattern_tracking(self, strategy_name: str, confidence: float, trigger_type: str) -> bool:
        """
        Inicia rastreamento de novo padrão
        
        Args:
            strategy_name: Nome da estratégia (ex: "Quantum+")
            confidence: Nível de confiança (0-100)
            trigger_type: Tipo de gatilho (ex: "LLLW", "LLL")
            
        Returns:
            bool: True se iniciado com sucesso
        """
        try:
            logger.info(f"[START_TRACKING] Iniciando: {strategy_name} ({confidence}%) - {trigger_type}")
            
            # Finalizar execução anterior se existir
            if self.current_execution:
                logger.warning(f"[START_TRACKING] Execução anterior em andamento, finalizando...")
                self._force_complete_current_execution()
            
            # Criar nova execução
            execution = StrategyExecution(
                bot_name=self.bot_name,
                strategy_name=strategy_name,
                confidence_level=confidence,
                trigger_type=trigger_type,
                status="WAITING"
            )
            
            # Validar antes de inserir
            is_valid, error_msg = execution.validate()
            if not is_valid:
                logger.error(f"[START_TRACKING] Dados inválidos: {error_msg}")
                return False
            
            # Inserir no banco
            insert_data = execution.to_dict()
            response = self.safe_insert(self.supabase, self.table_name, insert_data)
            
            if response.data and len(response.data) > 0:
                execution.id = response.data[0]['id']
                self.current_execution = execution
                
                logger.info(f"[START_TRACKING] Sucesso - ID: {execution.id}")
                return True
            else:
                logger.error(f"[START_TRACKING] Resposta vazia do banco")
                return False
                
        except Exception as e:
            logger.error(f"[START_TRACKING] Erro: {e}")
            return False
    
    def update_monitoring_status(self, operations_count: int = 0) -> bool:
        """
        Atualiza status para MONITORING
        
        Args:
            operations_count: Número de operações monitoradas
            
        Returns:
            bool: True se atualizado com sucesso
        """
        if not self.current_execution:
            logger.error(f"[UPDATE_MONITORING] Nenhuma execução ativa")
            return False
        
        try:
            self.current_execution.status = "MONITORING"
            self.current_execution.operations_count = operations_count
            self.current_execution.updated_at = datetime.now()
            
            update_data = {
                'status': 'MONITORING',
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.safe_update(
                self.supabase,
                self.table_name,
                update_data,
                'id',
                self.current_execution.id
            )
            
            if response.data:
                logger.info(f"[UPDATE_MONITORING] Status atualizado - Ops: {operations_count}")
                return True
            else:
                logger.error(f"[UPDATE_MONITORING] Falha na atualização")
                return False
                
        except Exception as e:
            logger.error(f"[UPDATE_MONITORING] Erro: {e}")
            return False
    
    def complete_execution(self, final_result: str, operations_count: int = 0) -> bool:
        """
        Completa execução atual
        
        Args:
            final_result: Resultado final (WIN/LOSS/TIMEOUT)
            operations_count: Número total de operações
            
        Returns:
            bool: True se completado com sucesso
        """
        if not self.current_execution:
            logger.error(f"[COMPLETE_EXECUTION] Nenhuma execução ativa")
            return False
        
        try:
            # Calcular resultado final
            self.current_execution.final_result = final_result
            self.current_execution.operations_count = operations_count
            final_result_calculated = self.current_execution.calculate_final_result()
            
            # Marcar como completada
            self.current_execution.mark_completed()
            
            update_data = {
                'status': 'COMPLETED',
                'final_result': final_result_calculated,
                'completed_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.safe_update(
                self.supabase,
                self.table_name,
                update_data,
                'id',
                self.current_execution.id
            )
            
            if response.data:
                logger.info(f"[COMPLETE_EXECUTION] Execução {self.current_execution.id} completada - Resultado: {final_result_calculated}")
                self.current_execution = None
                return True
            else:
                logger.error(f"[COMPLETE_EXECUTION] Falha na finalização")
                return False
                
        except Exception as e:
            logger.error(f"[COMPLETE_EXECUTION] Erro: {e}")
            return False
    
    def _force_complete_current_execution(self):
        """Força finalização da execução atual como TIMEOUT"""
        if self.current_execution:
            logger.warning(f"[FORCE_COMPLETE] Forçando finalização da execução {self.current_execution.id}")
            self.complete_execution("TIMEOUT", self.current_execution.operations_count)
    
    def get_current_execution_info(self) -> Optional[Dict[str, Any]]:
        """Retorna informações da execução atual"""
        if not self.current_execution:
            return None
        
        return {
            'id': self.current_execution.id,
            'strategy_name': self.current_execution.strategy_name,
            'confidence_level': self.current_execution.confidence_level,
            'trigger_type': self.current_execution.trigger_type,
            'status': self.current_execution.status,
            'operations_count': self.current_execution.operations_count,
            'created_at': self.current_execution.created_at.isoformat() if self.current_execution.created_at else None,
            'updated_at': self.current_execution.updated_at.isoformat() if self.current_execution.updated_at else None
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna histórico de execuções"""
        try:
            # Usar query direta do Supabase para order e limit
            response = self.supabase.table(self.table_name) \
                .select("*") \
                .eq("bot_name", self.bot_name) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            if response.data:
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"[GET_HISTORY] Erro: {e}")
            return []


def test_strategy_logger():
    """Função de teste para StrategyLogger"""
    print("\n=== TESTE STRATEGY LOGGER ===")
    
    # Mock do cliente Supabase para teste
    class MockSupabaseClient:
        def table(self, table_name):
            return MockTable()
    
    class MockTable:
        def select(self, columns):
            return self
        
        def eq(self, column, value):
            return self
        
        def order(self, column, desc=False):
            return self
        
        def limit(self, count):
            return self
        
        def execute(self):
            class MockResponse:
                data = []
            return MockResponse()
        
        def insert(self, data):
            return self
        
        def update(self, data):
            return self
    
    try:
        # Teste 1: Inicialização com bot name válido
        print("\n1. Teste de inicialização...")
        mock_client = MockSupabaseClient()
        logger_instance = StrategyLogger(mock_client, "test_bot_v1")
        print("✅ Inicialização bem-sucedida")
        
        # Teste 2: Bot name inválido
        print("\n2. Teste de validação de bot name...")
        try:
            StrategyLogger(mock_client, "")
            print("❌ Deveria ter falhado com bot name vazio")
        except ValueError as e:
            print(f"✅ Validação funcionou: {e}")
        
        # Teste 3: Informações da execução atual (vazia)
        print("\n3. Teste de execução atual (vazia)...")
        info = logger_instance.get_current_execution_info()
        if info is None:
            print("✅ Nenhuma execução ativa (correto)")
        else:
            print("❌ Deveria retornar None")
        
        # Teste 4: Histórico de execuções
        print("\n4. Teste de histórico...")
        history = logger_instance.get_execution_history(5)
        if isinstance(history, list):
            print(f"✅ Histórico retornado: {len(history)} registros")
        else:
            print("❌ Histórico deveria ser uma lista")
        
        print("\n✅ Todos os testes do StrategyLogger passaram!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_strategy_logger()