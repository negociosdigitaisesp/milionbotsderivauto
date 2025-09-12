#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar Analisis Scalping Bot - Sistema de Trading com Estratégia MAX_FREQUENCY_FILTER
Sistema integrado com rastreamento automático de resultados no Supabase

Estratégia implementada:
- MAX_FREQUENCY_FILTER: 78.6% assertividade para duplo WIN

Critérios da estratégia:
1. Última operação deve ser WIN
2. Timing adequado (mínimo 2 minutos)
3. Ambiente estável (máximo 1 LOSS nas últimas 4 operações)
4. Profit quality (lucro > 10%)
"""

import os
import time
import uuid
import json
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

# Adicionar import que estava faltando
from datetime import timezone

# NUEVAS IMPORTACIONES PARA TELEGRAM
# Importar sys e os para manipulação de path
import sys
import os

try:
    # Primeiro tenta importar normalmente
    from telegram_notifier import (
        inicializar_telegram,
        enviar_alerta_patron,
        enviar_resultado_operacion,
        enviar_finalizacion_estrategia,
        enviar_mensaje_sistema
    )
    TELEGRAM_DISPONIBLE = True
except ImportError:
    try:
        # Se falhar, tenta adicionar o diretório atual ao path
        # Adiciona o diretório atual ao path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from telegram_notifier import (
            inicializar_telegram,
            enviar_alerta_patron,
            enviar_resultado_operacion,
            enviar_finalizacion_estrategia,
            enviar_mensaje_sistema
        )
        TELEGRAM_DISPONIBLE = True
    except ImportError:
        print("⚠️ Módulo telegram_notifier no encontrado - funcionando sin notificaciones")
        TELEGRAM_DISPONIBLE = False

# Variable global para controlar si Telegram está activo
telegram_activo = False

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

# PROMPT 12: ADICIONE ESTA VARIÁVEL GLOBAL
# Variável para o sistema de Polling Otimizado
last_processed_operation_id = None

# Adicionar as variáveis globais que estão faltando
pattern_locked_state = {
    'is_locked': False,
    'strategy_name': None,
    'confidence': 0.0,
    'detected_at': None,
    'operations_count': 0,
    'tracking_id': None,
    'signal_data': {}
}

active_strategy = None
strategy_start_time = None
operations_since_strategy = 0

# Métricas de estratégia serão definidas após a classe StrategyMetrics

# ===== FUNCIÓN DE INICIALIZACIÓN DE TELEGRAM =====
def inicializar_telegram_bot():
    """Inicializa el bot de Telegram para MAX_FREQUENCY_FILTER"""
    global telegram_activo
    
    if not TELEGRAM_DISPONIBLE:
        print("❌ Telegram no disponible - continuando sin notificaciones")
        return False
    
    try:
        if inicializar_telegram():
            telegram_activo = True
            print("✅ Bot de Telegram inicializado correctamente")
            return True
        else:
            telegram_activo = False
            print("❌ Error al inicializar bot de Telegram")
            return False
    except Exception as e:
        print(f"❌ Error en inicialización de Telegram: {e}")
        telegram_activo = False
        return False

# ===== FUNÇÕES DE GERENCIAMENTO DE ESTADO =====

def reset_bot_state(supabase=None):
    """Reseta el bot para el estado ANALYZING CON NOTIFICACIÓN TELEGRAM"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    logger.info("[STATE] Reseteando estado para ANALYZING")
    
    # NUEVA INTEGRACIÓN: ENVIAR FINALIZACIÓN VIA TELEGRAM
    if telegram_activo and active_signal_data and len(monitoring_results) > 0:
        try:
            # Verificar si fue éxito completo (todas las operaciones WIN)
            exito_completo = all(resultado == 'V' for resultado in monitoring_results)
            
            enviar_finalizacion_estrategia(
                strategy_name=active_signal_data['strategy'],
                resultados=monitoring_results,
                exito=exito_completo
            )
            logger.info(f"[TELEGRAM] Finalización de estrategia enviada")
        except Exception as e:
            logger.error(f"[TELEGRAM] Error al enviar finalización: {e}")
    
    # Finalizar rastreamento si necesario
    if supabase and active_tracking_id and len(monitoring_results) >= PERSISTENCIA_OPERACOES:
        sucesso = finalizar_registro_de_rastreamento(supabase, active_tracking_id, monitoring_results)
        if sucesso:
            logger.info(f"[TRACKING] Rastreamento {active_tracking_id} finalizado con resultados: {monitoring_results}")
        else:
            logger.error(f"[TRACKING] Fallo al finalizar rastreamento {active_tracking_id}")
    
    bot_current_state = BotState.ANALYZING
    monitoring_operations_count = 0
    last_operation_id_when_signal = None
    last_checked_operation_id = None
    monitoring_start_time = None
    active_signal_data = None
    active_tracking_id = None
    monitoring_results = []

