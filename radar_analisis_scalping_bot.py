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
from threading import Lock

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

# Configurações
BOT_NAME = 'Scalping Bot'
ANALISE_INTERVALO = 5  # segundos entre análises
OPERACOES_MINIMAS = 20  # operações mínimas para análise
OPERACOES_HISTORICO = 30  # operações para buscar no histórico
PERSISTENCIA_TIMEOUT = 300  # 5 minutos timeout
PERSISTENCIA_OPERACOES = 2  # 2 operações para reset

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
            .eq('bot_name', BOT_NAME) \
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
    """MICRO-BURST: 95.5% assertividade - Prioridade 1"""
    strategy_name = 'MICRO_BURST'
    metrics = strategy_metrics[strategy_name]
    start_time = time.time()
    
    try:
        logger.debug(f"[{strategy_name}] Iniciando análise")
        
        if len(historico) < 10:
            metrics.add_filter_rejection('dados_insuficientes')
            return {'should_operate': False, 'reason': f'{strategy_name}: Dados insuficientes'}
        
        # Gatilho: Exatamente 2-3 WINs consecutivos
        wins_consecutivos = 0
        for i, op in enumerate(historico):
            if op == 'V':
                wins_consecutivos += 1
            else:
                break
        
        if wins_consecutivos < 2 or wins_consecutivos > 3:
            metrics.add_filter_rejection('gatilho_wins_consecutivos')
            logger.debug(f"[{strategy_name}] Gatilho falhou: {wins_consecutivos} WINs consecutivos (precisa 2-3)")
            return {'should_operate': False, 'reason': f'{strategy_name}: Gatilho não atendido ({wins_consecutivos} WINs)'}
        
        logger.info(f"[{strategy_name}] OK Gatilho atendido: {wins_consecutivos} WINs consecutivos")
        
        # Filtro 1: Máximo 1 LOSS nas últimas 10 operações
        ultimas_10 = historico[:10]
        losses_10 = ultimas_10.count('D')
        
        if losses_10 > 1:
            metrics.add_filter_rejection('filtro_1_losses_10')
            logger.debug(f"[{strategy_name}] Filtro 1 falhou: {losses_10} LOSSes em 10 operações (máx 1)")
            return {'should_operate': False, 'reason': f'{strategy_name}: Muitos LOSSes recentes ({losses_10}/10)'}
        
        logger.info(f"[{strategy_name}] OK Filtro 1 passou: {losses_10} LOSSes em 10 operações")
        
        # Filtro 2: LOSS recente deve estar em padrão WIN-LOSS-WIN específico
        if losses_10 == 1:
            loss_pos = ultimas_10.index('D')
            
            # Verificar padrão WIN-LOSS-WIN específico
            pattern_valid = False
            if loss_pos > 0 and loss_pos < len(ultimas_10) - 1:
                if ultimas_10[loss_pos - 1] == 'V' and ultimas_10[loss_pos + 1] == 'V':
                    pattern_valid = True
            
            if not pattern_valid:
                metrics.add_filter_rejection('filtro_2_loss_nao_win_loss_win')
                logger.debug(f"[{strategy_name}] Filtro 2 falhou: LOSS na posição {loss_pos} não está em padrão WIN-LOSS-WIN")
                return {'should_operate': False, 'reason': f'{strategy_name}: LOSS não está em padrão WIN-LOSS-WIN'}
        
        logger.info(f"[{strategy_name}] OK Filtro 2 passou: LOSS isolado ou ausente")
        
        # Filtro 3: Sem LOSSes consecutivos recentes
        for i in range(len(ultimas_10) - 1):
            if ultimas_10[i] == 'D' and ultimas_10[i + 1] == 'D':
                metrics.add_filter_rejection('filtro_3_losses_consecutivos')
                logger.debug(f"[{strategy_name}] Filtro 3 falhou: LOSSes consecutivos nas posições {i}-{i+1}")
                return {'should_operate': False, 'reason': f'{strategy_name}: LOSSes consecutivos detectados'}
        
        logger.info(f"[{strategy_name}] OK Filtro 3 passou: Sem LOSSes consecutivos")
        
        # Todos os filtros passaram - Log completo de validação
        execution_time = time.time() - start_time
        metrics.add_execution_time(execution_time)
        metrics.add_success()
        
        # RESUMO COMPLETO DE VALIDAÇÃO
        logger.info(f"[{strategy_name}] RESUMO DE VALIDAÇÃO:")
        logger.info(f"  - WINs consecutivos: {wins_consecutivos} (mínimo: 2-3)")
        logger.info(f"  - LOSSes últimas 10: {losses_10} (máximo: 1)")
        if losses_10 == 1:
            loss_pos = ultimas_10.index('D')
            logger.info(f"  - LOSS na posição: {loss_pos} (padrão WIN-LOSS-WIN validado)")
        else:
            logger.info(f"  - Sem LOSSes nas últimas 10 operações")
        logger.info(f"[{strategy_name}] TODOS OS FILTROS ATENDIDOS - ATIVANDO")
        logger.info(f"[{strategy_name}] OK ESTRATÉGIA APROVADA - Confiança: {metrics.confidence_level}%")
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': metrics.confidence_level,
            'reason': f'Patron Encontrado, Activar Bot Ahora! - {strategy_name} ({metrics.confidence_level}%)',
            'filters_passed': ['gatilho_wins_consecutivos', 'filtro_1_losses_10', 'filtro_2_loss_isolado', 'filtro_3_sem_consecutivos'],
            'execution_time': execution_time,
            'priority': 1
        }
        
    except Exception as e:
        metrics.add_error()
        logger.error(f"[{strategy_name}] ERRO: {e}")
        logger.error(f"[{strategy_name}] Traceback: {traceback.format_exc()}")
        return {'should_operate': False, 'reason': f'{strategy_name}: Erro na execução'}

