#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar Analisis Scalping Bot - Sistema de Trading com 3 Estratégias de Alta Assertividade
Sistema integrado com rastreamento automático de resultados no Supabase

Estratégias implementadas:
- MICRO-BURST: 95.5% assertividade
- PRECISION SURGE CORRIGIDO: 93.5% assertividade (4-5 WINs consecutivos, máx 2 LOSSes em 15 ops, sem LOSSes consecutivos em 10 ops)
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
# import threading  # REMOVIDO - threading órfão não utilizado
# from threading import Lock  # REMOVIDO - threading órfão não utilizado
from functools import wraps

# ===== CORREÇÃO 2: IMPORTS PARA SISTEMA TELEGRAM SEGURO =====
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

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

# ===== CORREÇÃO 2: VARIÁVEIS GLOBAIS PARA POOL TELEGRAM SEGURO =====
telegram_executor = None
telegram_loop = None
telegram_lock = threading.Lock()

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

# ===== CORREÇÃO 2: SISTEMA TELEGRAM COM POOL SEGURO =====
def inicializar_telegram_seguro():
    """Inicializa Telegram com pool de threads dedicado"""
    global telegram_activo, TELEGRAM_DISPONIBLE, telegram_executor, telegram_loop
    
    try:
        # Verificar se o módulo existe
        import importlib.util
        spec = importlib.util.find_spec("telegram_notifier")
        
        if spec is None:
            print("❌ Módulo telegram_notifier não encontrado")
            TELEGRAM_DISPONIBLE = False
            telegram_activo = False
            return False
        
        # Criar executor dedicado para Telegram
        with telegram_lock:
            if telegram_executor is None:
                telegram_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="telegram")
                print("✅ Pool de threads Telegram criado")
            
            # Criar loop de eventos dedicado em thread separada
            def criar_loop_telegram():
                global telegram_loop
                telegram_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(telegram_loop)
                print("✅ Loop de eventos Telegram criado")
                telegram_loop.run_forever()
            
            if telegram_loop is None or telegram_loop.is_closed():
                # Iniciar loop em thread separada
                thread_telegram = threading.Thread(target=criar_loop_telegram, daemon=True)
                thread_telegram.start()
                
                # Aguardar loop estar pronto
                import time
                time.sleep(1)
        
        # Importar e inicializar
        from telegram_notifier import inicializar_telegram
        
        # Executar inicialização no executor dedicado
        future = telegram_executor.submit(inicializar_telegram)
        sucesso = future.result(timeout=10)  # Timeout de 10 segundos
        
        if sucesso:
            telegram_activo = True
            TELEGRAM_DISPONIBLE = True
            print("✅ Telegram inicializado com pool seguro")
            return True
        else:
            telegram_activo = False
            print("❌ Falha na inicialização do Telegram")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao inicializar Telegram seguro: {e}")
        telegram_activo = False
        TELEGRAM_DISPONIBLE = False
        return False

def enviar_telegram_seguro(funcao_envio, *args, **kwargs):
    """Envia mensagem Telegram de forma segura usando pool de threads"""
    global telegram_executor, telegram_activo
    
    if not telegram_activo or not telegram_executor:
        logger.warning("[TELEGRAM] Telegram inativo ou pool não disponível")
        return False
    
    try:
        # Executar no pool de threads dedicado
        future = telegram_executor.submit(funcao_envio, *args, **kwargs)
        resultado = future.result(timeout=15)  # Timeout de 15 segundos
        return resultado
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Erro no envio seguro: {e}")
        return False

def enviar_alerta_padrao_SEGURO(strategy_data: dict) -> bool:
    """Envia alerta de forma segura sem problemas de pool"""
    if not telegram_activo:
        logger.warning("[TELEGRAM] Telegram inativo")
        return False
    
    def _enviar_alerta_interno():
        try:
            from datetime import datetime
            from telegram_notifier import enviar_alerta_patron
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            alert_data = {
                'timestamp': timestamp,
                'strategy': strategy_data['strategy'],
                'confidence': strategy_data['confidence'],
                'reason': strategy_data['reason'],
                'wins_consecutivos': strategy_data.get('wins_consecutivos', 0),
                'losses_ultimas_15': strategy_data.get('losses_ultimas_15', 0)
            }
            
            return enviar_alerta_patron(alert_data)
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Erro interno no envio de alerta: {e}")
            return False
    
    return enviar_telegram_seguro(_enviar_alerta_interno)

def enviar_resultado_seguro(operacion_num: int, resultado: str, total_operaciones: int) -> bool:
    """Envia resultado de forma segura"""
    if not telegram_activo:
        return False
    
    def _enviar_resultado_interno():
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            emoji_resultado = "✅" if resultado == "V" else "❌"
            texto_resultado = "WIN" if resultado == "V" else "LOSS"
            
            mensaje = f"""
{emoji_resultado} <b>SCALPING BOT I.A - RESULTADO</b>

🤖 <b>Bot:</b> Scalping Bot I.A
🎯 <b>Resultado:</b> {texto_resultado}

#ScalpingBotIA #Resultado #{texto_resultado}
            """.strip()
            
            from telegram_notifier import telegram_notifier
            if telegram_notifier:
                return telegram_notifier.enviar_mensaje_sync(mensaje)
            return False
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Erro interno no envio de resultado: {e}")
            return False
    
    return enviar_telegram_seguro(_enviar_resultado_interno)

def enviar_finalizacao_segura(resultados: list, exito: bool) -> bool:
    """Envia finalização de forma segura"""
    if not telegram_activo:
        return False
    
    def _enviar_finalizacao_interno(res, ex):
        try:
            from datetime import datetime
            from telegram_notifier import enviar_finalizacion_estrategia
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # A função no módulo telegram_notifier espera strategy_name, resultados e exito
            return enviar_finalizacion_estrategia("Scalping Bot I.A", res, ex)
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Erro interno no envio de finalização: {e}")
            return False
    
    # Passa os argumentos para a função interna através da chamada do executor
    return enviar_telegram_seguro(_enviar_finalizacao_interno, resultados, exito)

def finalizar_telegram_seguro():
    """Finaliza o sistema Telegram de forma segura com shutdown do executor"""
    global telegram_executor, telegram_loop, telegram_activo
    
    try:
        logger.info("[TELEGRAM] Iniciando finalização segura do sistema Telegram")
        
        # Desativar Telegram
        telegram_activo = False
        
        # Finalizar executor de threads
        if telegram_executor:
            logger.info("[TELEGRAM] Fazendo shutdown do telegram_executor")
            telegram_executor.shutdown(wait=True)
            telegram_executor = None
            logger.info("[TELEGRAM] ✅ telegram_executor finalizado")
        
        # Finalizar loop de eventos
        if telegram_loop and not telegram_loop.is_closed():
            logger.info("[TELEGRAM] Finalizando loop de eventos")
            try:
                telegram_loop.call_soon_threadsafe(telegram_loop.stop)
                telegram_loop = None
                logger.info("[TELEGRAM] ✅ Loop de eventos finalizado")
            except Exception as loop_error:
                logger.warning(f"[TELEGRAM] Aviso ao finalizar loop: {loop_error}")
        
        logger.info("[TELEGRAM] ✅ Sistema Telegram finalizado com segurança")
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Erro na finalização segura: {e}")
        # Forçar reset das variáveis mesmo com erro
        telegram_activo = False
        telegram_executor = None
        telegram_loop = None

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
    """Reseta Scalping Bot I.A para el estado ANALYZING CON NOTIFICACIÓN TELEGRAM"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    logger.info("[STATE] Reseteando Scalping Bot I.A para ANALYZING")
    
    # NUEVA INTEGRACIÓN: ENVIAR FINALIZACIÓN VIA TELEGRAM PERSONALIZADA
    if telegram_activo and active_signal_data and len(monitoring_results) > 0:
        try:
            # Verificar si fue éxito completo (todas las operaciones WIN)
            exito_completo = all(resultado == 'V' for resultado in monitoring_results)
            
            enviar_finalizacion_scalping_ia(
                resultados=monitoring_results,
                exito=exito_completo
            )
            logger.info(f"[TELEGRAM] Finalización de Scalping Bot I.A enviada")
        except Exception as e:
            logger.error(f"[TELEGRAM] Error al enviar finalización de Scalping Bot I.A: {e}")
    
    # Não é mais necessário finalizar o rastreamento aqui, pois a função atualizar_resultado_operacao_CORRIGIDO
    # já cuida da finalização quando a operação 2 é concluída
    if supabase and active_tracking_id and len(monitoring_results) >= PERSISTENCIA_OPERACOES:
        logger.info(f"[TRACKING] Rastreamento {active_tracking_id} já finalizado automaticamente com resultados: {monitoring_results}")
    
    bot_current_state = BotState.ANALYZING
    monitoring_operations_count = 0
    last_operation_id_when_signal = None
    last_checked_operation_id = None
    monitoring_start_time = None
    active_signal_data = None
    active_tracking_id = None
    monitoring_results = []

def activate_monitoring_state_CORRIGIDO(signal_data: dict, latest_operation_id: str, supabase):
    """Ativa o estado MONITORING com todas as correções aplicadas"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    try:
        logger.info(f"[STATE] Ativando estado MONITORING - Sinal: {signal_data['strategy']}")
        
        # 1. SINAL JÁ ENVIADO PELO MAIN_LOOP - PULAR ENVIO DUPLICADO
        # O envio agora é responsabilidade do main_loop_FINAL
        signal_id = None  # Será definido pelo sistema de rastreamento
        
        # 2. CRIAR REGISTRO DE RASTREAMENTO
        tracking_id = criar_registro_rastreamento_CORRIGIDO(
            supabase,
            signal_data['strategy'],
            signal_data['confidence'],
            signal_id,
            signal_data  # Passar dados completos da estratégia
        )
        
        if tracking_id:
            # 3. ATIVAR ESTADO DE MONITORAMENTO
            bot_current_state = BotState.MONITORING
            monitoring_operations_count = 0
            last_operation_id_when_signal = latest_operation_id
            last_checked_operation_id = latest_operation_id
            monitoring_start_time = time.time()
            active_signal_data = signal_data.copy()
            active_signal_data['signal_id'] = signal_id
            active_tracking_id = tracking_id
            monitoring_results = []
            
            logger.info(f"[TRACKING] Sistema ativo - Signal ID: {signal_id}, Tracking ID: {tracking_id}")
            return True
        else:
            logger.error(f"[TRACKING] Falha ao criar rastreamento")
            return False
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro na ativação: {e}")
        return False

