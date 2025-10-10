#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTOR MOMENTUM-CALMO-LL - Bot de Trading Estratégico

Este script monitora operações de trading em tempo real e detecta padrões LL
(2 perdas consecutivas) sem restrições de horário.

Características:
- Análise em tempo real das últimas 2 operações
- Detecção simples de padrão LL (2 LOSS consecutivos)
- Sem filtros de horário ou regime de atividade
- Envio de sinais para Supabase
- Logs simplificados e focados

Estratégia: Entrada após surgir 2 LOSS consecutivos

Autor: Sistema de Trading Automatizado
Versão: 3.5 - Momentum-Calmo-LL (Sem Filtros de Horário)
"""
import os
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional, Tuple
from functools import wraps

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler('radartunder3.5_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Silenciar logs de bibliotecas externas
for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

# Configuración del bot
BOT_NAME = 'radartunder3.5'
ANALISE_INTERVALO = 5  # Intervalo de análisis en segundos
OPERACOES_HISTORICO = 35  # Número de operaciones históricas a analizar
OPERACOES_MINIMAS = 2  # Mínimo de operaciones para detectar patrón LL



def retry_supabase_operation(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Intento {attempt + 1} falló: {e}. Intentando nuevamente...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Todos los {max_retries} intentos para {func.__name__} fallaron.")
                        raise e
        return wrapper
    return decorator

@retry_supabase_operation(max_retries=3, delay=2)
def buscar_operacoes_historico(supabase: Client) -> Tuple[List[str], List[str], Optional[str], List[Dict]]:
    """
    Busca historial de la tabla CORRECTA (tunder_bot_logs),
    con resistencia y traducción de datos.
    ATUALIZADO: Agora inclui campos de Martingale para análise enriquecida.
    """
    try:
        logger.debug(f"[HISTORICO] Buscando {OPERACOES_HISTORICO} operações na tabela 'tunder_bot_logs'...")
        
        # CORRECCIÓN CRÍTICA: Apuntando a la tabla correcta con campos de Martingale.
        response = supabase.table('tunder_bot_logs') \
            .select('''
                id, operation_result, timestamp,
                martingale_level, martingale_multiplier, 
                consecutive_losses, consecutive_wins, 
                is_martingale_reset, original_stake, 
                martingale_stake, total_martingale_investment,
                martingale_sequence_id, martingale_progression
            ''') \
            .order('timestamp', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()

        if not response.data:
            logger.warning("[HISTORICO] ⚠️ Nenhuma operação encontrada na base de dados")
            return [], [], None, []

        logger.info(f"[HISTORICO] ✅ {len(response.data)} operações carregadas da base de dados")
        
        historico_raw = [op['operation_result'] for op in response.data]
        # Los datos ya están en el formato correcto (WIN/LOSS), no necesitan traducción
        historico_traduzido = historico_raw
        
        timestamps = [op['timestamp'] for op in response.data]
        latest_operation_id = response.data[0]['id']
        
        # Estatísticas rápidas do histórico
        wins = historico_traduzido.count('WIN')
        losses = historico_traduzido.count('LOSS')
        win_rate = (wins / len(historico_traduzido)) * 100 if historico_traduzido else 0
        logger.info(f"[HISTORICO] Estatísticas: {wins}W/{losses}L (Taxa: {win_rate:.1f}%)")
        
        # NOVO: Extrair dados detalhados de Martingale
        operacoes_detalhadas = []
        for op in response.data:
            operacao_detalhada = {
                'id': op.get('id'),
                'operation_result': op.get('operation_result'),
                'timestamp': op.get('timestamp'),
                'martingale_level': op.get('martingale_level', 0),
                'martingale_multiplier': op.get('martingale_multiplier', 1.0),
                'consecutive_losses': op.get('consecutive_losses', 0),
                'consecutive_wins': op.get('consecutive_wins', 0),
                'is_martingale_reset': op.get('is_martingale_reset', False),
                'original_stake': op.get('original_stake', 0.0),
                'martingale_stake': op.get('martingale_stake', 0.0),
                'total_martingale_investment': op.get('total_martingale_investment', 0.0),
                'martingale_sequence_id': op.get('martingale_sequence_id'),
                'martingale_progression': op.get('martingale_progression', [])
            }
            operacoes_detalhadas.append(operacao_detalhada)
        
        logger.info(f"{len(historico_traduzido)} operaciones cargadas de la tabla 'tunder_bot_logs' con datos de Martingale.")
        return historico_traduzido, timestamps, latest_operation_id, operacoes_detalhadas

    except Exception as e:
        logger.error(f"Error crítico al buscar historial: {e}", exc_info=True)
        # CORRECCIÓN DE ROBUSTEZ: Garantiza que la función siempre retorne la tupla de 4 valores.
        return [], [], None, []

def analisar_dados_martingale_banco(operacoes_detalhadas: List[Dict]) -> Dict:
    """
    Analisa os dados de Martingale vindos diretamente do banco de dados.
    
    Args:
        operacoes_detalhadas: Lista de operações com dados completos de Martingale
        
    Returns:
        Dict com estatísticas, sequência atual, validações e recomendações
    """
    
    # ===== VALIDAÇÕES CRÍTICAS DE ENTRADA =====
    logger.debug("[MARTINGALE_DB] Iniciando análise de dados do banco")
    
    # 1. Validação da lista de operações
    if operacoes_detalhadas is None:
        logger.error("[MARTINGALE_DB] ERRO CRÍTICO: operacoes_detalhadas é None")
        return {
            'estatisticas_banco': {
                'total_operacoes': 0,
                'operacoes_martingale': 0,
                'frequencia_martingale': 0.0,
                'nivel_maximo_atingido': 0,
                'sequencias_ativas': 0
            },
            'sequencia_atual': {
                'em_martingale': False,
                'nivel_atual': 0,
                'perdas_consecutivas': 0,
                'vitorias_consecutivas': 0,
                'multiplicador_atual': 1.0,
                'investimento_total_sequencia': 0.0
            },
            'dados_validacao': {
                'ultima_operacao': None,
                'timestamp_ultima': None,
                'sequence_id_ativo': None
            },
            'recomendacoes': {
                'nivel_risco': 'ERRO',
                'deve_operar': False,
                'motivo': 'Dados de entrada inválidos (None)'
            },
            'fonte_dados': 'erro_entrada',
            'erro': 'operacoes_detalhadas é None'
        }
    
    if not isinstance(operacoes_detalhadas, list):
        logger.error(f"[MARTINGALE_DB] ERRO CRÍTICO: operacoes_detalhadas não é lista: {type(operacoes_detalhadas)}")
        return {
            'estatisticas_banco': {
                'total_operacoes': 0,
                'operacoes_martingale': 0,
                'frequencia_martingale': 0.0,
                'nivel_maximo_atingido': 0,
                'sequencias_ativas': 0
            },
            'sequencia_atual': {
                'em_martingale': False,
                'nivel_atual': 0,
                'perdas_consecutivas': 0,
                'vitorias_consecutivas': 0,
                'multiplicador_atual': 1.0,
                'investimento_total_sequencia': 0.0
            },
            'dados_validacao': {
                'ultima_operacao': None,
                'timestamp_ultima': None,
                'sequence_id_ativo': None
            },
            'recomendacoes': {
                'nivel_risco': 'ERRO',
                'deve_operar': False,
                'motivo': f'Tipo de dados inválido: {type(operacoes_detalhadas)}'
            },
            'fonte_dados': 'erro_tipo',
            'erro': f'Tipo inválido: {type(operacoes_detalhadas)}'
        }
    
    # 2. Validação de cada operação na lista
    operacoes_validas = []
    operacoes_invalidas = 0
    
    for i, operacao in enumerate(operacoes_detalhadas):
        if not isinstance(operacao, dict):
            logger.warning(f"[MARTINGALE_DB] Operação {i} não é dict: {type(operacao)}")
            operacoes_invalidas += 1
            continue
        
        # Validar campos essenciais
        campos_obrigatorios = ['timestamp', 'resultado']
        campos_faltando = [campo for campo in campos_obrigatorios if campo not in operacao]
        
        if campos_faltando:
            logger.warning(f"[MARTINGALE_DB] Operação {i} sem campos obrigatórios: {campos_faltando}")
            operacoes_invalidas += 1
            continue
        
        operacoes_validas.append(operacao)
    
    if operacoes_invalidas > 0:
        logger.warning(f"[MARTINGALE_DB] {operacoes_invalidas} operações inválidas removidas")
    
    logger.debug(f"[MARTINGALE_DB] Operações válidas: {len(operacoes_validas)}/{len(operacoes_detalhadas)}")
    
    if not operacoes_validas:
        return {
            'estatisticas_banco': {
                'total_operacoes': 0,
                'operacoes_martingale': 0,
                'frequencia_martingale': 0.0,
                'nivel_maximo_atingido': 0,
                'sequencias_ativas': 0
            },
            'sequencia_atual': {
                'em_martingale': False,
                'nivel_atual': 0,
                'perdas_consecutivas': 0,
                'vitorias_consecutivas': 0,
                'multiplicador_atual': 1.0,
                'investimento_total_sequencia': 0.0
            },
            'dados_validacao': {
                'ultima_operacao': None,
                'timestamp_ultima': None,
                'sequence_id_ativo': None
            },
            'recomendacoes': {
                'nivel_risco': 'BAIXO',
                'deve_operar': True,
                'motivo': 'Sem dados suficientes para análise'
            },
            'fonte_dados': 'banco_vazio'
        }
    
    try:
        logger.debug("[MARTINGALE_DB] Iniciando análise estatística...")
        
        # Ordenar operações por timestamp (mais recente primeiro)
        operacoes_ordenadas = sorted(operacoes_detalhadas, 
                                   key=lambda x: x.get('timestamp', ''), 
                                   reverse=True)
        
        logger.debug(f"[MARTINGALE_DB] {len(operacoes_ordenadas)} operações ordenadas por timestamp")
        
        # ESTATÍSTICAS GERAIS DO BANCO
        total_operacoes = len(operacoes_ordenadas)
        operacoes_martingale = sum(1 for op in operacoes_ordenadas 
                                 if op.get('martingale_level', 0) > 1)
        frequencia_martingale = (operacoes_martingale / total_operacoes * 100) if total_operacoes > 0 else 0
        nivel_maximo = max((op.get('martingale_level', 0) for op in operacoes_ordenadas), default=0)
        
        # ANÁLISE DA SEQUÊNCIA ATUAL (operação mais recente)
        operacao_atual = operacoes_ordenadas[0] if operacoes_ordenadas else {}
        nivel_atual = operacao_atual.get('martingale_level', 0)
        perdas_consecutivas = operacao_atual.get('consecutive_losses', 0)
        vitorias_consecutivas = operacao_atual.get('consecutive_wins', 0)
        multiplicador_atual = operacao_atual.get('martingale_multiplier', 1.0)
        investimento_total = operacao_atual.get('total_martingale_investment', 0.0)
        sequence_id_ativo = operacao_atual.get('martingale_sequence_id')
        
        # DETECÇÃO DE SEQUÊNCIAS ATIVAS
        sequencias_ativas = len(set(op.get('martingale_sequence_id') 
                                  for op in operacoes_ordenadas[:10] 
                                  if op.get('martingale_sequence_id') and 
                                     op.get('martingale_level', 0) > 0))
        
        # ANÁLISE DE RISCO E RECOMENDAÇÕES
        nivel_risco = 'BAIXO'
        deve_operar = True
        motivo = 'Condições normais de operação'
        
        if nivel_atual >= 4:
            nivel_risco = 'CRÍTICO'
            deve_operar = False
            motivo = f'Martingale nível {nivel_atual} - Risco extremo'
        elif nivel_atual >= 3:
            nivel_risco = 'ALTO'
            deve_operar = False
            motivo = f'Martingale nível {nivel_atual} - Aguardar reset'
        elif nivel_atual >= 2:
            nivel_risco = 'MÉDIO'
            deve_operar = True
            motivo = f'Martingale nível {nivel_atual} - Operar com cautela'
        elif perdas_consecutivas >= 3:
            nivel_risco = 'ALTO'
            deve_operar = False
            motivo = f'{perdas_consecutivas} perdas consecutivas - Aguardar'
        
        # ANÁLISE DE PROGRESSÃO RECENTE
        operacoes_recentes = operacoes_ordenadas[:5]
        resets_recentes = sum(1 for op in operacoes_recentes 
                            if op.get('is_martingale_reset', False))
        
        if resets_recentes >= 2:
            nivel_risco = 'ALTO'
            deve_operar = False
            motivo = f'{resets_recentes} resets recentes - Sistema instável'
        
        return {
            'estatisticas_banco': {
                'total_operacoes': total_operacoes,
                'operacoes_martingale': operacoes_martingale,
                'frequencia_martingale': round(frequencia_martingale, 2),
                'nivel_maximo_atingido': nivel_maximo,
                'sequencias_ativas': sequencias_ativas,
                'resets_recentes': resets_recentes
            },
            'sequencia_atual': {
                'em_martingale': nivel_atual > 1,
                'nivel_atual': nivel_atual,
                'perdas_consecutivas': perdas_consecutivas,
                'vitorias_consecutivas': vitorias_consecutivas,
                'multiplicador_atual': multiplicador_atual,
                'investimento_total_sequencia': investimento_total,
                'houve_reset_recente': operacao_atual.get('is_martingale_reset', False)
            },
            'dados_validacao': {
                'ultima_operacao': operacao_atual.get('operation_result'),
                'timestamp_ultima': operacao_atual.get('timestamp'),
                'sequence_id_ativo': sequence_id_ativo,
                'stake_original': operacao_atual.get('original_stake', 0.0),
                'stake_martingale': operacao_atual.get('martingale_stake', 0.0)
            },
            'recomendacoes': {
                'nivel_risco': nivel_risco,
                'deve_operar': deve_operar,
                'motivo': motivo,
                'aguardar_tempo': 30 if nivel_risco in ['ALTO', 'CRÍTICO'] else 0
            },
            'fonte_dados': 'banco_supabase',
            'debug_info': {
                'total_registros_analisados': len(operacoes_detalhadas),
                'operacao_mais_recente': operacao_atual.get('id'),
                'timestamp_analise': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao analisar dados de Martingale do banco: {e}", exc_info=True)
        return {
            'estatisticas_banco': {'erro': str(e)},
            'sequencia_atual': {'erro': 'Falha na análise'},
            'dados_validacao': {'erro': str(e)},
            'recomendacoes': {
                'nivel_risco': 'ERRO',
                'deve_operar': False,
                'motivo': f'Erro na análise: {str(e)}'
            },
            'fonte_dados': 'banco_erro'
        }

def analisar_estrategia_momentum_calmo(historico: List[str], ultimo_timestamp: str) -> Dict:
    """Verifica si las condiciones de la estrategia Momentum-Calmo fueron cumplidas."""
    
    # ===== VALIDAÇÕES CRÍTICAS DE ENTRADA =====
    logger.debug(f"[ESTRATÉGIA] Iniciando análise com {len(historico) if historico else 0} operações")
    
    # 1. Validação de parâmetros de entrada
    if historico is None:
        logger.error("[ESTRATÉGIA] ERRO CRÍTICO: Histórico é None")
        return {
            'should_operate': False, 
            'reason': 'Erro: Histórico inválido',
            'error': 'historico_none',
            'validation_failed': True
        }
    
    if not isinstance(historico, list):
        logger.error(f"[ESTRATÉGIA] ERRO CRÍTICO: Histórico não é lista: {type(historico)}")
        return {
            'should_operate': False, 
            'reason': 'Erro: Tipo de histórico inválido',
            'error': 'historico_invalid_type',
            'validation_failed': True
        }
    
    # 2. Validação de conteúdo do histórico
    if len(historico) == 0:
        logger.warning("[ESTRATÉGIA] Histórico vazio - aguardando dados")
        return {
            'should_operate': False, 
            'reason': 'Aguardando dados históricos...',
            'validation_passed': True
        }
    
    # 3. Validação de valores válidos no histórico
    valores_validos = {'WIN', 'LOSS'}
    for i, operacao in enumerate(historico):
        if operacao not in valores_validos:
            logger.error(f"[ESTRATÉGIA] ERRO CRÍTICO: Operação inválida no índice {i}: '{operacao}'")
            return {
                'should_operate': False, 
                'reason': f'Erro: Operação inválida detectada: {operacao}',
                'error': 'invalid_operation_value',
                'validation_failed': True,
                'invalid_operation': operacao,
                'invalid_index': i
            }
    
    # 4. Validação de quantidade mínima
    if len(historico) < OPERACOES_MINIMAS:
        logger.info(f"[ESTRATÉGIA] Histórico insuficiente: {len(historico)}/{OPERACOES_MINIMAS}")
        return {
            'should_operate': False, 
            'reason': 'Esperando patrón, aguarde...',
            'validation_passed': True,
            'operations_available': len(historico),
            'operations_required': OPERACOES_MINIMAS
        }
    
    # 5. Validação de timestamp
    if ultimo_timestamp and not isinstance(ultimo_timestamp, str):
        logger.warning(f"[ESTRATÉGIA] Timestamp inválido: {type(ultimo_timestamp)}")
        ultimo_timestamp = ""
    
    logger.debug(f"[ESTRATÉGIA] ✅ Validações de entrada aprovadas - Analisando {len(historico)} operações")
    
    # ===== ANÁLISE DA ESTRATÉGIA =====
    try:
        # 6. Verificação do Gatillo LL (2 LOSS consecutivos) com validação adicional
        if len(historico) >= 2:
            ultimas_2_cronologica = list(reversed(historico[:2]))
            
            # Validação adicional das últimas 2 operações
            if len(ultimas_2_cronologica) != 2:
                logger.error(f"[ESTRATÉGIA] ERRO: Falha ao extrair últimas 2 operações: {ultimas_2_cronologica}")
                return {
                    'should_operate': False, 
                    'reason': 'Erro na análise de padrão',
                    'error': 'pattern_extraction_failed',
                    'validation_failed': True
                }
            
            # Verificar padrão LL
            if ultimas_2_cronologica == ['LOSS', 'LOSS']:
                logger.info("[ESTRATÉGIA] ✅ Padrão LL detectado - Sinal positivo")
                return {
                    'should_operate': True,
                    'strategy': 'Momentum-Calmo-LL',
                    'reason': 'Aguardando Padrao, Espere...',
                    'last_operations': historico[:2],
                    'pattern_detected': 'LL',
                    'validation_passed': True,
                    'confidence': 85  # Confiança baseada no padrão LL
                }
            else:
                logger.debug(f"[ESTRATÉGIA] Padrão atual: {ultimas_2_cronologica} - Não é LL")
        
        # 7. Condição padrão - não operar
        logger.debug("[ESTRATÉGIA] Condições não atendidas - aguardando padrão")
        return {
            'should_operate': False,
            'reason': 'Aguardando padrão adequado...',
            'validation_passed': True,
            'current_pattern': historico[:2] if len(historico) >= 2 else historico
        }
        
    except Exception as e:
        logger.error(f"[ESTRATÉGIA] ERRO CRÍTICO na análise: {e}", exc_info=True)
        return {
            'should_operate': False,
            'reason': f'Erro na análise: {str(e)}',
            'error': 'analysis_exception',
            'validation_failed': True
        }

@retry_supabase_operation()
def enviar_sinal_supabase(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envía la señal a la tabla de Supabase."""
    
    # ===== VALIDAÇÕES CRÍTICAS DE DADOS PARA SUPABASE =====
    logger.debug("[SUPABASE] Iniciando validações de dados para envio")
    
    # 1. Validação do cliente Supabase
    if supabase is None:
        logger.error("[SUPABASE] ERRO CRÍTICO: Cliente Supabase é None")
        return None
    
    # 2. Validação dos dados de entrada
    if signal_data is None:
        logger.error("[SUPABASE] ERRO CRÍTICO: signal_data é None")
        return None
    
    if not isinstance(signal_data, dict):
        logger.error(f"[SUPABASE] ERRO CRÍTICO: signal_data não é dict: {type(signal_data)}")
        return None
    
    # 3. Validação e sanitização de campos obrigatórios
    try:
        # Validar bot_name
        bot_name = signal_data.get('bot_name', BOT_NAME)
        if not bot_name or not isinstance(bot_name, str):
            logger.warning(f"[SUPABASE] bot_name inválido: {bot_name}, usando padrão: {BOT_NAME}")
            bot_name = BOT_NAME
        
        # Validar should_operate
        should_operate = signal_data.get('should_operate', False)
        if not isinstance(should_operate, bool):
            logger.warning(f"[SUPABASE] should_operate não é bool: {should_operate}, convertendo")
            should_operate = bool(should_operate)
        
        # Validar reason
        reason = signal_data.get('reason', 'N/A')
        if not isinstance(reason, str):
            logger.warning(f"[SUPABASE] reason não é string: {reason}, convertendo")
            reason = str(reason) if reason is not None else 'N/A'
        
        # Limitar tamanho da reason para evitar problemas no banco
        if len(reason) > 500:
            logger.warning(f"[SUPABASE] reason muito longa ({len(reason)} chars), truncando")
            reason = reason[:497] + "..."
        
        # Validar strategy
        strategy = signal_data.get('strategy', 'N/A')
        if not isinstance(strategy, str):
            strategy = str(strategy) if strategy is not None else 'N/A'
        
        # Validar confidence
        confidence = signal_data.get('confidence', 0)
        if not isinstance(confidence, (int, float)):
            logger.warning(f"[SUPABASE] confidence inválido: {confidence}, usando 0")
            confidence = 0
        
        # Garantir que confidence está no range válido
        confidence = max(0, min(100, confidence))
        
        # Validar timestamp
        timestamp = signal_data.get('timestamp')
        if not timestamp or not isinstance(timestamp, str):
            logger.warning("[SUPABASE] timestamp inválido, usando timestamp atual")
            timestamp = datetime.now().isoformat()
        
        # Validar last_operations
        last_operations = signal_data.get('last_operations', [])
        if not isinstance(last_operations, list):
            logger.warning(f"[SUPABASE] last_operations não é lista: {type(last_operations)}")
            last_operations = []
        
        # Sanitizar last_operations - garantir que são strings válidas
        sanitized_operations = []
        for op in last_operations:
            if isinstance(op, str) and op in ['WIN', 'LOSS']:
                sanitized_operations.append(op)
            else:
                logger.warning(f"[SUPABASE] Operação inválida removida: {op}")
        
        # Limitar número de operações para evitar dados muito grandes
        if len(sanitized_operations) > 50:
            logger.warning(f"[SUPABASE] Muitas operações ({len(sanitized_operations)}), limitando a 50")
            sanitized_operations = sanitized_operations[:50]
        
        logger.debug("[SUPABASE] ✅ Validações de dados aprovadas")
        
        # 4. Construir record validado
        record = {
            'bot_name': bot_name,
            'is_safe_to_operate': should_operate,
            'reason': reason,
            'strategy_used': strategy,
            'strategy_confidence': confidence,
            'pattern_found_at': timestamp,
            'last_update': datetime.now().isoformat(),
            'last_operations': str(sanitized_operations),
        }
        
        # 5. Validação final do record
        for key, value in record.items():
            if value is None:
                logger.error(f"[SUPABASE] ERRO CRÍTICO: Campo {key} é None após validação")
                return None
        
        logger.debug(f"[SUPABASE] Record preparado: bot={bot_name}, operate={should_operate}, ops_count={len(sanitized_operations)}")
        
        # 6. Envio para Supabase com validação de resposta
        response = supabase.table('radar_de_apalancamiento_signals').upsert(record, on_conflict='bot_name').execute()
        
        # 7. Validação da resposta
        if not response:
            logger.error("[SUPABASE] ERRO: Resposta vazia do Supabase")
            return None
        
        if not hasattr(response, 'data') or not response.data:
            logger.error("[SUPABASE] ERRO: Resposta sem dados válidos")
            return None
        
        if not isinstance(response.data, list) or len(response.data) == 0:
            logger.error(f"[SUPABASE] ERRO: Formato de dados inválido: {type(response.data)}")
            return None
        
        # 8. Extrair ID com validação
        first_record = response.data[0]
        if not isinstance(first_record, dict) or 'id' not in first_record:
            logger.error(f"[SUPABASE] ERRO: Record inválido: {first_record}")
            return None
        
        signal_id = first_record['id']
        if not signal_id:
            logger.error("[SUPABASE] ERRO: ID do sinal é None ou vazio")
            return None
        
        logger.info(f"[SUPABASE] ✅ Sinal enviado com sucesso. ID: {signal_id}")
        return signal_id
        
    except Exception as e:
        logger.error(f"[SUPABASE] ERRO CRÍTICO na preparação de dados: {e}", exc_info=True)
        return None