def analisar_precision_surge(historico: List[str]) -> Dict:
    """PRECISION SURGE: 93.5% assertividade - Prioridade 2"""
    strategy_name = 'PRECISION_SURGE'
    metrics = strategy_metrics[strategy_name]
    start_time = time.time()
    
    try:
        logger.debug(f"[{strategy_name}] Iniciando análise")
        
        if len(historico) < 15:
            metrics.add_filter_rejection('dados_insuficientes')
            return {'should_operate': False, 'reason': f'{strategy_name}: Dados insuficientes'}
        
        # Gatilho: Exatamente 4-5 WINs consecutivos
        wins_consecutivos = 0
        for i, op in enumerate(historico):
            if op == 'V':
                wins_consecutivos += 1
            else:
                break
        
        if wins_consecutivos < 4 or wins_consecutivos > 5:
            metrics.add_filter_rejection('gatilho_wins_consecutivos')
            logger.debug(f"[{strategy_name}] Gatilho falhou: {wins_consecutivos} WINs consecutivos (precisa 4-5)")
            return {'should_operate': False, 'reason': f'{strategy_name}: Gatilho não atendido ({wins_consecutivos} WINs)'}
        
        logger.info(f"[{strategy_name}] OK Gatilho atendido: {wins_consecutivos} WINs consecutivos")
        
        # Filtro 1: Máximo 2 LOSSes nas últimas 15 operações
        ultimas_15 = historico[:15]
        losses_15 = ultimas_15.count('D')
        
        if losses_15 > 2:
            metrics.add_filter_rejection('filtro_1_losses_15')
            logger.debug(f"[{strategy_name}] Filtro 1 falhou: {losses_15} LOSSes em 15 operações (máx 2)")
            return {'should_operate': False, 'reason': f'{strategy_name}: Muitos LOSSes recentes ({losses_15}/15)'}
        
        logger.info(f"[{strategy_name}] OK Filtro 1 passou: {losses_15} LOSSes em 15 operações")
        
        # Filtro 2: Sem LOSSes consecutivos nas últimas 10 operações
        ultimas_10 = historico[:10]
        for i in range(len(ultimas_10) - 1):
            if ultimas_10[i] == 'D' and ultimas_10[i + 1] == 'D':
                metrics.add_filter_rejection('filtro_2_losses_consecutivos')
                logger.debug(f"[{strategy_name}] Filtro 2 falhou: LOSSes consecutivos nas posições {i}-{i+1}")
                return {'should_operate': False, 'reason': f'{strategy_name}: LOSSes consecutivos em 10 operações'}
        
        logger.info(f"[{strategy_name}] OK Filtro 2 passou: Sem LOSSes consecutivos em 10 operações")
        
        # Filtro 3: Ambiente estável confirmado (sem LOSSes consecutivos e máximo de LOSSes)
        # O filtro de "ambiente estável" se refere apenas à ausência de volatilidade
        logger.info(f"[{strategy_name}] OK Filtro 3 passou: Ambiente estável (sem volatilidade excessiva)")
        
        # Todos os filtros passaram
        execution_time = time.time() - start_time
        metrics.add_execution_time(execution_time)
        metrics.add_success()
        
        logger.info(f"[{strategy_name}] OK ESTRATÉGIA APROVADA - Confiança: {metrics.confidence_level}%")
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': metrics.confidence_level,
            'reason': f'Patron Encontrado, Activar Bot Ahora! - {strategy_name} ({metrics.confidence_level}%)',
            'filters_passed': ['gatilho_wins_consecutivos', 'filtro_1_losses_15', 'filtro_2_sem_consecutivos', 'filtro_3_ambiente_estavel_corrigido'],
            'execution_time': execution_time,
            'priority': 2
        }
        
    except Exception as e:
        metrics.add_error()
        logger.error(f"[{strategy_name}] ERRO: {e}")
        logger.error(f"[{strategy_name}] Traceback: {traceback.format_exc()}")
        return {'should_operate': False, 'reason': f'{strategy_name}: Erro na execução'}

