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
        logging.FileHandler('radartunder1.5_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

BOT_NAME = 'executor_momentum_calmo_ll_v1'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 35
OPERACOES_MINIMAS = 2  # Requisito mínimo para WW



def retry_supabase_operation(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Tentativa {attempt + 1} falhou: {e}. Tentando novamente...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Todas as {max_retries} tentativas para {func.__name__} falharam.")
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
        return {'should_operate': False, 'reason': 'Aguardando Padrao, Espere...'}

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
    return {'should_operate': False, 'reason': 'Aguardando Padrao, Espere...'}

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
    """Bucle principal del bot de análisis Momentum-Calmo-LL."""
    logger.info("=== INICIANDO EXECUTOR MOMENTUM-CALMO-LL ===")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Fallo fatal al conectar con Supabase. Cerrando.")
        return

    logger.info("Bot inicializado exitosamente.")
    print("\n[INICIO] Iniciando bot EXECUTOR MOMENTUM-CALMO-LL")
    print("[INFO] Configuração: Análisis de las últimas 2 operaciones")
    print("[INFO] Objetivo: Detectar patrón LL (2 LOSS consecutivos)")
    print("[INFO] Estratégia: Entrada após 2 LOSS consecutivos (sem filtros de horário)")
    print("[INFO] Intervalo de análisis: 5 segundos")
    print("[INFO] Actualizaciones automáticas para Supabase")
    print("-" * 60)
    print("\nPresiona Ctrl+C para detener.\n")

    last_update_time = 0  # Control para atualizações regulares

    while True:
        try:
            current_time = time.time()
            historico, timestamps, latest_id = buscar_operacoes_historico(supabase)
            
            if not historico:
                print("Esperando datos del historial...")
                time.sleep(ANALISE_INTERVALO)
                continue

            # Analisa a estratégia Momentum-Calmo
            resultado_analise = analisar_estrategia_momentum_calmo(historico, timestamps[0])
            
            # A lógica de decisão é agora muito mais simples.
            # Envia o sinal se as condições forem atendidas OU a cada 5 segundos para manter o status atualizado.
            if resultado_analise['should_operate'] or (current_time - last_update_time >= ANALISE_INTERVALO):
                if resultado_analise['should_operate']:
                    print(f"\n[SEÑAL] {resultado_analise['reason']}")
                else:
                    print(f"[AGUARDO] {resultado_analise['reason']}")

                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                
                if signal_id:
                    print(f"[OK] Sinal/Atualização enviado com ID: {signal_id}")
                    last_update_time = current_time
                else:
                    print("[ERROR] Erro ao enviar sinal/atualização")
            
            time.sleep(ANALISE_INTERVALO)
            
        except KeyboardInterrupt:
            logger.info("Bot interrompido pelo usuário.")
            print("\n[STOP] Bot parado pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}", exc_info=True)
            print(f"[ERROR] Erro: {e}")
            time.sleep(ANALISE_INTERVALO)

if __name__ == "__main__":
    main_loop()