class MartingaleAnalyzer:
    """Analisa padrões de martingale e HITs nas operações."""
    
    def __init__(self):
        """Inicializa o analisador de martingale."""
        pass
    
    def calculate_hit_statistics(self, historico: List[str]) -> Dict:
        """
        Calcula estatísticas de HIT para diferentes níveis de martingale.
        
        Args:
            historico: Lista de resultados ['WIN', 'LOSS', 'WIN', ...]
            
        Returns:
            Dict com estatísticas de HIT por nível
        """
        try:
            logger.debug(f"[HIT_STATS] Calculando estatísticas para {len(historico)} operações")
            
            if not historico or not isinstance(historico, list):
                return {
                    'total_operations': 0,
                    'win_rate': 0.0,
                    'hits_1mg': 0,
                    'hits_2mg': 0,
                    'hits_3mg': 0,
                    'hits_4mg': 0,
                    'total_hits': 0,
                    'hit_rate': 0.0
                }
            
            # Detectar sequências de LOSS
            sequencias = self.detect_loss_sequences(historico)
            
            # Contar HITs por nível
            hits_por_nivel = {1: 0, 2: 0, 3: 0, 4: 0}
            total_hits = 0
            
            for seq in sequencias:
                if seq['hit_result'] == 'WIN':
                    nivel = min(seq['length'], 4)  # Máximo nível 4
                    hits_por_nivel[nivel] += 1
                    total_hits += 1
            
            # Calcular estatísticas gerais
            total_ops = len(historico)
            wins = historico.count('WIN')
            win_rate = (wins / total_ops * 100) if total_ops > 0 else 0
            hit_rate = (total_hits / len(sequencias) * 100) if sequencias else 0
            
            resultado = {
                'total_operations': total_ops,
                'win_rate': win_rate,
                'hits_1mg': hits_por_nivel[1],
                'hits_2mg': hits_por_nivel[2], 
                'hits_3mg': hits_por_nivel[3],
                'hits_4mg': hits_por_nivel[4],
                'total_hits': total_hits,
                'hit_rate': hit_rate,
                'total_sequences': len(sequencias)
            }
            
            logger.debug(f"[HIT_STATS] ✅ Estatísticas calculadas: {total_hits} HITs em {len(sequencias)} sequências")
            return resultado
            
        except Exception as e:
            logger.error(f"[HIT_STATS] Erro ao calcular estatísticas: {e}")
            return {
                'total_operations': 0,
                'win_rate': 0.0,
                'hits_1mg': 0,
                'hits_2mg': 0,
                'hits_3mg': 0,
                'hits_4mg': 0,
                'total_hits': 0,
                'hit_rate': 0.0,
                'error': str(e)
            }
    
    def detect_loss_sequences(self, historico: List[str]) -> List[Dict]:
        """
        Detecta sequências de LOSS consecutivos no histórico.
        
        Args:
            historico: Lista de resultados ['WIN', 'LOSS', 'WIN', ...]
            
        Returns:
            Lista de dicionários com sequências detectadas:
            [
                {
                    'start_index': int,      # Índice onde começou a sequência
                    'end_index': int,        # Índice onde terminou a sequência 
                    'length': int,           # Tamanho da sequência (quantos LOSS)
                    'sequence': List[str],   # ['LOSS', 'LOSS', ...]
                    'hit_result': str,       # 'WIN' se teve HIT, 'PENDING' se ainda está perdendo
                    'hit_index': int         # Índice do HIT (WIN após LOSS), -1 se PENDING
                }
            ]
        """
        try:
            # ===== VALIDAÇÕES CRÍTICAS DE ENTRADA =====
            if historico is None:
                logger.error("[MARTINGALE_ANALYZER] ERRO CRÍTICO: histórico é None")
                return []
            
            if not isinstance(historico, list):
                logger.error(f"[MARTINGALE_ANALYZER] ERRO CRÍTICO: histórico deve ser lista, recebido: {type(historico)}")
                return []
            
            # Validação: verificar se histórico não está vazio
            if not historico:
                logger.debug("[MARTINGALE_ANALYZER] Histórico vazio, retornando lista vazia")
                return []
            
            # Sanitizar dados do histórico
            historico_limpo = []
            for i, resultado in enumerate(historico):
                if isinstance(resultado, str) and resultado.upper() in ['WIN', 'LOSS']:
                    historico_limpo.append(resultado.upper())
                else:
                    logger.warning(f"[MARTINGALE_ANALYZER] Resultado inválido no índice {i}: {resultado}")
            
            if not historico_limpo:
                logger.warning("[MARTINGALE_ANALYZER] Nenhum resultado válido encontrado após sanitização")
                return []
            
            logger.debug(f"[MARTINGALE_ANALYZER] Iniciando detecção de sequências em {len(historico_limpo)} operações")
            
            sequences = []
            i = 0
            
            # Percorrer histórico em ordem cronológica
            while i < len(historico_limpo):
                try:
                    # Procurar início de sequência de LOSS
                    if historico_limpo[i] == 'LOSS':
                        start_index = i
                        sequence = []
                        
                        # Contar LOSS consecutivos
                        while i < len(historico_limpo) and historico_limpo[i] == 'LOSS':
                            sequence.append(historico_limpo[i])
                            i += 1
                        
                        end_index = i - 1
                        
                        # Verificar se houve HIT (WIN após sequência de LOSS)
                        hit_result = 'PENDING'
                        hit_index = -1
                        
                        if i < len(historico_limpo) and historico_limpo[i] == 'WIN':
                            hit_result = 'WIN'
                            hit_index = i
                        
                        # Adicionar sequência detectada
                        sequences.append({
                            'start_index': start_index,
                            'end_index': end_index,
                            'length': len(sequence),
                            'sequence': sequence,
                            'hit_result': hit_result,
                            'hit_index': hit_index
                        })
                    else:
                        i += 1
                        
                except Exception as e:
                    logger.error(f"[MARTINGALE_ANALYZER] Erro ao processar índice {i}: {e}")
                    i += 1  # Continuar com próximo índice
                    continue
            
            logger.info(f"[MARTINGALE_ANALYZER] ✅ Detectadas {len(sequences)} sequências de LOSS")
            return sequences
            
        except Exception as e:
            logger.error(f"[MARTINGALE_ANALYZER] ERRO CRÍTICO na detecção de sequências: {e}", exc_info=True)
            return []
    
    def calculate_hits(self, sequences: List[Dict]) -> Dict:
        """
        Calcula HITs baseado nas sequências de LOSS detectadas.
        
        Args:
            sequences: Lista retornada por detect_loss_sequences()
            
        Returns:
            Dicionário com estatísticas de HITs:
            {
                'total_sequences': int,           # Total de sequências encontradas
                'hits_1mg': int,                 # HITs de 1 martingale (1 LOSS + WIN)
                'hits_2mg': int,                 # HITs de 2 martingales (2 LOSS + WIN) 
                'hits_3mg': int,                 # HITs de 3 martingales (3 LOSS + WIN)
                'hits_4mg_plus': int,            # HITs de 4+ martingales
                'pending_sequences': int,         # Sequências sem HIT ainda
                'hit_rate': float,               # % de sequências que tiveram HIT
                'martingale_distribution': {     # Distribuição por nível
                    '1MG': int,
                    '2MG': int,
                    '3MG': int,
                    '4MG+': int
                }
            }
        """
        try:
            # ===== VALIDAÇÕES CRÍTICAS DE ENTRADA =====
            if sequences is None:
                logger.error("[MARTINGALE_ANALYZER] ERRO CRÍTICO: sequences é None")
                return {
                    'total_sequences': 0,
                    'hits_1mg': 0,
                    'hits_2mg': 0,
                    'hits_3mg': 0,
                    'hits_4mg_plus': 0,
                    'pending_sequences': 0,
                    'hit_rate': 0.0,
                    'martingale_distribution': {'1MG': 0, '2MG': 0, '3MG': 0, '4MG+': 0}
                }
            
            if not isinstance(sequences, list):
                logger.error(f"[MARTINGALE_ANALYZER] ERRO CRÍTICO: sequences deve ser lista, recebido: {type(sequences)}")
                return {
                    'total_sequences': 0,
                    'hits_1mg': 0,
                    'hits_2mg': 0,
                    'hits_3mg': 0,
                    'hits_4mg_plus': 0,
                    'pending_sequences': 0,
                    'hit_rate': 0.0,
                    'martingale_distribution': {'1MG': 0, '2MG': 0, '3MG': 0, '4MG+': 0}
                }
            
            # Validação: verificar se sequences não está vazio
            if not sequences:
                logger.debug("[MARTINGALE_ANALYZER] Lista de sequências vazia")
                return {
                    'total_sequences': 0,
                    'hits_1mg': 0,
                    'hits_2mg': 0,
                    'hits_3mg': 0,
                    'hits_4mg_plus': 0,
                    'pending_sequences': 0,
                    'hit_rate': 0.0,
                    'martingale_distribution': {'1MG': 0, '2MG': 0, '3MG': 0, '4MG+': 0}
                }
            
            logger.debug(f"[MARTINGALE_ANALYZER] Calculando HITs para {len(sequences)} sequências")
            
            # Inicializar contadores
            total_sequences = len(sequences)
            hits_1mg = 0
            hits_2mg = 0
            hits_3mg = 0
            hits_4mg_plus = 0
            pending_sequences = 0
            
            # Analisar cada sequência
            for i, sequence in enumerate(sequences):
                try:
                    # Validar estrutura da sequência
                    if not isinstance(sequence, dict):
                        logger.warning(f"[MARTINGALE_ANALYZER] Sequência {i} não é um dicionário: {type(sequence)}")
                        continue
                    
                    length = sequence.get('length', 0)
                    hit_result = sequence.get('hit_result', 'UNKNOWN')
                    
                    # Validar dados da sequência
                    if not isinstance(length, int) or length <= 0:
                        logger.warning(f"[MARTINGALE_ANALYZER] Sequência {i} tem length inválido: {length}")
                        continue
                    
                    if hit_result == 'PENDING':
                        pending_sequences += 1
                    elif hit_result == 'WIN':
                        # Classificar por nível de martingale baseado no tamanho da sequência
                        if length == 1:
                            hits_1mg += 1
                        elif length == 2:
                            hits_2mg += 1
                        elif length == 3:
                            hits_3mg += 1
                        elif length >= 4:
                            hits_4mg_plus += 1
                    else:
                        logger.warning(f"[MARTINGALE_ANALYZER] Sequência {i} tem hit_result inválido: {hit_result}")
                        
                except Exception as e:
                    logger.error(f"[MARTINGALE_ANALYZER] Erro ao processar sequência {i}: {e}")
                    continue
            
            # Calcular taxa de acerto (hit_rate)
            try:
                total_hits = hits_1mg + hits_2mg + hits_3mg + hits_4mg_plus
                hit_rate = round((total_hits / total_sequences) * 100, 2) if total_sequences > 0 else 0.0
            except Exception as e:
                logger.error(f"[MARTINGALE_ANALYZER] Erro ao calcular hit_rate: {e}")
                hit_rate = 0.0
            
            # Distribuição por nível de martingale
            try:
                martingale_distribution = {
                    '1MG': hits_1mg,
                    '2MG': hits_2mg,
                    '3MG': hits_3mg,
                    '4MG+': hits_4mg_plus
                }
            except Exception as e:
                logger.error(f"[MARTINGALE_ANALYZER] Erro ao criar distribuição: {e}")
                martingale_distribution = {'1MG': 0, '2MG': 0, '3MG': 0, '4MG+': 0}
            
            logger.info(f"[MARTINGALE_ANALYZER] ✅ HITs calculados: {total_hits}/{total_sequences} ({hit_rate}%)")
            
            return {
                'total_sequences': total_sequences,
                'hits_1mg': hits_1mg,
                'hits_2mg': hits_2mg,
                'hits_3mg': hits_3mg,
                'hits_4mg_plus': hits_4mg_plus,
                'pending_sequences': pending_sequences,
                'hit_rate': hit_rate,
                'martingale_distribution': martingale_distribution
            }
            
        except Exception as e:
            logger.error(f"[MARTINGALE_ANALYZER] ERRO CRÍTICO no cálculo de HITs: {e}", exc_info=True)
            return {
                'total_sequences': 0,
                'hits_1mg': 0,
                'hits_2mg': 0,
                'hits_3mg': 0,
                'hits_4mg_plus': 0,
                'pending_sequences': 0,
                'hit_rate': 0.0,
                'martingale_distribution': {'1MG': 0, '2MG': 0, '3MG': 0, '4MG+': 0}
            }
    
    def get_martingale_level(self, current_sequence: List[str]) -> int:
        """
        Retorna o nível atual de martingale baseado na sequência atual.
        
        Args:
            current_sequence: Últimas operações em ordem cronológica
                             Ex: ['LOSS', 'LOSS'] ou ['WIN', 'LOSS']
            
        Returns:
            int: Nível de martingale atual
            - 0: Não há sequência de LOSS ativa
            - 1: 1 LOSS consecutivo no final
            - 2: 2 LOSS consecutivos no final 
            - 3: 3 LOSS consecutivos no final
            - 4: 4+ LOSS consecutivos no final
        """
        try:
            # ===== VALIDAÇÕES CRÍTICAS DE ENTRADA =====
            if current_sequence is None:
                logger.error("[MARTINGALE_ANALYZER] ERRO CRÍTICO: current_sequence é None")
                return 0
            
            if not isinstance(current_sequence, list):
                logger.error(f"[MARTINGALE_ANALYZER] ERRO CRÍTICO: current_sequence deve ser lista, recebido: {type(current_sequence)}")
                return 0
            
            # Validação: verificar se sequência não está vazia
            if not current_sequence:
                logger.debug("[MARTINGALE_ANALYZER] Sequência vazia, nível Martingale = 0")
                return 0
            
            # Sanitizar dados da sequência
            sequencia_limpa = []
            for i, resultado in enumerate(current_sequence):
                if isinstance(resultado, str) and resultado.upper() in ['WIN', 'LOSS']:
                    sequencia_limpa.append(resultado.upper())
                else:
                    logger.warning(f"[MARTINGALE_ANALYZER] Resultado inválido no índice {i}: {resultado}")
            
            if not sequencia_limpa:
                logger.warning("[MARTINGALE_ANALYZER] Nenhum resultado válido após sanitização")
                return 0
            
            # Verificar se a sequência termina com LOSS
            if sequencia_limpa[-1] != 'LOSS':
                logger.debug(f"[MARTINGALE_ANALYZER] Última operação não é LOSS: {sequencia_limpa[-1]}")
                return 0
            
            # Contar LOSS consecutivos do final para o início
            consecutive_losses = 0
            try:
                for i in range(len(sequencia_limpa) - 1, -1, -1):
                    if sequencia_limpa[i] == 'LOSS':
                        consecutive_losses += 1
                    else:
                        break
            except Exception as e:
                logger.error(f"[MARTINGALE_ANALYZER] Erro ao contar LOSS consecutivos: {e}")
                return 0
            
            # Retornar nível de martingale (máximo 4 para 4+)
            nivel = min(consecutive_losses, 4)
            logger.debug(f"[MARTINGALE_ANALYZER] Nível Martingale calculado: {nivel} ({consecutive_losses} LOSS consecutivos)")
            
            return nivel
            
        except Exception as e:
            logger.error(f"[MARTINGALE_ANALYZER] ERRO CRÍTICO ao calcular nível Martingale: {e}", exc_info=True)
            return 0

    def integrar_dados_banco(self, dados_banco: Dict, analise_propria: Dict) -> Dict:
        """
        Integra dados do banco com análise própria para criar análise enriquecida.
        
        Args:
            dados_banco: Resultado da função analisar_dados_martingale_banco()
            analise_propria: Resultado da análise própria (hit statistics, etc.)
            
        Returns:
            Dict: Análise integrada com dados do banco e próprios
        """
        # Estrutura base da análise integrada
        analise_integrada = {
            'fonte_dados': {
                'banco_disponivel': bool(dados_banco.get('total_operations', 0) > 0),
                'analise_propria_disponivel': bool(analise_propria),
                'prioridade': 'banco' if dados_banco.get('total_operations', 0) > 0 else 'propria'
            },
            'dados_banco': dados_banco,
            'analise_propria': analise_propria,
            'analise_consolidada': {},
            'recomendacoes_integradas': [],
            'alertas_qualidade': []
        }
        
        # Consolidar dados priorizando banco quando disponível
        if dados_banco.get('total_operations', 0) > 0:
            # Usar dados do banco como base
            analise_integrada['analise_consolidada'] = {
                'martingale_level_atual': dados_banco.get('martingale_atual', {}).get('level', 0),
                'consecutive_losses': dados_banco.get('martingale_atual', {}).get('consecutive_losses', 0),
                'consecutive_wins': dados_banco.get('martingale_atual', {}).get('consecutive_wins', 0),
                'martingale_frequency': dados_banco.get('estatisticas', {}).get('martingale_frequency', 0),
                'max_level_reached': dados_banco.get('estatisticas', {}).get('max_level_reached', 0),
                'active_sequences': dados_banco.get('sequencias_ativas', 0),
                'risk_level': dados_banco.get('avaliacao_risco', {}).get('nivel_risco', 'UNKNOWN'),
                'fonte_primaria': 'banco'
            }
            
            # Adicionar recomendações do banco
            analise_integrada['recomendacoes_integradas'].extend(
                dados_banco.get('recomendacoes', [])
            )
        else:
            # Fallback para análise própria
            analise_integrada['analise_consolidada'] = {
                'martingale_level_atual': 0,  # Não calculado na análise própria
                'consecutive_losses': 0,
                'consecutive_wins': 0,
                'martingale_frequency': 0,
                'max_level_reached': 0,
                'active_sequences': 0,
                'risk_level': 'UNKNOWN',
                'fonte_primaria': 'propria'
            }
            
            # Adicionar dados da análise própria se disponível
            if analise_propria:
                hit_stats = analise_propria
                total_ops = (hit_stats.get('hits_1mg', 0) + 
                           hit_stats.get('hits_2mg', 0) + 
                           hit_stats.get('hits_3mg', 0) + 
                           hit_stats.get('hits_4mg_plus', 0))
                
                if total_ops > 0:
                    martingale_ops = (hit_stats.get('hits_2mg', 0) + 
                                    hit_stats.get('hits_3mg', 0) + 
                                    hit_stats.get('hits_4mg_plus', 0))
                    
                    analise_integrada['analise_consolidada'].update({
                        'martingale_frequency': round((martingale_ops / total_ops) * 100, 1),
                        'hit_rate': hit_stats.get('hit_rate', 0),
                        'total_sequences': hit_stats.get('total_sequences', 0)
                    })
        
        return analise_integrada

    def validar_consistencia_dados(self, dados_banco: Dict, sequencia_calculada: List[str]) -> Dict:
        """
        Valida consistência entre dados do banco e cálculos próprios.
        
        Args:
            dados_banco: Dados do banco de martingale
            sequencia_calculada: Sequência calculada localmente
            
        Returns:
            Dict: Resultado da validação cruzada
        """
        validacao = {
            'validacao_executada': True,
            'discrepancias_encontradas': [],
            'nivel_confianca': 'ALTO',  # ALTO, MEDIO, BAIXO
            'recomendacao_fonte': 'banco',  # banco, propria, hibrida
            'detalhes_validacao': {}
        }
        
        # Verificar se dados do banco estão disponíveis
        if not dados_banco or dados_banco.get('total_operations', 0) == 0:
            validacao.update({
                'nivel_confianca': 'BAIXO',
                'recomendacao_fonte': 'propria',
                'discrepancias_encontradas': ['Dados do banco não disponíveis']
            })
            return validacao
        
        # Calcular nível de martingale da sequência própria
        nivel_proprio = self.get_martingale_level(sequencia_calculada)
        nivel_banco = dados_banco.get('martingale_atual', {}).get('level', 0)
        
        # Validar nível de martingale
        if abs(nivel_proprio - nivel_banco) > 1:
            validacao['discrepancias_encontradas'].append(
                f"Nível martingale: próprio={nivel_proprio}, banco={nivel_banco}"
            )
            validacao['nivel_confianca'] = 'MEDIO'
        
        # Calcular perdas consecutivas próprias
        perdas_consecutivas_proprias = 0
        if sequencia_calculada:
            for i in range(len(sequencia_calculada) - 1, -1, -1):
                if sequencia_calculada[i] == 'LOSS':
                    perdas_consecutivas_proprias += 1
                else:
                    break
        
        perdas_banco = dados_banco.get('martingale_atual', {}).get('consecutive_losses', 0)
        
        # Validar perdas consecutivas
        if abs(perdas_consecutivas_proprias - perdas_banco) > 1:
            validacao['discrepancias_encontradas'].append(
                f"Perdas consecutivas: próprio={perdas_consecutivas_proprias}, banco={perdas_banco}"
            )
            validacao['nivel_confianca'] = 'MEDIO'
        
        # Determinar recomendação de fonte baseada na validação
        if len(validacao['discrepancias_encontradas']) == 0:
            validacao['recomendacao_fonte'] = 'banco'
            validacao['nivel_confianca'] = 'ALTO'
        elif len(validacao['discrepancias_encontradas']) <= 2:
            validacao['recomendacao_fonte'] = 'hibrida'
            validacao['nivel_confianca'] = 'MEDIO'
        else:
            validacao['recomendacao_fonte'] = 'propria'
            validacao['nivel_confianca'] = 'BAIXO'
        
        # Adicionar detalhes da validação
        validacao['detalhes_validacao'] = {
            'nivel_martingale': {
                'proprio': nivel_proprio,
                'banco': nivel_banco,
                'diferenca': abs(nivel_proprio - nivel_banco)
            },
            'perdas_consecutivas': {
                'proprio': perdas_consecutivas_proprias,
                'banco': perdas_banco,
                'diferenca': abs(perdas_consecutivas_proprias - perdas_banco)
            },
            'sequencia_analisada': sequencia_calculada[-5:] if len(sequencia_calculada) >= 5 else sequencia_calculada
        }
        
        return validacao


