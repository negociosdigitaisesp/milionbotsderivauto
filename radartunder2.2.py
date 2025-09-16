#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tunder Bot - Sistema de Trading com Estratégia WWL
Sistema integrado com rastreamento automático de resultados no Supabase

Estratégia implementada:
- WWL: Estratégia Win-Win-Loss com 78.6% de assertividade

Gatilhos:
- Padrão WWL nas últimas 3 operações
- Máximo 5 derrotas nas últimas 20 operações
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

# NUEVAS IMPORTACIONES PARA TELEGRAM
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
        import sys
        import os
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
        logging.FileHandler('tunder_bot_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduzir logs de bibliotecas externas
# Silenciar logs detalhados de bibliotecas externas, mostrando apenas erros críticos.
external_libs = ['httpx', 'httpcore', 'supabase', 'postgrest', 'urllib3', 'hpack', 'h2', 'requests']
for lib in external_libs:
    logging.getLogger(lib).setLevel(logging.ERROR)

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
BOT_NAME = 'Tunder Bot'  # <-- NOME MANTIDO CONFORME SOLICITADO
ANALISE_INTERVALO = 5  # segundos entre análises
# A estratégia WWL precisa de no mínimo 20 operações para análise de saldo.
OPERACOES_MINIMAS = 20
OPERACOES_HISTORICO = 25 # Buscamos 25 para uma margem de segurança.
PERSISTENCIA_TIMEOUT = 300  # 5 minutos timeout
PERSISTENCIA_OPERACOES = 1  # A Regra 3 (Saída) dita que o bot para após 1 operação.

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
    
    # NOVO: Timeout mais agressivo (2 minutos)
    if monitoring_start_time and (time.time() - monitoring_start_time) > 120:  # 2 min em vez de 5
        logger.warning(f"[STATE] Timeout de segurança atingido: 120s")
        return True
    
    # NOVO: Verificação de sanidade - se monitoring_start_time é None mas estado é MONITORING
    if monitoring_start_time is None and bot_current_state == BotState.MONITORING:
        logger.error(f"[STATE] Estado inconsistente detectado - forçando reset")
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

def inicializar_telegram_bot():
    """Inicializa el bot de Telegram"""
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
            
        # CORREÇÃO CRÍTICA: Aceitar formato real do banco
        valid_values = {'WIN', 'LOSS'}  # MUDOU de {'V', 'D'}
        invalid_values = [val for val in historico if val not in valid_values]
        if invalid_values:
            logger.error(f"[DATA_INTEGRITY] Valores inválidos encontrados: {set(invalid_values)}")
            return False
            
        # Verificar se há dados suficientes para análise
        if len(historico) < OPERACOES_MINIMAS:
            logger.warning(f"[DATA_INTEGRITY] Histórico insuficiente: {len(historico)} < {OPERACOES_MINIMAS}")
            return False
            
        # Verificar distribuição básica
        win_rate = (historico.count('WIN') / len(historico)) * 100  # MUDOU de 'V'
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
        # NOVO: Tentar ambas as tabelas para debug
        tables_to_try = ['tunder_bot_logs', 'scalping_accumulator_bot_logs']
        
        for table_name in tables_to_try:
            logger.info(f"[HISTORICO] Tentando tabela: {table_name}")
            try:
                response = supabase.table(table_name) \
                    .select('id, operation_result, timestamp') \
                    .order('timestamp', desc=True) \
                    .limit(OPERACOES_HISTORICO) \
                    .execute()
                
                if response.data and len(response.data) > 0:
                    logger.info(f"[HISTORICO] Sucesso na tabela: {table_name} ({len(response.data)} registros)")
                    
                    historico = [op['operation_result'] for op in response.data]
                    timestamps = [op['timestamp'] for op in response.data]
                    latest_operation_id = response.data[0]['id']
                    
                    # DEBUG dos dados encontrados
                    logger.info(f"[HISTORICO] Primeiros 5 resultados: {historico[:5]}")
                    logger.info(f"[HISTORICO] Tipos de resultado únicos: {set(historico)}")
                    
                    return historico, timestamps, latest_operation_id
                else:
                    logger.warning(f"[HISTORICO] Tabela {table_name} vazia ou sem dados")
                    
            except Exception as table_error:
                logger.warning(f"[HISTORICO] Erro na tabela {table_name}: {table_error}")
                continue
        
        # Se chegou aqui, nenhuma tabela funcionou
        logger.error("[HISTORICO] Nenhuma tabela de operações foi encontrada")
        return [], [], None
        
    except Exception as e:
        logger.error(f"[HISTORICO_ERROR] Erro geral: {e}")
        return [], [], None

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
            'strategy_confidence': confidence_level,
            'bot_name': BOT_NAME,
            'status': 'ACTIVE'
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
    """Cria registro na tabela strategy_results_tracking linkado com signal_id"""
    try:
        # Usar campos que existem na tabela e evitar duplicações
        data = {
            'signal_id': signal_id,
            'strategy_name': strategy_name,
            'strategy_confidence': confidence_level,
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
        
        # Determinar sucesso do padrão
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

# ===== IMPLEMENTAÇÃO DA ESTRATÉGIA WWL =====

def analisar_estrategia_wwl(historico: List[str]) -> Dict: 
    """ 
    Tunder Bot - Estratégia WWL: Analisa o histórico de operações em busca 
    do padrão WWL (Win-Win-Loss) nos últimos 3 resultados. 
    Filtro: Máximo 7 derrotas nas últimas 20 operações. 
    Assertividade Histórica: 78.6% 
    """ 
    strategy_name = "WWL" 
    logger.debug(f"[{strategy_name}] Iniciando análise...") 
    
    # NOVO DEBUG DETALHADO 
    logger.info(f"[{strategy_name}] Histórico recebido: {len(historico)} operações") 
    logger.info(f"[{strategy_name}] Primeiras 5: {historico[:5]}") 
    logger.info(f"[{strategy_name}] Verificando se >= 20 operações...") 
    
    try: 
        # Verificar dados suficientes (mínimo 20 para análise de derrotas) 
        if len(historico) < 20: 
            logger.warning(f"[{strategy_name}] INSUFICIENTE: {len(historico)} < 20") 
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': f"Datos insuficientes para {strategy_name} (necesario 20, encontrado {len(historico)})" 
            } 
        
        logger.info(f"[{strategy_name}] Dados suficientes. Verificando gatilhos...") 
        
        # ===== REGRA 1: VERIFICAR PADRÃO WWL ===== 
        # As 3 operações mais recentes devem ser Win-Win-Loss 
        padrao_wwl = ['WIN', 'WIN', 'LOSS'] 
        ultimas_3 = historico[:3] 
        
        logger.info(f"[{strategy_name}] Verificando Gatilho 1 (WWL)") 
        logger.info(f"[{strategy_name}] Sequência atual: {ultimas_3} vs {padrao_wwl}") 
        
        if ultimas_3 != padrao_wwl: 
            logger.info(f"[{strategy_name}] Padrão WWL não encontrado: {ultimas_3}") 
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': f"Patrón {strategy_name} no encontrado: {ultimas_3}" 
            } 
        
        logger.info(f"[{strategy_name}] GATILHO DETECTADO! Verificando filtros...") 
        
        # ===== REGRA 2: CONTAR DERROTAS NAS ÚLTIMAS 20 OPERAÇÕES ===== 
        ultimas_20 = historico[:20] 
        total_derrotas = ultimas_20.count('LOSS') 
        
        logger.info(f"[{strategy_name}] Analisando derrotas nas últimas 20 operações") 
        logger.info(f"[{strategy_name}] REGRA 2 - Contagem de derrotas nas últimas 20 operações") 
        logger.info(f"[{strategy_name}] Total de derrotas encontradas: {total_derrotas}") 
        logger.info(f"[{strategy_name}] Critério máximo permitido: 5 derrotas") 
        
        # Critério: Derrotas <= 5 
        if total_derrotas > 5: 
            logger.info(f"[{strategy_name}] ❌ REGRA 2 FALHOU: Muitas derrotas ({total_derrotas} > 5)") 
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': f"Muitas derrotas: {total_derrotas}/20 operações (máximo: 5)" 
            } 
        
        logger.info(f"[{strategy_name}] ✅ REGRA 2 APROVADA: Derrotas dentro do limite ({total_derrotas} <= 5)") 
        
        # ===== RESULTADO FINAL: TODAS AS REGRAS APROVADAS ===== 
        logger.info(f"[{strategy_name}] 🎯 === PADRÃO WWL COMPLETO DETECTADO ===") 
        logger.info(f"[{strategy_name}] ✅ REGRA 1: Padrão WWL confirmado") 
        logger.info(f"[{strategy_name}] ✅ REGRA 2: Derrotas adequadas ({total_derrotas}/5)") 
        logger.info(f"[{strategy_name}] 🔥 SINAL DE ENTRADA ATIVADO - Assertividade: 78.6%") 
        
        return { 
            'should_operate': True, 
            'strategy': strategy_name, 
            'confidence': 78.6, 
            'reason': f"Padrão WWL detectado com {total_derrotas} derrotas (≤5)", 
            'pattern_details': { 
                'trigger': 'WWL', 
                'total_derrotas_20_ops': total_derrotas, 
                'ultimas_3': ultimas_3 
            } 
        } 
        
    except Exception as e: 
        logger.error(f"[{strategy_name}] ERRO CRÍTICO: {e}") 
        logger.error(f"[{strategy_name}] Traceback: {traceback.format_exc()}") 
        return { 
            'should_operate': False, 
            'strategy': strategy_name, 
            'confidence': 0, 
            'reason': f"Erro na execução da estratégia: {str(e)}" 
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

@retry_supabase_operation(max_retries=3, delay=2)
def enviar_sinal_supabase_corrigido(supabase, signal_data: Dict) -> int:
    """Envia sinal e retorna o signal_id para linking"""
    try:
        signal_record = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': signal_data['should_operate'],
            'reason': signal_data['reason'],
            'strategy_used': signal_data['strategy'],
            'strategy_confidence': signal_data['confidence'],
            'losses_in_last_10_ops': signal_data.get('losses_ultimas_15', 0),
            'wins_in_last_5_ops': min(5, signal_data.get('wins_consecutivos', 0)),
            'historical_accuracy': signal_data['confidence'] / 100.0,
            'pattern_found_at': datetime.now().isoformat() if signal_data['should_operate'] else None,
            'operations_after_pattern': 0,
            'auto_disable_after_ops': 2,
            'available_strategies': 1,
            'filters_applied': [],
            'execution_time_ms': 0
        }
        
        response = supabase.table('radar_de_apalancamiento_signals').insert(signal_record).execute()
        
        if response.data and len(response.data) > 0:
            signal_id = response.data[0]['id']
            logger.info(f"[SIGNAL_SENT] Sinal enviado com ID: {signal_id}")
            return signal_id
        else:
            logger.error(f"[SIGNAL_ERROR] Resposta vazia")
            return None
            
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
        
        # Status da estratégia Vigilância de Regime
        status['strategies']['Vigilância de Regime'] = {
            'confidence_level': 75.32,
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
    """Ciclo com máquina de estados - ANALYZING/MONITORING (VERSÃO CORRIGIDA)"""
    try: 
        global bot_current_state, active_signal_data 
        
        logger.info(f"[CICLO] === CICLO ESTADO: {bot_current_state} ===") 
        
        historico, timestamps, latest_operation_id = buscar_operacoes_historico(supabase) 
        
        # NOVO DEBUG CRÍTICO 
        logger.info(f"[DEBUG] Histórico recebido: {len(historico)} operações") 
        if historico: 
            logger.info(f"[DEBUG] Primeiras 10 operações: {historico[:10]}") 
            logger.info(f"[DEBUG] Últimas 5 operações: {historico[-5:]}") 
        logger.info(f"[DEBUG] Latest operation ID: {latest_operation_id}") 
        
        if not historico: 
            dados_sem_historico = { 
                'should_operate': False, 
                'reason': 'Aguardando dados...', 
                'strategy': 'N/A', 
                'confidence': 0 
            } 
            enviar_sinal_supabase_corrigido(supabase, dados_sem_historico) 
            return { 
                'status': 'NO_DATA', 
                'message': 'Aguardando dados' 
            } 
 
        # NOVO: Validar dados antes de analisar 
        if not validar_integridade_historico(historico): 
            logger.error("[DEBUG] Validação de integridade FALHOU") 
            return {'status': 'VALIDATION_ERROR', 'message': 'Dados inválidos'} 
        else: 
            logger.info("[DEBUG] Validação de integridade PASSOU") 

        if bot_current_state == BotState.ANALYZING: 
            logger.info("[STATE] Estado ANALYZING - Buscando padrões") 
            logger.info(f"[DEBUG] Chamando analisar_estrategia_wwl com {len(historico)} operações") 
            
            resultado_analise = analisar_estrategia_wwl(historico) 
            
            # NOVO DEBUG DA ANÁLISE 
            logger.info(f"[DEBUG] Resultado da análise: {resultado_analise}") 
            
            if resultado_analise['should_operate']: 
                logger.info(f"[DEBUG] PADRÃO ENCONTRADO! Ativando monitoramento...") 
                sucesso_ativacao = activate_monitoring_state(resultado_analise, latest_operation_id, supabase) 
                if not sucesso_ativacao: 
                    logger.error("Falha ao ativar o estado de monitoramento.") 
                    sinal_de_falha = {**resultado_analise, 'should_operate': False, 'reason': 'Erro interno ao ativar o sinal'} 
                    enviar_sinal_supabase_corrigido(supabase, sinal_de_falha) 
            else: 
                logger.info("[DEBUG] Nenhum padrão encontrado. Enviando status de espera.") 
                enviar_sinal_supabase_corrigido(supabase, resultado_analise)

        elif bot_current_state == BotState.MONITORING:
            logger.info(f"[STATE] Estado MONITORING - Operações: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
            
            # 1. Verificar se novas operações ocorreram
            check_new_operations(supabase, latest_operation_id)
            
            # 2. Verificar se o monitoramento deve terminar
            if should_reset_to_analyzing():
                logger.info("[STATE_CHANGE] MONITORING → ANALYZING (monitoramento concluído)")
                resultado_final = {
                    'should_operate': False,
                    'reason': f"Estrategia {active_signal_data.get('strategy')} completada. Resultados: {monitoring_results}",
                    'strategy': active_signal_data.get('strategy'),
                    'confidence': 0  # Confiança zerada pois o ciclo acabou
                }
                enviar_sinal_supabase_corrigido(supabase, resultado_final)
                reset_bot_state(supabase)  # Finaliza o rastreamento no DB
            else:
                # 3. Se o monitoramento continua, REENVIAR o sinal ATIVO
                logger.info("[MONITORING] Mantendo sinal ativo.")
                remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count
                # Usamos os dados do sinal que foram salvos quando o padrão foi encontrado
                sinal_ativo_para_reenvio = {
                    'should_operate': True,
                    'reason': f"Patrón encontrado: {active_signal_data.get('strategy')} - esperando {remaining_ops} op.",
                    'strategy': active_signal_data.get('strategy'),
                    'confidence': active_signal_data.get('confidence'),
                    'pattern_details': active_signal_data.get('pattern_details', {})
                }
                enviar_sinal_supabase_corrigido(supabase, sinal_ativo_para_reenvio)

        return {
            'status': 'COMPLETED'
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
    logger.info("[MAIN] Estratégia: Vigilância de Regime (75.32%)")
    logger.info(f"[MAIN] Persistência: {PERSISTENCIA_OPERACOES} operações ou {PERSISTENCIA_TIMEOUT}s")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        logger.error("[MAIN] ERRO CRÍTICO: Não foi possível conectar ao Supabase")
        print("FAIL Erro crítico na conexão com Supabase")
        return
    
    # NUEVA INTEGRACIÓN: INICIALIZAR TELEGRAM
    print("\n📱 Inicializando Bot de Telegram...")
    telegram_iniciado = inicializar_telegram_bot()
    
    if telegram_iniciado:
        # Enviar mensaje de inicio del sistema
        try:
            enviar_mensaje_sistema("🚀 Radar Analisis Bot iniciado - Quantum+ activo", "SUCCESS")
        except:
            pass
    
    # Resetar estado inicial
    reset_bot_state()
    
    logger.info("[MAIN] ✅ Sistema inicializado com sucesso")
    print("\n🚀 RADAR ANALISIS SCALPING BOT COM ESTADOS ATIVO")
    print("📊 Sistema de gerenciamento de estado implementado")
    print("🔄 Estados: ANALYZING (busca padrões) → MONITORING (mantém sinal)")
    print("⏱️  Análise a cada 5 segundos")
    print("🎯 Estratégia: Vigilância de Regime (75.32%)")
    print(f"📱 Telegram: {'✅ ACTIVO' if telegram_activo else '❌ INACTIVO'}")
    print("🔍 Gatilho: WWL com filtros de saldo positivo ou negativo")
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
                # Exibir status baseado no estado atual do bot
                if bot_current_state == BotState.ANALYZING:
                    print(f"🔍 Analisando padrões... (Ciclo {ciclo_count})")
                elif bot_current_state == BotState.MONITORING:
                    remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count
                    strategy_name = active_signal_data.get('strategy', 'N/A') if active_signal_data else 'N/A'
                    print(f"👁️ Monitorando {strategy_name} - {monitoring_operations_count}/{PERSISTENCIA_OPERACOES} ops (restam {remaining_ops})")
                    
            elif status == 'NO_DATA':
                print(f"📊 {message}")
            elif status == 'ERROR':
                print(f"❌ {message}")
                logger.error(f"[MAIN] Erro no ciclo {ciclo_count}: {message}")
            
            # Aguardar próximo ciclo
            time.sleep(ANALISE_INTERVALO)
            
    except KeyboardInterrupt:
        logger.info("[MAIN] Bot interrumpido por el usuario")
        print("\n🛑 Bot interrumpido por el usuario")
        print(f"📊 Estado final: {bot_current_state}")
        if bot_current_state == BotState.MONITORING:
            print(f"⚡ Operações monitoreadas: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        print("🔄 Sistema con estados finalizado")
        
        # Enviar mensaje de finalización via Telegram
        if telegram_activo:
            try:
                enviar_mensaje_sistema("🛑 Sistema detenido por el usuario", "WARNING")
            except:
                pass
        
    except Exception as e:
        logger.error(f"[MAIN] ERROR CRÍTICO: {e}")
        logger.error(f"[MAIN] Traceback: {traceback.format_exc()}")
        print(f"\n💥 ERROR CRÍTICO: {e}")
        
        # Enviar error crítico via Telegram
        if telegram_activo:
            try:
                enviar_mensaje_sistema(f"💥 Error crítico: {str(e)[:100]}", "ERROR")
            except:
                pass
        
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

def testar_estrategia_wwl():
    """Testa a estratégia WWL com dados simulados"""
    try:
        print("\n🧪 Probando estrategia WWL con datos simulados...")
        
        # Teste 1: Padrão WWL com saldo positivo (deve aprovar)
        historico_teste_1 = ['WIN', 'WIN', 'LOSS'] + ['WIN'] * 17
        print(f"📊 Teste 1 - Padrão WWL com saldo positivo: {' '.join(historico_teste_1[:10])}...")
        
        resultado_1 = analisar_estrategia_wwl(historico_teste_1)
        print(f"🎯 Resultado: {resultado_1['should_operate']} - {resultado_1['confidence']:.2f}%")
        print(f"📝 Razón: {resultado_1['reason']}")
        
        # Teste 2: Padrão incorreto (não WWL) (deve rejeitar)
        historico_teste_2 = ['WIN', 'LOSS', 'WIN'] + ['WIN'] * 17
        print(f"\n📊 Teste 2 - Padrão incorreto (não WWL): {' '.join(historico_teste_2[:10])}...")
        
        resultado_2 = analisar_estrategia_wwl(historico_teste_2)
        print(f"🎯 Resultado: {resultado_2['should_operate']} - {resultado_2['confidence']:.2f}%")
        print(f"📝 Razón: {resultado_2['reason']}")
        
        # Teste 3: Dados insuficientes
        historico_teste_3 = ['WIN', 'WIN', 'LOSS'] + ['WIN'] * 5
        print(f"\n📊 Teste 3 - Dados insuficientes: {' '.join(historico_teste_3)}")
        
        resultado_3 = analisar_estrategia_wwl(historico_teste_3)
        print(f"🎯 Resultado: {resultado_3['should_operate']} - {resultado_3['confidence']:.2f}%")
        print(f"📝 Razón: {resultado_3['reason']}")
        
        print("\n✅ Prueba de la estrategia WWL completada")
        return True
        
    except Exception as e:
        print(f"❌ ERROR en la prueba de la estrategia: {e}")
        return False

def testar_nova_estrategia():
    """Função de teste dedicada para a estratégia WWL."""
    print("\n🧪 Probando la nueva estrategia WWL...")

    # Cenário 1: Deve ativar com padrão WWL e saldo adequado
    historico_gatilho1 = ['WIN', 'WIN', 'LOSS'] + ['WIN'] * 17
    print("\n--- Testando padrão WWL com saldo positivo ---")
    resultado1 = analisar_estrategia_wwl(historico_gatilho1)
    if resultado1['should_operate']:
        print(f"✅ SUCESSO: Padrão WWL ativado corretamente.")
        print(f"   Razón: {resultado1['reason']}")
    else:
        print(f"❌ FALHA: Padrão WWL não foi ativado.")
        print(f"   Razón: {resultado1['reason']}")

    # Cenário 2: Não deve ativar (padrão incorreto)
    historico_gatilho2 = ['WIN', 'LOSS', 'WIN'] + ['WIN'] * 17
    print("\n--- Testando padrão incorreto (não WWL) ---")
    resultado2 = analisar_estrategia_wwl(historico_gatilho2)
    if not resultado2['should_operate']:
        print(f"✅ SUCESSO: Padrão incorreto rejeitado corretamente.")
        print(f"   Razón: {resultado2['reason']}")
    else:
        print(f"❌ FALHA: Padrão incorreto foi ativado incorretamente.")
        print(f"   Razón: {resultado2['reason']}")

    # Cenário 3: Não deve ativar (saldo insuficiente)
    historico_falha = ['WIN', 'WIN', 'LOSS'] + ['LOSS'] * 17
    print("\n--- Testando cenário com saldo insuficiente ---")
    resultado3 = analisar_estrategia_wwl(historico_falha)
    if not resultado3['should_operate']:
        print(f"✅ SUCESSO: O padrão não foi ativado devido ao saldo negativo, como esperado.")
        print(f"   Razón: {resultado3['reason']}")
    else:
        print(f"❌ FALHA: O padrão foi ativado incorretamente.")
        print(f"   Razón: {resultado3['reason']}")

def testar_estrategia_wwl_local():
    """Testa a estratégia WWL com dados controlados - VERSÃO ATUALIZADA"""
    print("\n=== TESTE ESTRATÉGIA WWL - FILTRO DE DERROTAS ===")
    
    # Teste 1: WWL com poucas derrotas (DEVE ATIVAR)
    print("\n--- Teste 1: WWL com 5 derrotas (DEVE ATIVAR) ---")
    # Padrão WWL + 5 derrotas nas 20 operações = APROVADO
    historico_teste1 = ['WIN', 'WIN', 'LOSS'] + ['WIN'] * 12 + ['LOSS'] * 5
    
    resultado1 = analisar_estrategia_wwl(historico_teste1)
    print(f"Resultado: {resultado1['should_operate']}")
    print(f"Confiança: {resultado1['confidence']}")
    print(f"Razão: {resultado1['reason']}")
    
    # Teste 2: WWL com exatamente 5 derrotas (DEVE ATIVAR)
    print("\n--- Teste 2: WWL com exatamente 5 derrotas (DEVE ATIVAR) ---")
    # Padrão WWL + 5 derrotas nas 20 operações = APROVADO
    historico_teste2 = ['WIN', 'WIN', 'LOSS'] + ['WIN'] * 12 + ['LOSS'] * 5
    
    resultado2 = analisar_estrategia_wwl(historico_teste2)
    print(f"Resultado: {resultado2['should_operate']}")
    print(f"Confiança: {resultado2['confidence']}")
    print(f"Razão: {resultado2['reason']}")
    
    # Teste 3: WWL com 6 derrotas (NÃO DEVE ATIVAR)
    print("\n--- Teste 3: WWL com 6 derrotas (NÃO DEVE ATIVAR) ---")
    # Padrão WWL + 6 derrotas nas 20 operações = REJEITADO
    historico_teste3 = ['WIN', 'WIN', 'LOSS'] + ['WIN'] * 11 + ['LOSS'] * 6
    
    resultado3 = analisar_estrategia_wwl(historico_teste3)
    print(f"Resultado: {resultado3['should_operate']}")
    print(f"Confiança: {resultado3['confidence']}")
    print(f"Razão: {resultado3['reason']}")
    
    # Teste 4: Padrão errado (NÃO DEVE ATIVAR)
    print("\n--- Teste 4: Padrão WLL em vez de WWL ---")
    historico_teste4 = ['WIN', 'LOSS', 'LOSS'] + ['WIN'] * 15 + ['LOSS'] * 2
    
    resultado4 = analisar_estrategia_wwl(historico_teste4)
    print(f"Resultado: {resultado4['should_operate']}")
    print(f"Confiança: {resultado4['confidence']}")
    print(f"Razão: {resultado4['reason']}")
    
    # Validar resultados
    if (resultado1['should_operate'] and
        resultado2['should_operate'] and
        not resultado3['should_operate'] and
        not resultado4['should_operate']):
        print("\n✅ TODOS OS TESTES WWL PASSARAM!")
        return True
    else:
        print("\n❌ ALGUNS TESTES WWL FALHARAM!")
        return False

def executar_testes_completos():
    """Executa bateria completa de testes"""
    print("🔬 === EXECUTANDO TESTES COMPLETOS - TUNDER BOT WWL ===")
    
    # Teste 1: Conexão Supabase
    teste1 = testar_conexao_supabase()
    
    # Teste 2: Estratégia WWL
    teste2 = testar_estrategia_wwl()
    
    # Resultado final
    if teste1 and teste2:
        print("\n✅ TODOS OS TESTES PASSARAM")
        print("🚀 Tunder Bot WWL pronto para execução")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique la configuración antes de ejecutar")
        return False

# ===== PONTO DE ENTRADA =====

def testar_deteccao_padroes_local():
    """Testa detecção de padrões com dados controlados localmente"""
    print("\n=== TESTE DE DETECÇÃO DE PADRÕES ===")
    
    # Teste 1: 7 vitórias consecutivas e zero perdas nas últimas 15 (deve aprovar)
    print("\n--- Teste 1: 7 vitórias consecutivas sem perdas recentes (DEVE ATIVAR) ---")
    historico_teste1 = ['WIN'] * 7 + ['LOSS', 'WIN', 'WIN', 'WIN', 'WIN', 'WIN', 'WIN', 'WIN']
    
    resultado1 = analisar_estrategia_quantum_plus(historico_teste1)
    print(f"Resultado: {resultado1['should_operate']}")
    print(f"Confiança: {resultado1['confidence']}")
    print(f"Razão: {resultado1['reason']}")
    
    # Teste 2: 9 vitórias consecutivas mas com perdas recentes (deve rejeitar)
    print("\n--- Teste 2: 9 vitórias mas com perdas recentes (NÃO DEVE ATIVAR) ---")
    historico_teste2 = ['WIN'] * 9 + ['LOSS', 'WIN', 'WIN', 'LOSS', 'WIN', 'WIN', 'WIN', 'WIN']
    
    resultado2 = analisar_estrategia_quantum_plus(historico_teste2)
    print(f"Resultado: {resultado2['should_operate']}")
    print(f"Confiança: {resultado2['confidence']}")
    print(f"Razão: {resultado2['reason']}")
    
    # Teste 3: Dados insuficientes
    print("\n--- Teste 3: Dados Insuficientes (NÃO DEVE ATIVAR) ---")
    historico_teste3 = ['WIN'] * 5 + ['LOSS', 'WIN', 'WIN']  # Operações insuficientes
    
    resultado3 = analisar_estrategia_quantum_plus(historico_teste3)
    print(f"Resultado: {resultado3['should_operate']}")
    print(f"Confiança: {resultado3['confidence']}")
    print(f"Razão: {resultado3['reason']}")
    
    # Validar resultados
    if resultado1['should_operate'] and not resultado2['should_operate'] and not resultado3['should_operate']:
        print("\n✅ TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        return False


def probar_telegram():
    """Prueba la integración de Telegram (versión síncrona - OBSOLETA)"""
    print("⚠️ Esta función está obsoleta. Use 'python radar_tunder_new.py telegram' para probar con la versión asíncrona.")
    return False

async def probar_telegram_async():
    """Prueba la integración de Telegram de forma asíncrona y segura."""
    print("🧪 === PROBANDO INTEGRACIÓN DE TELEGRAM ===")
    
    # Inicializa o bot UMA VEZ
    if not inicializar_telegram():
        print("❌ Error al inicializar Telegram")
        return False

    print("✅ Telegram inicializado correctamente")
    
    # Dados de prueba
    test_signal = {
        'strategy': 'Bot - Tunder Bot', 'confidence': 72.0,
        'reason': 'Prueba de patrón detectado', 'should_operate': True
    }
    
    try:
        print("📤 Enviando alerta de prueba...")
        await enviar_alerta_patron(test_signal)
        print("✅ Alerta enviada correctamente")

        print("📤 Enviando resultado de prueba...")
        await enviar_resultado_operacion("Bot - Tunder Bot", 1, "V", 1)
        print("✅ Resultado enviado correctamente")

        print("📤 Enviando finalización de prueba...")
        await enviar_finalizacion_estrategia("Bot - Tunder Bot", ["V"], True)
        print("✅ Finalización enviada correctamente")

        print("🎉 ¡Todas las pruebas de Telegram exitosas!")
        return True

    except Exception as e:
        logger.error(f"[TELEGRAM] Error en las pruebas asíncronas: {e}")
        print("❌ Error en las pruebas de Telegram")
        return False


if __name__ == "__main__":
    import sys
    import asyncio # Importe asyncio aqui
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        # Comando de teste
        testar_nova_estrategia()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "telegram":
        # Comando para probar Telegram
        # Usa asyncio.run para gerenciar o loop corretamente
        asyncio.run(probar_telegram_async())
    elif len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "testlocal":
            # NOVO comando para testar sem banco
            testar_deteccao_padroes_local()
        elif comando == "testwwl":
            # Testar estratégia WWL específica
            testar_estrategia_wwl_local()
        elif comando == "testall":
            # Executar testes completos
            executar_testes_completos()
        elif comando == "status":
            # Mostrar status
            imprimir_status_detalhado()
        elif comando == "help":
            # Mostrar ajuda
            print("\n📖 TUNDER BOT WWL - Ajuda")
            print("="*50)
            print("Uso: python radar_tunder_new.py [comando]")
            print("\nComandos disponíveis:")
            print("  (sem comando) - Executar bot principal")
            print("  test         - Testar nova estratégia WWL")
            print("  telegram     - Probar integración de Telegram")
            print("  testlocal    - Testar detecção de padrões localmente")
            print("  testwwl      - Testar estratégia WWL específica")
            print("  testall      - Executar testes completos do sistema")
            print("  status       - Mostrar status detalhado")
            print("  help         - Mostrar esta ajuda")
            print("\n🎯 Estratégia implementada:")
            print("  • WWL: 78.6% assertividade com análise de saldo")
            print("\n📊 Gatilhos: Padrão WWL nas últimas 3 operações e saldo >= -$5.00 nas últimas 20 operações")
        else:
            print(f"❌ Comando desconhecido: {comando}")
            print("Use 'python radar_tunder_new.py help' para ver comandos disponíveis")
    else:
        # Executar bot principal
        print("🚀 Iniciando Tunder Bot WWL com integração Telegram automática...")
        
        # Inicializar Telegram
        print("\n📱 Inicializando Bot de Telegram...")
        inicializar_telegram_bot() # Esta função já trata o sucesso/falha
        
        # Executar bot principal
        print("🤖 Iniciando bot principal...")
        main_loop()

def main():
    """Função principal - ponto de entrada alternativo"""
    main_loop()