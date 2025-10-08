#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTOR L-L-L PATTERN - Bot de Trading Estratégico

Este script monitora operaciones de trading en tiempo real y detecta patrones L-L-L
(3 perdas consecutivas) para identificar oportunidades de reversão.

Características:
- Análisis en tiempo real de las últimas 4 operaciones
- Detección de patrón L-L-L (3 perdas consecutivas)
- Sin filtros de horário - análisis continuo
- Envío de señales a Supabase após detección del patrón
- Logs simplificados y enfocados

Autor: Sistema de Trading Automatizado
Versión: 2.0 - L-L-L Pattern
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
OPERACOES_MINIMAS = 1  # Requisito mínimo para detectar padrão L

# Controle de estado do padrão L
pattern_state = {
    'pattern_detected': False,
    'pattern_timestamp': None,
    'pattern_operations_ids': [],
    'waiting_first_operation': False,
    'last_analyzed_operation_id': None
}



# Funções de filtro de horário removidas - estratégia agora analisa apenas padrão L-L-L

def retry_supabase_operation(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Intento {attempt + 1} falló: {e}. Reintentando...")
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
            logger.warning("No se retornó ningún historial de operaciones desde la base de datos.")
            return [], [], None

        historico_raw = [op['operation_result'] for op in response.data]
        # Los datos ya están en el formato correcto (WIN/LOSS), no necesitan traducción
        historico_traduzido = historico_raw
        
        timestamps = [op['timestamp'] for op in response.data]
        latest_operation_id = response.data[0]['id']
        
        logger.info(f"{len(historico_traduzido)} operaciones cargadas desde la tabla 'tunder_bot_logs'.")
        return historico_traduzido, timestamps, latest_operation_id

    except Exception as e:
        logger.error(f"Error crítico al buscar historial: {e}", exc_info=True)
        # CORRECCIÓN DE ROBUSTEZ: Garantiza que la función siempre retorne la tupla de 3 valores.
        return [], [], None

def analisar_estrategia_momentum_medio(historico: List[str], ultimo_timestamp: str, latest_operation_id: str = None) -> Dict:
    """Verifica si las condiciones de la estrategia L fueron cumplidas."""
    global pattern_state
    
    # 1. Validación Mínima de Datos - Necesitamos al menos 1 operación para detectar L
    if len(historico) < 1:
        return {'should_operate': False, 'reason': 'Esperando historial mínimo (1 operación)'}

    # 2. Verificar si hay nueva operación desde el último análisis
    nova_operacao = (latest_operation_id != pattern_state['last_analyzed_operation_id'])
    if nova_operacao:
        pattern_state['last_analyzed_operation_id'] = latest_operation_id
        logger.info(f"Nueva operación detectada: ID {latest_operation_id}")
    
    # 3. Análisis de las últimas operaciones en orden cronológico (más antigua a más reciente)
    # El historial viene en orden DESC (más reciente primero), entonces invertimos para análisis cronológico
    historico_cronologico = list(reversed(historico))
    
    # 4. Verificar patrón L en la última operación (posición final del historial cronológico)
    ultima_operacao = historico_cronologico[-1] if len(historico_cronologico) >= 1 else None
    
    # Debug: mostrar la última operación analizada
    logger.debug(f"Historial completo (cronológico): {historico_cronologico}")
    logger.debug(f"Última operación analizada: {ultima_operacao}")
    logger.debug(f"Estado actual del patrón: {pattern_state}")
    
    # 5. Si ya tenemos un patrón detectado y estamos esperando la primera operación
    if pattern_state['waiting_first_operation'] and nova_operacao:
        # Nueva operación después del patrón L detectado
        primeira_operacao_pos_padrao = historico[0]  # Operación más reciente
        pattern_state['pattern_detected'] = False
        pattern_state['waiting_first_operation'] = False
        pattern_state['pattern_timestamp'] = None
        
        logger.info(f"Primera operación después del patrón L ejecutada: {primeira_operacao_pos_padrao}")
        
        return {
            'should_operate': False,
            'strategy': 'L-Pattern-Executed',
            'reason': 'Aguardando Padrao, Espere...',
            'last_operations': historico[:2] if len(historico) >= 2 else historico,
            'pattern_detected': False,
            'pattern_completed': True,
            'first_operation_result': primeira_operacao_pos_padrao
        }
    
    # 6. Si ya estamos esperando la primera operación, mantener señal activa
    if pattern_state['waiting_first_operation']:
        return {
            'should_operate': True,
            'strategy': 'L-Pattern-Active',
            'reason': 'Aguardando Padrao, Espere...',
            'last_operations': historico[:1],
            'pattern_detected': True,
            'pattern_completed': False,
            'confidence': 95
        }
    
    # 7. Verificar si la última operación forma el patrón L
    if ultima_operacao == 'LOSS':
        # ¡Patrón L detectado por primera vez!
        pattern_state['pattern_detected'] = True
        pattern_state['waiting_first_operation'] = True
        pattern_state['pattern_timestamp'] = datetime.now().isoformat()
        
        logger.info("¡PATRÓN L DETECTADO! Activando señal...")
        
        return {
            'should_operate': True,
            'strategy': 'L-Pattern-Active',
            'reason': 'Aguardando Padrao, Espere...',
            'last_operations': historico[:1],
            'pattern_detected': True,
            'pattern_completed': False,
            'confidence': 95
        }
    
    # 8. Condición estándar - mostrar patrón actual de la última operación
    padrao_atual = 'L' if ultima_operacao == 'LOSS' else 'W' if ultima_operacao == 'WIN' else 'N/A'
    return {
        'should_operate': False, 
        'reason': 'Aguardando Padrao, Espere...',
        'last_operations': historico[:1] if len(historico) >= 1 else historico,
        'pattern_detected': False,
        'current_pattern': padrao_atual
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
            logger.info(f"Señal enviada exitosamente a Supabase. ID: {signal_id}")
            return signal_id
        return None
    except Exception as e:
        logger.error(f"Error al enviar señal a Supabase: {e}", exc_info=True)
        return None





def main_loop():
    """Bucle principal del bot de análisis de patrón L."""
    print("=" * 60)
    print("INICIANDO EXECUTOR L PATTERN")
    print("Detectar patrón L (1 pérdida)")
    print("=" * 60)
    
    logger.info("Iniciando Executor L Pattern - Análisis de patrón L")
    
    # Configuración de Supabase
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Error fatal al conectar con Supabase. Cerrando.")
        return

    last_update_time = 0
    update_interval = 30  # Actualizar cada 30 segundos

    while True:
        try:
            current_time = time.time()
            
            # Buscar operaciones históricas
            historico, timestamps, latest_operation_id = buscar_operacoes_historico(supabase)
            
            if not historico:
                logger.warning("Sin historial disponible. Esperando...")
                print("[AGUARDO] Sin historial disponible. Esperando...")
                time.sleep(ANALISE_INTERVALO)
                continue
            
            # Analizar estrategia
            resultado = analisar_estrategia_momentum_medio(historico, timestamps[0] if timestamps else "", latest_operation_id)
            
            # Mostrar estado actual
            if current_time - last_update_time >= update_interval:
                print(f"[AGUARDO] {resultado['reason']}")
                logger.info(f"Estado actual: {resultado['reason']}")
                
                signal_id = enviar_sinal_supabase(supabase, resultado)
                
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