#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTOR MOMENTUM-MEDIO - Bot de Trading Estratégico

Este script monitora operaciones de trading en tiempo real y detecta patrones WW
(2 victorias consecutivas) durante condiciones específicas de mercado.

Características:
- Análisis en tiempo real de las últimas 2 operaciones
- Detección de patrón WW en Actividad Media + Apertura de Hora
- Filtros basados en régimen de actividad UTC
- Envío de señales a Supabase
- Logs simplificados y enfocados

Autor: Sistema de Trading Automatizado
Versión: 1.0 - Momentum-Medio
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
        logging.FileHandler('executor_momentum_medio_v1_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

BOT_NAME = 'executor_momentum_medio_v1'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 35
OPERACOES_MINIMAS = 2  # Requisito mínimo para WW

# Constantes de regime de atividade (UTC)
HORAS_BAIXA_ATIVIDADE_UTC = [3, 4, 5, 6, 7, 8, 9, 10]
HORAS_MEDIA_ATIVIDADE_UTC = [11, 12, 13, 14, 15, 16, 17, 18]



def get_regime_atividade_utc(timestamp_str: str) -> str:
    """Determina el régimen de actividad basado en la hora UTC."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        hora_utc = dt.hour
        
        if hora_utc in HORAS_BAIXA_ATIVIDADE_UTC:
            return 'Baixa Atividade'
        elif hora_utc in HORAS_MEDIA_ATIVIDADE_UTC:
            return 'Média Atividade'
        else:
            return 'Alta Atividade'
    except Exception as e:
        logger.warning(f"Error al procesar timestamp {timestamp_str}: {e}")
        return 'Alta Atividade'  # Default seguro

def get_padrao_intra_hora_utc(timestamp_str: str) -> str:
    """Determina si estamos en el período de apertura de la hora."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        minuto_utc = dt.minute
        
        if 0 <= minuto_utc <= 5:
            return 'Apertura de Hora'
        else:
            return 'Otro Período'
    except Exception as e:
        logger.warning(f"Error al procesar timestamp {timestamp_str}: {e}")
        return 'Otro Período'  # Default seguro

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
    Busca historial de la tabla CORRECTA (tunder_bot_logs),
    con resistencia y traducción de datos.
    """
    try:
        # CORRECCIÓN CRÍTICA: Apuntando a la tabla correcta.
        response = supabase.table('tunder_bot_logs') \
            .select('id, operation_result, timestamp') \
            .order('timestamp', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()

        if not response.data:
            logger.warning("Ningún historial de operaciones fue retornado por la base de datos.")
            return [], [], None

        historico_raw = [op['operation_result'] for op in response.data]
        # Los datos ya están en el formato correcto (WIN/LOSS), no necesitan traducción
        historico_traduzido = historico_raw
        
        timestamps = [op['timestamp'] for op in response.data]
        latest_operation_id = response.data[0]['id']
        
        logger.info(f"{len(historico_traduzido)} operaciones cargadas de la tabla 'tunder_bot_logs'.")
        return historico_traduzido, timestamps, latest_operation_id

    except Exception as e:
        logger.error(f"Error crítico al buscar historial: {e}", exc_info=True)
        # CORRECCIÓN DE ROBUSTEZ: Garantiza que la función siempre retorne la tupla de 3 valores.
        return [], [], None

def analisar_estrategia_momentum_medio(historico: List[str], ultimo_timestamp: str) -> Dict:
    """Verifica si las condiciones de la estrategia Momentum-Medio fueron cumplidas."""
    
    # 1. Validación Mínima de Datos
    if len(historico) < OPERACOES_MINIMAS:
        return {'should_operate': False, 'reason': 'Esperando historial mínimo'}

    # 2. Análisis de Contexto (UTC)
    regime = get_regime_atividade_utc(ultimo_timestamp)
    periodo = get_padrao_intra_hora_utc(ultimo_timestamp)

    # 3. Verificación Rápida de Filtros (Fail-Fast)
    if regime != 'Média Atividade':
        return {'should_operate': False, 'reason': f'Filtro Rechazado: Régimen actual es {regime}'}
    
    if periodo != 'Apertura de Hora':
        return {'should_operate': False, 'reason': f'Filtro Rechazado: Período no es Apertura'}

    # 4. Verificación del Gatillo WW
    ultimas_2_cronologica = list(reversed(historico[:2]))
    if ultimas_2_cronologica == ['WIN', 'WIN']:
        return {
            'should_operate': True,
            'strategy': 'Momentum-Medio',
            'reason': 'SEÑAL ACTIVA: WW | Media + Apertura',
            'last_operations': historico[:2]
        }
    
    # 5. Condición Estándar
    padrao_atual = ''.join(['W' if op == 'WIN' else 'L' for op in ultimas_2_cronologica])
    return {'should_operate': False, 'reason': f'Esperando gatillo WW. Patrón actual: {padrao_atual}'}

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
            logger.info(f"Señal enviada exitosamente a Supabase. ID: {signal_id}")
            return signal_id
        return None
    except Exception as e:
        logger.error(f"Fallo al enviar señal a Supabase: {e}", exc_info=True)
        return None





def main_loop():
    """Bucle principal del bot de análisis Momentum-Medio."""
    logger.info("=== INICIANDO EXECUTOR MOMENTUM-MEDIO ===")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Fallo fatal al conectar con Supabase. Cerrando.")
        return

    logger.info("Bot inicializado exitosamente.")
    print("\n[INICIO] Iniciando bot EXECUTOR MOMENTUM-MEDIO")
    print("[INFO] Configuración: Análisis de las últimas 2 operaciones")
    print("[INFO] Objetivo: Detectar patrón WW en Actividad Media + Apertura de Hora")
    print("[INFO] Intervalo de análisis: 5 segundos")
    print("[INFO] Actualizaciones automáticas para Supabase")
    print("-" * 60)
    print("\nPresiona Ctrl+C para detener.\n")

    last_update_time = 0  # Control para actualizaciones regulares

    while True:
        try:
            current_time = time.time()
            historico, timestamps, latest_id = buscar_operacoes_historico(supabase)
            
            if not historico:
                print("Esperando datos del historial...")
                time.sleep(ANALISE_INTERVALO)
                continue

            # Analiza la estrategia Momentum-Medio
            resultado_analise = analisar_estrategia_momentum_medio(historico, timestamps[0])
            
            # La lógica de decisión es ahora mucho más simple.
            # Envía la señal si las condiciones son cumplidas O cada 5 segundos para mantener el status actualizado.
            if resultado_analise['should_operate'] or (current_time - last_update_time >= ANALISE_INTERVALO):
                if resultado_analise['should_operate']:
                    print(f"\n[SEÑAL] {resultado_analise['reason']}")
                else:
                    print(f"[AGUARDO] {resultado_analise['reason']}")

                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                
                if signal_id:
                    print(f"[OK] Señal/Actualización enviada con ID: {signal_id}")
                    last_update_time = current_time
                else:
                    print("[ERROR] Error al enviar señal/actualización")
            
            time.sleep(ANALISE_INTERVALO)
            
        except KeyboardInterrupt:
            logger.info("Bot interrumpido por el usuario.")
            print("\n[STOP] Bot detenido por el usuario.")
            break
        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}", exc_info=True)
            print(f"[ERROR] Error: {e}")
            time.sleep(ANALISE_INTERVALO)

if __name__ == "__main__":
    main_loop()