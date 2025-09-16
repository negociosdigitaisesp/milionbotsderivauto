#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radarscalpingia3.5 - Sistema de Trading com Estratégia Precision Surge Pattern
Estratégia implementada:
- Precision Surge Pattern (4-5 WINs consecutivos com 93.5% assertividade)
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
        logging.FileHandler('radarscalpingia3.5_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

BOT_NAME = 'Radar Scalping I.A'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 35
OPERACOES_MINIMAS = 4  # Requisito mínimo para Precision Surge Pattern

# Estados de rastreamento de padrão
PADRAO_NAO_ENCONTRADO = 0
PADRAO_ENCONTRADO = 1
PRIMEIRA_OPERACAO_REGISTRADA = 2

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
def buscar_operacoes_historico(supabase: Client) -> Tuple[List[str], List[str], Optional[str]]:
    """
    Busca histórico da tabela scalping_accumulator_bot_logs,
    com resiliência e tradução de dados.
    """
    try:
        # CORREÇÃO CRÍTICA: Apontando para a tabela correta.
        response = supabase.table('scalping_accumulator_bot_logs') \
            .select('id, operation_result, timestamp') \
            .order('timestamp', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()

        if not response.data:
            logger.warning("Ningún historial de operaciones fue retornado por la base de datos.")
            return [], [], None

        historico_raw = [op['operation_result'] for op in response.data]
        # Os dados já estão no formato correto (WIN/LOSS), não precisam de tradução
        historico_traduzido = historico_raw
        
        timestamps = [op['timestamp'] for op in response.data]
        latest_operation_id = response.data[0]['id']
        
        logger.info(f"{len(historico_traduzido)} operaciones cargadas de la tabla 'scalping_accumulator_bot_logs'.")
        return historico_traduzido, timestamps, latest_operation_id

    except Exception as e:
        logger.error(f"Error crítico al buscar historial: {e}", exc_info=True)
        # CORRECCIÓN DE ROBUSTEZ: Garantiza que la función siempre retorne la tupla de 3 valores.
        return [], [], None

def analisar_estrategia_precision_surge_pattern(historico: List[str]) -> Dict:
    """Analiza patrón Precision Surge Pattern (4-5 WINs consecutivos)."""
    strategy_name = "Precision Surge Pattern"
    
    if len(historico) < OPERACOES_MINIMAS:
        return {
            'should_operate': False,
            'reason': f"Datos insuficientes ({len(historico)}/{OPERACOES_MINIMAS})",
            'last_operations': historico[:5] if len(historico) > 0 else []
        }

    # Verifica padrão de 4 ou 5 WINs consecutivos
    wins_consecutivos = 0
    for op in historico:
        if op == 'WIN':
            wins_consecutivos += 1
        else:
            break
    
    logger.info(f"[{strategy_name}] WINs consecutivos detectados: {wins_consecutivos}")
    
    # GATILLO: Exactamente 4 o 5 WINs consecutivos
    if wins_consecutivos == 4 or wins_consecutivos == 5:
        logger.info(f"[{strategy_name}] PATRÓN DETECTADO! {wins_consecutivos} WINs consecutivos. Verificando filtros...")
        
        # FILTRO 1: Verificar se há 2 ou mais losses nas últimas 15 operações
        ultimas_15 = historico[:15] if len(historico) >= 15 else historico
        losses_nas_15 = ultimas_15.count('LOSS')
        
        logger.info(f"[{strategy_name}] Losses nas últimas {len(ultimas_15)} operações: {losses_nas_15}")
        
        if losses_nas_15 >= 2:
            logger.info(f"[{strategy_name}] FILTRO 1 REJEITADO! {losses_nas_15} losses ≥ 2 nas últimas 15 operações. Não operando.")
            return {
                'should_operate': False,
                'reason': f"Padrão detectado mas Filtro 1 rejeitado ({losses_nas_15} losses ≥ 2 nas últimas 15 ops)",
                'last_operations': historico[:5],
                'pattern_details': {
                    'trigger': f'{wins_consecutivos}_WINS',
                    'consecutive_wins': wins_consecutivos,
                    'filter_1_passed': False,
                    'losses_in_15': losses_nas_15
                }
            }
        
        # FILTRO 2: Verificar se há losses consecutivos nas últimas 10 operações
        ultimas_10 = historico[:10] if len(historico) >= 10 else historico
        losses_consecutivos = 0
        for op in ultimas_10:
            if op == 'LOSS':
                losses_consecutivos += 1
            else:
                break
        
        logger.info(f"[{strategy_name}] Losses consecutivos nas últimas {len(ultimas_10)} operações: {losses_consecutivos}")
        
        if losses_consecutivos > 0:
            logger.info(f"[{strategy_name}] FILTRO 2 REJEITADO! {losses_consecutivos} losses consecutivos nas últimas 10 operações. Não operando.")
            return {
                'should_operate': False,
                'reason': f"Padrão detectado mas Filtro 2 rejeitado ({losses_consecutivos} losses consecutivos nas últimas 10 ops)",
                'last_operations': historico[:5],
                'pattern_details': {
                    'trigger': f'{wins_consecutivos}_WINS',
                    'consecutive_wins': wins_consecutivos,
                    'filter_2_passed': False,
                    'consecutive_losses_in_10': losses_consecutivos
                }
            }
        
        # Se passou por todos os filtros, ativa o sinal
        logger.info(f"[{strategy_name}] TODOS OS FILTROS APROVADOS! Ativando sinal.")
        return {
            'should_operate': True,
            'strategy': strategy_name,
            'confidence': 93.5,
            'reason': f"Patrón Precision Surge: {wins_consecutivos} WINs consecutivos + Filtros OK",
            'pattern_details': {
                'trigger': f'{wins_consecutivos}_WINS',
                'consecutive_wins': wins_consecutivos,
                'momentum_confirmed': True,
                'filter_1_passed': True,
                'filter_2_passed': True,
                'losses_in_15': losses_nas_15,
                'consecutive_losses_in_10': losses_consecutivos
            },
            'last_operations': historico[:5]
        }
    elif wins_consecutivos >= 6:
        logger.info(f"[{strategy_name}] SATURACIÓN DETECTADA! {wins_consecutivos} WINs (posible saturación). No operando.")
        return {
            'should_operate': False,
            'reason': f"Saturação detectada: {wins_consecutivos} WINs consecutivos (>5)",
            'last_operations': historico[:5],
            'pattern_details': {
                'trigger': 'SATURATION',
                'consecutive_wins': wins_consecutivos,
                'momentum_saturated': True
            }
        }
    elif wins_consecutivos >= 1 and wins_consecutivos <= 3:
        logger.info(f"[{strategy_name}] MOMENTUM INSUFICIENTE! {wins_consecutivos} WINs (momentum no confirmado). Esperando.")
        return {
            'should_operate': False,
            'reason': f"Momentum insuficiente: {wins_consecutivos} WINs consecutivos (<4)",
            'last_operations': historico[:5],
            'pattern_details': {
                'trigger': 'INSUFFICIENT_MOMENTUM',
                'consecutive_wins': wins_consecutivos,
                'momentum_confirmed': False
            }
        }
    
    # Se não há WINs consecutivos, retorna aguardando
    ultimas_ops = historico[:5]
    padrao_atual = ''.join(['W' if op == 'WIN' else 'L' if op == 'LOSS' else 'X' for op in ultimas_ops])
    
    return {
        'should_operate': False,
        'reason': f"Esperando patrón Precision Surge. Patrón actual: {padrao_atual}",
        'last_operations': ultimas_ops
    }

@retry_supabase_operation()
def enviar_sinal_supabase(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envía la señal a la tabla de Supabase."""
    try:
        record = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': signal_data.get('should_operate', False),
            'reason': signal_data.get('reason', 'N/A'),
            'strategy_used': signal_data.get('strategy', 'N/A'),
            'strategy_confidence': signal_data.get('confidence', 0),
            'pattern_found_at': datetime.now().isoformat() if signal_data.get('should_operate') else None,
            'last_update': datetime.now().isoformat(),  # Sempre atualiza o timestamp
            'last_operations': str(signal_data.get('last_operations', [])),  # Últimas operações
        }
        response = supabase.table('radar_de_apalancamiento_signals').upsert(record, on_conflict='bot_name').execute()
        
        if response.data:
            signal_id = response.data[0]['id']
            logger.info(f"Señal enviada con éxito a Supabase. ID: {signal_id}")
            return signal_id
        return None
    except Exception as e:
        logger.error(f"Falla al enviar señal a Supabase: {e}", exc_info=True)
        return None

@retry_supabase_operation()
def enviar_para_strategy_execution_logs(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envia dados completos para strategy_execution_logs após completar as 2 operações."""
    try:
        record = {
            'bot_name': BOT_NAME,
            'strategy_name': signal_data.get('strategy', 'Precision Surge Pattern'),
            'pattern_detected_at': signal_data.get('pattern_detected_at'),
            'confidence_level': signal_data.get('confidence', 93.5),
            'trigger_type': 'PRECISION_SURGE',
            'operation_1_result': signal_data.get('operation_1_result'),
            'operation_1_completed_at': signal_data.get('operation_1_completed_at'),
            'operation_2_result': signal_data.get('operation_2_result'),
            'operation_2_completed_at': signal_data.get('operation_2_completed_at'),
            'final_result': signal_data.get('final_result'),
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat()
        }
        
        response = supabase.table('strategy_execution_logs').insert(record).execute()
        
        if response.data:
            record_id = response.data[0]['id']
            logger.info(f"Registro completo enviado a strategy_execution_logs. ID: {record_id}")
            return record_id
        return None
    except Exception as e:
        logger.error(f"Error al enviar a strategy_execution_logs: {e}")
        return None



def main_loop():
    logger.info("=== INICIANDO RADAR SCALPING I.A CON ESTRATEGIA PRECISION SURGE PATTERN ===")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Falla fatal al conectar con Supabase. Cerrando.")
        return

    logger.info("Bot inicializado con éxito.")
    print("\n🚀 RADAR SCALPING I.A ACTIVO")
    print("🥈 ESTRATEGIA: PRECISION SURGE PATTERN (93.5% ASERTIVIDAD)")
    print("🎯 Gatillo: Detectar 4 o 5 WINs consecutivos")
    print("📊 Momentum confirmado pero no saturado")
    print("⏱️  Análisis cada 5 segundos.")
    print("🔍 Rastreando 2 operaciones después del patrón detectado")
    print("📊 Enviando resultados a strategy_execution_logs")
    print("\nPresione Ctrl+C para detener.\n")

    last_processed_id = None  # Control para evitar señales duplicadas
    last_update_time = 0  # Control para actualizaciones regulares
    padrao_estado = PADRAO_NAO_ENCONTRADO  # Estado inicial del rastreo de patrón
    padrao_id = None  # ID de la operación donde se encontró el patrón
    pattern_detected_at = None  # Timestamp de cuando se detectó el patrón
    operation_1_result = None  # Resultado de la primera operación
    operation_1_completed_at = None  # Timestamp de la primera operación
    operation_2_result = None  # Resultado de la segunda operación
    operation_2_completed_at = None  # Timestamp de la segunda operación

    while True:
        try:
            current_time = time.time()
            historico, timestamps, latest_id = buscar_operacoes_historico(supabase)
            
            if not historico:
                print("Esperando datos del historial...")
                time.sleep(ANALISE_INTERVALO)
                continue

            is_new_operation = (latest_id != last_processed_id)
            
            # PASSO 1: MODIFICAR A LÓGICA PRINCIPAL - Pular análise quando rastreando
            if padrao_estado != PADRAO_NAO_ENCONTRADO:
                # Quando estiver rastreando, NÃO analisa novos padrões
                print(f"🔍 Rastreando operações... Estado: {padrao_estado}")
            
            # Rastreo de las dos operaciones después del patrón
            if padrao_estado == PADRAO_ENCONTRADO and is_new_operation:
                # Primera operación después de encontrar el patrón
                operation_1_result = "WIN" if historico[0] == "WIN" else "LOSS"
                operation_1_completed_at = datetime.now().isoformat()
                print(f"\n🔍 Primera operación después del patrón: {operation_1_result}")
                
                # Actualiza el reason para mostrar progreso
                resultado_analise['reason'] = f"Padrón encontrado + resta apenas 1 operação (1ª: {operation_1_result})"
                
                # Envía actualización a radar_de_apalancamiento_signals
                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                
                if signal_id:
                    print(f"✅ Primera operación registrada con ID: {signal_id}")
                else:
                    print("❌ Error al registrar primera operación")
                
                padrao_estado = PRIMEIRA_OPERACAO_REGISTRADA
                last_processed_id = latest_id
                last_update_time = current_time
                
            elif padrao_estado == PRIMEIRA_OPERACAO_REGISTRADA and is_new_operation:
                # Segunda operación después de encontrar el patrón
                operation_2_result = "WIN" if historico[0] == "WIN" else "LOSS"
                operation_2_completed_at = datetime.now().isoformat()
                print(f"\n🔍 Segunda operación después del patrón: {operation_2_result}")
                
                # Determina resultado final basado en la lógica:
                # WIN+WIN = WIN, cualquier LOSS = LOSS
                if operation_1_result == "WIN" and operation_2_result == "WIN":
                    final_result = "WIN"
                else:
                    final_result = "LOSS"
                
                print(f"🎯 Resultado final: {final_result} (Op1: {operation_1_result}, Op2: {operation_2_result})")
                
                # Prepara datos completos para envío
                complete_signal_data = {
                    **resultado_analise,
                    'pattern_detected_at': pattern_detected_at,
                    'operation_1_result': operation_1_result,
                    'operation_1_completed_at': operation_1_completed_at,
                    'operation_2_result': operation_2_result,
                    'operation_2_completed_at': operation_2_completed_at,
                    'final_result': final_result,
                    'resultado_operacion': final_result
                }
                
                # Envía a todas las tablas
                signal_id = enviar_sinal_supabase(supabase, complete_signal_data)
                strategy_log_id = enviar_para_strategy_execution_logs(supabase, complete_signal_data)
                
                # Reporte de envíos
                success_count = sum([bool(signal_id), bool(strategy_log_id)])
                if success_count == 2:
                    print(f"✅ Resultado completo enviado - Signal: {signal_id}, Strategy: {strategy_log_id}")
                else:
                    print(f"⚠️ Envío parcial - Signal: {signal_id}, Strategy: {strategy_log_id}")
                
                # PASSO 3: ELIMINAR ESTADO REDUNDANTE - Reset direto para PADRAO_NAO_ENCONTRADO
                padrao_estado = PADRAO_NAO_ENCONTRADO
                last_processed_id = latest_id
                last_update_time = current_time
                
                # Limpia variables para próximo patrón
                operation_1_result = None
                operation_1_completed_at = None
                operation_2_result = None
                operation_2_completed_at = None
                pattern_detected_at = None
            
            # PASSO 2: REORGANIZAR O FLUXO - SÓ analisa quando não estiver rastreando
            elif padrao_estado == PADRAO_NAO_ENCONTRADO:
                # SÓ AQUI analisa novos padrões
                resultado_analise = analisar_estrategia_precision_surge_pattern(historico)
                should_update = (current_time - last_update_time >= ANALISE_INTERVALO)
                
                if resultado_analise['should_operate']:
                    print(f"\n🎯 {resultado_analise['reason']}")
                    print(f"📊 Últimas 5 operaciones: {historico[:5]}")
                    signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                    if signal_id:
                        print(f"✅ Patrón detectado - Señal enviada con ID: {signal_id}")
                        padrao_estado = PADRAO_ENCONTRADO  # Detectou padrão, muda estado
                        padrao_id = latest_id  # Guarda el ID donde se encontró el patrón
                        pattern_detected_at = datetime.now().isoformat()  # Timestamp del patrón
                        last_processed_id = latest_id  # Actualiza para evitar duplicados
                        last_update_time = current_time
                    else:
                        print("❌ Error al enviar señal")
                elif should_update or is_new_operation:
                    # Envía actualizaciones regulares incluso sin patrón
                    print(f"⏳ {resultado_analise['reason']}")
                    print(f"📊 Últimas 5 operaciones: {historico[:5]}")
                    signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                    if signal_id:
                        print(f"✅ Actualización enviada con ID: {signal_id}")
                        last_update_time = current_time
                        if is_new_operation:
                            last_processed_id = latest_id
                    else:
                        print("❌ Error al enviar actualización")
                else:
                    print(f"⏳ {resultado_analise['reason']}")
                    print(f"📊 Últimas 5 operaciones: {historico[:5]}")
            
            time.sleep(ANALISE_INTERVALO)
            
        except KeyboardInterrupt:
            logger.info("Bot interrumpido por el usuario.")
            print("\n🛑 Bot parado por el usuario.")
            break
        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            time.sleep(ANALISE_INTERVALO)

if __name__ == "__main__":
    main_loop()