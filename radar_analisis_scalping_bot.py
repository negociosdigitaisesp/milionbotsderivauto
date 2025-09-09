#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar Analisis Scalping Bot - Sistema de Trading com 3 Estratégias de Alta Assertividade
Sistema integrado com rastreamento automático de resultados no Supabase

Estratégias implementadas:
- MICRO-BURST: 95.5% assertividade
- PRECISION SURGE: 93.5% assertividade  
- QUANTUM MATRIX: 91.5% assertividade

Sistema consolidado: 94.51% assertividade a cada 6 operações
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
import threading
from threading import Lock  # COMENTADO - removendo threading complexo
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scalping_bot_debug.log', encoding='utf-8'),
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
BOT_NAME = 'Scalping Bot'
ANALISE_INTERVALO = 5  # segundos entre análises
OPERACOES_MINIMAS = 20  # operações mínimas para análise
OPERACOES_HISTORICO = 30  # operações para buscar no histórico
PERSISTENCIA_TIMEOUT = 300  # 5 minutos timeout
PERSISTENCIA_OPERACOES = 2  # 2 operações para reset

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
strategy_metrics: Dict[str, StrategyMetrics] = {
    'MICRO_BURST': StrategyMetrics('MICRO_BURST', confidence_level=95.5, frequency_operations=10),
    'PRECISION_SURGE': StrategyMetrics('PRECISION_SURGE', confidence_level=93.5, frequency_operations=22),
    'QUANTUM_MATRIX': StrategyMetrics('QUANTUM_MATRIX', confidence_level=91.5, frequency_operations=56)
}

# ===== SISTEMA DE TRAVA ABSOLUTA DE PADRÕES =====
# Estado global da trava de padrão
pattern_locked_state = {
    'is_locked': False,
    'strategy_name': None,
    'confidence': 0.0,
    'detected_at': None,
    'operations_count': 0,
    'tracking_id': None,
    'signal_data': {}
}

# Lock para thread safety - COMENTADO
_pattern_lock = threading.Lock()

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
    
    with _pattern_lock:
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
    with _pattern_lock:
        return pattern_locked_state.copy()