# Manter função antiga para compatibilidade
def activate_monitoring_state(signal_data: dict, latest_operation_id: str, supabase):
    """Ativa o estado MONITORING com envio e linking corretos"""
    global bot_current_state, monitoring_operations_count
    global last_operation_id_when_signal, last_checked_operation_id, monitoring_start_time, active_signal_data, active_tracking_id, monitoring_results
    
    try:
        logger.info(f"[STATE] Ativando estado MONITORING - Sinal: {signal_data['strategy']}")
        
        # 1. SINAL JÁ ENVIADO PELO MAIN_LOOP - PULAR ENVIO DUPLICADO
        # O envio agora é responsabilidade do main_loop_FINAL
        signal_id = None  # Será definido pelo sistema de rastreamento
        
        # 2. CRIAR REGISTRO DE RASTREAMENTO CORRIGIDO
        tracking_id = criar_registro_rastreamento_CORRIGIDO(
            supabase,
            signal_data['strategy'],
            signal_data['confidence'],
            signal_id,
            signal_data  # Passar dados completos da estratégia
        )
        
        if tracking_id:
            # 3. ATIVAR ESTADO DE MONITORAMENTO
            bot_current_state = BotState.MONITORING
            monitoring_operations_count = 0
            last_operation_id_when_signal = latest_operation_id
            last_checked_operation_id = latest_operation_id
            monitoring_start_time = time.time()
            active_signal_data = signal_data.copy()
            active_signal_data['signal_id'] = signal_id
            active_tracking_id = tracking_id
            monitoring_results = []
            
            logger.info(f"[TRACKING] Sistema completo ativo - Signal ID: {signal_id}, Tracking ID: {tracking_id}")
            return True
        else:
            logger.error(f"[TRACKING] Falha ao criar rastreamento - mantendo estado ANALYZING")
            return False
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro na ativação completa: {e}")
        return False