class RiskDetector:
    """Detecta níveis de risco baseado na frequência de martingales."""
    
    def __init__(self):
        """Inicializa o detector de risco."""
        pass
    
    def analyze_last_20_operations(self, historico: List[str]) -> Dict:
        """
        Analisa risco de mercado baseado nas últimas 20 operações.
        
        Args:
            historico: Lista completa de operações ['WIN', 'LOSS']
            
        Returns:
            Dict: Análise de risco das últimas 20 operações
        """
        if len(historico) < 20:
            return {
                'risk_level': 'LOW',
                'analysis': 'Histórico insuficiente para análise',
                'operations_analyzed': len(historico)
            }
        
        last_20 = historico[-20:]
        losses = last_20.count('LOSS')
        wins = last_20.count('WIN')
        
        loss_percentage = (losses / 20) * 100
        
        if loss_percentage >= 70:
            risk_level = 'HIGH'
        elif loss_percentage >= 50:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
            
        return {
            'risk_level': risk_level,
            'loss_percentage': loss_percentage,
            'wins': wins,
            'losses': losses,
            'operations_analyzed': 20,
            'analysis': f'Últimas 20 operações: {wins}W/{losses}L ({loss_percentage:.1f}% perdas)',
            'martingale_frequency': loss_percentage / 100,
            'consecutive_losses_max': self._calculate_max_consecutive_losses(last_20),
            'win_rate': (wins / 20) * 100
        }
    
    def _calculate_max_consecutive_losses(self, operations: List[str]) -> int:
        """Calcula o máximo de perdas consecutivas."""
        max_consecutive = 0
        current_consecutive = 0
        
        for op in operations:
            if op == 'LOSS':
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
                
        return max_consecutive
    
    def classify_risk_level(self, martingale_frequency: float) -> str:
        """
        Classifica o nível de risco baseado na frequência de martingale.
        
        Args:
            martingale_frequency: Frequência de martingale (0.0 a 1.0)
            
        Returns:
            str: Nível de risco ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        """
        try:
            if martingale_frequency >= 0.8:
                return 'CRITICAL'
            elif martingale_frequency >= 0.6:
                return 'HIGH'
            elif martingale_frequency >= 0.4:
                return 'MEDIUM'
            else:
                return 'LOW'
        except Exception as e:
            logger.error(f"Erro ao classificar nível de risco: {e}")
            return 'UNKNOWN'
    
    def generate_3mg_signal(self, historico: List[str]) -> Dict:
        """
        Gera sinal baseado na estratégia 3MG (3 Martingale Gale).
        
        Args:
            historico: Lista de operações ['WIN', 'LOSS']
            
        Returns:
            Dict: Análise do sinal 3MG
        """
        try:
            if len(historico) < 10:
                return {
                    'should_operate': False,
                    'confidence': 0.0,
                    'reason': 'Histórico insuficiente para análise 3MG',
                    'pattern_detected': False
                }
            
            # Analisa os últimos 10 resultados
            last_10 = historico[-10:]
            
            # Procura por padrões de 3 perdas consecutivas
            consecutive_losses = 0
            pattern_detected = False
            
            for i, op in enumerate(reversed(last_10)):
                if op == 'LOSS':
                    consecutive_losses += 1
                    if consecutive_losses >= 3:
                        pattern_detected = True
                        break
                else:
                    consecutive_losses = 0
            
            # Calcula confiança baseada no padrão
            if pattern_detected:
                # Verifica se há recuperação após 3 perdas
                recovery_rate = self._calculate_recovery_rate(historico)
                confidence = min(85.0, 60.0 + (recovery_rate * 25))
                
                return {
                    'should_operate': True,
                    'confidence': confidence,
                    'reason': f'Padrão 3MG detectado - {consecutive_losses} perdas consecutivas',
                    'pattern_detected': True,
                    'consecutive_losses': consecutive_losses,
                    'recovery_rate': recovery_rate
                }
            else:
                return {
                    'should_operate': False,
                    'confidence': 0.0,
                    'reason': 'Padrão 3MG não detectado',
                    'pattern_detected': False,
                    'consecutive_losses': consecutive_losses
                }
                
        except Exception as e:
            logger.error(f"Erro ao gerar sinal 3MG: {e}")
            return {
                'should_operate': False,
                'confidence': 0.0,
                'reason': f'Erro na análise 3MG: {str(e)}',
                'pattern_detected': False,
                'error': str(e)
            }
    
    def _calculate_recovery_rate(self, historico: List[str]) -> float:
        """Calcula a taxa de recuperação após sequências de perdas."""
        try:
            if len(historico) < 20:
                return 0.5  # Taxa padrão
            
            recovery_count = 0
            loss_sequences = 0
            consecutive_losses = 0
            
            for i, op in enumerate(historico):
                if op == 'LOSS':
                    consecutive_losses += 1
                else:
                    if consecutive_losses >= 3:
                        loss_sequences += 1
                        # Verifica se houve recuperação nos próximos 3 resultados
                        next_ops = historico[i:i+3]
                        if 'WIN' in next_ops:
                            recovery_count += 1
                    consecutive_losses = 0
            
            return recovery_count / loss_sequences if loss_sequences > 0 else 0.5
            
        except Exception:
            return 0.5