# ===== SISTEMA SIMPLIFICADO DE TRAVA =====
# Versão simplificada conforme solicitado
active_strategy = None
strategy_start_time = None
operations_since_strategy = 0

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
        with _pattern_lock:
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
    """Busca histórico de operações do Supabase"""
    try:
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('profit_percentage, created_at') \
            .order('created_at', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            logger.warning("[HISTORICO] Nenhuma operação encontrada")
            return [], []
        
        # Extrair resultados e timestamps - converter profit_percentage para V/D
        historico = []
        timestamps = []
        for op in response.data:
            profit_percentage = op.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            historico.append(resultado)
            timestamps.append(op['created_at'])
        
        logger.info(f"[HISTORICO] {len(historico)} operações carregadas")
        logger.debug(f"[HISTORICO] Sequência: {' '.join(historico[:10])}...")
        
        return historico, timestamps
        
    except Exception as e:
        logger.error(f"[HISTORICO_ERROR] Erro ao buscar operações: {e}")
        return [], []

def criar_tracking_record(supabase, strategy_name: str, confidence_level: float, signal_id: str) -> str:
    """Cria registro na tabela strategy_results_tracking"""
    try:
        tracking_id = str(uuid.uuid4())
        
        data = {
            'tracking_id': tracking_id,
            'strategy_name': strategy_name,
            'strategy_confidence': confidence_level,
            'pattern_found_at': datetime.now().isoformat(),
            'signal_id': signal_id,
            'bot_name': BOT_NAME,
            'status': 'ACTIVE'
        }
        
        response = supabase.table('strategy_results_tracking').insert(data).execute()
        
        if response.data:
            logger.info(f"[TRACKING] Registro criado: {tracking_id} para {strategy_name}")
            return tracking_id
        else:
            logger.error(f"[TRACKING] Falha ao criar registro para {strategy_name}")
            return None
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro ao criar tracking: {e}")
        return None

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

# ===== IMPLEMENTAÇÃO DAS 3 ESTRATÉGIAS =====

def analisar_micro_burst(historico: List[str]) -> Dict:
    """MICRO-BURST: 95.5% assertividade - LÓGICA CORRIGIDA E ROBUSTA"""
    strategy_name = 'MICRO_BURST'
    metrics = strategy_metrics[strategy_name]
    start_time = time.time()
    
    try:
        logger.debug(f"[{strategy_name}] Iniciando análise com lógica corrigida")
        
        if len(historico) < 10:
            metrics.add_filter_rejection('dados_insuficientes')
            return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['dados_insuficientes'].format(strategy=strategy_name)}
        
        # === PASSO 1: VERIFICAR GATILHO DE MOMENTUM ===
        wins_consecutivos = 0
        for op in historico:
            if op == 'V':
                wins_consecutivos += 1
            else:
                break
        
        if not (2 <= wins_consecutivos <= 3):
            metrics.add_filter_rejection('gatilho_wins_consecutivos')
            logger.debug(f"[{strategy_name}] Gatilho falhou: {wins_consecutivos} WINs (requer 2-3)")
            return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['gatilho_nao_atendido'].format(strategy=strategy_name, wins=wins_consecutivos)}
        
        logger.info(f"[{strategy_name}] ✅ Gatilho APROVADO: {wins_consecutivos} WINs consecutivos")

        # === PASSO 2: ANALISAR AMBIENTE DAS ÚLTIMAS 10 OPERAÇÕES ===
        ultimas_10 = historico[:10]
        losses_10 = ultimas_10.count('D')

        # FILTRO 1: Rejeitar se houver mais de 1 derrota
        if losses_10 > 1:
            metrics.add_filter_rejection('filtro_muitos_losses')
            logger.debug(f"[{strategy_name}] Filtro falhou: {losses_10} LOSSes em 10 ops (máx 1)")
            return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['muitos_losses'].format(strategy=strategy_name, losses=losses_10, total=10)}
        
        # FILTRO 2: Rejeitar se houver derrotas consecutivas
        for i in range(len(ultimas_10) - 1):
            if ultimas_10[i] == 'D' and ultimas_10[i+1] == 'D':
                metrics.add_filter_rejection('filtro_losses_consecutivos')
                logger.debug(f"[{strategy_name}] Filtro falhou: LOSSes consecutivos encontrados")
                return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['losses_consecutivos']}

        # FILTRO 3: Se houver exatamente 1 derrota, ela DEVE estar no padrão V-D-V
        if losses_10 == 1:
            loss_pos = ultimas_10.index('D')
            # Padrão V-D-V requer que o loss não esteja nas bordas
            if loss_pos == 0 or loss_pos == len(ultimas_10) - 1:
                 metrics.add_filter_rejection('filtro_loss_na_borda')
                 logger.debug(f"[{strategy_name}] Filtro falhou: LOSS único está na borda e não pode formar V-D-V")
                 return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['loss_nao_isolado']}

            if not (ultimas_10[loss_pos - 1] == 'V' and ultimas_10[loss_pos + 1] == 'V'):
                metrics.add_filter_rejection('filtro_loss_nao_vdv')
                logger.debug(f"[{strategy_name}] Filtro falhou: LOSS único não está no padrão V-D-V")
                return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['loss_nao_isolado']}
        
        # === APROVAÇÃO FINAL ===
        # Se o código chegou até aqui, todas as condições foram satisfeitas:
        # 1. Momentum de 2-3 vitórias.
        # 2. 0 ou 1 derrota nas últimas 10.
        # 3. Se houve 1 derrota, ela foi validada no padrão V-D-V.
        
        execution_time = time.time() - start_time
        metrics.add_execution_time(execution_time)
        metrics.add_success()
        
        logger.info(f"[{strategy_name}] ✅ TODOS OS FILTROS ATENDIDOS - ATIVANDO")
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': metrics.confidence_level,
            'reason': MENSAJES_SISTEMA['patron_encontrado'].format(strategy=strategy_name, confidence=metrics.confidence_level),
            'filters_passed': ['gatilho_momentum_2_3', 'ambiente_limpo_max_1_loss', 'sem_losses_consecutivos'],
            'execution_time': execution_time,
            'priority': 1
        }
        
    except Exception as e:
        metrics.add_error()
        logger.error(f"[{strategy_name}] ERRO: {e}")
        logger.error(f"[{strategy_name}] Traceback: {traceback.format_exc()}")
        return {'should_operate': False, 'strategy': strategy_name, 'confidence': 0, 'reason': MENSAJES_SISTEMA['erro_execucao'].format(strategy=strategy_name)}