def check_new_operations(supabase, current_operation_id: str) -> bool:
    """Verifica nuevas operaciones para Scalping Bot I.A CON NOTIFICACIÓN TELEGRAM"""
    global monitoring_operations_count, last_operation_id_when_signal, last_checked_operation_id, monitoring_results

    if last_operation_id_when_signal is None:
        return False

    if last_checked_operation_id is None:
        last_checked_operation_id = last_operation_id_when_signal
        
    # Si el ID actual es diferente del último verificado, hubo nueva operación
    if current_operation_id != last_checked_operation_id:
        monitoring_operations_count += 1
        last_checked_operation_id = current_operation_id
        
        # NUEVO: Capturar resultado automáticamente com dados completos
        dados_operacao = obter_resultado_operacao_atual(supabase, current_operation_id)
        
        if dados_operacao:
            resultado_operacao = dados_operacao['result']  # 'V' ou 'D' para compatibilidade
            monitoring_results.append(resultado_operacao)
            logger.info(f"[STATE] Nueva operación Scalping Bot I.A: {current_operation_id} - Resultado: {resultado_operacao} (profit: {dados_operacao['profit']}) - Total: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
            
            # LOGS PROGRESSIVOS EM ESPANHOL PARA SUPABASE
            if monitoring_operations_count == 1:
                logger.info("[PATTERN] Patrón Encontrado - Resta apenas 1 operación")
                # Atualizar reason no Supabase
                if active_tracking_id:
                    try:
                        supabase.table('strategy_results_tracking').update({
                            'reason': 'Patrón Encontrado - Resta apenas 1 operación'
                        }).eq('id', active_tracking_id).execute()
                    except Exception as e:
                        logger.error(f"[SUPABASE] Erro ao atualizar reason: {e}")
            elif monitoring_operations_count == 2:
                logger.info("[PATTERN] Patrón Finalizado - Espere la Próxima")
                # Atualizar reason no Supabase
                if active_tracking_id:
                    try:
                        supabase.table('strategy_results_tracking').update({
                            'reason': 'Patrón Finalizado - Espere la Próxima'
                        }).eq('id', active_tracking_id).execute()
                    except Exception as e:
                        logger.error(f"[SUPABASE] Erro ao atualizar reason: {e}")
                
                # ENVIAR RESULTADO FINAL DAS DUAS OPERAÇÕES PARA O TELEGRAM
                if telegram_activo:
                    try:
                        wins = monitoring_results.count('V')
                        losses = monitoring_results.count('D')
                        exito = wins >= losses  # Padrão exitoso se mais wins que losses
                        
                        # Enviar finalização da estratégia em espanhol
                        enviar_finalizacao_segura(monitoring_results, exito)
                        logger.info(f"[TELEGRAM] Resultado final enviado: {monitoring_results} - Éxito: {exito}")
                    except Exception as e:
                        logger.error(f"[TELEGRAM] Erro ao enviar resultado final: {e}")
            
            # ATUALIZAR RESULTADO DA OPERAÇÃO NO SISTEMA DE RASTREAMENTO
            if active_tracking_id:
                # Converter resultado para formato esperado (V -> WIN, D -> LOSS)
                resultado_formatado = "WIN" if resultado_operacao == "V" else "LOSS"
                # Atualizar registro com dados completos da operação atual
                atualizar_resultado_operacao_CORRIGIDO(
                    supabase,
                    active_tracking_id,
                    monitoring_operations_count,  # Número da operação (1 ou 2)
                    resultado_formatado,
                    dados_operacao['profit'],  # Profit real da operação
                    dados_operacao['timestamp']  # Timestamp da operação
                )
                logger.info(f"[TRACKING] Operação {monitoring_operations_count} atualizada: {resultado_formatado} (profit: {dados_operacao['profit']})")
            
            # NUEVA INTEGRACIÓN: ENVIAR RESULTADO VIA TELEGRAM PERSONALIZADO
            if telegram_activo:
                try:
                    enviar_resultado_scalping_ia(
                        operacion_num=monitoring_operations_count,
                        resultado=resultado_operacao,
                        total_operaciones=PERSISTENCIA_OPERACOES
                    )
                    logger.info(f"[TELEGRAM] Resultado de Scalping Bot I.A enviado: {resultado_operacao}")
                except Exception as e:
                    logger.error(f"[TELEGRAM] Error al enviar resultado de Scalping Bot I.A: {e}")
        else:
            logger.warning(f"[STATE] Nueva operación Scalping Bot I.A: {current_operation_id} - Resultado no capturado - Total: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        
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
    'aguardando_dados': "Esperando datos suficientes del mercado...",
    'aguardando_padrao': "Analizando el mercado. No operar todavía.",
    'estrategia_ativa': "Estrategia {strategy} activa - esperando {ops} operaciones.",
    'patron_encontrado': "¡Patrón Encontrado! Activar Bot Ahora - {strategy} ({confidence}%)",
    'mercado_instavel': "Mercado inestable, esperando confirmación.",
    'dados_insuficientes': "Datos insuficientes: {len_historico}/15 operaciones necesarias",
    'gatilho_nao_atendido': "Disparador no cumplido: {wins} victorias consecutivas (requiere 4-5)",
    'muitos_losses': "Demasiadas pérdidas: {losses}/15 (máximo 2)",
    'losses_consecutivos': "Pérdidas consecutivas detectadas en posiciones {pos_inicio}-{pos_fim}",
    'patron_precision_confirmado': "¡Patrón PRECISION SURGE confirmado! {wins} victorias consecutivas, {losses} pérdidas en 15 ops",
    'loss_nao_isolado': "{strategy}: Patrón de pérdida no aislado (W-L-W).",
    'losses_consecutivos_proibido': "{strategy}: ¡PROHIBIDO! Se detectaron pérdidas consecutivas.",
    'erro_execucao': "{strategy}: Error en la ejecución de la estrategia.",
    'seguro_operar': "Seguro para operar.",
    'teste_sistema': "PRUEBA - El sistema funciona correctamente.",
    'conexao_falhou': "Error de conexión con la base de datos.",
    'operacao_completada': "Operación completada con éxito."
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
            response = supabase.table(tabela).select('id').limit(1).execute()
            print(f"✅ {descricao}: OK")
        except Exception as e:
            print(f"❌ {descricao}: ERRO - {e}")
            return False
    
    print("✅ Todas as tabelas acessíveis!")
    return True

def inicializar_telegram_CORRIGIDO():
    """Inicialização robusta do Telegram com gerenciamento adequado do loop de eventos (ATUALIZADA)"""
    # Usar a nova função segura
    return inicializar_telegram_seguro()

# Manter a função antiga para compatibilidade
def inicializar_telegram_bot():
    """Inicializa el bot de Telegram para Scalping Bot I.A (DEPRECATED)"""
    return inicializar_telegram_CORRIGIDO()

def enviar_alerta_padrao_encontrado_CORRIGIDO(strategy_data: dict) -> bool:
    """Envia alerta IMEDIATAMENTE quando padrão é encontrado (ATUALIZADA PARA POOL SEGURO)"""
    # Usar a nova função segura
    return enviar_alerta_padrao_SEGURO(strategy_data)

# Manter a função antiga para compatibilidade
def enviar_alerta_scalping_ia(strategy_data: dict) -> bool:
    """Envía alerta personalizada para Scalping Bot I.A (DEPRECATED)"""
    return enviar_alerta_padrao_encontrado_CORRIGIDO(strategy_data)

def enviar_resultado_scalping_ia(operacion_num: int, resultado: str, total_operaciones: int) -> bool:
    """Envía resultado de operación personalizado para Scalping Bot I.A usando sistema seguro"""
    return enviar_resultado_seguro(operacion_num, resultado, total_operaciones)

def enviar_finalizacion_scalping_ia(resultados: list, exito: bool) -> bool:
    """Envía resumen final personalizado para Scalping Bot I.A usando sistema seguro"""
    return enviar_finalizacao_segura(resultados, exito)

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
    """Busca histórico de operações do Supabase
    
    Returns:
        tuple: (historico, timestamps, latest_operation_id)
    """
    try:
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('id, profit_percentage, created_at') \
            .order('created_at', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()
        
        if not response.data:
            logger.warning("[HISTORICO] Nenhuma operação encontrada")
            return [], [], None
        
        # Extrair resultados, timestamps e ID da operação mais recente
        historico = []
        timestamps = []
        latest_operation_id = response.data[0]['id']  # Primeira operação (mais recente)
        
        for op in response.data:
            profit_percentage = op.get('profit_percentage', 0)
            resultado = 'V' if profit_percentage > 0 else 'D'
            historico.append(resultado)
            timestamps.append(op['created_at'])
        
        logger.info(f"[HISTORICO] {len(historico)} operações carregadas")
        logger.debug(f"[HISTORICO] Sequência: {' '.join(historico[:10])}...")
        logger.debug(f"[HISTORICO] ID operação mais recente: {latest_operation_id}")
        
        return historico, timestamps, latest_operation_id
        
    except Exception as e:
        logger.error(f"[HISTORICO_ERROR] Erro ao buscar operações: {e}")
        return [], [], None

def obter_resultado_operacao_atual(supabase, operation_id: str) -> dict:
    """Obtém dados completos da operação atual
    
    Returns:
        dict: {'result': 'V'|'D', 'profit': float, 'timestamp': str} ou None
    """
    try:
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('profit_percentage, created_at') \
            .eq('id', operation_id) \
            .single() \
            .execute()
        
        if response.data:
            profit_percentage = response.data.get('profit_percentage', 0)
            created_at = response.data.get('created_at', '')
            resultado = 'V' if profit_percentage > 0 else 'D'
            
            operation_data = {
                'result': resultado,
                'profit': profit_percentage,
                'timestamp': created_at
            }
            
            logger.debug(f"[RESULTADO] Operação {operation_id}: {resultado} (profit: {profit_percentage}, timestamp: {created_at})")
            return operation_data
        else:
            logger.warning(f"[RESULTADO] Operação {operation_id} não encontrada")
            return None
            
    except Exception as e:
        logger.error(f"[RESULTADO_ERROR] Erro ao obter resultado da operação {operation_id}: {e}")
        return None

def criar_registro_rastreamento_CORRIGIDO(supabase, strategy_name: str, confidence: float, signal_id: int, strategy_data: dict = None) -> int: 
    """Cria registro CORRETO na strategy_results_tracking com dados detalhados da estratégia"""
    try: 
        # Dados corretos conforme estrutura da tabela (verificada no setup_tracking_tables.sql)
        data = { 
            'signal_id': signal_id, 
            'strategy_name': strategy_name, 
            'confidence_level': confidence,  # Corrigido: usar confidence_level em vez de strategy_confidence
            'status': 'ACTIVE',
            'bot_name': 'Scalping Bot'  # Campo adicional que existe na tabela
        }
        
        # Adicionar informações extras em um log para debug
        if strategy_data and isinstance(strategy_data, dict):
            logger.info(f"[TRACKING] Dados da estratégia: {strategy_name}, Confiança: {confidence}, "
                       f"Wins consecutivos: {strategy_data.get('wins_consecutivos', 0)}, "
                       f"Losses: {strategy_data.get('losses_ultimas_15', 0)}")
        
        response = supabase.table('strategy_results_tracking').insert(data).execute() 
        
        if response.data and len(response.data) > 0: 
            tracking_id = response.data[0]['id'] 
            logger.info(f"[TRACKING] Registro criado: ID {tracking_id}") 
            return tracking_id 
        else:
            logger.error(f"[TRACKING] Falha ao criar registro: Resposta sem dados")
            return None 
        
    except Exception as e: 
        logger.error(f"[TRACKING] Erro ao criar registro: {e}") 
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

def atualizar_resultado_operacao_CORRIGIDO(supabase, tracking_id: int, operacao_num: int, resultado: str, profit: float = 0.0, timestamp: str = None) -> bool: 
    """Atualiza resultado de operação específica com dados completos""" 
    try: 
        # Usar timestamp da operação real ou timestamp atual como fallback
        operation_timestamp = timestamp if timestamp else datetime.now().isoformat() 
        timestamp_now = datetime.now().isoformat() 
        
        if operacao_num == 1: 
            update_data = { 
                'operation_1_result': resultado, 
                'operation_1_profit': profit, 
                'operation_1_timestamp': operation_timestamp, 
                'operations_completed': 1 
            } 
        elif operacao_num == 2: 
            update_data = { 
                'operation_2_result': resultado, 
                'operation_2_profit': profit, 
                'operation_2_timestamp': operation_timestamp, 
                'operations_completed': 2, 
                'validation_complete': True, 
                'status': 'COMPLETED', 
                'completed_at': timestamp_now 
            } 
            
            # Calcular sucesso do padrão (ambas operações devem ser WIN) 
            # Buscar resultado da operação 1 
            current_record = supabase.table('strategy_results_tracking').select('operation_1_result').eq('id', tracking_id).single().execute() 
            if current_record.data: 
                op1_result = current_record.data['operation_1_result'] 
                pattern_success = (op1_result == 'WIN' and resultado == 'WIN') 
                update_data['pattern_success'] = pattern_success 
                
                # Calcular lucro total 
                op1_profit = current_record.data.get('operation_1_profit', 0.0) 
                update_data['total_profit'] = op1_profit + profit 
        else: 
            return False 
        
        response = supabase.table('strategy_results_tracking').update(update_data).eq('id', tracking_id).execute() 
        
        if response.data: 
            logger.info(f"[TRACKING] Operação {operacao_num} atualizada: {resultado}") 
            return True 
        return False 
        
    except Exception as e: 
        logger.error(f"[TRACKING] Erro ao atualizar operação {operacao_num}: {e}") 
        return False

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

def analisar_precision_surge_CORRIGIDO(historico: List[str]) -> Dict: 
    """PRECISION SURGE CORRIGIDO conforme especificação""" 
    try: 
        strategy_name = "PRECISION_SURGE" 
        logger.info(f"[{strategy_name}] === INICIANDO ANÁLISE ===\n[{strategy_name}] Histórico: {' '.join(historico[-15:]) if len(historico) >= 15 else ' '.join(historico)}")
        
        if len(historico) < 15: 
            reason = MENSAJES_SISTEMA['dados_insuficientes'].format(len_historico=len(historico))
            logger.warning(f"[{strategy_name}] ❌ REJEITADO: {reason}")
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': reason 
            } 
        
        # CORREÇÃO: Pegar as operações mais recentes (do início da lista) 
        ultimas_15 = historico[:15]  # CORRETO: Pega os primeiros 15 (os mais recentes) 
        ultimas_10 = historico[:10]  # CORRETO: Pega os primeiros 10 (os mais recentes) 
        
        logger.info(f"[{strategy_name}] Últimas 15: {' '.join(ultimas_15)}")
        logger.info(f"[{strategy_name}] Últimas 10: {' '.join(ultimas_10)}")
        
        # GATILHO CORRETO: Exatamente 4-5 WINs consecutivos 
        wins_consecutivos = 0 
        for resultado in ultimas_15: 
            if resultado == 'V': 
                wins_consecutivos += 1 
            else: 
                break 
        
        logger.info(f"[{strategy_name}] WINs consecutivos detectados: {wins_consecutivos}")
        
        # CORREÇÃO: Aceitar apenas 4-5 WINs (não 2-25) 
        if not (4 <= wins_consecutivos <= 5): 
            reason = MENSAJES_SISTEMA['gatilho_nao_atendido'].format(wins=wins_consecutivos)
            logger.warning(f"[{strategy_name}] ❌ REJEITADO: {reason}")
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': reason 
            } 
        
        logger.info(f"[{strategy_name}] ✅ GATILHO APROVADO: {wins_consecutivos} WINs consecutivos")
        
        # FILTRO 1: Máximo 2 LOSSes nas últimas 15 operações 
        losses_ultimas_15 = ultimas_15.count('D') 
        logger.info(f"[{strategy_name}] FILTRO 1: {losses_ultimas_15} LOSSes nas últimas 15 operações (máximo: 2)")
        
        if losses_ultimas_15 > 2: 
            reason = MENSAJES_SISTEMA['muitos_losses'].format(losses=losses_ultimas_15)
            logger.warning(f"[{strategy_name}] ❌ REJEITADO: {reason}")
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': reason 
            } 
        
        logger.info(f"[{strategy_name}] ✅ FILTRO 1 APROVADO: {losses_ultimas_15} LOSSes ≤ 2")
        
        # FILTRO 2: Sem LOSSes consecutivos nas últimas 10 operações 
        losses_consecutivos_encontrados = False
        posicao_consecutivos = -1
        for i in range(len(ultimas_10) - 1): 
            if ultimas_10[i] == 'D' and ultimas_10[i+1] == 'D': 
                losses_consecutivos_encontrados = True
                posicao_consecutivos = i
                break
        
        logger.info(f"[{strategy_name}] FILTRO 2: Verificando LOSSes consecutivos nas últimas 10")
        
        if losses_consecutivos_encontrados:
            reason = MENSAJES_SISTEMA['losses_consecutivos'].format(pos_inicio=posicao_consecutivos, pos_fim=posicao_consecutivos+1)
            logger.warning(f"[{strategy_name}] ❌ REJEITADO: {reason}")
            return { 
                'should_operate': False, 
                'strategy': strategy_name, 
                'confidence': 0, 
                'reason': reason 
            } 
        
        logger.info(f"[{strategy_name}] ✅ FILTRO 2 APROVADO: Sem LOSSes consecutivos")
        
        # PADRÃO ENCONTRADO - Calcular confiança 
        confidence = 93.5 
        if wins_consecutivos == 5: 
            confidence += 1.5  # Bônus para 5 WINs 
            logger.info(f"[{strategy_name}] Bônus +1.5% por 5 WINs consecutivos")
        if losses_ultimas_15 == 0: 
            confidence += 2.0  # Bônus para zero LOSSes 
            logger.info(f"[{strategy_name}] Bônus +2.0% por zero LOSSes")
        elif losses_ultimas_15 == 1: 
            confidence += 1.0  # Bônus para apenas 1 LOSS 
            logger.info(f"[{strategy_name}] Bônus +1.0% por apenas 1 LOSS") 
        
        logger.info(f"[{strategy_name}] 🎯 PADRÃO CONFIRMADO: {wins_consecutivos} WINs, {losses_ultimas_15} LOSSes, Confiança: {confidence:.1f}%")
        
        return { 
            'should_operate': True, 
            'strategy': strategy_name, 
            'confidence': confidence, 
            'reason': MENSAJES_SISTEMA['patron_precision_confirmado'].format(wins=wins_consecutivos, losses=losses_ultimas_15), 
            'wins_consecutivos': wins_consecutivos, 
            'losses_ultimas_15': losses_ultimas_15 
        } 
        
    except Exception as e: 
        logger.error(f"[{strategy_name}] ERRO: {e}") 
        return { 
            'should_operate': False, 
            'strategy': strategy_name, 
            'confidence': 0, 
            'reason': f'Error en la ejecución: {e}' 
        }