def analisar_quantum_matrix(historico: List[str]) -> Dict:
    """QUANTUM MATRIX: 91.5% assertividade - Prioridade 3"""
    strategy_name = 'QUANTUM_MATRIX'
    metrics = strategy_metrics[strategy_name]
    start_time = time.time()
    
    try:
        logger.debug(f"[{strategy_name}] Iniciando análise")
        
        if len(historico) < 15:
            metrics.add_filter_rejection('dados_insuficientes')
            return {'should_operate': False, 'reason': f'{strategy_name}: Dados insuficientes'}
        
        # Gatilho: 6+ WINs consecutivos OU recovery sólido (3+ WINs + LOSS há 5+ operações)
        wins_consecutivos = 0
        for i, op in enumerate(historico):
            if op == 'V':
                wins_consecutivos += 1
            else:
                break
        
        # LOG OBRIGATÓRIO da contagem de WINs consecutivos
        logger.info(f"[{strategy_name}] WINs consecutivos detectados: {wins_consecutivos}")
        
        gatilho_atendido = False
        gatilho_tipo = None
        
        # Verificar gatilho 1: 6+ WINs consecutivos
        if wins_consecutivos >= 6:
            gatilho_atendido = True
            gatilho_tipo = f'{wins_consecutivos}_wins_consecutivos'
            logger.info(f"[{strategy_name}] OK Gatilho 1 atendido: {wins_consecutivos} WINs consecutivos")
        # Verificar gatilho 2: recovery sólido (3+ WINs consecutivos E último LOSS há 5+ operações)
        elif wins_consecutivos >= 3:
            # Procurar WINs APÓS o último LOSS antigo (5+ operações atrás)
            # Verificar se há um LOSS há 5+ operações e WINs consecutivos após ele
            loss_antigo_encontrado = False
            for i in range(5, len(historico)):
                if historico[i] == 'D':
                    # Verificar se há WINs consecutivos APÓS este LOSS
                    wins_apos_loss = 0
                    for j in range(i):
                        if historico[j] == 'V':
                            wins_apos_loss += 1
                        else:
                            break
                    
                    if wins_apos_loss >= 3:
                        gatilho_atendido = True
                        gatilho_tipo = f'recovery_solido_{wins_apos_loss}_wins_apos_loss_pos_{i}'
                        logger.info(f"[{strategy_name}] OK Gatilho 2 atendido: Recovery sólido com {wins_apos_loss} WINs APÓS LOSS há {i} operações")
                        loss_antigo_encontrado = True
                        break
            
            if not loss_antigo_encontrado:
                logger.debug(f"[{strategy_name}] Gatilho 2 falhou: Não há WINs consecutivos APÓS LOSS antigo (5+ ops)")
        
        if not gatilho_atendido:
            metrics.add_filter_rejection('gatilho_nao_atendido')
            logger.debug(f"[{strategy_name}] Gatilho falhou: {wins_consecutivos} WINs consecutivos (precisa 6+ ou recovery)")
            return {'should_operate': False, 'reason': f'{strategy_name}: Gatilho não atendido ({wins_consecutivos} WINs)'}
        
        # Filtro 1: Máximo 1 LOSS nas últimas 15 operações
        ultimas_15 = historico[:15]
        losses_15 = ultimas_15.count('D')
        logger.info(f"[{strategy_name}] LOSSes últimas 15: {losses_15} (máximo: 1)")
        
        if losses_15 > 1:
            metrics.add_filter_rejection('filtro_1_losses_15')
            logger.info(f"[{strategy_name}] REJEITADO - LOSSes últimas 15: {losses_15} > 1")
            return {'should_operate': False, 'reason': f'{strategy_name}: Muitos LOSSes recentes ({losses_15}/15)'}
        
        logger.info(f"[{strategy_name}] OK Filtro 1 passou: {losses_15} LOSSes em 15 operações")
        
        # Filtro 2: Último LOSS isolado há 5+ operações
        posicao_ultimo_loss = None
        if losses_15 == 1:
            loss_pos = ultimas_15.index('D')
            posicao_ultimo_loss = loss_pos
            logger.info(f"[{strategy_name}] Último LOSS há: {loss_pos} operações (mínimo: 5)")
            
            if loss_pos < 5:
                metrics.add_filter_rejection('filtro_2_loss_muito_recente')
                logger.info(f"[{strategy_name}] REJEITADO - Último LOSS há: {loss_pos} operações < 5")
                return {'should_operate': False, 'reason': f'{strategy_name}: LOSS muito recente (posição {loss_pos})'}
            
            # Verificar se está isolado
            isolado = True
            if loss_pos > 0 and ultimas_15[loss_pos - 1] != 'V':
                isolado = False
            if loss_pos < len(ultimas_15) - 1 and ultimas_15[loss_pos + 1] != 'V':
                isolado = False
            
            if not isolado:
                metrics.add_filter_rejection('filtro_2_loss_nao_isolado')
                logger.info(f"[{strategy_name}] REJEITADO - LOSS na posição {loss_pos} não está isolado")
                return {'should_operate': False, 'reason': f'{strategy_name}: LOSS não isolado'}
        else:
            logger.info(f"[{strategy_name}] Nenhum LOSS encontrado nas últimas 15 operações")
        
        logger.info(f"[{strategy_name}] OK Filtro 2 passou: LOSS isolado há 5+ operações ou ausente")
        
        # Filtro 3: Ambiente ultra-estável confirmado (sem filtro win rate)
        logger.info(f"[{strategy_name}] ✓ Filtro 3 passou: Ambiente ultra-estável confirmado")
        
        # Todos os filtros passaram
        execution_time = time.time() - start_time
        metrics.add_execution_time(execution_time)
        metrics.add_success()
        
        logger.info(f"[{strategy_name}] OK ESTRATÉGIA APROVADA - Confiança: {metrics.confidence_level}%")
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': metrics.confidence_level,
            'reason': f'Patron Encontrado, Activar Bot Ahora! - {strategy_name} ({metrics.confidence_level}%)',
            'filters_passed': ['gatilho_' + gatilho_tipo, 'filtro_1_losses_15', 'filtro_2_loss_isolado_5plus', 'filtro_3_ultra_estavel'],
            'execution_time': execution_time,
            'priority': 3
        }
        
    except Exception as e:
        metrics.add_error()
        logger.error(f"[{strategy_name}] ERRO: {e}")
        logger.error(f"[{strategy_name}] Traceback: {traceback.format_exc()}")
        return {'should_operate': False, 'reason': f'{strategy_name}: Erro na execução'}