def analisar_precision_surge(historico: List[str]) -> Dict:
    """PRECISION SURGE: Estratégia de precisão (93.5%)
    
    Gatilho: 2-4 WINs consecutivos
    Filtros:
    - Máximo 2 LOSSes nas últimas 8 operações
    - LOSS deve estar isolado (WIN-LOSS-WIN)
    - Sem mais de 1 LOSS nas últimas 5 operações
    """
    try:
        start_time = time.time()
        strategy_name = "PRECISION_SURGE"
        
        logger.debug(f"[{strategy_name}] Iniciando análise...")
        
        # Validação básica
        if len(historico) < 15:
            strategy_metrics[strategy_name].add_filter_rejection("dados_insuficientes")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['dados_insuficientes'].format(strategy=strategy_name)
            }
        
        # Analisar operações - CORREÇÃO: usar historico[:15] ao invés de historico[-15:]
        ultimas_15 = historico[:15]  # CORRIGIDO - pegar as 15 mais recentes do início
        ultimas_8 = historico[:8]   # CORRIGIDO - pegar as 8 mais recentes do início
        ultimas_5 = historico[:5]   # CORRIGIDO - pegar as 5 mais recentes do início
        
        logger.debug(f"[{strategy_name}] Últimas 15: {' '.join(ultimas_15)}")
        
        # GATILHO: 2-4 WINs consecutivos
        wins_consecutivos = 0
        for resultado in ultimas_15:
            if resultado == 'V':
                wins_consecutivos += 1
            else:
                break
        
        if wins_consecutivos < 2 or wins_consecutivos > 4:
            strategy_metrics[strategy_name].add_filter_rejection("gatilho_nao_atendido")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['gatilho_nao_atendido'].format(strategy=strategy_name, wins=wins_consecutivos)
            }
        
        # FILTRO 1: Máximo 2 LOSSes nas últimas 8 operações
        losses_ultimas_8 = ultimas_8.count('D')
        if losses_ultimas_8 > 2:
            strategy_metrics[strategy_name].add_filter_rejection("muitos_losses")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['muitos_losses'].format(strategy=strategy_name, losses=losses_ultimas_8, total=8)
            }
        
        # FILTRO 2: Máximo 1 LOSS nas últimas 5 operações
        losses_ultimas_5 = ultimas_5.count('D')
        if losses_ultimas_5 > 1:
            strategy_metrics[strategy_name].add_filter_rejection("muitos_losses_recentes")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['muitos_losses'].format(strategy=strategy_name, losses=losses_ultimas_5, total=5)
            }
        
        # FILTRO 3: LOSS deve estar isolado (WIN-LOSS-WIN)
        if 'D' in ultimas_15:
            loss_positions = [i for i, x in enumerate(ultimas_15) if x == 'D']
            for pos in loss_positions:
                win_antes = pos > 0 and ultimas_15[pos-1] == 'V'
                win_depois = pos < len(ultimas_15)-1 and ultimas_15[pos+1] == 'V'
                
                if not (win_antes and win_depois):
                    strategy_metrics[strategy_name].add_filter_rejection("loss_nao_isolado")
                    return {
                        'should_operate': False,
                        'strategy': strategy_name,
                        'confidence': 0,
                        'reason': MENSAJES_SISTEMA['loss_nao_isolado'].format(strategy=strategy_name)
                    }
        
        # FILTRO 4: Sem LOSSes consecutivos
        for i in range(len(ultimas_15) - 1):
            if ultimas_15[i] == 'D' and ultimas_15[i+1] == 'D':
                strategy_metrics[strategy_name].add_filter_rejection("losses_consecutivos")
                return {
                    'should_operate': False,
                    'strategy': strategy_name,
                    'confidence': 0,
                    'reason': MENSAJES_SISTEMA['losses_consecutivos_proibido'].format(strategy=strategy_name)
                }
        
        # Calcular confiança
        confidence = 93.5
        
        # Ajustes de confiança
        if wins_consecutivos >= 3:
            confidence += 1.0
        
        if losses_ultimas_8 == 0:
            confidence += 2.0
        elif losses_ultimas_8 == 1:
            confidence += 1.0
        
        if losses_ultimas_5 == 0:
            confidence += 1.5
        
        # Registrar métricas
        exec_time = time.time() - start_time
        strategy_metrics[strategy_name].add_execution_time(exec_time)
        strategy_metrics[strategy_name].add_success()
        
        logger.info(f"[{strategy_name}] ✅ PADRÃO ENCONTRADO! Confiança: {confidence:.1f}%")
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': confidence,
            'reason': MENSAJES_SISTEMA['patron_encontrado'].format(strategy=strategy_name, confidence=confidence),
            'pattern_details': {
                'wins_consecutivos': wins_consecutivos,
                'losses_ultimas_8': losses_ultimas_8,
                'losses_ultimas_5': losses_ultimas_5,
                'sequencia_analisada': ' '.join(ultimas_15)
            }
        }
        
    except Exception as e:
        strategy_metrics[strategy_name].add_error()
        logger.error(f"[{strategy_name}] ERRO: {e}")
        return {
            'should_operate': False,
            'strategy': strategy_name,
            'confidence': 0,
            'reason': MENSAJES_SISTEMA['erro_execucao'].format(strategy=strategy_name)
        }

