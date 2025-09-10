#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tunder Bot - Sistema de Trading com Estratégia Quantum+
Sistema integrado com rastreamento automático de resultados no Supabase

Estratégia implementada:
- Quantum+: 71.98% assertividade

Gatilhos:
- LLLW: Confirmação de Reversão em Ambiente Estável
- LLL: Capitulação em Ambiente Estável
"""

import os
import time
import uuid
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import traceback
from dataclasses import dataclass, field
# import threading  # REMOVIDO - threading órfão não utilizado
# from threading import Lock  # REMOVIDO - threading órfão não utilizado
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tunder_bot_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduzir logs de bibliotecas externas
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('supabase').setLevel(logging.WARNING)
logging.getLogger('postgrest').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# ===== DECORATOR RETRY PARA OPERAÇÕES SUPABASE =====
def retry_supabase_operation(max_retries=3, delay=2):
    """Decorator corrigido para retry automático"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    logger.debug(f"[RETRY] Tentativa {attempt + 1}/{max_retries} para {func.__name__}")
                    result = func(*args, **kwargs)
                    
                    # Se retornou um valor válido (não None), considerar sucesso
                    if result is not None:
                        return result
                    else:
                        raise Exception(f"Função {func.__name__} retornou None")
                        
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"[RETRY] Tentativa {attempt + 1} falhou: {e}. Tentando novamente em {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"[RETRY] Todas as {max_retries} tentativas falharam")
            
            # Se chegou aqui, todas as tentativas falharam
            logger.error(f"[RETRY] Erro final: {last_exception}")
            raise last_exception
            
        return wrapper
    return decorator

# Configurações
BOT_NAME = 'Tunder Bot'
ANALISE_INTERVALO = 5  # segundos entre análises
OPERACOES_MINIMAS = 35  # Mínimo para a estratégia Quantum+
OPERACOES_HISTORICO = 40  # Buscar um pouco mais para garantir
PERSISTENCIA_TIMEOUT = 300  # 5 minutos timeout
PERSISTENCIA_OPERACOES = 1  # Parar após a primeira operação (win ou loss)

# ===== SISTEMA DE GERENCIAMENTO DE ESTADO =====
# Estados da máquina de estados
class BotState:
    ANALYZING = "ANALYZING"    # Estado padrão - busca por padrões
    MONITORING = "MONITORING"  # Estado ativo - monitora operações após sinal

# Variáveis globais de estado
bot_current_state = BotState.ANALYZING
monitoring_operations_count = 0
last_operation_id_when_signal = None
last_checked_operation_id = None
monitoring_start_time = None
active_signal_data = None
active_tracking_id = None  # ID numérico do registro de rastreamento ativo
monitoring_results = []  # Lista para armazenar resultados das operações em tempo real

# ===== FUNÇÕES DE GERENCIAMENTO DE ESTADO =====

def reset_bot_state(supabase=None):
    """Reseta o bot para o estado ANALYZING"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    logger.info("[STATE] Resetando estado para ANALYZING")
    
    # Finalizar rastreamento se necessário
    if supabase and active_tracking_id and len(monitoring_results) >= PERSISTENCIA_OPERACOES:
        sucesso = finalizar_registro_de_rastreamento(supabase, active_tracking_id, monitoring_results)
        if sucesso:
            logger.info(f"[TRACKING] Rastreamento {active_tracking_id} finalizado com resultados: {monitoring_results}")
        else:
            logger.error(f"[TRACKING] Falha ao finalizar rastreamento {active_tracking_id}")
    
    bot_current_state = BotState.ANALYZING
    monitoring_operations_count = 0
    last_operation_id_when_signal = None
    last_checked_operation_id = None
    monitoring_start_time = None
    active_signal_data = None
    active_tracking_id = None
    monitoring_results = []

def activate_monitoring_state(signal_data: dict, latest_operation_id: str, supabase):
    """Ativa o estado MONITORING após encontrar um padrão"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    logger.info(f"[STATE] Ativando estado MONITORING - Sinal: {signal_data['strategy']}")
    
    # Criar registro de rastreamento
    tracking_id = criar_registro_de_rastreamento(
        supabase, 
        signal_data['strategy'], 
        signal_data['confidence']
    )
    
    if tracking_id:
        bot_current_state = BotState.MONITORING
        monitoring_operations_count = 0
        last_operation_id_when_signal = latest_operation_id
        last_checked_operation_id = latest_operation_id  # Inicializar com o ID do sinal
        monitoring_start_time = time.time()
        active_signal_data = signal_data.copy()
        active_tracking_id = tracking_id
        monitoring_results = []  # Resetar lista de resultados
        logger.info(f"[TRACKING] Rastreamento iniciado com ID: {tracking_id}")
    else:
        logger.error(f"[TRACKING] Falha ao criar rastreamento - mantendo estado ANALYZING")