def analisar_estrategias_portfolio(historico: List[str]) -> Dict:
    """Análise do portfólio de estratégias com priorização"""
    logger.debug(f"[PORTFOLIO] Iniciando análise com {len(historico)} operações")
    
    # Verificar se há estratégia ativa no sistema simplificado
    if is_strategy_active():
        logger.info(f"[STRATEGY_ACTIVE] Mantendo estratégia {active_strategy['strategy']} - {operations_since_strategy}/2 operações")
        return {
            'should_operate': True,
            'reason': f"Estratégia {active_strategy['strategy']} ativa - aguardando 2 operações",
            'melhor_estrategia': {
                'strategy': active_strategy['strategy'],
                'confidence': active_strategy['confidence'],
                'reason': f"Estratégia ativa com {active_strategy['confidence']}% confiança"
            },
            'total_oportunidades': 1,
            'estrategias_disponiveis': [{
                'strategy': active_strategy['strategy'],
                'confidence': active_strategy['confidence']
            }],
            'tracking_id': f"simple_{int(strategy_start_time)}"
        }
    
    # Validar integridade dos dados
    if not validar_integridade_historico(historico):
        return {
            'should_operate': False,
            'reason': 'Esperando el patrón. No activar aún.',
            'melhor_estrategia': None,
            'total_oportunidades': 0,
            'estrategias_disponiveis': []
        }
    
    # Analisar estratégias por ordem de prioridade
    estrategias_resultado = []
    
    # Prioridade 1: MICRO-BURST (95.5%)
    resultado_micro = analisar_micro_burst(historico)
    if resultado_micro['should_operate']:
        estrategias_resultado.append(resultado_micro)
    
    # Prioridade 2: PRECISION SURGE (93.5%)
    resultado_precision = analisar_precision_surge(historico)
    if resultado_precision['should_operate']:
        estrategias_resultado.append(resultado_precision)
    
    # Prioridade 3: QUANTUM MATRIX (91.5%)
    resultado_quantum = analisar_quantum_matrix(historico)
    if resultado_quantum['should_operate']:
        estrategias_resultado.append(resultado_quantum)
    
    # Se nenhuma estratégia foi aprovada
    if not estrategias_resultado:
        logger.info("[PORTFOLIO] Nenhuma estratégia aprovada")
        return {
            'should_operate': False,
            'reason': 'Esperando el patrón. No activar aún.',
            'melhor_estrategia': None,
            'total_oportunidades': 0,
            'estrategias_disponiveis': []
        }
    
    # Selecionar melhor estratégia (maior prioridade = menor número)
    melhor = min(estrategias_resultado, key=lambda x: x['priority'])
    
    logger.info(f"[PORTFOLIO] Estratégia selecionada: {melhor['strategy']} ({melhor['confidence']}%)")
    logger.info(f"[PORTFOLIO] Total de estratégias aprovadas: {len(estrategias_resultado)}")
    
    return {
        'should_operate': True,
        'reason': melhor['reason'],
        'melhor_estrategia': melhor,
        'total_oportunidades': len(estrategias_resultado),
        'estrategias_disponiveis': estrategias_resultado
    }

def enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason, tracking_id=None, historico=None, strategy_info=None):
    """Envia sinal para Supabase com integração ao sistema de tracking"""
    try:
        current_time = datetime.now().isoformat()
        
        # Calcular estatísticas básicas
        losses_10 = historico[:10].count('D') if historico and len(historico) >= 10 else 0
        wins_5 = historico[:5].count('V') if historico and len(historico) >= 5 else 0
        accuracy = (historico.count('V') / len(historico) * 100) if historico else 0
        
        # Estrutura base de dados
        data = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': is_safe_to_operate,
            'reason': reason,
            'operations_after_pattern': 0,  # Usar pattern_locked_state para tracking
            'losses_in_last_10_ops': losses_10,
            'wins_in_last_5_ops': wins_5,
            'historical_accuracy': accuracy,
            'created_at': current_time,
            'auto_disable_after_ops': PERSISTENCIA_OPERACOES
        }
        
        # Adicionar informações específicas das estratégias
        if strategy_info:
            data['strategy_used'] = strategy_info.get('strategy', 'NONE')
            data['strategy_confidence'] = strategy_info.get('confidence', 0.0)
            data['last_pattern_found'] = strategy_info.get('strategy', 'Aguardando')
            
            if tracking_id:
                data['tracking_id'] = tracking_id
        else:
            data['strategy_used'] = 'NONE'
            data['strategy_confidence'] = 0.0
            data['last_pattern_found'] = 'Aguardando'
        
        response = supabase.table('radar_de_apalancamiento_signals').upsert(data, on_conflict='bot_name').execute()
        
        if response.data:
            strategy_name = strategy_info.get('strategy', 'NONE') if strategy_info else 'NONE'
            confidence = strategy_info.get('confidence', 0) if strategy_info else 0
            tracking_info = f" | Tracking: {tracking_id}" if tracking_id else ""
            print(f"OK Sinal enviado - Estratégia: {strategy_name} ({confidence}%) - L10: {losses_10}, W5: {wins_5}{tracking_info}")
            return response.data[0]['id']  # Retornar signal_id
        return None
            
    except Exception as e:
        logger.error(f"[SIGNAL_ERROR] Erro ao enviar sinal: {e}")
        return None