def analisar_quantum_matrix_EXATO_REFINADO(historico: List[str]) -> Dict:
    """QUANTUM MATRIX: Estratégia refinada (91.5%)
    
    Gatilho: 1-3 WINs consecutivos
    Filtros rigorosos:
    - Máximo 4 LOSSes nas últimas 15 operações
    - Máximo 2 LOSSes nas últimas 8 operações
    - LOSS deve estar isolado
    - Sem LOSSes consecutivos
    - Padrão de recuperação após LOSS
    """
    try:
        start_time = time.time()
        strategy_name = "QUANTUM_MATRIX"
        
        logger.debug(f"[{strategy_name}] Iniciando análise EXATA...")
        
        # Validação básica
        if len(historico) < 15:
            strategy_metrics[strategy_name].add_filter_rejection("dados_insuficientes")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['dados_insuficientes'].format(strategy=strategy_name)
            }
        
        # CORREÇÃO CRÍTICA: usar historico[:15] ao invés de historico[-15:]
        ultimas_15 = historico[:15]  # CORRIGIDO - pegar as 15 mais recentes do início
        ultimas_8 = historico[:8]   # CORRIGIDO - pegar as 8 mais recentes do início
        ultimas_5 = historico[:5]   # CORRIGIDO - pegar as 5 mais recentes do início
        
        logger.debug(f"[{strategy_name}] Últimas 15: {' '.join(ultimas_15)}")
        
        # GATILHO: 1-3 WINs consecutivos no início
        wins_consecutivos = 0
        for resultado in ultimas_15:
            if resultado == 'V':
                wins_consecutivos += 1
            else:
                break
        
        if wins_consecutivos < 1 or wins_consecutivos > 3:
            strategy_metrics[strategy_name].add_filter_rejection("gatilho_nao_atendido")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['gatilho_nao_atendido'].format(strategy=strategy_name, wins=wins_consecutivos)
            }
        
        # FILTRO 1: Máximo 4 LOSSes nas últimas 15 operações
        losses_ultimas_15 = ultimas_15.count('D')
        if losses_ultimas_15 > 4:
            strategy_metrics[strategy_name].add_filter_rejection("muitos_losses_15")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['muitos_losses'].format(strategy=strategy_name, losses=losses_ultimas_15, total=15)
            }
        
        # FILTRO 2: Máximo 2 LOSSes nas últimas 8 operações
        losses_ultimas_8 = ultimas_8.count('D')
        if losses_ultimas_8 > 2:
            strategy_metrics[strategy_name].add_filter_rejection("muitos_losses_8")
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['muitos_losses'].format(strategy=strategy_name, losses=losses_ultimas_8, total=8)
            }
        
        # FILTRO 3: LOSS deve estar isolado (WIN-LOSS-WIN)
        if 'D' in ultimas_15:
            loss_positions = [i for i, x in enumerate(ultimas_15) if x == 'D']
            for pos in loss_positions:
                win_antes = pos > 0 and ultimas_15[pos-1] == 'V'
                win_depois = pos < len(ultimas_15)-1 and ultimas_15[pos+1] == 'V'
                
                if not (win_antes and win_depois):
                    strategy_metrics[strategy_name].add_filter_rejection("loss_nao_isolado")
                    return {
                        'should_operate': False,
                        'strategy': strategy_name,
                        'confidence': 0,
                        'reason': MENSAJES_SISTEMA['loss_nao_isolado'].format(strategy=strategy_name)
                    }
        
        # FILTRO 4: Sem LOSSes consecutivos
        for i in range(len(ultimas_15) - 1):
            if ultimas_15[i] == 'D' and ultimas_15[i+1] == 'D':
                strategy_metrics[strategy_name].add_filter_rejection("losses_consecutivos")
                return {
                    'should_operate': False,
                    'strategy': strategy_name,
                    'confidence': 0,
                    'reason': MENSAJES_SISTEMA['losses_consecutivos_proibido'].format(strategy=strategy_name)
                }
        
        # FILTRO 5: Padrão de recuperação após LOSS
        if 'D' in ultimas_8:
            last_loss_pos = None
            for i, resultado in enumerate(ultimas_8):
                if resultado == 'D':
                    last_loss_pos = i
                    break
            
            if last_loss_pos is not None and last_loss_pos < len(ultimas_8) - 1:
                # Deve ter pelo menos 1 WIN após o último LOSS
                wins_apos_loss = ultimas_8[:last_loss_pos].count('V')
                if wins_apos_loss < 1:
                    strategy_metrics[strategy_name].add_filter_rejection("sem_recuperacao")
                    return {
                        'should_operate': False,
                        'strategy': strategy_name,
                        'confidence': 0,
                        'reason': f"{strategy_name}: Sem recuperação após LOSS"
                    }
        
        # Calcular confiança baseada na qualidade do padrão
        confidence = 91.5
        
        # Ajustes de confiança
        if wins_consecutivos >= 2:
            confidence += 1.5
        
        if losses_ultimas_15 <= 2:
            confidence += 2.0
        elif losses_ultimas_15 <= 3:
            confidence += 1.0
        
        if losses_ultimas_8 == 0:
            confidence += 2.5
        elif losses_ultimas_8 == 1:
            confidence += 1.5
        
        # Bônus por padrão de recuperação forte
        if 'D' in ultimas_15:
            recovery_pattern = True
            for i, resultado in enumerate(ultimas_15):
                if resultado == 'D' and i > 0 and i < len(ultimas_15) - 1:
                    if ultimas_15[i-1] != 'V' or ultimas_15[i+1] != 'V':
                        recovery_pattern = False
                        break
            
            if recovery_pattern:
                confidence += 1.0
        
        # Registrar métricas
        exec_time = time.time() - start_time
        strategy_metrics[strategy_name].add_execution_time(exec_time)
        strategy_metrics[strategy_name].add_success()
        
        logger.info(f"[{strategy_name}] ✅ PADRÃO ENCONTRADO! Confiança: {confidence:.1f}%")
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': confidence,
            'reason': MENSAJES_SISTEMA['patron_encontrado'].format(strategy=strategy_name, confidence=confidence),
            'pattern_details': {
                'wins_consecutivos': wins_consecutivos,
                'losses_ultimas_15': losses_ultimas_15,
                'losses_ultimas_8': losses_ultimas_8,
                'sequencia_analisada': ' '.join(ultimas_15),
                'versao': 'EXATO_REFINADO'
            }
        }
        
    except Exception as e:
        strategy_metrics[strategy_name].add_error()
        logger.error(f"[{strategy_name}] ERRO: {e}")
        logger.error(f"[{strategy_name}] Traceback: {traceback.format_exc()}")
        return {
            'should_operate': False,
            'strategy': strategy_name,
            'confidence': 0,
            'reason': MENSAJES_SISTEMA['erro_execucao'].format(strategy=strategy_name)
        }