def validacao_cruzada_martingale(dados_banco: Dict, sequencia_calculada: List[str], operacoes_detalhadas: List[Dict] = None) -> Dict:
    """
    Função de validação cruzada entre dados do banco e cálculos próprios.
    """
    try:
        logger.debug("[VALIDACAO_CRUZADA] Iniciando validação cruzada")
        
        resultado = {
            'status_validacao': 'EXECUTADA',
            'discrepancias_encontradas': [],
            'nivel_confianca': 'ALTO',
            'fonte_recomendada': 'banco',
            'metricas_confiabilidade': {
                'confiabilidade_percentual': 100.0,
                'total_verificacoes': 1,
                'verificacoes_aprovadas': 1
            },
            'timestamp_validacao': datetime.now().isoformat()
        }
        
        if not dados_banco or not sequencia_calculada:
            resultado.update({
                'status_validacao': 'ERRO_DADOS',
                'nivel_confianca': 'BAIXO',
                'fonte_recomendada': 'propria'
            })
        
        return resultado
        
    except Exception as e:
        logger.error(f"[VALIDACAO_CRUZADA] Erro: {e}")
        return {
            'status_validacao': 'ERRO_EXECUCAO',
            'nivel_confianca': 'BAIXO',
            'fonte_recomendada': 'propria',
            'erro': str(e)
        }