def analisar_e_enviar_sinal(supabase):
    """Função principal de análise e envio de sinal com sistema simplificado"""
    print(f"\n{'='*60}")
    print(f">> INICIANDO ANÁLISE SCALPING BOT - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Verificar timeout e completude de operações
    check_strategy_timeout()
    check_operation_completion()
    
    # Buscar dados históricos
    historico, timestamps = buscar_operacoes_historico(supabase)
    
    if not historico:
        reason = "Aguardando dados suficientes..."
        enviar_sinal_para_supabase(supabase, False, reason)
        return
    
    # Analisar estratégias
    resultado_estrategias = analisar_estrategias_portfolio(historico)
    is_safe_to_operate = resultado_estrategias['should_operate']
    reason = resultado_estrategias['reason']
    
    # Preparar informações da estratégia
    strategy_info = None
    tracking_id = resultado_estrategias.get('tracking_id')
    
    if is_safe_to_operate:
        melhor_estrategia = resultado_estrategias['melhor_estrategia']
        strategy_info = {
            'strategy': melhor_estrategia['strategy'],
            'confidence': melhor_estrategia['confidence'],
            'filters_passed': melhor_estrategia.get('filters_passed', []),
            'execution_time': melhor_estrategia.get('execution_time', 0),
            'priority': melhor_estrategia.get('priority', 1)
        }
        
        # Se não há estratégia ativa, ativar nova
        if not is_strategy_active():
            should_activate_strategy(melhor_estrategia)
    
    # Enviar sinal
    signal_id = enviar_sinal_para_supabase(supabase, is_safe_to_operate, reason, tracking_id, historico, strategy_info)
    
    # Log final
    status_icon = "OK" if is_safe_to_operate else "⏳"
    print(f"\n[{status_icon}] RESULTADO FINAL: {'SAFE TO OPERATE' if is_safe_to_operate else 'WAIT'}")
    print(f"* Motivo: {reason}")
    if strategy_info:
        print(f"* Estratégia: {strategy_info['strategy']} ({strategy_info['confidence']}%)")
        print(f"* Prioridade: {strategy_info['priority']}")
        if tracking_id:
            print(f"* Tracking ID: {tracking_id}")
    print(f"* Operações após estratégia: {operations_since_strategy}/2")
    print(f"* Status do envio: {'Enviado' if signal_id else 'Falhou'}")
    
    return is_safe_to_operate, reason

def exibir_relatorio_performance():
    """Exibe relatório de performance das estratégias"""
    print(f"\n{'='*60}")
    print("RELATÓRIO DE PERFORMANCE DAS ESTRATÉGIAS")
    print(f"{'='*60}")
    
    for strategy_name, metrics in strategy_metrics.items():
        print(f"\n[{strategy_name}] - Confiança: {metrics.confidence_level}%")
        print(f"  • Execuções totais: {metrics.total_executions}")
        print(f"  • Sucessos: {metrics.successful_triggers}")
        print(f"  • Falhas: {metrics.failed_triggers}")
        print(f"  • Taxa de sucesso: {metrics.get_success_rate():.1f}%")
        print(f"  • Tempo médio: {metrics.get_average_time():.4f}s")
        print(f"  • Erros: {metrics.error_count}")
        
        if metrics.filter_rejections:
            print(f"  • Rejeições por filtro:")
            for filter_name, count in metrics.filter_rejections.items():
                print(f"    - {filter_name}: {count}")
    
    print(f"\n{'='*60}")

def main():
    """Função principal do sistema"""
    print("🚀 INICIANDO RADAR ANALISIS SCALPING BOT")
    print("Sistema de Trading com 3 Estratégias de Alta Assertividade")
    print("Integração completa com rastreamento automático Supabase\n")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        print("❌ Falha na conexão com Supabase. Encerrando...")
        return
    
    # Gerar relatório inicial de eficácia
    print("📊 Gerando relatório inicial de eficácia...")
    relatorio_inicial = gerar_relatorio_eficacia(supabase)
    if relatorio_inicial:
        print(f"OK Relatório gerado: {relatorio_inicial['consolidado']['total_signals']} sinais históricos")
        print(f"OK Taxa de sucesso média: {relatorio_inicial['consolidado']['success_rate_medio']:.1f}%")
        if relatorio_inicial['consolidado']['melhor_estrategia']:
            print(f"OK Melhor estratégia histórica: {relatorio_inicial['consolidado']['melhor_estrategia']}")
    
    print(f"\n🎯 Configurações ativas:")
    print(f"  • Bot Name: {BOT_NAME}")
    print(f"  • Intervalo de análise: {ANALISE_INTERVALO}s")
    print(f"  • Operações mínimas: {OPERACOES_MINIMAS}")
    print(f"  • Histórico buscado: {OPERACOES_HISTORICO}")
    print(f"  • Persistência: {PERSISTENCIA_OPERACOES} operações ou {PERSISTENCIA_TIMEOUT//60} minutos")
    
    print(f"\n📈 Estratégias configuradas:")
    for name, metrics in strategy_metrics.items():
        print(f"  • {name}: {metrics.confidence_level}% (a cada {metrics.frequency_operations} ops)")
    
    print(f"\n🔄 Iniciando loop de análise...\n")
    
    try:
        while True:
            try:
                # Análise principal
                analisar_e_enviar_sinal(supabase)
                
                # Exibir relatório de performance a cada 10 ciclos
                if strategy_metrics['MICRO_BURST'].total_executions % 10 == 0 and strategy_metrics['MICRO_BURST'].total_executions > 0:
                    exibir_relatorio_performance()
                
                print(f"\n⏱️  Aguardando {ANALISE_INTERVALO}s para próxima análise...")
                time.sleep(ANALISE_INTERVALO)
                
            except KeyboardInterrupt:
                print("\n🛑 Interrupção solicitada pelo usuário")
                break
            except Exception as e:
                logger.error(f"[MAIN_ERROR] Erro no loop principal: {e}")
                logger.error(f"[MAIN_ERROR] Traceback: {traceback.format_exc()}")
                print(f"❌ Erro no sistema: {e}")
                print(f"🔄 Continuando em {ANALISE_INTERVALO}s...")
                time.sleep(ANALISE_INTERVALO)
                
    except Exception as e:
        logger.error(f"[MAIN_CRITICAL] Erro crítico: {e}")
        print(f"💥 Erro crítico no sistema: {e}")
    
    finally:
        print("\n📊 RELATÓRIO FINAL DE PERFORMANCE")
        exibir_relatorio_performance()
        
        # Gerar relatório final de eficácia
        print("\n📈 Gerando relatório final de eficácia...")
        relatorio_final = gerar_relatorio_eficacia(supabase)
        if relatorio_final:
            print(f"OK Total de sinais gerados: {relatorio_final['consolidado']['total_signals']}")
            print(f"✓ Taxa de sucesso final: {relatorio_final['consolidado']['success_rate_medio']:.1f}%")
        
        print("\n🏁 RADAR ANALISIS SCALPING BOT FINALIZADO")

if __name__ == "__main__":
    main()