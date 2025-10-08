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

def analisar_estrategia_momentum_calmo(historico: List[str], ultimo_timestamp: str) -> Dict:
    """Verifica si las condiciones de la estrategia Momentum-Calmo fueron cumplidas."""
    
    # 1. Validación Mínima de Datos
    if len(historico) < OPERACOES_MINIMAS:
        return {'should_operate': False, 'reason': 'Esperando patrón, aguarde...'}

    # 2. Verificación del Gatillo LL (2 LOSS consecutivos)
    ultimas_2_cronologica = list(reversed(historico[:2]))
    if ultimas_2_cronologica == ['LOSS', 'LOSS']:
        return {
            'should_operate': True,
            'strategy': 'Momentum-Calmo-LL',
            'reason': 'Aguardando Padrao, Espere...',
            'last_operations': historico[:2]
        }
    
    # 3. Condición Estándar
    padrao_atual = ''.join(['W' if op == 'WIN' else 'L' for op in ultimas_2_cronologica])
    return {'should_operate': False, 'reason': 'Esperando patrón, aguarde...'}

@retry_supabase_operation()
def enviar_sinal_supabase(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envía la señal a la tabla de Supabase."""
    try:
        record = {
            'bot_name': signal_data.get('bot_name', BOT_NAME),
            'is_safe_to_operate': signal_data.get('should_operate', False),
            'reason': signal_data.get('reason', 'N/A'),
            'strategy_used': signal_data.get('strategy', 'N/A'),
            'strategy_confidence': signal_data.get('confidence', 0),
            'pattern_found_at': signal_data.get('timestamp', datetime.now().isoformat()),
            'last_update': datetime.now().isoformat(),
            'last_operations': str(signal_data.get('last_operations', [])),
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
    """Bucle principal del bot de análisis de patrones LL."""
    print("=" * 60)
    print("INICIANDO RADAR TUNDER 3.5")
    print("Detectar patrón LL (2 pérdidas consecutivas)")
    print("=" * 60)
    
    logger.info("Iniciando Radar Tunder 3.5 - Análisis de patrón LL")
    
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
            resultado = analisar_estrategia_momentum_calmo(historico, timestamps[0] if timestamps else "")
            
            # Mostrar estado actual
            if current_time - last_update_time >= update_interval:
                print(f"[AGUARDO] {resultado['reason']}")
                logger.info(f"Estado actual: {resultado['reason']}")
                
                # Preparar datos para envío
                signal_data = {
                    'bot_name': BOT_NAME,
                    'should_operate': resultado['should_operate'],
                    'reason': resultado['reason'],
                    'timestamp': datetime.now().isoformat(),
                    'last_operations': historico[:5] if len(historico) >= 5 else historico
                }
                
                signal_id = enviar_sinal_supabase(supabase, signal_data)
                
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