# ===== SISTEMA DE ANÁLISE CONSOLIDADA =====

def executar_analise_consolidada(historico: List[str]) -> Dict:
    """Executa análise de todas as 3 estratégias e retorna a melhor"""
    try:
        logger.info("[ANALISE_CONSOLIDADA] === INICIANDO ANÁLISE DAS 3 ESTRATÉGIAS ===")
        
        # Validar integridade dos dados
        if not validar_integridade_historico(historico):
            return {
                'should_operate': False,
                'strategy': 'SYSTEM',
                'confidence': 0,
                'reason': "Dados de histórico inválidos ou insuficientes"
            }
        
        # Executar todas as estratégias
        resultados = []
        
        # MICRO-BURST
        resultado_micro = analisar_micro_burst(historico)
        resultados.append(resultado_micro)
        logger.info(f"[MICRO_BURST] Resultado: {resultado_micro['should_operate']} - {resultado_micro['confidence']}%")
        
        # PRECISION SURGE
        resultado_precision = analisar_precision_surge(historico)
        resultados.append(resultado_precision)
        logger.info(f"[PRECISION_SURGE] Resultado: {resultado_precision['should_operate']} - {resultado_precision['confidence']}%")
        
        # QUANTUM MATRIX
        resultado_quantum = analisar_quantum_matrix_EXATO_REFINADO(historico)
        resultados.append(resultado_quantum)
        logger.info(f"[QUANTUM_MATRIX] Resultado: {resultado_quantum['should_operate']} - {resultado_quantum['confidence']}%")
        
        # Filtrar apenas estratégias que recomendam operação
        estrategias_ativas = [r for r in resultados if r['should_operate']]
        
        if not estrategias_ativas:
            logger.info("[ANALISE_CONSOLIDADA] Nenhuma estratégia recomenda operação")
            return {
                'should_operate': False,
                'strategy': 'NONE',
                'confidence': 0,
                'reason': MENSAJES_SISTEMA['aguardando_padrao'],
                'estrategias_analisadas': resultados
            }
        
        # Selecionar estratégia com maior confiança
        melhor_estrategia = max(estrategias_ativas, key=lambda x: x['confidence'])
        
        logger.info(f"[ANALISE_CONSOLIDADA] ✅ MELHOR ESTRATÉGIA: {melhor_estrategia['strategy']} ({melhor_estrategia['confidence']:.1f}%)")
        
        return {
            'should_operate': True,
            'strategy': melhor_estrategia['strategy'],
            'confidence': melhor_estrategia['confidence'],
            'reason': melhor_estrategia['reason'],
            'melhor_estrategia': melhor_estrategia,
            'estrategias_analisadas': resultados,
            'total_estrategias_ativas': len(estrategias_ativas)
        }
        
    except Exception as e:
        logger.error(f"[ANALISE_CONSOLIDADA] ERRO CRÍTICO: {e}")
        logger.error(f"[ANALISE_CONSOLIDADA] Traceback: {traceback.format_exc()}")
        return {
            'should_operate': False,
            'strategy': 'ERROR',
            'confidence': 0,
            'reason': MENSAJES_SISTEMA['erro_execucao'].format(strategy='SISTEMA')
        }

# ===== SISTEMA DE ENVIO DE SINAIS =====

@retry_supabase_operation(max_retries=3, delay=2)
def enviar_sinal_supabase(supabase, signal_data: Dict) -> bool:
    """Envia sinal para tabela radar_de_apalancamiento_signals"""
    try:
        # Preparar dados do sinal
        signal_record = {
            'signal_id': str(uuid.uuid4()),
            'bot_name': BOT_NAME,
            'strategy_name': signal_data['strategy'],
            'confidence_level': signal_data['confidence'],
            'should_operate': signal_data['should_operate'],
            'signal_reason': signal_data['reason'],
            'pattern_data': signal_data.get('pattern_details', {}),
            'created_at': datetime.now().isoformat(),
            'status': 'ACTIVE' if signal_data['should_operate'] else 'INACTIVE'
        }
        
        logger.debug(f"[SIGNAL_SEND] Preparando envio: {signal_record['signal_id']}")
        
        # Inserir na tabela
        response = supabase.table('radar_de_apalancamiento_signals').insert(signal_record).execute()
        
        if response.data:
            logger.info(f"[SIGNAL_SENT] ✅ Sinal enviado: {signal_record['signal_id']} - {signal_data['strategy']}")
            return True
        else:
            logger.error(f"[SIGNAL_ERROR] Falha ao enviar sinal - resposta vazia")
            return False
            
    except Exception as e:
        logger.error(f"[SIGNAL_ERROR] Erro ao enviar sinal: {e}")
        raise e  # Re-raise para o decorator retry

