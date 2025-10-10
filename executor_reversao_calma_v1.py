#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALISADOR DE HITS CONTÍNUO - Bot de Trading Estratégico

Este script monitora operações de trading em tempo real e detecta padrões de HITS
(WIN seguido de múltiplas LOSS consecutivas).

Características:
- Análise contínua das últimas operações
- Detecção de padrões HIT_2, HIT_3 e HIT_4
- Análise de risco baseada em perdas recentes
- Envio de sinais para Supabase
- Logs simplificados e focados

Padrões detectados:
- HIT_2: WIN, LOSS, LOSS
- HIT_3: WIN, LOSS, LOSS, LOSS  
- HIT_4: WIN, LOSS, LOSS, LOSS, LOSS

Autor: Sistema de Trading Automatizado
Versão: 2.0 - Analisador de HITS
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
        logging.FileHandler('executor_reversao_calma_v1_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

BOT_NAME = 'analisador_hits_continuo'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 20  # Precisamos de no máximo 20 para a análise de risco
LIMIAR_RISCO_PERDAS = 8  # Número de perdas em 20 operações para considerar o mercado arriscado

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
        
        logger.info(f"{len(historico_traduzido)} operações cargadas de la tabla 'tunder_bot_logs'.")
        return historico_traduzido, timestamps, latest_operation_id

    except Exception as e:
        logger.error(f"Error crítico al buscar historial: {e}", exc_info=True)
        # CORRECCIÓN DE ROBUSTEZ: Garantiza que la función siempre retorne la tupla de 3 valores.
        return [], [], None

def analisar_sequencia_de_hits(historico: List[str]) -> Dict:
    """Analisa sequências de HITS para detectar padrões de trading."""
    
    # 1. Verificação Mínima de Dados
    if len(historico) < 5:
        return {
            'sinal_ativo': False,
            'tipo_de_sinal': 'NENHUM',
            'mercado_arriscado': False,
            'motivo_risco': 'Aguardando mais dados (mínimo 5 operações)',
            'ultimas_operacoes': historico
        }

    # 2. Análise de Risco - Últimas 20 operações
    ultimas_20 = historico[:20] if len(historico) >= 20 else historico
    perdas_count = ultimas_20.count('LOSS')
    mercado_arriscado = perdas_count >= LIMIAR_RISCO_PERDAS
    motivo_risco = f"{perdas_count} perdas nas últimas {len(ultimas_20)} operações" if mercado_arriscado else ""

    # 3. Detecção de HITS - Ordem cronológica (mais antigo para mais novo)
    # Verificar HIT_4: ['WIN', 'LOSS', 'LOSS', 'LOSS', 'LOSS']
    if len(historico) >= 5:
        ultimas_5_operacoes = list(reversed(historico[:5]))
        if ultimas_5_operacoes == ['WIN', 'LOSS', 'LOSS', 'LOSS', 'LOSS']:
            return {
                'sinal_ativo': True,
                'tipo_de_sinal': 'HIT_4',
                'mercado_arriscado': mercado_arriscado,
                'motivo_risco': motivo_risco,
                'ultimas_operacoes': historico[:5]
            }

    # Verificar HIT_3: ['WIN', 'LOSS', 'LOSS', 'LOSS']
    if len(historico) >= 4:
        ultimas_4_operacoes = list(reversed(historico[:4]))
        if ultimas_4_operacoes == ['WIN', 'LOSS', 'LOSS', 'LOSS']:
            return {
                'sinal_ativo': True,
                'tipo_de_sinal': 'HIT_3',
                'mercado_arriscado': mercado_arriscado,
                'motivo_risco': motivo_risco,
                'ultimas_operacoes': historico[:4]
            }

    # Verificar HIT_2: ['WIN', 'LOSS', 'LOSS']
    if len(historico) >= 3:
        ultimas_3_operacoes = list(reversed(historico[:3]))
        if ultimas_3_operacoes == ['WIN', 'LOSS', 'LOSS']:
            return {
                'sinal_ativo': True,
                'tipo_de_sinal': 'HIT_2',
                'mercado_arriscado': mercado_arriscado,
                'motivo_risco': motivo_risco,
                'ultimas_operacoes': historico[:3]
            }

    # 4. Nenhum padrão encontrado
    return {
        'sinal_ativo': False,
        'tipo_de_sinal': 'NENHUM',
        'mercado_arriscado': mercado_arriscado,
        'motivo_risco': motivo_risco,
        'ultimas_operacoes': historico[:5]
    }

@retry_supabase_operation()
def enviar_sinal_supabase(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envía la señal a la tabla de Supabase."""
    try:
        record = {
            'bot_name': BOT_NAME,
            'is_safe_to_operate': not signal_data.get('mercado_arriscado', False),  # Contrário de mercado_arriscado
            'reason': signal_data.get('motivo_risco', 'Mercado em condições normais'),
            'last_pattern_found': signal_data.get('tipo_de_sinal', 'NENHUM'),
            'strategy_used': f"HITS - {signal_data.get('tipo_de_sinal', 'NENHUM')}",
            'strategy_confidence': 100 if signal_data.get('sinal_ativo') else 0,
            'pattern_found_at': datetime.now().isoformat() if signal_data.get('sinal_ativo') else None,
            'last_update': datetime.now().isoformat(),
            'last_operations': str(signal_data.get('ultimas_operacoes', []))
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
    """Bucle principal do Analisador de HITS contínuo."""
    logger.info("=== INICIANDO ANALISADOR DE HITS CONTÍNUO ===")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Fallo fatal al conectar con Supabase. Cerrando.")
        return

    logger.info("Bot inicializado exitosamente.")
    print("\n[INICIO] Iniciando ANALISADOR DE HITS CONTÍNUO")
    print("[INFO] Configuração: Análise de sequências de HITS (HIT_2, HIT_3, HIT_4)")
    print("[INFO] Objetivo: Detectar padrões WIN seguido de múltiplas LOSS")
    print("[INFO] Análise de risco: Máximo 8 perdas em 20 operações")
    print("[INFO] Intervalo de análise: 5 segundos")
    print("[INFO] Atualizações automáticas para Supabase")
    print("-" * 60)
    print("\nPresiona Ctrl+C para detener.\n")

    last_update_time = 0

    while True:
        try:
            current_time = time.time()
            historico, timestamps, latest_id = buscar_operacoes_historico(supabase)
            
            if not historico:
                print("Esperando dados do historial...")
                time.sleep(ANALISE_INTERVALO)
                continue

            # Analisa sequências de HITS
            resultado_analise = analisar_sequencia_de_hits(historico)
            
            # Envia sinal sempre para manter o painel de status vivo
            if resultado_analise['sinal_ativo']:
                risk_msg = f" | RISCO: {resultado_analise['motivo_risco']}" if resultado_analise['mercado_arriscado'] else ""
                
                # Mensagem especial em espanhol para HIT_4
                if resultado_analise['tipo_de_sinal'] == 'HIT_4':
                    print(f"\n[PATRÓN ENCONTRADO] {resultado_analise['tipo_de_sinal']} - ¡Activar bot ahora!{risk_msg}")
                else:
                    print(f"\n[SINAL ATIVO] {resultado_analise['tipo_de_sinal']}{risk_msg}")
            else:
                risk_msg = f" | RISCO: {resultado_analise['motivo_risco']}" if resultado_analise['mercado_arriscado'] else ""
                print(f"[AGUARDO] Nenhum padrão detectado{risk_msg}")

            signal_id = enviar_sinal_supabase(supabase, resultado_analise)
            
            if signal_id:
                print(f"[OK] Sinal/Atualização enviada com ID: {signal_id}")
                last_update_time = current_time
            else:
                print("[ERROR] Erro ao enviar sinal/atualização")
            
            time.sleep(ANALISE_INTERVALO)
            
        except KeyboardInterrupt:
            logger.info("Bot interrompido pelo usuário.")
            print("\n[STOP] Bot detido pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro no bucle principal: {e}", exc_info=True)
            print(f"[ERROR] Erro: {e}")
            time.sleep(ANALISE_INTERVALO)

if __name__ == "__main__":
    main_loop()