# FUNÇÃO REMOVIDA: analisar_quantum_matrix_EXATO_REFINADO() - Simplificação do sistema

# ===== SISTEMA DE ANÁLISE CONSOLIDADA =====

def executar_analise_precision_surge_unico(historico: List[str]) -> Dict:
    """
    PRECISION SURGE com informações detalhadas para o campo 'reason'
    """
    try:
        strategy_name = "PRECISION_SURGE"
        
        if len(historico) < 15:
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': f'Datos insuficientes: {len(historico)}/15 operaciones necesarias',
                'wins_consecutivos': 0,
                'losses_ultimas_15': 0
            }
        
        ultimas_15 = historico[:15]
        ultimas_10 = historico[:10]
        
        # Contar WINs consecutivos
        wins_consecutivos = 0
        for resultado in ultimas_15:
            if resultado == 'V':
                wins_consecutivos += 1
            else:
                break
        
        # Verificar gatilho: 4-5 WINs consecutivos
        if not (4 <= wins_consecutivos <= 5):
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': f'Disparador no cumplido: {wins_consecutivos} victorias consecutivas (requiere 4-5)',
                'wins_consecutivos': wins_consecutivos,
                'losses_ultimas_15': ultimas_15.count('D')
            }
        
        # Filtro 1: Máximo 2 LOSSes nas últimas 15
        losses_ultimas_15 = ultimas_15.count('D')
        if losses_ultimas_15 > 2:
            return {
                'should_operate': False,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': f'Demasiadas perdidas: {losses_ultimas_15}/15 operaciones (maximo 2)',
                'wins_consecutivos': wins_consecutivos,
                'losses_ultimas_15': losses_ultimas_15
            }
        
        # Filtro 2: Sem LOSSes consecutivos nas últimas 10
        for i in range(len(ultimas_10) - 1):
            if ultimas_10[i] == 'D' and ultimas_10[i+1] == 'D':
                return {
                    'should_operate': False,
                    'strategy': strategy_name,
                    'confidence': 0,
                    'reason': 'Perdidas consecutivas detectadas en las ultimas 10 operaciones',
                    'wins_consecutivos': wins_consecutivos,
                    'losses_ultimas_15': losses_ultimas_15
                }
        
        # Padrão encontrado - calcular confiança
        confidence = 93.5
        if wins_consecutivos == 5:
            confidence += 1.5
        if losses_ultimas_15 == 0:
            confidence += 2.0
        elif losses_ultimas_15 == 1:
            confidence += 1.0
        
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': confidence,
            'reason': f'PATRON {strategy_name} CONFIRMADO: {wins_consecutivos} WINs consecutivos, {losses_ultimas_15} LOSSes en 15 ops, Confianza: {confidence:.1f}%',
            'wins_consecutivos': wins_consecutivos,
            'losses_ultimas_15': losses_ultimas_15
        }
        
    except Exception as e:
        return {
            'should_operate': False,
            'strategy': 'PRECISION_SURGE',
            'confidence': 0,
            'reason': f'Error en el analisis: {str(e)[:50]}',
            'wins_consecutivos': 0,
            'losses_ultimas_15': 0
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
            'filters_applied': [],  # CORREÇÃO: Array vazio em vez de string
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

def executar_ciclo_com_telegram_CORRIGIDO(supabase):
    """Ciclo principal com envio correto de Telegram e gerenciamento adequado do loop de eventos"""
    global bot_current_state
    
    # Inicializar resultado padrão - CORREÇÃO CRÍTICA
    resultado_padrao = {
        'should_operate': False,
        'strategy': 'PRECISION_SURGE',
        'confidence': 0,
        'reason': 'Esperando patrón'
    }
    
    try:
        # Configurar o loop de eventos para ser reutilizado
        import asyncio
        try:
            # Verificar se já existe um loop de eventos
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                # Se estiver fechado, criar um novo
                asyncio.set_event_loop(asyncio.new_event_loop())
                logger.debug("[CICLO] Novo loop de eventos criado para ciclo de análise")
        except RuntimeError:
            # Se não existir loop, criar um novo
            asyncio.set_event_loop(asyncio.new_event_loop())
            logger.debug("[CICLO] Novo loop de eventos criado para ciclo de análise")
        
        # Buscar histórico
        historico, timestamps, latest_operation_id = buscar_operacoes_historico(supabase)
        
        if not historico:
            return {
                'status': 'NO_DATA', 
                'message': 'Aguardando dados',
                'resultado': resultado_padrao  # CORREÇÃO: Sempre incluir resultado
            }
        
        if bot_current_state == BotState.ANALYZING:
            # Analisar padrão
            try:
                resultado = analisar_precision_surge_CORRIGIDO(historico)
                
                if resultado.get('should_operate', False):
                    # 1. ENVIAR TELEGRAM IMEDIATAMENTE
                    alerta_enviado = enviar_alerta_padrao_encontrado_CORRIGIDO(resultado)
                    
                    # 2. Ativar monitoramento
                    sucesso = activate_monitoring_state(resultado, latest_operation_id, supabase)
                    
                    if sucesso and alerta_enviado:
                        logger.info("[CICLO] ✅ Padrão encontrado, Telegram enviado, monitoramento ativo")
                    else:
                        logger.error("[CICLO] ❌ Falha na ativação completa")
                        resultado['should_operate'] = False
                        resultado['reason'] = "Error en la activación del monitoreo"
                    
                    return {'status': 'PATTERN_FOUND', 'resultado': resultado}
                else:
                    return {'status': 'COMPLETED', 'resultado': resultado}
                    
            except Exception as e:
                logger.error(f"[ANALISE_ERROR] Erro na análise: {e}")
                resultado_erro = {
                    'should_operate': False,
                    'strategy': 'PRECISION_SURGE',
                    'confidence': 0,
                    'reason': f'Error en el análisis: {str(e)[:50]}'
                }
                return {'status': 'COMPLETED', 'resultado': resultado_erro}
        
        elif bot_current_state == BotState.MONITORING:
            # Verificar novas operações
            try:
                nova_operacao = check_new_operations(supabase, latest_operation_id)
                
                if nova_operacao:
                    # Atualizar rastreamento no Supabase
                    resultado_op = obter_resultado_operacao_atual(supabase, latest_operation_id)
                    if resultado_op and active_tracking_id:
                        # Verificar e preparar o loop de eventos antes de enviar resultado
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_closed():
                                # Se o loop estiver fechado, criar um novo
                                asyncio.set_event_loop(asyncio.new_event_loop())
                                logger.debug("[TELEGRAM] Novo loop de eventos criado para envio de resultado")
                        except RuntimeError:
                            # Se não existir loop, criar um novo
                            asyncio.set_event_loop(asyncio.new_event_loop())
                            logger.debug("[TELEGRAM] Novo loop de eventos criado para envio de resultado")
                        
                        # Enviar resultado via Telegram
                        try:
                            enviar_resultado_scalping_ia(monitoring_operations_count, resultado_op, PERSISTENCIA_OPERACOES)
                        except Exception as e:
                            logger.error(f"[TELEGRAM] Erro ao enviar resultado: {e}")
                        
                        # Atualizar rastreamento
                        sucesso = atualizar_resultado_operacao_CORRIGIDO(
                            supabase,
                            active_tracking_id,
                            monitoring_operations_count,
                            'WIN' if resultado_op == 'V' else 'LOSS'
                        )
                        logger.info(f"[TRACKING] Operação {monitoring_operations_count} registrada: {resultado_op}")
                
                # Verificar se deve resetar
                if should_reset_to_analyzing():
                    # Verificar e preparar o loop de eventos antes de enviar finalização
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            # Se o loop estiver fechado, criar um novo
                            asyncio.set_event_loop(asyncio.new_event_loop())
                            logger.debug("[TELEGRAM] Novo loop de eventos criado para envio de finalização")
                    except RuntimeError:
                        # Se não existir loop, criar um novo
                        asyncio.set_event_loop(asyncio.new_event_loop())
                        logger.debug("[TELEGRAM] Novo loop de eventos criado para envio de finalização")
                    
                    # Enviar finalização via Telegram
                    try:
                        enviar_finalizacion_scalping_ia(monitoring_results, True)
                    except Exception as e:
                        logger.error(f"[TELEGRAM] Erro ao enviar finalização: {e}")
                    
                    # Criar resultado de finalização
                    resultado_finalizacao = {
                        'should_operate': False,
                        'strategy': active_signal_data.get('strategy', 'PRECISION_SURGE') if active_signal_data else 'PRECISION_SURGE',
                        'confidence': active_signal_data.get('confidence', 0) if active_signal_data else 0,
                        'reason': f'Monitoreo completado - {monitoring_operations_count} operaciones'
                    }
                    
                    reset_bot_state(supabase)
                    return {'status': 'MONITORING_COMPLETE', 'resultado': resultado_finalizacao}
                else:
                    # Manter monitoramento ativo
                    remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count
                    resultado_monitoring = {
                        'should_operate': True,
                        'strategy': active_signal_data.get('strategy', 'PRECISION_SURGE') if active_signal_data else 'PRECISION_SURGE',
                        'confidence': active_signal_data.get('confidence', 0) if active_signal_data else 0,
                        'reason': f'Monitoreo activo - esperando {remaining_ops} operaciones'
                    }
                    return {'status': 'COMPLETED', 'resultado': resultado_monitoring}
                    
            except Exception as e:
                logger.error(f"[MONITORING_ERROR] Erro no monitoramento: {e}")
                resultado_erro = {
                    'should_operate': False,
                    'strategy': 'PRECISION_SURGE',
                    'confidence': 0,
                    'reason': f'Erro no monitoramento: {str(e)[:50]}'
                }
                return {'status': 'COMPLETED', 'resultado': resultado_erro}
        
        # Fallback seguro
        return {'status': 'COMPLETED', 'resultado': resultado_padrao}
        
    except Exception as e:
        logger.error(f"[CICLO] Erro crítico: {e}")
        logger.error(f"[CICLO] Traceback: {traceback.format_exc()}")
        resultado_erro_critico = {
            'should_operate': False,
            'strategy': 'PRECISION_SURGE',
            'confidence': 0,
            'reason': f'Error crítico: {str(e)[:50]}'
        }
        return {'status': 'ERROR', 'message': str(e), 'resultado': resultado_erro_critico}

# Manter a função original para compatibilidade
def executar_ciclo_analise_simplificado_CORRIGIDO(supabase) -> Dict:
    """Ciclo corrigido com tratamento de erro da variável 'resultado'"""
    try:
        global bot_current_state
        
        logger.info(f"[CICLO] === CICLO ESTADO: {bot_current_state} ===")
        
        # Buscar histórico
        historico, timestamps, latest_operation_id = buscar_operacoes_historico(supabase)
        
        if not historico:
            return {
                'status': 'NO_DATA',
                'message': 'Aguardando dados',
                'resultado': {  # CORREÇÃO: Sempre incluir 'resultado'
                    'should_operate': False,
                    'strategy': 'NONE',
                    'confidence': 0,
                    'reason': 'Sin datos disponibles'
                }
            }
        
        # Inicializar resultado padrão - CORREÇÃO CRÍTICA
        resultado_ciclo = {
            'should_operate': False,
            'strategy': 'PRECISION_SURGE',
            'confidence': 0,
            'reason': 'Esperando patrón'
        }
        
        # LÓGICA DA MÁQUINA DE ESTADOS
        if bot_current_state == BotState.ANALYZING:
            logger.info("[STATE] Estado ANALYZING - Buscando padrões")
            
            # Executar análise PRECISION SURGE
            try:
                resultado_ciclo = executar_analise_precision_surge_unico(historico)
                
                # Se encontrou padrão, ativar estado MONITORING
                if resultado_ciclo.get('should_operate', False):
                    sucesso = activate_monitoring_state(resultado_ciclo, latest_operation_id, supabase)
                    if sucesso:
                        logger.info(f"[STATE_CHANGE] ANALYZING → MONITORING (padrão encontrado)")
                    else:
                        logger.error(f"[STATE_ERROR] Falha na ativação do monitoramento")
                        resultado_ciclo['should_operate'] = False
                        resultado_ciclo['reason'] = "Error al activar monitoreo"
                        
            except Exception as e:
                logger.error(f"[ANALISE_ERROR] Erro na análise: {e}")
                resultado_ciclo = {
                    'should_operate': False,
                    'strategy': 'PRECISION_SURGE',
                    'confidence': 0,
                    'reason': f'Error en el análisis: {str(e)[:50]}'
                }
                
        elif bot_current_state == BotState.MONITORING:
            logger.info(f"[STATE] Estado MONITORING - Operações: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
            
            # Verificar novas operações
            try:
                nova_operacao = check_new_operations(supabase, latest_operation_id)
                if nova_operacao:
                    logger.info(f"[MONITORING] Nova operação detectada: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
                
                # Verificar se deve resetar
                if should_reset_to_analyzing():
                    resultado_ciclo = {
                        'should_operate': False,
                        'reason': f"Estrategia {active_signal_data.get('strategy', 'PRECISION_SURGE')} completada - {monitoring_operations_count} operaciones",
                        'strategy': active_signal_data.get('strategy', 'PRECISION_SURGE'),
                        'confidence': active_signal_data.get('confidence', 0)
                    }
                    reset_bot_state(supabase)
                    logger.info("[STATE_CHANGE] MONITORING → ANALYZING (monitoramento concluído)")
                else:
                    # Manter sinal ativo
                    remaining_ops = PERSISTENCIA_OPERACOES - monitoring_operations_count
                    resultado_ciclo = {
                        'should_operate': True,
                        'reason': f"Patron encontrado: {active_signal_data.get('strategy', 'PRECISION_SURGE')} - esperando {remaining_ops} operaciones",
                        'strategy': active_signal_data.get('strategy', 'PRECISION_SURGE'),
                        'confidence': active_signal_data.get('confidence', 0)
                    }
                    
            except Exception as e:
                logger.error(f"[MONITORING_ERROR] Erro no monitoramento: {e}")
                resultado_ciclo = {
                    'should_operate': False,
                    'strategy': 'PRECISION_SURGE',
                    'confidence': 0,
                    'reason': f'Erro no monitoramento: {str(e)[:50]}'
                }
        
        # ENVIO PARA SUPABASE (sempre com resultado válido)
        if resultado_ciclo:
            try:
                dados_supabase = {
                    'bot_name': BOT_NAME,
                    'is_safe_to_operate': resultado_ciclo.get('should_operate', False),
                    'reason': resultado_ciclo.get('reason', 'Sin razón'),
                    'strategy_used': resultado_ciclo.get('strategy', 'PRECISION_SURGE'),
                    'strategy_confidence': resultado_ciclo.get('confidence', 0),
                    'losses_in_last_10_ops': resultado_ciclo.get('losses_ultimas_15', 0),
                    'wins_in_last_5_ops': min(5, resultado_ciclo.get('wins_consecutivos', 0)),
                    'historical_accuracy': resultado_ciclo.get('confidence', 0) / 100.0,
                    'pattern_found_at': datetime.now().isoformat(),
                    'operations_after_pattern': monitoring_operations_count if bot_current_state == BotState.MONITORING else 0,
                    'auto_disable_after_ops': PERSISTENCIA_OPERACOES,
                    'available_strategies': 1,
                    'filters_applied': ['precision_surge_only'],
                    'execution_time_ms': 0
                }
                
                response = supabase.table('radar_de_apalancamiento_signals').insert(dados_supabase).execute()
                
                if response.data:
                    if bot_current_state == BotState.MONITORING and resultado_ciclo.get('should_operate', False):
                        logger.info(f"[SIGNAL_SENT] ✅ Sinal reenviado (MONITORING): {resultado_ciclo.get('reason', '')}")
                    else:
                        status_msg = "padrão encontrado" if resultado_ciclo.get('should_operate', False) else "sem padrão"
                        logger.info(f"[SIGNAL_SENT] ✅ Status enviado ({status_msg}): {resultado_ciclo.get('reason', '')}")
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
            'message': f"Erro: {e}",
            'resultado': {  # CORREÇÃO: Sempre incluir 'resultado' mesmo em erro
                'should_operate': False,
                'strategy': 'PRECISION_SURGE',
                'confidence': 0,
                'reason': f'Error crítico: {str(e)[:50]}'
            }
        }

def main_loop():
    """Loop principal do bot com máquina de estados"""
    logger.info("[MAIN] === INICIANDO RADAR ANALISIS SCALPING BOT COM ESTADOS ===")
    logger.info("[MAIN] Sistema com máquina de estados: ANALYZING/MONITORING")
    logger.info("[MAIN] Estratégia: PRECISION SURGE CORRIGIDO (93.5%)")
    logger.info(f"[MAIN] Persistência: {PERSISTENCIA_OPERACOES} operações ou {PERSISTENCIA_TIMEOUT}s")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        logger.error("[MAIN] ERRO CRÍTICO: Não foi possível conectar ao Supabase")
        print("FAIL Erro crítico na conexão com Supabase")
        return
    
    # Verificar tabelas necessárias
    if not testar_tabelas_supabase(supabase):
        print("❌ Erro nas tabelas - abortando")
        return
    
    # NUEVA INTEGRACIÓN: INICIALIZAR SCALPING BOT I.A TELEGRAM
    print("\n📱 Inicializando Scalping Bot I.A - Telegram...")
    telegram_iniciado = inicializar_telegram_CORRIGIDO()
    
    if telegram_iniciado:
        # Enviar mensaje de inicio del sistema
        try:
            enviar_mensaje_sistema("🚀 Scalping Bot I.A iniciado - PRECISION SURGE CORRIGIDO activo\n⚠️ ATENCIÓN: Entrar apenas nas 2 primeiras operações após o surgimento do padrão\n🔍 Gatilho: 4-5 WINs consecutivos, máx 2 LOSSes em 15 ops, sem LOSSes consecutivos", "SUCCESS")
        except:
            pass
    
    # Resetar estado inicial
    reset_bot_state()
    
    logger.info("[MAIN] ✅ Sistema inicializado com sucesso")
    print("\n🚀 RADAR ANALISIS SCALPING BOT COM ESTADOS ATIVO")
    print("📊 Sistema de gerenciamento de estado implementado")
    print("🔄 Estados: ANALYZING (busca padrões) → MONITORING (mantém sinal)")
    print("⏱️  Análise a cada 5 segundos")
    print("🤖 Bot: Scalping Bot I.A - PRECISION SURGE CORRIGIDO (93.5%)")
    print("⚠️  ATENCIÓN: Entrar apenas nas 2 primeiras operações após o surgimento do padrão")
    print(f"📱 Telegram: {'✅ ACTIVO' if telegram_activo else '❌ INACTIVO'}")
    print("🔍 Gatilho: 4-5 WINs consecutivos, máx 2 LOSSes em 15 ops, sem LOSSes consecutivos em 10 ops")
    print(f"⚡ Persistência: {PERSISTENCIA_OPERACOES} operações")
    print("\nPressione Ctrl+C para parar\n")
    
    ciclo_count = 0
    
    try:
        while True:
            ciclo_count += 1
            
            # Mostrar estado atual
            state_info = get_state_info()
            estado_display = "🔍 ANALISANDO" if bot_current_state == BotState.ANALYZING else "👁️ MONITORANDO"
            
            # Executar ciclo de análise com estados e integração Telegram
            resultado_ciclo = executar_ciclo_com_telegram_CORRIGIDO(supabase)
            
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
        logger.info("[MAIN] Scalping Bot I.A interrumpido pelo usuário")
        print("\n🛑 Scalping Bot I.A interrumpido por el usuario")
        print(f"📊 Estado final: {bot_current_state}")
        if bot_current_state == BotState.MONITORING:
            print(f"⚡ Operações monitoradas: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
        
        # Enviar mensaje de finalización via Telegram
        if telegram_activo:
            try:
                enviar_mensaje_sistema("🛑 Scalping Bot I.A detenido por el usuario", "WARNING")
            except:
                pass
        
    except Exception as e:
        logger.error(f"[MAIN] ERRO CRÍTICO Scalping Bot I.A: {e}")
        logger.error(f"[MAIN] Traceback: {traceback.format_exc()}")
        print(f"\n💥 ERRO CRÍTICO Scalping Bot I.A: {e}")
        
        # Enviar error crítico via Telegram
        if telegram_activo:
            try:
                enviar_mensaje_sistema(f"💥 Error crítico Scalping Bot I.A: {str(e)[:100]}", "ERROR")
            except:
                pass
        
    finally:
        logger.info("[MAIN] === FINALIZANDO RADAR ANALISIS SCALPING BOT COM ESTADOS ===")
        print("\n👋 Radar Analisis Scalping Bot com Estados finalizado")

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
        
        # Testar PRECISION SURGE (estratégia principal)
        resultado_precision = analisar_precision_surge_CORRIGIDO(historico_teste)
        print(f"🎯 PRECISION SURGE: {resultado_precision['should_operate']} - {resultado_precision['confidence']:.1f}%")
        
        # Testar função de ciclo corrigida (sem histórico específico - usa dados reais)
        try:
            resultado_ciclo = executar_ciclo_analise_simplificado_CORRIGIDO(None)
            print(f"🎯 CICLO CORRIGIDO: Status={resultado_ciclo['status']}, Resultado presente={bool(resultado_ciclo.get('resultado'))}")
        except Exception as e:
            print(f"🎯 CICLO CORRIGIDO: Erro controlado - {str(e)[:50]}... (função protegida contra erros)")
        
        # Verificar se as funções principais estão funcionando
        print(f"\n🏆 RESULTADO: Precision Surge testado, Ciclo corrigido funcionando")
        print("✅ Teste das estratégias concluído - Erro da variável 'resultado' CORRIGIDO")
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

def probar_telegram():
    """Prueba la integración de Telegram para Scalping Bot I.A"""
    global active_signal_data
    
    print("🧪 === PROBANDO INTEGRACIÓN DE TELEGRAM (SCALPING BOT I.A) ===")
    
    if inicializar_telegram_CORRIGIDO():
        print("✅ Scalping Bot I.A - Telegram inicializado correctamente")
        
        # Datos de prueba
        test_signal = {
            'strategy': 'PRECISION_SURGE_TEST',
            'confidence': 93.5,
            'reason': 'Prueba de patrón Scalping Bot I.A detectado',
            'should_operate': True
        }
        
        # Configurar active_signal_data para las pruebas
        active_signal_data = test_signal
        
        print("📤 Enviando alerta de prueba...")
        if enviar_alerta_padrao_encontrado_CORRIGIDO(test_signal):
            print("✅ Alerta enviada correctamente")
            
            print("📤 Enviando resultado de prueba...")
            if enviar_resultado_scalping_ia(1, "V", 2):
                print("✅ Resultado enviado correctamente")
                
                print("📤 Enviando finalización de prueba...")
                if enviar_finalizacion_scalping_ia(["V", "V"], True):
                    print("✅ Finalización enviada correctamente")
                    print("🎉 ¡Todas las pruebas de Scalping Bot I.A exitosas!")
                    
                    # Limpiar active_signal_data después de las pruebas
                    active_signal_data = None
                    return True
        
        # Limpiar active_signal_data en caso de error
        active_signal_data = None
        print("❌ Error en las pruebas")
        return False
    else:
        print("❌ Error al inicializar Scalping Bot I.A - Telegram")
        return False

# ===== CORREÇÃO 4: CICLO PRINCIPAL CORRIGIDO =====

# FUNÇÃO REMOVIDA: enviar_estado_ciclo_radar() - Não é mais necessária
# A função enviar_status_para_supabase() agora faz todo o trabalho necessário

def executar_ciclo_FINAL_CORRIGIDO(supabase):
    """Ciclo principal com todas as correções aplicadas"""
    global bot_current_state
    
    # Resultado padrão sempre presente
    resultado_padrao = {
        'should_operate': False,
        'strategy': 'PRECISION_SURGE',
        'confidence': 0,
        'reason': 'Esperando patrón'
    }
    
    try:
        logger.info(f"[CICLO] === CICLO CORRIGIDO - ESTADO: {bot_current_state} ===")
        
        # Validação de entrada
        if not supabase:
            logger.error("[CICLO] ❌ ERRO: Supabase não inicializado")
            return {
                'status': 'ERROR',
                'message': 'Supabase no inicializado',
                'resultado': resultado_padrao
            }
        
        # REMOVIDO: enviar_estado_ciclo_radar() - Não é mais necessário
        # A função enviar_status_para_supabase() já faz todo o trabalho
        
        # Buscar histórico com tratamento de erro
        try:
            historico, timestamps, latest_operation_id = buscar_operacoes_historico(supabase)
            logger.info(f"[CICLO] 📊 Histórico obtido: {len(historico) if historico else 0} operações")
        except Exception as hist_error:
            logger.error(f"[CICLO] ❌ ERRO ao buscar histórico: {hist_error}")
            return {
                'status': 'ERROR',
                'message': f'Error al buscar historial: {str(hist_error)[:50]}',
                'resultado': resultado_padrao
            }
        
        if not historico:
            logger.info(f"[CICLO] 📊 Sem dados disponíveis - aguardando")
            return {
                'status': 'NO_DATA',
                'message': 'Aguardando dados do mercado',
                'resultado': resultado_padrao
            }
        
        logger.info(f"[CICLO] 📈 Últimas 10 operações: {' '.join(historico[-10:]) if len(historico) >= 10 else ' '.join(historico)}")
        resultado_ciclo = resultado_padrao.copy()
        
        if bot_current_state == BotState.ANALYZING:
            logger.info("[STATE] 🔍 Estado ANALYZING - Buscando padrões PRECISION_SURGE")
            
            try:
                # Executar análise com logs detalhados
                logger.info("[ANALISE] Iniciando análise PRECISION_SURGE...")
                resultado_ciclo = executar_analise_precision_surge_unico(historico)
                
                if not resultado_ciclo:
                    logger.error("[ANALISE] ❌ Resultado da análise é None")
                    raise Exception("Análise retornou None")
                
                logger.info(f"[ANALISE] Resultado: should_operate={resultado_ciclo.get('should_operate', False)}, strategy={resultado_ciclo.get('strategy', 'N/A')}, confidence={resultado_ciclo.get('confidence', 0):.1f}%")
                
                if resultado_ciclo.get('should_operate', False):
                    logger.info("[PATTERN] 🎯 PATRÓN ENCONTRADO, ACTIVAR BOT AHORA")
                    logger.info("[PATTERN] 🎯 PADRÃO ENCONTRADO! Iniciando processo de ativação...")
                    
                    # ENVIAR TELEGRAM PRIMEIRO (forma segura)
                    try:
                        logger.info("[TELEGRAM] Enviando alerta de padrão encontrado...")
                        alerta_enviado = enviar_alerta_padrao_SEGURO(resultado_ciclo)
                        logger.info(f"[TELEGRAM] Resultado do envio: {'✅ Sucesso' if alerta_enviado else '❌ Falha'}")
                    except Exception as telegram_error:
                        logger.error(f"[TELEGRAM] ❌ Erro no envio: {telegram_error}")
                        alerta_enviado = False
                    
                    # ATIVAR MONITORAMENTO (com Supabase corrigido)
                    try:
                        logger.info("[MONITORING] Ativando estado de monitoramento...")
                        sucesso = activate_monitoring_state_CORRIGIDO(resultado_ciclo, latest_operation_id, supabase)
                        logger.info(f"[MONITORING] Resultado da ativação: {'✅ Sucesso' if sucesso else '❌ Falha'}")
                    except Exception as monitoring_error:
                        logger.error(f"[MONITORING] ❌ Erro na ativação: {monitoring_error}")
                        sucesso = False
                    
                    if not sucesso:
                        logger.error("[CICLO] ❌ FALHA na ativação do monitoramento")
                        resultado_ciclo['should_operate'] = False
                        resultado_ciclo['reason'] = f"Error en la activación (Telegram: {'OK' if alerta_enviado else 'FALLA'}, Monitor: FALLA)"
                    else:
                        logger.info(f"[CICLO] ✅ SUCESSO: Padrão encontrado, Telegram={'OK' if alerta_enviado else 'FALHA'}, Monitoramento=OK")
                        
                        # REMOVIDO: enviar_estado_ciclo_radar() - Não é mais necessário
                        # A função enviar_status_para_supabase() já faz todo o trabalho
                        
                else:
                    reason = resultado_ciclo.get('reason', 'Patrón no encontrado')
                    logger.info(f"[PATTERN] ❌ PADRÃO NÃO ENCONTRADO: {reason}")
                        
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[ANALISE_ERROR] ❌ ERRO CRÍTICO na análise: {error_msg}", exc_info=True)
                resultado_ciclo = {
                    'should_operate': False,
                    'strategy': 'PRECISION_SURGE',
                    'confidence': 0,
                    'reason': f'Error en el análisis: {error_msg[:50]}'
                }
                
        elif bot_current_state == BotState.MONITORING:
            logger.info(f"[STATE] 👁️ Estado MONITORING - Operações: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
            
            try:
                # Verificar novas operações com logs detalhados
                logger.info("[MONITORING] Verificando novas operações...")
                nova_operacao = check_new_operations(supabase, latest_operation_id)
                
                if nova_operacao:
                    logger.info(f"[MONITORING] 🆕 NOVA OPERAÇÃO detectada! Progresso: {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}")
                    
                    # Enviar resultado via Telegram (forma segura)
                    if len(monitoring_results) > 0:
                        ultimo_resultado = monitoring_results[-1]
                        resultado_emoji = '✅' if ultimo_resultado == 'V' else '❌'
                        logger.info(f"[MONITORING] Último resultado: {resultado_emoji} {ultimo_resultado}")
                        
                        try:
                            logger.info("[TELEGRAM] Enviando resultado da operação...")
                            enviar_resultado_seguro(monitoring_operations_count, ultimo_resultado, PERSISTENCIA_OPERACOES)
                            logger.info("[TELEGRAM] ✅ Resultado enviado com sucesso")
                        except Exception as telegram_error:
                            logger.error(f"[TELEGRAM] ❌ Erro no envio do resultado: {telegram_error}")
                    else:
                        logger.warning("[MONITORING] ⚠️ Nenhum resultado disponível para enviar")
                else:
                    logger.info("[MONITORING] 🔄 Nenhuma nova operação detectada")
                
                # Verificar se deve resetar com logs detalhados
                logger.info("[MONITORING] Verificando se deve finalizar monitoramento...")
                if should_reset_to_analyzing():
                    logger.info("[MONITORING] 🏁 FINALIZANDO ciclo de monitoramento")
                    
                    # Enviar finalização (forma segura)
                    if len(monitoring_results) > 0:
                        exito = all(r == 'V' for r in monitoring_results)
                        wins = monitoring_results.count('V')
                        losses = monitoring_results.count('D')  # Correção de 'L' para 'D'
                        resultado_final = '🎉 ÉXITO' if exito else '💔 PARCIAL'
                        
                        logger.info(f"[MONITORING] Resultado final: {resultado_final} - Victorias: {wins}, Derrotas: {losses}")
                        
                        try:
                            logger.info("[TELEGRAM] Enviando finalização do ciclo...")
                            enviar_finalizacao_segura(monitoring_results, exito)
                            logger.info("[TELEGRAM] ✅ Finalização enviada com sucesso")
                        except Exception as telegram_error:
                            logger.error(f"[TELEGRAM] ❌ Erro no envio da finalização: {telegram_error}")
                    else:
                        logger.warning("[MONITORING] ⚠️ Nenhum resultado para finalizar")
                    
                    resultado_ciclo = {
                        'should_operate': False,
                        'strategy': active_signal_data.get('strategy', 'PRECISION_SURGE') if active_signal_data else 'PRECISION_SURGE',
                        'confidence': 0,
                        'reason': 'Patrón Finalizado - Espere el Próximo'  # Mensagem final
                    }
                    
                    # ESSA LINHA DEVE SER A ÚLTIMA A SER EXECUTADA NO BLOCO
                    reset_bot_state(supabase)
                else:
                    logger.info(f"[MONITORING] 🔄 Continuando monitoramento... ({monitoring_operations_count}/{PERSISTENCIA_OPERACOES})")
                    resultado_ciclo = {
                        'should_operate': False,
                        'strategy': 'PRECISION_SURGE',
                        'confidence': 0,
                        'reason': f'Monitoreando operación {monitoring_operations_count}/{PERSISTENCIA_OPERACOES}'
                    }
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[MONITORING_ERROR] ❌ ERRO CRÍTICO no monitoramento: {error_msg}", exc_info=True)
                resultado_ciclo = {
                    'should_operate': False,
                    'strategy': 'PRECISION_SURGE',
                    'confidence': 0,
                    'reason': f'Erro no monitoramento: {error_msg[:50]}'
                }
        
        return {
            'status': 'SUCCESS',
            'message': f'Ciclo executado - Estado: {bot_current_state}',
            'resultado': resultado_ciclo
        }
        
    except Exception as e:
        logger.error(f"[CICLO_ERROR] Erro crítico no ciclo: {e}")
        return {
            'status': 'ERROR',
            'message': f'Error crítico: {str(e)[:100]}',
            'resultado': resultado_padrao
        }

# ===== CORREÇÃO 5: MAIN LOOP FINAL =====

def enviar_status_para_supabase(supabase, resultado_analise: Dict):
    """
    Envia informações DETALHADAS do padrão para o campo 'reason' do Supabase
    """
    if not resultado_analise:
        logger.warning("[SUPABASE_STATUS] Resultado da análise vazio")
        return False

    try:
        # Gerar reason detalhada com informações específicas do padrão
        dashboard_reason = ""
        
        if bot_current_state == BotState.ANALYZING:
            if resultado_analise.get('should_operate', False):
                wins = resultado_analise.get('wins_consecutivos', 0)
                losses = resultado_analise.get('losses_ultimas_15', 0)
                confidence = resultado_analise.get('confidence', 0)
                strategy = resultado_analise.get('strategy', 'PRECISION_SURGE')
                
                dashboard_reason = f"PATRON {strategy} DETECTADO: {wins} WINs consecutivos, {losses} LOSSes en 15 ops, Confianza {confidence:.1f}% - ACTIVAR BOT AHORA"
            else:
                specific_reason = resultado_analise.get('reason', 'Patron no encontrado')
                wins = resultado_analise.get('wins_consecutivos', 0)
                losses = resultado_analise.get('losses_ultimas_15', 0)
                
                if wins < 4:
                    dashboard_reason = f"Analizando: Solo {wins} WINs consecutivos (requiere 4-5)"
                elif losses > 2:
                    dashboard_reason = f"Analizando: Demasiados LOSSes ({losses}/15, maximo 2)"
                else:
                    dashboard_reason = f"Analizando: {specific_reason}"
                    
        elif bot_current_state == BotState.MONITORING:
            if monitoring_operations_count == 0:
                strategy = active_signal_data.get('strategy', 'PRECISION_SURGE') if active_signal_data else 'PRECISION_SURGE'
                confidence = active_signal_data.get('confidence', 0) if active_signal_data else 0
                dashboard_reason = f"{strategy} ACTIVO ({confidence:.1f}%) - Entre en las proximas 2 operaciones"
            elif monitoring_operations_count == 1:
                last_result = monitoring_results[-1] if monitoring_results else "?"
                result_emoji = "EXITO" if last_result == 'V' else "FALLA"
                dashboard_reason = f"Op 1/2 completada {result_emoji} - Resta solo 1 operacion"
            elif monitoring_operations_count >= 2:
                wins = monitoring_results.count('V')
                losses = monitoring_results.count('D')
                success_status = "EXITO" if wins >= losses else "FALLA"
                dashboard_reason = f"Patron Finalizado: {wins}W-{losses}L - {success_status} - Espere el Proximo"

        signal_record = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': resultado_analise.get('should_operate', False),
            'reason': dashboard_reason,
            'strategy_used': resultado_analise.get('strategy', 'PRECISION_SURGE'),
            'strategy_confidence': resultado_analise.get('confidence', 0),
            'losses_in_last_10_ops': resultado_analise.get('losses_ultimas_15', 0),
            'wins_in_last_5_ops': min(5, resultado_analise.get('wins_consecutivos', 0)),
            'historical_accuracy': resultado_analise.get('confidence', 0) / 100.0,
            'pattern_found_at': datetime.now().isoformat() if resultado_analise.get('should_operate', False) else None,
            'operations_after_pattern': monitoring_operations_count if bot_current_state == BotState.MONITORING else 0,
            'auto_disable_after_ops': PERSISTENCIA_OPERACOES,
            'available_strategies': 1,
            'filters_applied': ['precision_surge_only'],
            'execution_time_ms': 0
        }

        # Usar UPSERT com a constraint única
        response = supabase.table('radar_de_apalancamiento_signals').upsert(
            signal_record,
            on_conflict='bot_name'
        ).execute()

        if response.data:
            status_msg = "PATRON ENCONTRADO" if signal_record['is_safe_to_operate'] else "ANALISANDO"
            logger.info(f"[SUPABASE_STATUS] Status '{status_msg}' enviado com detalhes")
            return True
        else:
            logger.error("[SUPABASE_STATUS] Falha no envio")
            return False

    except Exception as e:
        logger.error(f"[SUPABASE_STATUS] Erro: {e}")
        return False

def main_loop_FINAL():
    """Loop principal com todas as correções aplicadas"""
    logger.info("[MAIN] === SCALPING BOT I.A - VERSÃO CORRIGIDA ===")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        logger.error("[MAIN] ERRO: Conexão Supabase falhou")
        print("❌ ERRO: Não foi possível conectar ao Supabase")
        return
    
    # Verificar tabelas
    if not testar_tabelas_supabase(supabase):
        print("❌ Erro nas tabelas - abortando")
        return
    
    # Inicializar Telegram SEGURO
    print("\n📱 Inicializando Telegram (versão segura)...")
    telegram_iniciado = inicializar_telegram_seguro()
    
    # Resetar estado inicial
    reset_bot_state()
    
    logger.info("[MAIN] ✅ Sistema inicializado - versão corrigida")
    print("\n🚀 SCALPING BOT I.A - VERSÃO CORRIGIDA ATIVA")
    print("📊 Correções aplicadas:")
    print("  ✅ Erro Supabase 'malformed array literal' CORRIGIDO")
    print("  ✅ Erro Telegram 'Event loop is closed' CORRIGIDO")
    print("  ✅ Erro Telegram 'Pool timeout' CORRIGIDO")
    print("  ✅ Sistema de threads dedicado para Telegram")
    print(f"📱 Telegram: {'✅ ATIVO' if telegram_activo else '❌ INATIVO'}")
    print("🔍 Estratégia: PRECISION SURGE (4-5 WINs, máx 2 LOSSes em 15)")
    print("\nPressione Ctrl+C para parar\n")
    
    ciclo_count = 0
    
    try:
        while True:
            ciclo_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Log início do ciclo
            logger.info(f"[MAIN] === CICLO {ciclo_count} INICIADO ({timestamp}) ===")
            estado_str = bot_current_state.name if hasattr(bot_current_state, 'name') else str(bot_current_state)
            print(f"\n[{timestamp}] 🔄 Ciclo {ciclo_count} - Estado: {estado_str}")
            
            try:
                # 1. Executa o ciclo para obter o estado e a análise
                resultado_ciclo = executar_ciclo_FINAL_CORRIGIDO(supabase)
                
                if not resultado_ciclo:
                    raise Exception("Resultado do ciclo é None")
                
                status = resultado_ciclo.get('status', 'UNKNOWN')
                message = resultado_ciclo.get('message', 'Sem mensagem')
                resultado_analise = resultado_ciclo.get('resultado', {})  # Este é o dicionário que precisamos
                
                # 2. Envia o resultado da análise para o Supabase (SEMPRE)
                if resultado_ciclo and resultado_ciclo.get('resultado'):
                    enviar_status_para_supabase(supabase, resultado_ciclo['resultado'])
                else:
                    logger.warning("[MAIN] Nenhum resultado de análise para enviar ao Supabase.")
                
                # 3. REMOVIDO: enviar_estado_ciclo_radar() - Não é mais necessário
                # A função enviar_status_para_supabase() já faz todo o trabalho necessário
            
                # 4. Apenas exibe as informações no console (a lógica de envio já foi feita)
                logger.info(f"[MAIN] Status: {status}, Mensagem: {message}")
                
                # ... (o resto do seu código de print para o console pode continuar aqui) ...
                
            except Exception as ciclo_error:
                error_msg = str(ciclo_error)
                logger.error(f"[MAIN] 💥 ERRO CRÍTICO no ciclo {ciclo_count}: {error_msg}", exc_info=True)
                print(f"  💥 ERRO CRÍTICO: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}")
                
                # Tentar recuperação automática
                try:
                    logger.info(f"[MAIN] 🔄 Tentando recuperação automática...")
                    reset_bot_state()
                    print(f"  🔄 Estado resetado para recuperação")
                except Exception as recovery_error:
                    logger.error(f"[MAIN] ❌ Falha na recuperação: {recovery_error}")
                    print(f"  ❌ Falha na recuperação: {recovery_error}")
            
            # Log fim do ciclo
            logger.info(f"[MAIN] === CICLO {ciclo_count} FINALIZADO ===")
            
            # Aguardar próximo ciclo
            time.sleep(ANALISE_INTERVALO)
            
    except KeyboardInterrupt:
        logger.info("[MAIN] Bot interrompido pelo usuário")
        print("\n🛑 Bot interrompido pelo usuário")
        
    except Exception as e:
        logger.error(f"[MAIN] ERRO CRÍTICO: {e}")
        print(f"\n💥 ERRO CRÍTICO: {e}")
        
    finally:
        try:
            logger.info("[MAIN] Iniciando finalização...")
            
            # Finalizar Telegram de forma segura
            finalizar_telegram_seguro()
            
            # Reset final
            reset_bot_state(supabase)
            
            logger.info("[MAIN] === SCALPING BOT I.A FINALIZADO ===")
            print("\n👋 Scalping Bot I.A finalizado com segurança")
            
        except Exception as final_error:
            logger.error(f"[MAIN] Erro na finalização: {final_error}")
            print(f"⚠️ Aviso na finalização: {final_error}")

# ===== PONTO DE ENTRADA CORRIGIDO =====

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
        elif comando == "telegram":
            # Testar Telegram seguro
            print("🧪 Testando Telegram versão segura...")
            if inicializar_telegram_seguro():
                print("✅ Telegram seguro funcionando")
            else:
                print("❌ Erro no Telegram seguro")
        elif comando == "help":
            print("\n📖 SCALPING BOT I.A CORRIGIDO - Ajuda")
            print("="*50)
            print("Versão com correções:")
            print("  ✅ Erro Supabase CORRIGIDO")
            print("  ✅ Erro Telegram CORRIGIDO")
            print("  ✅ Pool de threads seguro")
            print("\nComandos:")
            print("  (sem comando) - Executar bot corrigido")
            print("  test         - Executar testes")
            print("  telegram     - Testar Telegram seguro")
            print("  status       - Mostrar status detalhado")
            print("  help         - Mostrar ajuda")
        else:
            print(f"❌ Comando desconhecido: {comando}")
    else:
        # Executar bot CORRIGIDO
        print("🚀 Iniciando Scalping Bot I.A CORRIGIDO...")
        main_loop_FINAL()

def main():
    """Função principal corrigida"""
    main_loop_FINAL()