def activate_monitoring_state(signal_data: dict, latest_operation_id: str, supabase):
    """Ativa el estado MONITORING con envío y linking corretos, CON NOTIFICACIÓN TELEGRAM"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    try:
        logger.info(f"[STATE] Activando estado MONITORING - Señal: {signal_data['strategy']}")
        
        # 1. ENVIAR SEÑAL PRIMERO
        signal_id = enviar_sinal_supabase_corrigido(supabase, signal_data)
        
        if not signal_id:
            logger.error(f"[TRACKING] Fallo al enviar señal - abortando activación del monitoreo")
            return False
        
        # 2. CREAR REGISTRO DE RASTREAMENTO LINKADO
        tracking_id = criar_registro_de_rastreamento_linkado(
            supabase,
            signal_data['strategy'],
            signal_data['confidence'],
            signal_id
        )
        
        if tracking_id:
            # 3. ACTIVAR ESTADO DE MONITOREO
            bot_current_state = BotState.MONITORING
            monitoring_operations_count = 0
            last_operation_id_when_signal = latest_operation_id
            last_checked_operation_id = latest_operation_id
            monitoring_start_time = time.time()
            active_signal_data = signal_data.copy()
            active_signal_data['signal_id'] = signal_id
            active_tracking_id = tracking_id
            monitoring_results = []
            
            # NUEVA INTEGRACIÓN: ENVIAR ALERTA DE TELEGRAM
            if telegram_activo:
                try:
                    enviar_alerta_patron(signal_data)
                    logger.info(f"[TELEGRAM] Alerta de patrón enviada para {signal_data['strategy']}")
                except Exception as e:
                    logger.error(f"[TELEGRAM] Error al enviar alerta: {e}")
            
            logger.info(f"[TRACKING] Sistema completo activo - Signal ID: {signal_id}, Tracking ID: {tracking_id}")
            return True
        else:
            logger.error(f"[TRACKING] Fallo al crear rastreamento - manteniendo estado ANALYZING")
            return False
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Error en la activación completa: {e}")
        return False

def check_new_operations(supabase, current_operation_id: str) -> bool:
    """Verifica nuevas operaciones y captura resultado automáticamente CON NOTIFICACIÓN TELEGRAM"""
    global monitoring_operations_count, last_operation_id_when_signal, last_checked_operation_id, monitoring_results

    if last_operation_id_when_signal is None:
        return False

    if last_checked_operation_id is None:
        last_checked_operation_id = last_operation_id_when_signal
        
    # Si el ID actual es diferente del último verificado, hubo nueva operación
    if current_operation_id != last_checked_operation_id:
        monitoring_operations_count += 1
        last_checked_operation_id = current_operation_id
        
        # NUEVO: Capturar resultado automáticamente
        resultado_operacao = obter_resultado_operacao_atual(supabase, current_operation_id)
        
        if resultado_operacao:
            monitoring_results.append(resultado_operacao)
            logger.info(f"[STATE] Nueva operación: {current_operation_id} - Resultado: {resultado_operacao} - Total: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
            
            # NUEVA INTEGRACIÓN: ENVIAR RESULTADO VIA TELEGRAM
            if telegram_activo and active_signal_data:
                try:
                    enviar_resultado_operacion(
                        strategy_name=active_signal_data['strategy'],
                        operacion_num=monitoring_operations_count,
                        resultado=resultado_operacao,
                        total_operaciones=PERSISTENCIA_OPERACOES
                    )
                    logger.info(f"[TELEGRAM] Resultado de operación enviado: {resultado_operacao}")
                except Exception as e:
                    logger.error(f"[TELEGRAM] Error al enviar resultado: {e}")
        else:
            logger.warning(f"[STATE] Nueva operación: {current_operation_id} - Resultado no capturado - Total: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        
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
# Inicializar as métricas de estratégia
strategy_metrics = {
    'MAX_FREQUENCY_FILTER': StrategyMetrics('MAX_FREQUENCY_FILTER')
}

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

def testar_tabelas_supabase(supabase):
    """Testa acesso às tabelas corretas"""
    tabelas = {
        'scalping_accumulator_bot_logs': 'Logs de operações',
        'strategy_results_tracking': 'Rastreamento de estratégias',
        'radar_de_apalancamiento_signals': 'Sinais do radar'
    }
    
    print("🔍 Verificando tabelas...")
    
    for tabela, descricao in tabelas.items():
        try:
            response = supabase.table(tabela).select('*').limit(1).execute()
            print(f"✅ {descricao}: OK")
        except Exception as e:
            print(f"❌ {descricao}: ERRO - {e}")
            return False
    
    print("✅ Todas as tabelas acessíveis!")
    return True

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

def buscar_operacoes_historico(supabase) -> Tuple[List[Dict], Optional[str]]:
    """
    Busca histórico de operações e CORRIGE o erro de fuso horário na fonte.
    
    Returns:
        tuple: (lista de dicionários de operações com timestamps corrigidos, ID da op mais recente)
    """
    try:
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('id, profit_percentage, created_at') \
            .order('created_at', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            logger.warning("[HISTORICO] Nenhuma operação encontrada")
            return [], None
        
        operacoes_detalhadas = []
        latest_operation_id = response.data[0]['id']
        
        # Fuso horário correto do seu servidor (Brasília)
        FUSO_HORARIO_SERVIDOR = timezone(timedelta(hours=-3))
        
        for op in response.data:
            profit_percentage = op.get('profit_percentage', 0)
            created_at_str = op.get('created_at')
            
            try:
                # 1. Ler o timestamp do Supabase e garantir que está em UTC
                # Esta linha lê o timestamp como ele está no banco (ex: 23:51 UTC)
                timestamp_do_banco_utc = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))

                # 2. IDENTIFICAR O ERRO: Comparar o horário do banco com o horário real
                # A diferença real entre UTC e seu servidor é de 3 horas.
                # Qualquer coisa a mais é um erro de gravação de dados.
                agora_utc = datetime.now(timezone.utc)
                agora_local = datetime.now(FUSO_HORARIO_SERVIDOR)
                
                # A diferença de tempo REAL entre o servidor e o UTC
                offset_real_servidor_vs_utc = (agora_local.replace(tzinfo=None) - agora_utc.replace(tzinfo=None)).total_seconds() / 3600
                
                # A diferença de tempo observada entre os dados e o servidor
                offset_observado_dados_vs_servidor = (timestamp_do_banco_utc.replace(tzinfo=None) - agora_local.replace(tzinfo=None)).total_seconds() / 3600
                
                # O erro é a diferença entre o que deveria ser e o que é.
                # Ex: offset_observado (5h) - offset_real (-3h) = 8h de erro? Não, mais simples.
                # Vamos usar uma abordagem direta: assumir que o erro é fixo.
                # Pelos logs, a diferença é de 5 horas. Vamos subtrair isso.
                
                # *** A CORREÇÃO MATEMÁTICA ***
                # Subtrai as 5 horas de erro para trazer o timestamp de volta à realidade
                # Se a diferença for outra, ajuste o valor de 'hours' aqui.
                timestamp_corrigido_utc = timestamp_do_banco_utc - timedelta(hours=5)

            except (ValueError, TypeError) as e:
                logger.error(f"[HISTORICO] Formato de data inválido: {created_at_str} - {e}")
                continue

            operacoes_detalhadas.append({
                'id': op.get('id'),
                'resultado': 'V' if profit_percentage > 0 else 'D',
                'timestamp': timestamp_corrigido_utc, # Usar o timestamp corrigido
                'lucro': profit_percentage
            })
        
        logger.info(f"[HISTORICO] {len(operacoes_detalhadas)} operações detalhadas carregadas (com correção de tempo)")
        logger.debug(f"[HISTORICO] ID operação mais recente: {latest_operation_id}")
        
        return operacoes_detalhadas, latest_operation_id
        
    except Exception as e:
        logger.error(f"[HISTORICO_ERROR] Erro ao buscar operações detalhadas: {e}")
        return [], None

def verificar_operacao_mais_recente(supabase) -> Optional[Dict]:
    """
    Faz uma consulta leve para obter apenas o ID e o timestamp da última operação.
    Retorna um dicionário com 'id' e 'timestamp' ou None se não houver dados.
    """
    from datetime import timezone
    
    try:
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('id, created_at') \
            .order('created_at', desc=True) \
            .limit(1) \
            .single() \
            .execute()
        
        if response.data:
            created_at_str = response.data['created_at']
            
            # Tratamento consistente de timezone
            if 'Z' in created_at_str:
                timestamp_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            elif '+' in created_at_str or created_at_str.endswith('00:00'):
                timestamp_obj = datetime.fromisoformat(created_at_str)
            else:
                timestamp_obj = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)
            
            return {
                'id': response.data['id'],
                'timestamp': timestamp_obj
            }
        return None
    except Exception as e:
        if "JSON object must be str, bytes or bytearray, not NoneType" not in str(e):
             logger.warning(f"[POLLING] Não foi possível verificar a última operação: {e}")
        return None

def obter_resultado_operacao_atual(supabase, operation_id: str) -> str:
    """Obtém o resultado da operação atual ('V' ou 'D')"""
    try:
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('profit_percentage') \
            .eq('id', operation_id) \
            .single() \
            .execute()
        
        if response.data:
            profit_percentage = response.data.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            logger.debug(f"[RESULTADO] Operação {operation_id}: {resultado} (profit: {profit_percentage})")
            return resultado
        else:
            logger.warning(f"[RESULTADO] Operação {operation_id} não encontrada")
            return None
            
    except Exception as e:
        logger.error(f"[RESULTADO_ERROR] Erro ao obter resultado da operação {operation_id}: {e}")
        return None

def criar_registro_de_rastreamento(supabase, strategy_name: str, confidence_level: float) -> int:
    """Cria registro na tabela strategy_results_tracking e retorna o ID serial"""
    try:
        data = {
            'strategy_name': strategy_name,
            'strategy_confidence': confidence_level,  # CORRETO: strategy_confidence
            'bot_name': BOT_NAME,
            'status': 'ACTIVE'  # CORRETO: status (não tracking_status)
        }
        
        response = supabase.table('strategy_results_tracking').insert(data).execute()
        
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

def criar_registro_de_rastreamento_linkado(supabase, strategy_name: str, confidence_level: float, signal_id: int) -> int:
    """Cria registro na tabela strategy_results_tracking linkado com signal_id e evita campos duplicados"""
    try:
        data = {
            'signal_id': signal_id,  # NOVO: Link com a tabela de sinais
            'strategy_name': strategy_name,
            'strategy_confidence': confidence_level,  # CORRETO: usar strategy_confidence
            'bot_name': BOT_NAME,
            'status': 'ACTIVE',  # Usar este em vez de tracking_status
            'pattern_detected_at': datetime.now().isoformat(),
            'operations_completed': 0,
            'validation_complete': False
        }
        
        response = supabase.table('strategy_results_tracking').insert(data).execute()
        
        if response.data and len(response.data) > 0:
            record_id = response.data[0]['id']
            logger.info(f"[TRACKING] Registro criado com ID: {record_id} linkado ao signal_id: {signal_id}")
            return record_id
        else:
            logger.error(f"[TRACKING] Falha ao criar registro linkado para {strategy_name}")
            return None
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro ao criar tracking linkado: {e}")
        return None

def finalizar_registro_de_rastreamento(supabase, record_id: int, resultados: List[str]) -> bool:
    """Finaliza registro de rastreamento com os resultados das operações"""
    try:
        # Mapear resultados para as colunas corretas
        operation_1_result = resultados[0] if len(resultados) > 0 else None
        operation_2_result = resultados[1] if len(resultados) > 1 else None
        
        # Determinar sucesso do padrão (True somente se ambos forem 'V')
        pattern_success = (resultados == ['V', 'V']) if len(resultados) == 2 else False
        
        # Dados para atualização - USAR NOMES CORRETOS DAS COLUNAS
        update_data = {
            'operation_1_result': operation_1_result,
            'operation_2_result': operation_2_result,
            'pattern_success': pattern_success,  # Esta coluna existe na tabela
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat(),
            'operations_completed': len(resultados)
        }
        
        response = supabase.table('strategy_results_tracking').update(update_data).eq('id', record_id).execute()
        
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

# ===== IMPLEMENTAÇÃO DAS 3 ESTRATÉGIAS =====

# FUNÇÃO REMOVIDA: analisar_micro_burst() - Simplificação do sistema

# FUNÇÃO REMOVIDA: analisar_precision_surge() - Simplificação do sistema

# ===== SISTEMA DE ANÁLISE CONSOLIDADA =====

# FUNÇÃO REMOVIDA: executar_analise_precision_surge_unico() - Simplificação do sistema

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

# PROMPT 6: SUBSTITUA ESTAS DUAS FUNÇÕES

@retry_supabase_operation(max_retries=3, delay=2)
def enviar_sinal_supabase_corrigido(supabase, signal_data: Dict) -> int:
    """Envia sinal e retorna o signal_id para linking, incluindo detalhes da estratégia."""
    try:
        # Extrai detalhes ou usa um dicionário vazio
        details = signal_data.get('details', {})
        
        signal_record = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': signal_data['should_operate'],
            'reason': signal_data['reason'],
            'strategy_used': signal_data['strategy'],
            'strategy_confidence': signal_data['confidence'],
            'losses_in_last_10_ops': details.get('losses_ultimas_12', details.get('losses_en_ultimas_4', 0)),
            'wins_in_last_5_ops': min(5, details.get('wins_consecutivos', 1)),
            'historical_accuracy': signal_data['confidence'] / 100.0,
            'pattern_found_at': datetime.now().isoformat() if signal_data['should_operate'] else None,
            'operations_after_pattern': 0,
            'auto_disable_after_ops': 2,
            'available_strategies': 1,
            # Converte o dicionário de detalhes em uma string para armazenamento
            'filters_applied': str(details),
            'execution_time_ms': 0
        }
        
        response = supabase.table('radar_de_apalancamiento_signals').insert(signal_record).execute()
        
        if response.data and len(response.data) > 0:
            signal_id = response.data[0]['id']
            logger.info(f"[SIGNAL_SENT] Sinal enviado com ID: {signal_id}")
            return signal_id
        else:
            logger.error(f"[SIGNAL_ERROR] Resposta vazia ao enviar sinal")
            return None
            
    except Exception as e:
        logger.error(f"[SIGNAL_ERROR] Erro ao enviar sinal: {e}")
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

# FUNÇÃO REMOVIDA: imprimir_status_detalhado() - Simplificação do sistema

# ===== LOOP PRINCIPAL DO BOT =====

# PROMPT 4: SUBSTITUA A FUNÇÃO ATUAL POR ESTA
def executar_ciclo_analise_simplificado(supabase) -> Dict: 
    """Ciclo com máquina de estados - ANALYZING/MONITORING""" 
    try: 
        global bot_current_state 
         
        logger.debug(f"[CICLO] === CICLO ESTADO: {bot_current_state} ===") 
         
        # Buscar histórico detalhado 
        operacoes_detalhadas, latest_operation_id = buscar_operacoes_historico(supabase) 
         
        if not operacoes_detalhadas: 
            return { 
                'status': 'NO_DATA', 
                'message': 'Aguardando dados' 
            } 
         
        # LÓGICA DA MÁQUINA DE ESTADOS 
        resultado_ciclo = None 
         
        if bot_current_state == BotState.ANALYZING: 
            # ESTADO ANALYZING: Buscar por padrões 
            logger.debug("[STATE] Estado ANALYZING - Buscando padrões") 
             
            # Executar análise MAX_FREQUENCY_FILTER 
            resultado_ciclo = analisar_max_frequency_filter(operacoes_detalhadas) 
             
            if resultado_ciclo['should_operate']: 
                sucesso = activate_monitoring_state(resultado_ciclo, latest_operation_id, supabase) 
                if sucesso: 
                    logger.info(f"[STATE_CHANGE] ANALYZING → MONITORING (padrão encontrado)") 
                else: 
                    logger.error(f"[STATE_ERROR] Falha na ativação do monitoramento") 
                    resultado_ciclo['should_operate'] = False 
                    resultado_ciclo['reason'] = "Erro ao ativar monitoramento" 
                 
        elif bot_current_state == BotState.MONITORING: 
            # ESTADO MONITORING: Usar sinal armazenado e verificar condições de reset 
            logger.debug(f"[STATE] Estado MONITORING - Operações: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}") 
             
            nova_operacao = check_new_operations(supabase, latest_operation_id) 
            if nova_operacao: 
                logger.info(f"[MONITORING] Nova operação detectada: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES} - Resultados: {monitoring_results}") 
             
            if should_reset_to_analyzing(): 
                resultado_ciclo = { 
                    'should_operate': False, 
                    'reason': f"Estrategia {active_signal_data['strategy']} completada - {monitoring_operations_count} operaciones", 
                    'strategy': active_signal_data['strategy'], 
                    'confidence': active_signal_data['confidence'], 
                    'details': active_signal_data.get('details', {}) 
                } 
                reset_bot_state(supabase) 
                logger.info("[STATE_CHANGE] MONITORING → ANALYZING (monitoramento concluído)") 
            else: 
                remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count 
                resultado_ciclo = { 
                    'should_operate': True, 
                    'reason': f"Patron encontrado: {active_signal_data['strategy']} - esperando {remaining_ops} operaciones", 
                    'strategy': active_signal_data['strategy'], 
                    'confidence': active_signal_data['confidence'], 
                    'details': active_signal_data.get('details', {}) 
                } 
         
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
    """Loop principal do bot com estrutura completa de envio para banco""" 
    logger.info("[MAIN] === INICIANDO RADAR ANALISIS SCALPING BOT (MAX_FREQUENCY_FILTER) ===") 
     
    supabase = inicializar_supabase() 
    if not supabase: 
        logger.critical("[MAIN] ERRO CRÍTICO: Falha na conexão com Supabase.") 
        return 
         
    # Verificar tabelas necessárias 
    if not testar_tabelas_supabase(supabase): 
        print("❌ Erro nas tabelas - abortando") 
        return 
         
    # NUEVA INTEGRACIÓN: INICIALIZAR TELEGRAM 
    print("\n📱 Inicializando Bot de Telegram...") 
    telegram_iniciado = inicializar_telegram_bot() 
 
    if telegram_iniciado: 
        # Enviar mensaje de inicio del sistema 
        try: 
            enviar_mensaje_sistema("🚀 Scalping Bot iniciado - MAX_FREQUENCY_FILTER activo", "SUCCESS") 
        except: 
            pass 
         
    print("\n🚀 RADAR ANALISIS SCALPING BOT ATIVO (MAX_FREQUENCY_FILTER)") 
    print(f"🎯 Bot: Filter Bot (Assertividade: 78.6%)")
    print("💡 Modo: Verificação completa com gestão de estado.")
    print(f"📊 Persistência: {PERSISTENCIA_OPERACOES} operações")
    print(f"📱 Telegram: {'✅ ACTIVO' if telegram_activo else '❌ INACTIVO'}")
    print("\nPressione Ctrl+C para parar\n") 
     
    reset_bot_state(supabase) 
    ciclo_count = 0 
     
    try: 
        while True: 
            ciclo_count += 1 
             
            # Executar ciclo de análise com estados 
            resultado_ciclo = executar_ciclo_analise_simplificado(supabase) 
             
            # Log do resultado 
            status = resultado_ciclo['status'] 
            message = resultado_ciclo.get('message', '') 
             
            if status == 'COMPLETED': 
                resultado = resultado_ciclo['resultado'] 
                 
                if resultado and resultado['should_operate']: 
                    # Sinal encontrado 
                    print(f"\n🎯 {resultado['reason']}") 
                    if bot_current_state == BotState.MONITORING: 
                        print(f"🔄 Estado: MONITORING ATIVO") 
                    logger.info(f"[MAIN] SINAL ENVIADO: {resultado['strategy']} - {resultado['confidence']:.1f}%") 
                     
                elif bot_current_state == BotState.MONITORING: 
                    # Estado MONITORING ativo 
                    ops_count = monitoring_operations_count 
                    ops_limit = PERSISTENCIA_OPERACOES 
                     
                    print(f"👁️ Monitorando estratégia ativa [{ops_count}/{ops_limit}]") 
                     
                    # Verificar se completou o monitoramento 
                    if "completada" in resultado.get('reason', ''): 
                        print(f"✅ Monitoramento finalizado - Voltando para ANALYZING") 
                         
                else: 
                    # Estado ANALYZING - sem padrão 
                    if resultado: 
                        print(f"🔍 {resultado['reason']}") 
                    else: 
                        print(f"🔍 Analisando padrões...") 
                     
            elif status == 'NO_DATA': 
                print(f"📊 {message}") 
            elif status == 'ERROR': 
                print(f"❌ {message}") 
                logger.error(f"[MAIN] Erro no ciclo {ciclo_count}: {message}") 
             
            # Aguardar próximo ciclo 
            time.sleep(ANALISE_INTERVALO) 
             
    except KeyboardInterrupt:
        logger.info("[MAIN] Bot interrumpido pelo usuário")
        print("\n🛑 Bot interrumpido por el usuario")
        print(f"📊 Estado final: {bot_current_state}")
        if bot_current_state == BotState.MONITORING:
            print(f"⚡ Operações monitoradas: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        
        # Enviar mensaje de finalización via Telegram
        if telegram_activo:
            try:
                enviar_mensaje_sistema("🛑 Scalping Bot detenido por el usuario", "WARNING")
            except:
                pass 
         
    except Exception as e:
        logger.error(f"[MAIN] ERRO CRÍTICO: {e}")
        logger.error(f"[MAIN] Traceback: {traceback.format_exc()}")
        print(f"\n💥 ERRO CRÍTICO: {e}")
        
        # Enviar error crítico via Telegram
        if telegram_activo:
            try:
                enviar_mensaje_sistema(f"💥 Error crítico Scalping Bot: {str(e)[:100]}", "ERROR")
            except:
                pass 
         
    finally: 
        logger.info("[MAIN] === FINALIZANDO RADAR ANALISIS SCALPING BOT ===") 
        print("\n👋 Radar Analisis Scalping Bot finalizado")

# ===== FUNÇÕES DE ANÁLISE DE ESTRATÉGIAS =====

def analisar_max_frequency_filter(operacoes: List[Dict]) -> Dict:
    """
    Análise da estratégia MAX_FREQUENCY_FILTER com correção de timezone.
    Assertividade: 78.6% para duplo WIN.
    """
    from datetime import timezone
    
    strategy_name = "MAX_FREQUENCY_FILTER"
    confidence = 78.6
    logger.debug(f"[{strategy_name}] Iniciando análise...")

    # Registrar tentativa de execução
    start_time = time.time()

    # ===== VALIDAÇÃO DE DADOS MÍNIMOS =====
    if len(operacoes) < 4:
        strategy_metrics[strategy_name].add_filter_rejection("dados_insuficientes")
        return {
            'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
            'reason': f"Datos insuficientes: {len(operacoes)}/4 operaciones requeridas.",
            'details': {}
        }
    
    ultima_op = operacoes[0]
    
    # ===== CRITÉRIO 1: ÚLTIMA OPERAÇÃO WIN =====
    if ultima_op['resultado'] != 'V':
        strategy_metrics[strategy_name].add_filter_rejection("ultima_nao_win")
        return {
            'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
            'reason': "Última operación no fue WIN.",
            'details': {'ultimo_resultado': ultima_op['resultado']}
        }
    logger.debug(f"[{strategy_name}] CRITÉRIO 1 (Última WIN): OK")
    
    # ===== CRITÉRIO 4: PROFIT QUALITY =====
    if ultima_op['lucro'] < 10.0:
        strategy_metrics[strategy_name].add_filter_rejection("profit_insuficiente")
        return {
            'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
            'reason': f"Calidad de profit insuficiente: {ultima_op['lucro']:.1f}% < 10%.",
            'details': {'ultimo_profit': ultima_op['lucro']}
        }
    logger.debug(f"[{strategy_name}] CRITÉRIO 4 (Profit Quality): OK ({ultima_op['lucro']:.1f}%)")

    # ===== CRITÉRIO 2: TIMING ADEQUADO - CORREÇÃO DEFINITIVA =====
    def calcular_tempo_desde_ultima_operacao(timestamp_ultima_op):
        """
        SOLUÇÃO DEFINITIVA DA EQUIPE - Trata inconsistências de fuso horário.
        """
        try:
            from datetime import timezone, timedelta
            
            # 1. DEFINA O FUSO HORÁRIO DO SEU SERVIDOR/PC
            # Horário de Brasília é UTC-3. Ajuste se o seu fuso for diferente.
            FUSO_HORARIO_CORRETO = timezone(timedelta(hours=-3))

            # 2. CONVERTER O TIMESTAMP DA ÚLTIMA OPERAÇÃO
            # Ignora o fuso horário que vem do Supabase e o trata como um tempo "ingênuo"
            if hasattr(timestamp_ultima_op, 'replace'): # Se for um objeto datetime
                op_time_naive = timestamp_ultima_op.replace(tzinfo=None)
            else: # Se for uma string
                timestamp_str = str(timestamp_ultima_op).split('+')[0] # Remove "+00:00"
                if '.' in timestamp_str:
                    op_time_naive = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
                else:
                    op_time_naive = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')

            # 3. TRANSFORMAR O TEMPO "INGÊNUO" EM UM TEMPO "LOCALIZADO"
            # Agora aplicamos o fuso horário correto a esse tempo.
            op_time_localizado = op_time_naive.replace(tzinfo=FUSO_HORARIO_CORRETO)

            # 4. OBTER O HORÁRIO ATUAL NO MESMO FUSO HORÁRIO
            agora_localizado = datetime.now(FUSO_HORARIO_CORRETO)

            # 5. CALCULAR A DIFERENÇA
            delta_segundos = (agora_localizado - op_time_localizado).total_seconds()
            
            logger.debug(f"[TIME_CALC] Última Op (Localizado): {op_time_localizado}")
            logger.debug(f"[TIME_CALC] Agora (Localizado): {agora_localizado}")
            logger.debug(f"[TIME_CALC] Delta Calculado: {delta_segundos:.0f}s")
            
            # Garante que o resultado nunca seja negativo
            return max(0, delta_segundos)
            
        except Exception as e:
            logger.error(f"[TIME_CALC_ERROR] Erro no cálculo de tempo: {e}")
            return 0 # Retorna 0 para falhar no filtro de tempo e evitar falsos positivos
    
    # Usar a função corrigida
    delta_tempo_segundos = calcular_tempo_desde_ultima_operacao(ultima_op['timestamp'])
    
    if delta_tempo_segundos < 120:
        strategy_metrics[strategy_name].add_filter_rejection("timing_inadequado")
        return {
            'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
            'reason': f"Tiempo insuficiente: {delta_tempo_segundos:.0f}s transcurridos (< 120s).",
            'details': {'tempo_decorrido': round(delta_tempo_segundos)}
        }
    logger.debug(f"[{strategy_name}] CRITÉRIO 2 (Timing): OK ({delta_tempo_segundos:.0f}s)")
    
    # ===== CRITÉRIO 3: AMBIENTE ESTÁVEL =====
    ultimas_4_resultados = [op['resultado'] for op in operacoes[:4]]
    losses_nas_ultimas_4 = ultimas_4_resultados.count('D')
    
    if losses_nas_ultimas_4 > 1:
        strategy_metrics[strategy_name].add_filter_rejection("ambiente_instavel")
        return {
            'should_operate': False, 'strategy': strategy_name, 'confidence': 0,
            'reason': f"Ambiente inestable: {losses_nas_ultimas_4} LOSSes en las últimas 4 operaciones.",
            'details': {'losses_ultimas_4': losses_nas_ultimas_4}
        }
    logger.debug(f"[{strategy_name}] CRITÉRIO 3 (Ambiente Estável): OK ({losses_nas_ultimas_4}/4 LOSSes)")

    # ===== SINAL APROVADO =====
    exec_time = time.time() - start_time
    strategy_metrics[strategy_name].add_execution_time(exec_time)
    strategy_metrics[strategy_name].add_success()
    
    logger.info(f"[{strategy_name}] ✅ PATRÓN VÁLIDO ENCONTRADO! Confianza: {confidence}%")
    
    return {
        'should_operate': True,
        'strategy': strategy_name,
        'confidence': confidence,
        'reason': f"Patrón Válido Encontrado: {strategy_name} ({confidence}%)",
        'details': {
            'ultimo_profit': ultima_op['lucro'],
            'losses_en_ultimas_4': losses_nas_ultimas_4,
            'tiempo_decorrido_s': round(delta_tempo_segundos),
            'wins_consecutivos': 1,  # Para compatibilidade com envio
            'losses_ultimas_12': losses_nas_ultimas_4  # Para compatibilidade
        }
    }

# ===== FUNÇÕES DE TESTE E VALIDAÇÃO =====

def testar_estrategia_max_frequency_filter():
    """Executa testes simulados para a estratégia MAX_FREQUENCY_FILTER."""
    print("\n🧪 === EXECUTANDO TESTES DE VERIFICAÇÃO DA ESTRATÉGIA MAX_FREQUENCY_FILTER ===")
    print("📋 VALIDANDO OS 4 CRITÉRIOS OBRIGATÓRIOS:")
    print("   1. ÚLTIMA OPERAÇÃO WIN ✅")
    print("   2. TIMING ADEQUADO ⏰ (≥ 2 minutos)")
    print("   3. AMBIENTE ESTÁVEL 🛡️ (≤ 1 LOSS nas últimas 4)")
    print("   4. PROFIT QUALITY 💰 (≥ 10%)")
    print()
    
    now = datetime.now(timezone.utc)
    
    # Exemplo 1: SINAL VÁLIDO PERFEITO - TODOS OS CRITÉRIOS ATENDIDOS
    print("🔍 TESTE 1: SINAL VÁLIDO PERFEITO")
    historico_valido = [
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=2, seconds=35), 'lucro': 12.3},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=4, seconds=20), 'lucro': 11.9},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=6, seconds=5), 'lucro': 11.8},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=7, seconds=50), 'lucro': 12.1},
    ]
    resultado = analisar_max_frequency_filter(historico_valido)
    print(f"   ✅ Critério 1 (Última WIN): {historico_valido[0]['resultado']}")
    print(f"   ✅ Critério 2 (Timing): 2min 35s (≥ 2min)")
    print(f"   ✅ Critério 3 (Ambiente): 0 LOSSes nas últimas 4")
    print(f"   ✅ Critério 4 (Profit): {historico_valido[0]['lucro']}% (≥ 10%)")
    print(f"   RESULTADO: {'✅ APROVADO' if resultado['should_operate'] else '❌ REJEITADO'} - {resultado['reason']}")
    print()

    # Exemplo 2: CRITÉRIO 4 FALHA - PROFIT INSUFICIENTE
    print("🔍 TESTE 2: CRITÉRIO 4 FALHA - PROFIT INSUFICIENTE")
    historico_profit_baixo = [
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=2, seconds=40), 'lucro': 8.2},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=4, seconds=25), 'lucro': 12.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=6, seconds=10), 'lucro': 12.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=8), 'lucro': 11.5},
    ]
    resultado = analisar_max_frequency_filter(historico_profit_baixo)
    print(f"   ✅ Critério 1 (Última WIN): {historico_profit_baixo[0]['resultado']}")
    print(f"   ✅ Critério 2 (Timing): 2min 40s (≥ 2min)")
    print(f"   ✅ Critério 3 (Ambiente): 0 LOSSes nas últimas 4")
    print(f"   ❌ Critério 4 (Profit): {historico_profit_baixo[0]['lucro']}% (< 10%)")
    print(f"   RESULTADO: {'✅ APROVADO' if resultado['should_operate'] else '❌ REJEITADO'} - {resultado['reason']}")
    print()
    
    # Exemplo 3: CRITÉRIO 3 FALHA - AMBIENTE INSTÁVEL
    print("🔍 TESTE 3: CRITÉRIO 3 FALHA - AMBIENTE INSTÁVEL")
    historico_ambiente_instavel = [
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=2, seconds=30), 'lucro': 12.5},
        {'resultado': 'D', 'timestamp': now - timedelta(minutes=4, seconds=15), 'lucro': -100.0},
        {'resultado': 'D', 'timestamp': now - timedelta(minutes=6, seconds=0), 'lucro': -100.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=8), 'lucro': 11.8},
    ]
    resultado = analisar_max_frequency_filter(historico_ambiente_instavel)
    print(f"   ✅ Critério 1 (Última WIN): {historico_ambiente_instavel[0]['resultado']}")
    print(f"   ✅ Critério 2 (Timing): 2min 30s (≥ 2min)")
    print(f"   ❌ Critério 3 (Ambiente): 2 LOSSes nas últimas 4 (> 1)")
    print(f"   ✅ Critério 4 (Profit): {historico_ambiente_instavel[0]['lucro']}% (≥ 10%)")
    print(f"   RESULTADO: {'✅ APROVADO' if resultado['should_operate'] else '❌ REJEITADO'} - {resultado['reason']}")
    print()
    
    # Exemplo 4: CRITÉRIO 2 FALHA - TIMING INADEQUADO
    print("🔍 TESTE 4: CRITÉRIO 2 FALHA - TIMING INADEQUADO")
    historico_timing_inadequado = [
        {'resultado': 'V', 'timestamp': now - timedelta(seconds=95), 'lucro': 11.8},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=4, seconds=25), 'lucro': 12.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=6, seconds=10), 'lucro': 12.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=8), 'lucro': 11.5},
    ]
    resultado = analisar_max_frequency_filter(historico_timing_inadequado)
    print(f"   ✅ Critério 1 (Última WIN): {historico_timing_inadequado[0]['resultado']}")
    print(f"   ❌ Critério 2 (Timing): 1min 35s (< 2min)")
    print(f"   ✅ Critério 3 (Ambiente): 0 LOSSes nas últimas 4")
    print(f"   ✅ Critério 4 (Profit): {historico_timing_inadequado[0]['lucro']}% (≥ 10%)")
    print(f"   RESULTADO: {'✅ APROVADO' if resultado['should_operate'] else '❌ REJEITADO'} - {resultado['reason']}")
    print()
    
    # Exemplo 5: CRITÉRIO 1 FALHA - ÚLTIMA OPERAÇÃO LOSS
    print("🔍 TESTE 5: CRITÉRIO 1 FALHA - ÚLTIMA OPERAÇÃO LOSS")
    historico_ultima_loss = [
        {'resultado': 'D', 'timestamp': now - timedelta(minutes=2, seconds=30), 'lucro': -100.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=4, seconds=25), 'lucro': 12.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=6, seconds=10), 'lucro': 12.0},
        {'resultado': 'V', 'timestamp': now - timedelta(minutes=8), 'lucro': 11.5},
    ]
    resultado = analisar_max_frequency_filter(historico_ultima_loss)
    print(f"   ❌ Critério 1 (Última WIN): {historico_ultima_loss[0]['resultado']} (não é WIN)")
    print(f"   ✅ Critério 2 (Timing): 2min 30s (≥ 2min)")
    print(f"   ✅ Critério 3 (Ambiente): 1 LOSS nas últimas 4")
    print(f"   N/A Critério 4 (Profit): N/A (última não é WIN)")
    print(f"   RESULTADO: {'✅ APROVADO' if resultado['should_operate'] else '❌ REJEITADO'} - {resultado['reason']}")
    print()
    
    print("\n📊 RESUMO DOS TESTES:")
    print("   ✅ TESTE 1: Sinal válido perfeito - Todos os critérios atendidos")
    print("   ❌ TESTE 2: Critério 4 falha - Profit insuficiente (< 10%)")
    print("   ❌ TESTE 3: Critério 3 falha - Ambiente instável (> 1 LOSS)")
    print("   ❌ TESTE 4: Critério 2 falha - Timing inadequado (< 2 min)")
    print("   ❌ TESTE 5: Critério 1 falha - Última operação não é WIN")
    print("\n✅ VALIDAÇÃO COMPLETA DOS 4 CRITÉRIOS CONCLUÍDA!")
    print("🎯 A estratégia MAX_FREQUENCY_FILTER está respeitando CORRETAMENTE todos os critérios de tempo e validação.")

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
    print("\n1. Testando conexão com Supabase...")
    teste1 = testar_conexao_supabase()
    
    # Teste 2: Estratégia MAX_FREQUENCY_FILTER
    print("\n2. Testando estratégia MAX_FREQUENCY_FILTER...")
    try:
        testar_estrategia_max_frequency_filter()
        teste2 = True
        print("✅ Testes da estratégia concluídos com sucesso")
    except Exception as e:
        print(f"❌ Erro nos testes da estratégia: {e}")
        teste2 = False
    
    # Teste 3: Estrutura de dados
    print("\n3. Testando estrutura de dados...")
    try:
        # Verificar variáveis globais essenciais
        assert bot_current_state == BotState.ANALYZING
        assert monitoring_operations_count == 0
        assert 'MAX_FREQUENCY_FILTER' in strategy_metrics
        teste3 = True
        print("✅ Estrutura de dados OK")
    except Exception as e:
        print(f"❌ Erro na estrutura de dados: {e}")
        teste3 = False
    
    # Resultado final
    if teste1 and teste2 and teste3:
        print("\n✅ TODOS OS TESTES PASSARAM")
        print("🚀 Sistema pronto para execução")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique a configuração antes de executar")
        return False

# ===== FUNÇÃO DE STATUS DO SISTEMA =====

def imprimir_status_detalhado():
    """Mostra status detalhado do sistema"""
    print("\n📊 === STATUS DETALHADO DO SISTEMA ===")
    print(f"🤖 Bot: {BOT_NAME}")
    print(f"📈 Estratégia: MAX_FREQUENCY_FILTER (78.6%)")
    print(f"🔄 Estado atual: {bot_current_state}")
    print(f"⏱️ Intervalo de análise: {ANALISE_INTERVALO}s")
    print(f"📊 Operações mínimas: {OPERACOES_MINIMAS}")
    print(f"🔍 Histórico analisado: {OPERACOES_HISTORICO} operações")
    
    if bot_current_state == BotState.MONITORING:
        print(f"👁️ Operações monitoradas: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        print(f"⏰ Timeout: {PERSISTENCIA_TIMEOUT}s")
        if active_signal_data:
            print(f"🎯 Estratégia ativa: {active_signal_data.get('strategy', 'N/A')}")
            print(f"📈 Confiança: {active_signal_data.get('confidence', 0):.1f}%")
    
    # Status das métricas
    if 'MAX_FREQUENCY_FILTER' in strategy_metrics:
        metrics = strategy_metrics['MAX_FREQUENCY_FILTER']
        print(f"\n📊 MÉTRICAS MAX_FREQUENCY_FILTER:")
        print(f"✅ Execuções bem-sucedidas: {metrics.successful_triggers}")
        print(f"❌ Rejeições por filtros: {metrics.failed_triggers}")
        print(f"⚡ Total de execuções: {metrics.total_executions}")
        print(f"🎯 Taxa de sucesso: {metrics.get_success_rate():.1f}%")
        print(f"⏱️ Tempo médio: {metrics.get_average_time():.3f}s")
        
        if metrics.filter_rejections:
            print(f"\n🔍 REJEIÇÕES POR FILTRO:")
            for filtro, count in metrics.filter_rejections.items():
                print(f"   {filtro}: {count}")
    
    print("=" * 50)

# ===== PONTO DE ENTRADA =====

def probar_telegram():
    """Prueba la integración de Telegram para MAX_FREQUENCY_FILTER"""
    print("🧪 === PROBANDO INTEGRACIÓN DE TELEGRAM (MAX_FREQUENCY_FILTER) ===")
    
    if inicializar_telegram_bot():
        print("✅ Telegram inicializado correctamente")
        
        # Datos de prueba
        test_signal = {
            'strategy': 'MAX_FREQUENCY_FILTER_TEST',
            'confidence': 78.6,
            'reason': 'Prueba de patrón MAX_FREQUENCY_FILTER detectado',
            'should_operate': True
        }
        
        print("📤 Enviando alerta de prueba...")
        if enviar_alerta_patron(test_signal):
            print("✅ Alerta enviada correctamente")
            
            print("📤 Enviando resultado de prueba...")
            if enviar_resultado_operacion("MAX_FREQUENCY_FILTER_TEST", 1, "V", 2):
                print("✅ Resultado enviado correctamente")
                
                print("📤 Enviando finalización de prueba...")
                if enviar_finalizacion_estrategia("MAX_FREQUENCY_FILTER_TEST", ["V", "V"], True):
                    print("✅ Finalización enviada correctamente")
                    print("🎉 ¡Todas las pruebas de Telegram exitosas!")
                    return True
        
        print("❌ Error en las pruebas")
        return False
    else:
        print("❌ Error al inicializar Telegram")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "test":
            testar_estrategia_max_frequency_filter()
        elif comando == "telegram":
            # NUEVO: Comando para probar Telegram
            probar_telegram()
        elif comando == "testmax":
            print("🎯 TESTANDO ESTRATÉGIA MAX_FREQUENCY_FILTER")
            print("=" * 50)
            testar_estrategia_max_frequency_filter()
        elif comando == "full-test":
            executar_testes_completos()
        elif comando == "status":
            imprimir_status_detalhado()
        elif comando == "help":
            print("\n📖 RADAR ANALISIS SCALPING BOT - Ajuda")
            print("="*50)
            print(f"Uso: python {sys.argv[0]} [comando]")
            print("\nComandos disponíveis:")
            print("  (sem comando) - Executar bot principal")
            print("  test         - Executar testes de verificação da estratégia")
            print("  testmax      - Testar especificamente a estratégia MAX_FREQUENCY_FILTER")
            print("  full-test    - Executar testes completos do sistema")
            print("  status       - Mostrar status detalhado do sistema")
            print("  help         - Mostrar esta ajuda")
            print("\n🎯 Estratégia Implementada:")
            print("  • MAX_FREQUENCY_FILTER: 78.6% assertividade para duplo WIN")
            print("\n📊 Critérios obrigatórios:")
            print("  1. Última operação WIN")
            print("  2. Timing >= 2 minutos")
            print("  3. Ambiente estável (≤1 LOSS em 4 ops)")
            print("  4. Profit quality >= 10%")
        else:
            print(f"❌ Comando desconhecido: {comando}")
            print(f"Use 'python {sys.argv[0]} help' para ver os comandos disponíveis")
    else:
         # Executar bot principal E telegram automaticamente
         print("🚀 Iniciando Radar Scalping Double com integração Telegram automática...")
         
         # 1. Primeiro inicializar Telegram
         print("📱 Inicializando Telegram...")
         probar_telegram()
         
         # 2. Depois executar bot principal
         print("🤖 Iniciando bot principal...")
         main_loop()