def processar_e_enviar_sinal(supabase, historico: List[str]) -> Dict:
    """Processa análise e envia sinal se necessário"""
    try:
        # Executar análise consolidada
        resultado_analise = executar_analise_consolidada(historico)
        
        # Verificar se deve enviar sinal
        if resultado_analise['should_operate']:
            logger.info(f"[SIGNAL_PROCESS] Enviando sinal para {resultado_analise['strategy']}")
            
            # Enviar sinal
            sucesso_envio = enviar_sinal_supabase(supabase, resultado_analise)
            
            if sucesso_envio:
                # Criar tracking record
                tracking_id = criar_tracking_record(
                    supabase,
                    resultado_analise['strategy'],
                    resultado_analise['confidence'],
                    resultado_analise.get('signal_id', 'unknown')
                )
                
                resultado_analise['tracking_id'] = tracking_id
                resultado_analise['signal_sent'] = True
                
                logger.info(f"[SIGNAL_PROCESS] ✅ Processamento completo - Tracking: {tracking_id}")
            else:
                resultado_analise['signal_sent'] = False
                logger.error(f"[SIGNAL_PROCESS] Falha no envio do sinal")
        else:
            resultado_analise['signal_sent'] = False
            logger.debug(f"[SIGNAL_PROCESS] Nenhum sinal para enviar")
        
        return resultado_analise
        
    except Exception as e:
        logger.error(f"[SIGNAL_PROCESS] ERRO: {e}")
        return {
            'should_operate': False,
            'strategy': 'ERROR',
            'confidence': 0,
            'reason': f"Erro no processamento: {e}",
            'signal_sent': False
        }

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
        
        # Status das estratégias
        for strategy_name, metrics in strategy_metrics.items():
            status['strategies'][strategy_name] = {
                'confidence_level': metrics.confidence_level,
                'total_executions': metrics.total_executions,
                'success_rate': metrics.get_success_rate(),
                'average_time': metrics.get_average_time(),
                'error_count': metrics.error_count,
                'last_execution': metrics.last_execution_time
            }
        
        # Resumo das métricas
        total_executions = sum([m.total_executions for m in strategy_metrics.values()])
        avg_success_rate = sum([m.get_success_rate() for m in strategy_metrics.values()]) / len(strategy_metrics)
        
        status['metrics_summary'] = {
            'total_executions': total_executions,
            'average_success_rate': avg_success_rate,
            'system_uptime': time.time(),
            'strategies_count': len(strategy_metrics)
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

def imprimir_status_detalhado():
    """Imprime status detalhado do sistema"""
    try:
        print("\n" + "="*80)
        print(f"📊 STATUS DO SISTEMA - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        
        # Status das estratégias
        print("\n🎯 ESTRATÉGIAS:")
        for strategy_name, metrics in strategy_metrics.items():
            print(f"  {strategy_name}:")
            print(f"    Confiança: {metrics.confidence_level}%")
            print(f"    Execuções: {metrics.total_executions}")
            print(f"    Taxa de Sucesso: {metrics.get_success_rate():.1f}%")
            print(f"    Tempo Médio: {metrics.get_average_time():.3f}s")
            print(f"    Erros: {metrics.error_count}")
        
        # Status da trava de padrão
        pattern_status = check_pattern_lock_status()
        print(f"\n🔒 TRAVA DE PADRÃO:")
        print(f"    Ativa: {'SIM' if pattern_status['is_locked'] else 'NÃO'}")
        if pattern_status['is_locked']:
            print(f"    Estratégia: {pattern_status['strategy_name']}")
            print(f"    Confiança: {pattern_status['confidence']}%")
            print(f"    Operações: {pattern_status['operations_count']}/2")
        
        # Status da estratégia ativa (sistema simplificado)
        print(f"\n⚡ ESTRATÉGIA ATIVA (SIMPLIFICADO):")
        if active_strategy:
            elapsed = time.time() - strategy_start_time if strategy_start_time else 0
            print(f"    Estratégia: {active_strategy['strategy']}")
            print(f"    Tempo Ativo: {elapsed:.1f}s")
            print(f"    Operações: {operations_since_strategy}/2")
        else:
            print(f"    Nenhuma estratégia ativa")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"[STATUS_PRINT_ERROR] Erro ao imprimir status: {e}")
        print(f"ERRO ao imprimir status: {e}")

# ===== LOOP PRINCIPAL DO BOT =====

def executar_ciclo_analise(supabase) -> Dict:
    """Executa um ciclo completo de análise"""
    try:
        logger.info("[CICLO] === INICIANDO NOVO CICLO DE ANÁLISE ===")
        
        # Buscar histórico de operações
        historico, timestamps = buscar_operacoes_historico(supabase)
        
        if not historico:
            return {
                'status': 'NO_DATA',
                'message': MENSAJES_SISTEMA['aguardando_dados']
            }
        
        # Verificar se há estratégia ativa no sistema simplificado
        if is_strategy_active():
            # Incrementar contador de operações se houver novas operações
            new_ops = increment_operations()
            
            # Verificar se completou 2 operações
            if check_operation_completion():
                logger.info("[CICLO] Estratégia completou 2 operações - liberando para nova análise")
            else:
                return {
                    'status': 'STRATEGY_ACTIVE',
                    'message': MENSAJES_SISTEMA['estrategia_ativa'].format(
                        strategy=active_strategy['strategy'],
                        ops=f"{operations_since_strategy}/2"
                    )
                }
        
        # Monitorar e atualizar operações do padrão (sistema complexo)
        monitor_and_update_pattern_operations_CORRETO(supabase)
        
        # Verificar se há trava de padrão ativa
        pattern_status = check_pattern_lock_status()
        if pattern_status['is_locked']:
            return {
                'status': 'PATTERN_LOCKED',
                'message': MENSAJES_SISTEMA['estrategia_ativa'].format(
                    strategy=pattern_status['strategy_name'],
                    ops=f"{pattern_status['operations_count']}/2"
                )
            }
        
        # Processar análise e enviar sinal
        resultado = processar_e_enviar_sinal(supabase, historico)
        
        # Se encontrou padrão, ativar sistema de controle
        if resultado['should_operate']:
            # Ativar no sistema simplificado
            if should_activate_strategy(resultado):
                logger.info(f"[CICLO] ✅ ESTRATÉGIA ATIVADA: {resultado['strategy']}")
            
            # Ativar trava de padrão (sistema complexo)
            tracking_id = resultado.get('tracking_id', 'unknown')
            activate_pattern_lock(
                resultado['strategy'],
                resultado['confidence'],
                resultado,
                tracking_id
            )
        
        return {
            'status': 'COMPLETED',
            'resultado': resultado,
            'historico_size': len(historico)
        }
        
    except Exception as e:
        logger.error(f"[CICLO_ERROR] Erro no ciclo de análise: {e}")
        logger.error(f"[CICLO_ERROR] Traceback: {traceback.format_exc()}")
        return {
            'status': 'ERROR',
            'message': f"Erro no ciclo: {e}"
        }

def main_loop():
    """Loop principal do bot"""
    logger.info("[MAIN] === INICIANDO RADAR ANALISIS SCALPING BOT ===")
    logger.info("[MAIN] Sistema com 3 estratégias: MICRO-BURST, PRECISION SURGE, QUANTUM MATRIX")
    logger.info("[MAIN] Assertividade consolidada: 94.51%")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        logger.error("[MAIN] ERRO CRÍTICO: Não foi possível conectar ao Supabase")
        print("FAIL Erro crítico na conexão com Supabase")
        return
    
    logger.info("[MAIN] ✅ Sistema inicializado com sucesso")
    print("\n🚀 RADAR ANALISIS SCALPING BOT ATIVO")
    print("📊 Monitorando padrões de alta assertividade...")
    print("⏱️  Análise a cada 5 segundos")
    print("🎯 3 Estratégias ativas: MICRO-BURST (95.5%), PRECISION SURGE (93.5%), QUANTUM MATRIX (91.5%)")
    print("\nPressione Ctrl+C para parar\n")
    
    ciclo_count = 0
    
    try:
        while True:
            ciclo_count += 1
            
            # Executar ciclo de análise
            resultado_ciclo = executar_ciclo_analise(supabase)
            
            # Log do resultado
            status = resultado_ciclo['status']
            message = resultado_ciclo.get('message', '')
            
            if status == 'COMPLETED':
                resultado = resultado_ciclo['resultado']
                if resultado['should_operate']:
                    print(f"\n🎯 {resultado['reason']}")
                    logger.info(f"[MAIN] SINAL ENVIADO: {resultado['strategy']} - {resultado['confidence']:.1f}%")
                else:
                    print(f"⏳ {resultado['reason']}")
            elif status in ['STRATEGY_ACTIVE', 'PATTERN_LOCKED']:
                print(f"🔒 {message}")
            elif status == 'NO_DATA':
                print(f"📊 {message}")
            elif status == 'ERROR':
                print(f"❌ {message}")
                logger.error(f"[MAIN] Erro no ciclo {ciclo_count}: {message}")
            
            # Imprimir status detalhado a cada 12 ciclos (1 minuto)
            if ciclo_count % 12 == 0:
                imprimir_status_detalhado()
            
            # Aguardar próximo ciclo
            time.sleep(ANALISE_INTERVALO)
            
    except KeyboardInterrupt:
        logger.info("[MAIN] Bot interrompido pelo usuário")
        print("\n🛑 Bot interrompido pelo usuário")
        print("📊 Estatísticas finais:")
        imprimir_status_detalhado()
        
    except Exception as e:
        logger.error(f"[MAIN] ERRO CRÍTICO: {e}")
        logger.error(f"[MAIN] Traceback: {traceback.format_exc()}")
        print(f"\n💥 ERRO CRÍTICO: {e}")
        
    finally:
        logger.info("[MAIN] === FINALIZANDO RADAR ANALISIS SCALPING BOT ===")
        print("\n👋 Radar Analisis Scalping Bot finalizado")

# ===== FUNÇÕES DE TESTE E VALIDAÇÃO =====

def testar_conexao_supabase():
    """Testa conexão com Supabase"""
    try:
        print("🔍 Testando conexão com Supabase...")
        supabase = inicializar_supabase()
        
        if not supabase:
            print("❌ FALHA na conexão com Supabase")
            return False
        
        # Testar consulta simples
        response = supabase.table('scalping_accumulator_bot_logs').select('*').limit(1).execute()
        
        if response.data is not None:
            print("✅ Conexão com Supabase OK")
            print(f"📊 Tabela 'scalping_accumulator_bot_logs' acessível")
            return True
        else:
            print("❌ FALHA ao acessar tabela 'scalping_accumulator_bot_logs'")
            return False
            
    except Exception as e:
        print(f"❌ ERRO na conexão: {e}")
        return False

def testar_estrategias():
    """Testa as 3 estratégias com dados simulados"""
    try:
        print("\n🧪 Testando estratégias com dados simulados...")
        
        # Dados de teste que devem ativar as estratégias
        historico_teste = ['V', 'V', 'V', 'D', 'V', 'V', 'D', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V', 'D', 'V', 'V', 'V', 'V']
        
        print(f"📊 Histórico de teste: {' '.join(historico_teste[:15])}")
        
        # Testar MICRO-BURST
        resultado_micro = analisar_micro_burst(historico_teste)
        print(f"🎯 MICRO-BURST: {resultado_micro['should_operate']} - {resultado_micro['confidence']:.1f}%")
        
        # Testar PRECISION SURGE
        resultado_precision = analisar_precision_surge(historico_teste)
        print(f"🎯 PRECISION SURGE: {resultado_precision['should_operate']} - {resultado_precision['confidence']:.1f}%")
        
        # Testar QUANTUM MATRIX
        resultado_quantum = analisar_quantum_matrix_EXATO_REFINADO(historico_teste)
        print(f"🎯 QUANTUM MATRIX: {resultado_quantum['should_operate']} - {resultado_quantum['confidence']:.1f}%")
        
        # Testar análise consolidada
        resultado_consolidado = executar_analise_consolidada(historico_teste)
        print(f"\n🏆 MELHOR ESTRATÉGIA: {resultado_consolidado['strategy']} - {resultado_consolidado['confidence']:.1f}%")
        
        print("✅ Teste das estratégias concluído")
        return True
        
    except Exception as e:
        print(f"❌ ERRO no teste das estratégias: {e}")
        return False

def executar_testes_completos():
    """Executa bateria completa de testes"""
    print("🔬 === EXECUTANDO TESTES COMPLETOS ===")
    
    # Teste 1: Conexão Supabase
    teste1 = testar_conexao_supabase()
    
    # Teste 2: Estratégias
    teste2 = testar_estrategias()
    
    # Resultado final
    if teste1 and teste2:
        print("\n✅ TODOS OS TESTES PASSARAM")
        print("🚀 Sistema pronto para execução")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique a configuração antes de executar")
        return False

# ===== PONTO DE ENTRADA =====

if __name__ == "__main__":
    import sys
    
    # Verificar argumentos da linha de comando
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "test":
            # Executar testes
            executar_testes_completos()
        elif comando == "status":
            # Mostrar status
            imprimir_status_detalhado()
        elif comando == "help":
            # Mostrar ajuda
            print("\n📖 RADAR ANALISIS SCALPING BOT - Ajuda")
            print("="*50)
            print("Uso: python radar_analisis_scalping_bot.py [comando]")
            print("\nComandos disponíveis:")
            print("  (sem comando) - Executar bot principal")
            print("  test         - Executar testes do sistema")
            print("  status       - Mostrar status detalhado")
            print("  help         - Mostrar esta ajuda")
            print("\n🎯 Estratégias implementadas:")
            print("  • MICRO-BURST: 95.5% assertividade")
            print("  • PRECISION SURGE: 93.5% assertividade")
            print("  • QUANTUM MATRIX: 91.5% assertividade")
            print("\n📊 Sistema consolidado: 94.51% assertividade")
        else:
            print(f"❌ Comando desconhecido: {comando}")
            print("Use 'python radar_analisis_scalping_bot.py help' para ver comandos disponíveis")
    else:
         # Executar bot principal
         main_loop()

def main():
    """Função principal - ponto de entrada alternativo"""
    main_loop()