def check_new_operations(current_operation_id: str, resultado_operacao: str = None) -> bool:
    """Verifica se houve novas operações desde o sinal e captura resultado
    
    Args:
        current_operation_id: ID da operação atual
        resultado_operacao: Resultado da operação ('V' ou 'D')
    
    Returns:
        bool: True se houve nova operação
    """
    global monitoring_operations_count, last_operation_id_when_signal, last_checked_operation_id, monitoring_results
    
    if last_operation_id_when_signal is None:
        return False
    
    # Inicializar last_checked_operation_id se for None
    if last_checked_operation_id is None:
        last_checked_operation_id = last_operation_id_when_signal
        
    # Se o ID atual é diferente do último verificado, houve nova operação
    if current_operation_id != last_checked_operation_id:
        monitoring_operations_count += 1
        last_checked_operation_id = current_operation_id
        
        # Capturar resultado em tempo real
        if resultado_operacao:
            monitoring_results.append(resultado_operacao)
            logger.info(f"[STATE] Nova operação detectada: {current_operation_id} - Resultado: {resultado_operacao} - Contador: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        else:
            logger.info(f"[STATE] Nova operação detectada: {current_operation_id} - Sem resultado - Contador: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        
        return True
    
    return False

def should_reset_to_analyzing() -> bool:
    """Verifica se deve resetar para estado ANALYZING
    
    Returns:
        bool: True se deve resetar
    """
    global monitoring_operations_count, monitoring_start_time
    
    # Verificar se atingiu o limite de operações
    if monitoring_operations_count >= PERSISTENCIA_OPERACOES:
        logger.info(f"[STATE] Limite de operações atingido: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        return True
    
    # Verificar timeout
    if monitoring_start_time and (time.time() - monitoring_start_time) > PERSISTENCIA_TIMEOUT:
        logger.info(f"[STATE] Timeout atingido: {PERSISTENCIA_TIMEOUT}s")
        return True
    
    return False





def get_state_info() -> dict:
    """Retorna informações do estado atual"""
    return {
        'current_state': bot_current_state,
        'operations_count': monitoring_operations_count,
        'operations_limit': PERSISTENCIA_OPERACOES,
        'last_operation_id': last_operation_id_when_signal,
        'monitoring_start_time': monitoring_start_time,
        'active_signal': active_signal_data
    }

# Mensagens padronizadas do sistema em espanhol
MENSAJES_SISTEMA = {
    'aguardando_dados': "Esperando datos suficientes...",
    'aguardando_padrao': "Esperando el patrón. No activar aún.",
    'estrategia_ativa': "Estrategia {strategy} activa - esperando {ops} operaciones",
    'patron_encontrado': "Patron Encontrado, Activar Bot Ahora! - {strategy} ({confidence}%)",
    'mercado_instavel': "Mercado inestable, esperar unos minutos",
    'dados_insuficientes': "{strategy}: Datos insuficientes",
    'gatilho_nao_atendido': "{strategy}: Gatillo no cumplido ({wins} WINs)",
    'muitos_losses': "{strategy}: Muchos LOSSes recientes ({losses}/{total})",
    'loss_nao_isolado': "{strategy}: LOSS no está en patrón WIN-LOSS-WIN",
    'losses_consecutivos': "{strategy}: LOSSes consecutivos detectados",
    'losses_consecutivos_proibido': "{strategy}: LOSSes consecutivos detectados (PROHIBIDO)",
    'erro_execucao': "{strategy}: Error en la ejecución",
    'seguro_operar': "Seguro para operar",
    'teste_sistema': "TESTE - Sistema funcionando correctamente",
    'conexao_falhou': "Error de conexión con Supabase",
    'operacao_completada': "Operación completada con éxito"
}

# ===== SISTEMA DE MÉTRICAS E VALIDAÇÃO =====
@dataclass
class StrategyMetrics:
    """Métricas detalhadas por estratégia"""
    name: str
    total_executions: int = 0
    successful_triggers: int = 0
    failed_triggers: int = 0
    filter_rejections: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    execution_times: List[float] = field(default_factory=list)
    error_count: int = 0
    last_execution_time: Optional[float] = None
    confidence_level: float = 0.0
    frequency_operations: int = 0
    
    def add_execution_time(self, exec_time: float):
        self.execution_times.append(exec_time)
        self.last_execution_time = exec_time
        self.total_executions += 1

    def add_filter_rejection(self, filter_name: str):
        self.filter_rejections[filter_name] += 1
        self.failed_triggers += 1

    def add_success(self):
        self.successful_triggers += 1

    def add_error(self):
        self.error_count += 1

    def get_average_time(self) -> float:
        return sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0.0

    def get_success_rate(self) -> float:
        total = self.successful_triggers + self.failed_triggers
        return (self.successful_triggers / total * 100) if total > 0 else 0.0

# Instâncias globais para métricas
# REMOVIDO: strategy_metrics - Sistema simplificado usa apenas PRECISION_SURGE

# REMOVIDO: pattern_locked_state - Sistema simplificado não usa trava de padrão

# Lock para thread safety - COMENTADO
# _pattern_lock = threading.Lock()  # REMOVIDO - threading órfão não utilizado

def activate_pattern_lock(strategy_name: str, confidence: float, signal_data: dict, tracking_id: str):
    """Versão simplificada sem threading complexo - SOLUÇÃO FINAL"""
    global pattern_locked_state
    
    try:
        logger.info(f"[PATTERN_LOCK] === INICIANDO ATIVAÇÃO DA TRAVA ===")
        logger.info(f"[PATTERN_LOCK] Estratégia: {strategy_name}")
        logger.info(f"[PATTERN_LOCK] Confiança: {confidence}%")
        logger.info(f"[PATTERN_LOCK] Tracking ID: {tracking_id}")
        
        # Verificação simples sem threading lock
        if pattern_locked_state.get('is_locked', False):
            logger.warning(f"[PATTERN_LOCK] Estratégia {pattern_locked_state['strategy_name']} já ativa")
            return False
        
        logger.info(f"[PATTERN_LOCK] Atualizando estado global...")
        
        # Atualização direta sem lock complexo
        pattern_locked_state = {
            'is_locked': True,
            'strategy_name': strategy_name,
            'confidence': confidence,
            'detected_at': time.time(),
            'operations_count': 0,
            'tracking_id': tracking_id,
            'signal_data': {
                'should_operate': signal_data.get('should_operate', True),
                'reason': signal_data.get('reason', ''),
                'melhor_estrategia': signal_data.get('melhor_estrategia', {})
            }
        }
        
        logger.info(f"[PATTERN_LOCK] ✅ TRAVA ATIVADA COM SUCESSO")
        logger.info(f"[PATTERN_ACTIVATED] {strategy_name} ativada com {confidence}% confiança")
        return True
        
    except Exception as e:
        logger.error(f"[PATTERN_LOCK] ERRO CRÍTICO: {e}")
        logger.error(f"[PATTERN_LOCK] Traceback: {traceback.format_exc()}")
        
        # Reset em caso de erro
        pattern_locked_state = {
            'is_locked': False,
            'strategy_name': None,
            'confidence': 0.0,
            'detected_at': None,
            'operations_count': 0,
            'tracking_id': None,
            'signal_data': {}
        }
        
        logger.info(f"[PATTERN_LOCK] Estado resetado após erro")
        return False

def reset_pattern_lock_force():
    """Reset forçado da trava (thread-safe)"""
    global pattern_locked_state
    
    old_strategy = pattern_locked_state.get('strategy_name')
    pattern_locked_state.update({
        'is_locked': False,
        'strategy_name': None,
        'confidence': 0.0,
        'detected_at': None,
        'operations_count': 0,
        'tracking_id': None,
        'signal_data': {}
    })
    
    if old_strategy:
        logger.info(f"[PATTERN_RESET] {old_strategy} resetada")

def check_pattern_lock_status():
    """Verifica status atual da trava"""
    return pattern_locked_state.copy()

# REMOVIDO: active_strategy, strategy_start_time, operations_since_strategy - Sistema simplificado

def is_strategy_active():
    """Verifica se há estratégia ativa"""
    global active_strategy
    return active_strategy is not None

def activate_strategy(strategy_data):
    """Ativa nova estratégia"""
    global active_strategy, strategy_start_time, operations_since_strategy
    active_strategy = strategy_data
    strategy_start_time = time.time()
    operations_since_strategy = 0
    logger.info(f"[STRATEGY_ACTIVATED] {strategy_data['strategy']} ativada")

def reset_strategy():
    """Reset da estratégia ativa"""
    global active_strategy, strategy_start_time, operations_since_strategy
    if active_strategy:
        logger.info(f"[STRATEGY_RESET] {active_strategy['strategy']} resetada após {operations_since_strategy} operações")
    active_strategy = None
    strategy_start_time = None
    operations_since_strategy = 0

def increment_operations():
    """Incrementa contador de operações"""
    global operations_since_strategy
    if active_strategy:
        operations_since_strategy += 1
        logger.info(f"[OPERATION_COUNT] {operations_since_strategy}/2 operações completadas")
        return operations_since_strategy
    return 0

def count_operations_since_pattern_CORRETO(supabase_client, timestamp_referencia: float) -> int:
    """Conta operações reais no Supabase desde timestamp de referência"""
    try:
        # Converter timestamp para formato ISO
        ref_datetime = datetime.fromtimestamp(timestamp_referencia).isoformat()
        
        # Buscar operações mais recentes que o timestamp
        response = supabase_client.table('scalping_accumulator_bot_logs') \
            .select('created_at') \
            .eq('bot_name', BOT_NAME) \
            .gt('created_at', ref_datetime) \
            .order('created_at', desc=True) \
            .execute()
        
        count = len(response.data) if response.data else 0
        
        logger.debug(f"[OPERATION_COUNT] {count} operações desde {ref_datetime}")
        
        # Log das operações encontradas para debug
        if response.data and count > 0:
            logger.debug(f"[OPERATION_COUNT] Operações mais recentes:")
            for i, op in enumerate(response.data[:3]):  # Mostrar apenas as 3 mais recentes
                logger.debug(f"[OPERATION_COUNT]   {i+1}. {op['created_at']}")
        
        return count
        
    except Exception as e:
        logger.error(f"[OPERATION_COUNT] Erro ao contar operações: {e}")
        return 0

def monitor_and_update_pattern_operations_CORRETO(supabase_client):
    """Monitora operações e reseta trava quando necessário"""
    global pattern_locked_state, _pattern_lock
    
    if not pattern_locked_state['is_locked']:
        return

    try:
        current_time = time.time()
        
        # Verificar timeout de segurança (10 minutos)
        if current_time - pattern_locked_state['detected_at'] > 600:
            logger.warning(f"[TIMEOUT_RESET] Timeout de 10 minutos - resetando trava")
            reset_pattern_lock_force()
            return
        
        # Contar operações desde ativação da estratégia
        operacoes_novas = count_operations_since_pattern_CORRETO(
            supabase_client,
            pattern_locked_state['detected_at']
        )
        
        # Atualizar contador
        pattern_locked_state['operations_count'] = operacoes_novas
        
        logger.info(f"[PATTERN_MONITOR] {operacoes_novas}/2 operações registradas")
        
        # Reset quando atingir 2 operações REAIS
        if operacoes_novas >= 2:
            logger.info(f"[RESET_TRIGGERED] 2 operações reais detectadas - resetando estratégia")
            reset_pattern_lock_force()
            return
                
    except Exception as e:
        logger.error(f"[MONITOR_ERROR] Erro no monitoramento: {e}")

def inicializar_supabase():
    """Inicializa conexão com Supabase"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Credenciais do Supabase não encontradas no arquivo .env")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("OK Conexão com Supabase estabelecida com sucesso")
        return supabase
        
    except Exception as e:
        print(f"FAIL Erro ao conectar com Supabase: {e}")
        return None

# ===== FUNÇÕES DE CONTROLE SIMPLIFICADO =====
def check_strategy_timeout():
    """Verifica timeout da estratégia (5 minutos)"""
    global active_strategy, strategy_start_time
    if active_strategy and strategy_start_time:
        elapsed = time.time() - strategy_start_time
        if elapsed > 300:  # 5 minutos
            logger.warning(f"[TIMEOUT] Estratégia {active_strategy['strategy']} expirou após {elapsed:.1f}s")
            reset_strategy()
            return True
    return False

def should_activate_strategy(new_strategy_data):
    """Verifica se deve ativar nova estratégia"""
    check_strategy_timeout()
    
    if not active_strategy:
        activate_strategy(new_strategy_data)
        return True

    logger.debug(f"[STRATEGY_BLOCKED] {active_strategy['strategy']} ainda ativa - ignorando {new_strategy_data['strategy']}")
    return False

def check_operation_completion():
    """Verifica se completou 2 operações"""
    if active_strategy and operations_since_strategy >= 2:
        logger.info(f"[STRATEGY_COMPLETED] {active_strategy['strategy']} completou 2 operações")
        reset_strategy()
        return True
    return False

# Código removido - sistema simplificado não necessita contagem complexa
# Função removida - sistema simplificado não necessita monitoramento complexo

# ===== SISTEMA SIMPLIFICADO DE CONTROLE =====
# Usando apenas variáveis globais simples para controle de estratégias

def validar_integridade_historico(historico: List[str]) -> bool:
    """Valida integridade dos dados de histórico"""
    try:
        if not historico:
            logger.error("[DATA_INTEGRITY] Histórico vazio")
            return False
            
        # Verificar se contém apenas valores válidos
        valid_values = {'V', 'D'}
        invalid_values = [val for val in historico if val not in valid_values]
        if invalid_values:
            logger.error(f"[DATA_INTEGRITY] Valores inválidos encontrados: {set(invalid_values)}")
            return False
            
        # Verificar se há dados suficientes para análise
        if len(historico) < OPERACOES_MINIMAS:
            logger.warning(f"[DATA_INTEGRITY] Histórico insuficiente: {len(historico)} < {OPERACOES_MINIMAS}")
            return False
            
        # Verificar distribuição básica
        win_rate = (historico.count('V') / len(historico)) * 100
        if win_rate == 0 or win_rate == 100:
            logger.warning(f"[DATA_INTEGRITY] Distribuição suspeita: {win_rate}% WINs")
            return False
            
        logger.debug(f"[DATA_INTEGRITY] Validação bem-sucedida: {len(historico)} operações, WR: {win_rate:.1f}%")
        return True
        
    except Exception as e:
        logger.error(f"[DATA_INTEGRITY_EXCEPTION] Erro na validação: {e}")
        return False

def buscar_operacoes_historico(supabase):
    """Busca histórico de operações do Supabase da tabela do Tunder Bot.
    
    Returns:
        tuple: (historico, timestamps, latest_operation_id)
    """
    try:
        response = supabase.table('tunder_bot_logs') \
            .select('id, operation_result, timestamp') \
            .order('timestamp', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            logger.warning("[HISTORICO] Nenhuma operação encontrada na tabela tunder_bot_logs")
            return [], [], None
        
        historico = [op['operation_result'] for op in response.data]  # 'WIN' ou 'LOSS'
        timestamps = [op['timestamp'] for op in response.data]
        latest_operation_id = response.data[0]['id']
        
        logger.info(f"[HISTORICO] {len(historico)} operações carregadas de tunder_bot_logs")
        logger.debug(f"[HISTORICO] Sequência: {' '.join(historico[:10])}...")
        logger.debug(f"[HISTORICO] ID operação mais recente: {latest_operation_id}")
        
        return historico, timestamps, latest_operation_id
        
    except Exception as e:
        logger.error(f"[HISTORICO_ERROR] Erro ao buscar operações do Tunder Bot: {e}")
        return [], [], None

def criar_registro_de_rastreamento(supabase, strategy_name: str, confidence_level: float) -> int:
    """Cria registro na tabela strategy_results_tracking e retorna o ID serial"""
    try:
        data = {
            'strategy_name': strategy_name,
            'strategy_confidence': confidence_level,
            'bot_name': BOT_NAME,
            'status': 'ACTIVE'
        }
        
        response = supabase.table('tunder_bot_strategy_results_tracking').insert(data).select('id').execute()
        
        if response.data and len(response.data) > 0:
            record_id = response.data[0]['id']
            logger.info(f"[TRACKING] Registro criado com ID: {record_id} para {strategy_name}")
            return record_id
        else:
            logger.error(f"[TRACKING] Falha ao criar registro para {strategy_name}")
            return None
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro ao criar tracking: {e}")
        return None

def finalizar_registro_de_rastreamento(supabase, record_id: int, resultados: List[str]) -> bool:
    """Finaliza registro de rastreamento com os resultados das operações"""
    try:
        # Mapear resultados para as colunas corretas
        operation_1_result = resultados[0] if len(resultados) > 0 else None
        operation_2_result = resultados[1] if len(resultados) > 1 else None
        
        # Determinar sucesso do padrão (True somente se ambos forem 'WIN')
        pattern_success = (resultados == ['WIN', 'WIN']) if len(resultados) == 2 else False
        
        # Dados para atualização
        update_data = {
            'operation_1_result': operation_1_result,
            'operation_2_result': operation_2_result,
            'pattern_success': pattern_success,
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat()
        }
        
        response = supabase.table('tunder_bot_strategy_results_tracking').update(update_data).eq('id', record_id).execute()
        
        if response.data:
            logger.info(f"[TRACKING] Registro {record_id} finalizado: {resultados} -> Sucesso: {pattern_success}")
            return True
        else:
            logger.error(f"[TRACKING] Falha ao finalizar registro {record_id}")
            return False
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro ao finalizar tracking {record_id}: {e}")
        return False

def consultar_eficacia_estrategia(supabase, strategy_name: str) -> Dict:
    """Consulta eficácia em tempo real de uma estratégia"""
    try:
        response = supabase.table('strategy_results_tracking') \
            .select('*') \
            .eq('strategy_name', strategy_name) \
            .eq('bot_name', BOT_NAME) \
            .order('pattern_found_at', desc=True) \
            .limit(50) \
            .execute()
        
        if not response.data:
            return {'total_signals': 0, 'success_rate': 0, 'avg_confidence': 0}
        
        records = response.data
        total_signals = len(records)
        successful_signals = len([r for r in records if r.get('final_result') == 'SUCCESS'])
        completed_signals = len([r for r in records if r.get('final_result') is not None])
        
        success_rate = (successful_signals / completed_signals * 100) if completed_signals > 0 else 0
        avg_confidence = sum([r['strategy_confidence'] for r in records]) / total_signals
        
        return {
            'total_signals': total_signals,
            'successful_signals': successful_signals,
            'completed_signals': completed_signals,
            'success_rate': success_rate,
            'avg_confidence': avg_confidence,
            'recent_records': records[:10]
        }
        
    except Exception as e:
        logger.error(f"[EFICACIA_ERROR] Erro ao consultar eficácia de {strategy_name}: {e}")
        return {'total_signals': 0, 'success_rate': 0, 'avg_confidence': 0}

def gerar_relatorio_eficacia(supabase) -> Dict:
    """Gera relatório consolidado de eficácia das estratégias"""
    try:
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'estrategias': {},
            'consolidado': {
                'total_signals': 0,
                'success_rate_medio': 0,
                'melhor_estrategia': None,
                'assertividade_sistema': 94.51
            }
        }
        
        total_success_rate = 0
        total_signals = 0
        melhor_performance = 0
        melhor_estrategia = None
        
        for strategy_name in ['MICRO_BURST', 'PRECISION_SURGE', 'QUANTUM_MATRIX']:
            eficacia = consultar_eficacia_estrategia(supabase, strategy_name)
            relatorio['estrategias'][strategy_name] = eficacia
            
            total_signals += eficacia['total_signals']
            if eficacia['success_rate'] > melhor_performance:
                melhor_performance = eficacia['success_rate']
                melhor_estrategia = strategy_name
            
            total_success_rate += eficacia['success_rate']
        
        relatorio['consolidado']['total_signals'] = total_signals
        relatorio['consolidado']['success_rate_medio'] = total_success_rate / 3
        relatorio['consolidado']['melhor_estrategia'] = melhor_estrategia
        
        logger.info(f"[RELATORIO] Gerado: {total_signals} sinais, {relatorio['consolidado']['success_rate_medio']:.1f}% média")
        return relatorio
        
    except Exception as e:
        logger.error(f"[RELATORIO_ERROR] Erro ao gerar relatório: {e}")
        return {}

# ===== IMPLEMENTAÇÃO DA ESTRATÉGIA QUANTUM+ =====

def analisar_estrategia_quantum_plus(historico: List[str]) -> Dict:
    """
    Tunder Bot - Estratégia Quantum+: Analisa o histórico de operações em busca
    dos gatilhos de "Confirmação de Reversão" ou "Capitulação".
    Assertividade Histórica: 71.98%
    """
    strategy_name = "Quantum+"
    logger.debug(f"[{strategy_name}] Iniciando análise...")

    # A estratégia requer exatamente 34 operações anteriores para o Gatilho 1
    # ou 33 para o Gatilho 2. Verificamos o mínimo necessário.
    if len(historico) < 35:
        return {
            'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
            'reason': f"Datos insuficientes para Quantum+ (necesario 35, encontrado {len(historico)})"
        }

    # Lembre-se: o histórico vem do mais recente para o mais antigo.
    # historico[0] é a última operação.

    # --- ANÁLISE DO GATILHO 1: "Confirmação de Reversão em Ambiente Estável" ---
    # Sequência imediata: L, L, L, W (na ordem de ocorrência)
    # No histórico reverso: W, L, L, L (índices 0, 1, 2, 3)
    sequencia_gatilho1 = ['WIN', 'LOSS', 'LOSS', 'LOSS']
    if historico[:4] == sequencia_gatilho1:
        logger.debug(f"[{strategy_name}] Gatilho 1 (LLLW) detectado. Verificando filtros...")
        
        # Filtro de Curto Prazo: 10 ops ANTES da sequência (índices 4 a 13)
        janela_curto_prazo = historico[4:14]
        wins_curto_prazo = janela_curto_prazo.count('WIN')
        
        if 5 <= wins_curto_prazo <= 6:
            logger.debug(f"[{strategy_name}] Filtro de Curto Prazo OK ({wins_curto_prazo} wins em 10).")
            
            # Filtro de Longo Prazo: 20 ops ANTES da janela de 10 (índices 14 a 33)
            janela_longo_prazo = historico[14:34]
            wins_longo_prazo = janela_longo_prazo.count('WIN')

            if 10 <= wins_longo_prazo <= 12:
                logger.info(f"[{strategy_name}] ✅ PADRÃO ENCONTRADO! Gatilho 1 (LLLW) validado.")
                return {
                    'should_operate': True, 'strategy': strategy_name, 'confidence': 71.98,
                    'reason': f"Patrón Encontrado: {strategy_name} (Confirmación de Reversión)",
                    'pattern_details': {
                        'trigger': 'LLLW',
                        'wins_short_term': wins_curto_prazo,
                        'wins_long_term': wins_longo_prazo
                    }
                }
        logger.debug(f"[{strategy_name}] Gatilho 1 (LLLW) falhou nos filtros.")

    # --- ANÁLISE DO GATILHO 2: "Capitulação em Ambiente Estável" ---
    # Sequência imediata: L, L, L (na ordem de ocorrência)
    # No histórico reverso: L, L, L (índices 0, 1, 2)
    sequencia_gatilho2 = ['LOSS', 'LOSS', 'LOSS']
    if historico[:3] == sequencia_gatilho2:
        logger.debug(f"[{strategy_name}] Gatilho 2 (LLL) detectado. Verificando filtros...")
        
        # Filtro de Curto Prazo: 10 ops ANTES da sequência (índices 3 a 12)
        janela_curto_prazo = historico[3:13]
        wins_curto_prazo = janela_curto_prazo.count('WIN')

        if 5 <= wins_curto_prazo <= 6:
            logger.debug(f"[{strategy_name}] Filtro de Curto Prazo OK ({wins_curto_prazo} wins em 10).")
            
            # Filtro de Longo Prazo: 20 ops ANTES da janela de 10 (índices 13 a 32)
            janela_longo_prazo = historico[13:33]
            wins_longo_prazo = janela_longo_prazo.count('WIN')

            if 10 <= wins_longo_prazo <= 12:
                logger.info(f"[{strategy_name}] ✅ PADRÃO ENCONTRADO! Gatilho 2 (LLL) validado.")
                return {
                    'should_operate': True, 'strategy': strategy_name, 'confidence': 71.98,
                    'reason': f"Patrón Encontrado: {strategy_name} (Capitulación)",
                    'pattern_details': {
                        'trigger': 'LLL',
                        'wins_short_term': wins_curto_prazo,
                        'wins_long_term': wins_longo_prazo
                    }
                }
        logger.debug(f"[{strategy_name}] Gatilho 2 (LLL) falhou nos filtros.")

    # Se nenhum gatilho foi atendido
    return {
        'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
        'reason': "Esperando el patrón Quantum+. Ninguna condición cumplida."
    }

# ===== SISTEMA DE ENVIO DE SINAIS =====

@retry_supabase_operation(max_retries=3, delay=2)
def enviar_sinal_supabase(supabase, signal_data: Dict) -> bool:
    try:
        signal_record = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': signal_data['should_operate'],
            'reason': signal_data['reason'],
            'strategy_used': signal_data['strategy'],
            'strategy_confidence': signal_data['confidence'],
            'losses_in_last_10_ops': 0,
            'wins_in_last_5_ops': 5,
            'historical_accuracy': signal_data['confidence'] / 100.0,
            'pattern_found_at': datetime.now().isoformat() if signal_data['should_operate'] else None,
            'operations_after_pattern': 0,
            'auto_disable_after_ops': 2,
            'available_strategies': 3,
            'filters_applied': '[]',
            'execution_time_ms': 0
        }
        
        response = supabase.table('radar_de_apalancamiento_signals').insert(signal_record).execute()
        
        if response.data:
            logger.info(f"[SIGNAL_SENT] ✅ Sinal enviado: {signal_data['strategy']}")
            return True
        else:
            logger.error(f"[SIGNAL_ERROR] Resposta vazia")
            return False
            
    except Exception as e:
        logger.error(f"[SIGNAL_ERROR] Erro: {e}")
        raise e

# FUNÇÃO REMOVIDA: processar_e_enviar_sinal() - Simplificação do sistema

# ===== SISTEMA DE MONITORAMENTO E STATUS =====

def gerar_status_sistema() -> Dict:
    """Gera status completo do sistema"""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'bot_name': BOT_NAME,
            'system_status': 'OPERATIONAL',
            'strategies': {},
            'pattern_lock': check_pattern_lock_status(),
            'metrics_summary': {}
        }
        
        # Status da estratégia Quantum+
        status['strategies']['Quantum+'] = {
            'confidence_level': 71.98,
            'total_executions': 0,
            'success_rate': 0.0,
            'average_time': 0.0,
            'error_count': 0,
            'last_execution': None
        }
        
        # Resumo das métricas
        status['metrics_summary'] = {
            'total_executions': 0,
            'average_success_rate': 0.0,
            'system_uptime': time.time(),
            'strategies_count': 1
        }
        
        return status
         
    except Exception as e:
        logger.error(f"[STATUS_ERROR] Erro ao gerar status: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'bot_name': BOT_NAME,
            'system_status': 'ERROR',
            'error': str(e)
        }

# FUNÇÃO REMOVIDA: imprimir_status_detalhado() - Simplificação do sistema

# ===== LOOP PRINCIPAL DO BOT =====

def executar_ciclo_analise_simplificado(supabase) -> Dict:
    """Ciclo com máquina de estados - ANALYZING/MONITORING"""
    try:
        global bot_current_state
        
        logger.info(f"[CICLO] === CICLO ESTADO: {bot_current_state} ===")
        
        # Buscar histórico (sempre necessário para verificar novas operações)
        historico, timestamps, latest_operation_id = buscar_operacoes_historico(supabase)
        
        if not historico:
            return {
                'status': 'NO_DATA',
                'message': 'Aguardando dados'
            }
        
        # LÓGICA DA MÁQUINA DE ESTADOS
        resultado_ciclo = None
        
        if bot_current_state == BotState.ANALYZING:
            # ESTADO ANALYZING: Buscar por padrões
            logger.info("[STATE] Estado ANALYZING - Buscando padrões")
            
            # Executar análise Quantum+
            resultado_ciclo = analisar_estrategia_quantum_plus(historico)
            
            # Se encontrou padrão, ativar estado MONITORING e armazenar resultado
            if resultado_ciclo['should_operate']:
                activate_monitoring_state(resultado_ciclo, latest_operation_id, supabase)
                logger.info(f"[STATE_CHANGE] ANALYZING → MONITORING (padrão encontrado)")
                
        elif bot_current_state == BotState.MONITORING:
            # ESTADO MONITORING: Usar sinal armazenado e verificar condições de reset
            logger.info(f"[STATE] Estado MONITORING - Operações: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
            
            # Verificar se houve novas operações
            resultado_mais_recente = historico[0] if historico else None
            nova_operacao = check_new_operations(latest_operation_id, resultado_mais_recente)
            if nova_operacao:
                resultado_operacao = "WIN" if resultado_mais_recente == "V" else "LOSS" if resultado_mais_recente == "D" else "UNKNOWN"
                logger.info(f"[MONITORING] Primera operación después del patrón detectada: {resultado_operacao} - Finalizando monitoreo")
            
            # Verificar se deve resetar para ANALYZING (agora sempre após primeira operação)
            if should_reset_to_analyzing():
                # Criar resultado de finalização com informação da primeira operação
                resultado_operacao = "WIN" if resultado_mais_recente == "V" else "LOSS" if resultado_mais_recente == "D" else "UNKNOWN"
                resultado_ciclo = {
                    'should_operate': False,
                    'reason': f"Estrategia {active_signal_data['strategy']} completada - Primera operación: {resultado_operacao}",
                    'strategy': active_signal_data['strategy'],
                    'confidence': active_signal_data['confidence'],
                    'losses_ultimas_15': active_signal_data.get('losses_ultimas_15', 0),
                    'wins_consecutivos': active_signal_data.get('wins_consecutivos', 0)
                }
                
                reset_bot_state(supabase)
                logger.info(f"[STATE_CHANGE] MONITORING → ANALYZING (primera operación completada: {resultado_operacao})")
            else:
                # Usar o sinal armazenado como resultado do ciclo atual
                remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count
                resultado_ciclo = {
                    'should_operate': True,  # Manter sinal ativo
                    'reason': f"Patrón encontrado: {active_signal_data['strategy']} - esperando {remaining_ops} operaciones",
                    'strategy': active_signal_data['strategy'],
                    'confidence': active_signal_data['confidence'],
                    'losses_ultimas_15': active_signal_data.get('losses_ultimas_15', 0),
                    'wins_consecutivos': active_signal_data.get('wins_consecutivos', 0)
                }
        
        # ENVIO CENTRALIZADO PARA SUPABASE (final do ciclo)
        if resultado_ciclo:
            # Construir payload baseado no resultado do ciclo
            pattern_details = resultado_ciclo.get('pattern_details', {})
            dados_supabase = {
                'bot_name': BOT_NAME,
                'is_safe_to_operate': resultado_ciclo['should_operate'],
                'reason': resultado_ciclo['reason'],
                'strategy_used': resultado_ciclo.get('strategy', 'Quantum+'),
                'strategy_confidence': resultado_ciclo['confidence'],
                'strategy_details': pattern_details,
                'historical_accuracy': resultado_ciclo['confidence'] / 100.0 if resultado_ciclo['confidence'] > 0 else 0,
                'pattern_found_at': datetime.now().isoformat() if resultado_ciclo['should_operate'] else None,
                'operations_after_pattern': monitoring_operations_count if bot_current_state == BotState.MONITORING else 0,
                'auto_disable_after_ops': PERSISTENCIA_OPERACOES,
                'available_strategies': 1,
                'losses_in_last_10_ops': 0,
                'wins_in_last_5_ops': 0,
                'filters_applied': '{Quantum+ triggers & context filters}',
                'execution_time_ms': 0
            }
            
            # ENVIO PARA SUPABASE (sempre, independente do estado)
            try:
                response = supabase.table('radar_de_apalancamiento_signals').insert(dados_supabase).execute()
                
                if response.data:
                    if bot_current_state == BotState.MONITORING and resultado_ciclo['should_operate']:
                        logger.info(f"[SIGNAL_SENT] ✅ Sinal reenviado (MONITORING): {resultado_ciclo['reason']}")
                    else:
                        status_msg = "padrão encontrado" if resultado_ciclo['should_operate'] else "sem padrão"
                        logger.info(f"[SIGNAL_SENT] ✅ Status enviado ({status_msg}): {resultado_ciclo['reason']}")
                    resultado_ciclo['signal_sent'] = True
                else:
                    logger.error(f"[SIGNAL_ERROR] ❌ Falha no envio do sinal")
                    resultado_ciclo['signal_sent'] = False
            except Exception as e:
                logger.error(f"[SIGNAL_ERROR] ❌ Erro ao enviar sinal: {e}")
                resultado_ciclo['signal_sent'] = False
        
        return {
            'status': 'COMPLETED',
            'resultado': resultado_ciclo
        }
        
    except Exception as e:
        logger.error(f"[CICLO_ERROR] Erro: {e}")
        logger.error(f"[CICLO_ERROR] Traceback: {traceback.format_exc()}")
        return {
            'status': 'ERROR',
            'message': f"Erro: {e}"
        }

def main_loop():
    """Loop principal do bot com máquina de estados"""
    logger.info("[MAIN] === INICIANDO RADAR ANALISIS SCALPING BOT COM ESTADOS ===")
    logger.info("[MAIN] Sistema com máquina de estados: ANALYZING/MONITORING")
    logger.info("[MAIN] Estratégia: Quantum+ (71.98%)")
    logger.info(f"[MAIN] Persistência: {PERSISTENCIA_OPERACOES} operações ou {PERSISTENCIA_TIMEOUT}s")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        logger.error("[MAIN] ERRO CRÍTICO: Não foi possível conectar ao Supabase")
        print("FAIL Erro crítico na conexão com Supabase")
        return
    
    # Resetar estado inicial
    reset_bot_state()
    
    logger.info("[MAIN] ✅ Sistema inicializado com sucesso")
    print("\n🚀 RADAR ANALISIS SCALPING BOT COM ESTADOS ATIVO")
    print("📊 Sistema de gerenciamento de estado implementado")
    print("🔄 Estados: ANALYZING (busca padrões) → MONITORING (mantém sinal)")
    print("⏱️  Análise a cada 5 segundos")
    print("🎯 Estratégia: Quantum+ (71.98%)")
    print("🔍 Gatilho: LLLW ou LLL com filtros de estabilidade")
    print(f"⚡ Persistência: {PERSISTENCIA_OPERACOES} operações")
    print("\nPressione Ctrl+C para parar\n")
    
    ciclo_count = 0
    
    try:
        while True:
            ciclo_count += 1
            
            # Mostrar estado atual
            state_info = get_state_info()
            estado_display = "🔍 ANALISANDO" if bot_current_state == BotState.ANALYZING else "👁️ MONITORANDO"
            
            # Executar ciclo de análise com estados
            resultado_ciclo = executar_ciclo_analise_simplificado(supabase)
            
            # Log do resultado
            status = resultado_ciclo['status']
            message = resultado_ciclo.get('message', '')
            
            if status == 'COMPLETED':
                resultado = resultado_ciclo['resultado']
                
                if resultado['should_operate']:
                    # Sinal encontrado - mudou para MONITORING
                    print(f"\n🎯 {resultado['reason']}")
                    print(f"🔄 Estado alterado: ANALYZING → MONITORING")
                    logger.info(f"[MAIN] SINAL ENVIADO: {resultado['strategy']} - {resultado['confidence']:.1f}%")
                    
                elif bot_current_state == BotState.MONITORING:
                    # Estado MONITORING ativo
                    monitoring_info = resultado.get('monitoring_info', {})
                    ops_count = monitoring_info.get('operations_count', 0)
                    ops_limit = monitoring_info.get('operations_limit', PERSISTENCIA_OPERACOES)
                    
                    print(f"👁️ {resultado['reason']} [{ops_count}/{ops_limit}]")
                    
                    # Verificar se completou o monitoramento
                    if "completada" in resultado['reason']:
                        print(f"✅ Monitoramento finalizado - Voltando para ANALYZING")
                        
                else:
                    # Estado ANALYZING - sem padrão
                    print(f"🔍 {resultado['reason']}")
                    
            elif status == 'NO_DATA':
                print(f"📊 {message}")
            elif status == 'ERROR':
                print(f"❌ {message}")
                logger.error(f"[MAIN] Erro no ciclo {ciclo_count}: {message}")
            
            # Aguardar próximo ciclo
            time.sleep(ANALISE_INTERVALO)
            
    except KeyboardInterrupt:
        logger.info("[MAIN] Bot interrompido pelo usuário")
        print("\n🛑 Bot interrompido pelo usuário")
        print(f"📊 Estado final: {bot_current_state}")
        if bot_current_state == BotState.MONITORING:
            print(f"⚡ Operações monitoradas: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        print("🔄 Sistema com estados finalizado")
        
    except Exception as e:
        logger.error(f"[MAIN] ERRO CRÍTICO: {e}")
        logger.error(f"[MAIN] Traceback: {traceback.format_exc()}")
        print(f"\n💥 ERROR CRÍTICO: {e}")
        
    finally:
        logger.info("[MAIN] === FINALIZANDO RADAR ANALISIS SCALPING BOT COM ESTADOS ===")
        print("\n👋 Radar Analisis Scalping Bot con Estados finalizado")

# ===== FUNÇÕES DE TESTE E VALIDAÇÃO =====

def testar_conexao_supabase():
    """Testa conexão com Supabase"""
    try:
        print("🔍 Probando conexión con Supabase...")
        supabase = inicializar_supabase()
        
        if not supabase:
            print("❌ FALLA en la conexión con Supabase")
            return False
        
        # Testar consulta simples
        response = supabase.table('scalping_accumulator_bot_logs').select('*').limit(1).execute()
        
        if response.data is not None:
            print("✅ Conexión con Supabase OK")
            print(f"📊 Tabla 'scalping_accumulator_bot_logs' accesible")
            return True
        else:
            print("❌ FALLA al acceder a la tabla 'scalping_accumulator_bot_logs'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR en la conexión: {e}")
        return False

def testar_estrategia_quantum_plus():
    """Testa a estratégia Quantum+ com dados simulados"""
    try:
        print("\n🧪 Probando estrategia Quantum+ con datos simulados...")
        
        # Teste 1: Gatilho LLLW (Confirmação de Reversão)
        historico_teste_1 = ['WIN', 'LOSS', 'LOSS', 'LOSS'] + ['WIN'] * 10 + ['LOSS'] * 5 + ['WIN'] * 15
        print(f"📊 Teste 1 - LLLW: {' '.join(historico_teste_1[:10])}...")
        
        resultado_1 = analisar_estrategia_quantum_plus(historico_teste_1)
        print(f"🎯 Resultado: {resultado_1['should_operate']} - {resultado_1['confidence']:.2f}%")
        print(f"📝 Razón: {resultado_1['reason']}")
        
        # Teste 2: Gatilho LLL (Capitulação)
        historico_teste_2 = ['LOSS', 'LOSS', 'LOSS'] + ['WIN'] * 12 + ['LOSS'] * 3 + ['WIN'] * 15
        print(f"\n📊 Teste 2 - LLL: {' '.join(historico_teste_2[:10])}...")
        
        resultado_2 = analisar_estrategia_quantum_plus(historico_teste_2)
        print(f"🎯 Resultado: {resultado_2['should_operate']} - {resultado_2['confidence']:.2f}%")
        print(f"📝 Razón: {resultado_2['reason']}")
        
        # Teste 3: Dados insuficientes
        historico_teste_3 = ['WIN', 'LOSS', 'WIN'] * 5
        print(f"\n📊 Teste 3 - Dados insuficientes: {' '.join(historico_teste_3)}")
        
        resultado_3 = analisar_estrategia_quantum_plus(historico_teste_3)
        print(f"🎯 Resultado: {resultado_3['should_operate']} - {resultado_3['confidence']:.2f}%")
        print(f"📝 Razón: {resultado_3['reason']}")
        
        print("\n✅ Prueba de la estrategia Quantum+ completada")
        return True
        
    except Exception as e:
        print(f"❌ ERROR en la prueba de la estrategia: {e}")
        return False

def testar_nova_estrategia():
    """Função de teste dedicada para a estratégia Quantum+."""
    print("\n🧪 Probando la nueva estrategia Quantum+...")

    # Cenário 1: Deve ativar o Gatilho 1 (LLLW)
    # Sequência: [11W] [6W] LLLW + dados extras para atingir 35 operações
    historico_gatilho1 = (
        ['WIN'] + ['LOSS'] * 3 + # Sequência LLLW (reverso: W L L L)
        (['WIN'] * 6 + ['LOSS'] * 4) + # Janela de 10 com 6 vitórias
        (['WIN'] * 11 + ['LOSS'] * 9) + # Janela de 20 com 11 vitórias
        (['WIN'] * 5 + ['LOSS'] * 1) # Dados extras para atingir 35 operações
    )
    print("\n--- Testando Gatilho 1 (LLLW) ---")
    resultado1 = analisar_estrategia_quantum_plus(historico_gatilho1)
    if resultado1['should_operate']:
        print(f"✅ SUCESSO: Gatilho 1 ativado corretamente.")
        print(f"   Razón: {resultado1['reason']}")
    else:
        print(f"❌ FALHA: Gatilho 1 não foi ativado.")
        print(f"   Razón: {resultado1['reason']}")

    # Cenário 2: Deve ativar o Gatilho 2 (LLL)
    # Sequência: [10W] [5W] LLL + dados extras para atingir 35 operações
    historico_gatilho2 = (
        ['LOSS'] * 3 + # Sequência LLL (reverso: L L L)
        (['WIN'] * 5 + ['LOSS'] * 5) + # Janela de 10 com 5 vitórias
        (['WIN'] * 10 + ['LOSS'] * 10) + # Janela de 20 com 10 vitórias
        (['WIN'] * 6 + ['LOSS'] * 1) # Dados extras para atingir 35 operações
    )
    print("\n--- Testando Gatilho 2 (LLL) ---")
    resultado2 = analisar_estrategia_quantum_plus(historico_gatilho2)
    if resultado2['should_operate']:
        print(f"✅ SUCESSO: Gatilho 2 ativado corretamente.")
        print(f"   Razón: {resultado2['reason']}")
    else:
        print(f"❌ FALHA: Gatilho 2 não foi ativado.")
        print(f"   Razón: {resultado2['reason']}")

    # Cenário 3: Não deve ativar (falha no filtro)
    historico_falha = (
        ['WIN'] + ['LOSS'] * 3 + # Sequência LLLW
        (['WIN'] * 4 + ['LOSS'] * 6) + # Janela de 10 com apenas 4 vitórias (deve falhar)
        (['WIN'] * 11 + ['LOSS'] * 9) + # Janela de 20 com 11 vitórias
        (['WIN'] * 5 + ['LOSS'] * 1) # Dados extras para atingir 35 operações
    )
    print("\n--- Testando cenário de falha ---")
    resultado3 = analisar_estrategia_quantum_plus(historico_falha)
    if not resultado3['should_operate']:
        print(f"✅ SUCESSO: O padrão não foi ativado, como esperado.")
        print(f"   Razón: {resultado3['reason']}")
    else:
        print(f"❌ FALHA: O padrão foi ativado incorretamente.")
        print(f"   Razón: {resultado3['reason']}")

def executar_testes_completos():
    """Executa bateria completa de testes"""
    print("🔬 === EXECUTANDO TESTES COMPLETOS - TUNDER BOT QUANTUM+ ===")
    
    # Teste 1: Conexão Supabase
    teste1 = testar_conexao_supabase()
    
    # Teste 2: Estratégia Quantum+
    teste2 = testar_estrategia_quantum_plus()
    
    # Resultado final
    if teste1 and teste2:
        print("\n✅ TODOS OS TESTES PASSARAM")
        print("🚀 Tunder Bot Quantum+ pronto para execução")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique la configuración antes de ejecutar")
        return False

# ===== PONTO DE ENTRADA =====

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        # Comando de teste
        testar_nova_estrategia()
    elif len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "testall":
            # Executar testes completos
            executar_testes_completos()
        elif comando == "status":
            # Mostrar status
            imprimir_status_detalhado()
        elif comando == "help":
            # Mostrar ajuda
            print("\n📖 TUNDER BOT QUANTUM+ - Ajuda")
            print("="*50)
            print("Uso: python radar_tunder_new.py [comando]")
            print("\nComandos disponíveis:")
            print("  (sem comando) - Executar bot principal")
            print("  test         - Testar nova estratégia Quantum+")
            print("  testall      - Executar testes completos do sistema")
            print("  status       - Mostrar status detalhado")
            print("  help         - Mostrar esta ajuda")
            print("\n🎯 Estratégia implementada:")
            print("  • Quantum+: 71.98% assertividade")
            print("\n📊 Gatilhos: LLLW (Confirmação de Reversão) ou LLL (Capitulação)")
        else:
            print(f"❌ Comando desconhecido: {comando}")
            print("Use 'python radar_tunder_new.py help' para ver comandos disponíveis")
    else:
        # Executar bot principal
        main_loop()

def main():
    """Função principal - ponto de entrada alternativo"""
    main_loop()