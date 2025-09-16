#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radartunder1.5 - Sistema de Trading com Estratégia Quantum+ MODIFICADA
Estratégia implementada:
- Quantum+ (Modo LLL Simplificado)
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

BOT_NAME = 'radartunder1.5'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 35
OPERACOES_MINIMAS = 3  # Requisito mínimo para LLL

# Estados de rastreamento de padrão
PADRAO_NAO_ENCONTRADO = 0
PADRAO_ENCONTRADO = 1
PADRAO_RESULTADO_REGISTRADO = 2

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
    Busca histórico da tabela CORRETA (tunder_bot_logs),
    com resiliência e tradução de dados.
    """
    try:
        # CORREÇÃO CRÍTICA: Apontando para a tabela correta.
        response = supabase.table('tunder_bot_logs') \
            .select('id, operation_result, timestamp') \
            .order('timestamp', desc=True) \
            .limit(OPERACOES_HISTORICO) \
            .execute()

        if not response.data:
            logger.warning("Nenhum histórico de operações foi retornado pelo banco de dados.")
            return [], [], None

        historico_raw = [op['operation_result'] for op in response.data]
        # Os dados já estão no formato correto (WIN/LOSS), não precisam de tradução
        historico_traduzido = historico_raw
        
        timestamps = [op['timestamp'] for op in response.data]
        latest_operation_id = response.data[0]['id']
        
        logger.info(f"{len(historico_traduzido)} operações carregadas da tabela 'tunder_bot_logs'.")
        return historico_traduzido, timestamps, latest_operation_id

    except Exception as e:
        logger.error(f"Erro crítico ao buscar histórico: {e}", exc_info=True)
        # CORREÇÃO DE ROBUSTEZ: Garante que a função sempre retorne a tupla de 3 valores.
        return [], [], None

def analisar_estrategia_simplificada_lll(historico: List[str]) -> Dict:
    """VERSÃO COM FILTRO: Analisa padrão LLL + filtro de losses nas últimas 20 operações."""
    strategy_name = "Quantum+ (Modo LLL Puro com Filtro)"
    
    if len(historico) < OPERACOES_MINIMAS:
        return {
            'should_operate': False,
            'reason': f"Datos insuficientes ({len(historico)}/{OPERACOES_MINIMAS})",
            'last_operations': historico[:3] if len(historico) > 0 else []
        }

    # CORREÇÃO: O gatilho LLL deve ser verificado em ordem cronológica (mais antiga -> mais recente)
    # Como o histórico vem em ordem DESC (mais recente primeiro), precisamos inverter para verificar
    ultimas_3_cronologica = list(reversed(historico[:3]))
    gatilho_lll = ['LOSS', 'LOSS', 'LOSS']
    
    # PASSO 1: Verifica se as 3 operações mais recentes (em ordem cronológica) são LLL
    logger.info(f"[{strategy_name}] Verificando padrão: {' -> '.join(ultimas_3_cronologica)} (ordem cronológica)")
    if ultimas_3_cronologica == gatilho_lll:
        logger.info(f"[{strategy_name}] Padrão LLL detectado! Verificando filtro das últimas 20 operações...")
        
        # PASSO 2: Aplica o filtro das últimas 20 operações
        ultimas_20 = historico[:20] if len(historico) >= 20 else historico
        losses_nas_20 = ultimas_20.count('LOSS')
        
        logger.info(f"[{strategy_name}] Losses nas últimas {len(ultimas_20)} operações: {losses_nas_20}")
        
        if losses_nas_20 <= 10:
            logger.info(f"[{strategy_name}] FILTRO APROVADO! {losses_nas_20} losses ≤ 10. Ativando sinal.")
            return {
                'should_operate': True,
                'strategy': strategy_name,
                'confidence': 0,
                'reason': f"Patrón LLL + Filtro OK ({losses_nas_20}/20 losses)",
                'pattern_details': {
                    'trigger': 'LLL',
                    'losses_in_20': losses_nas_20,
                    'filter_passed': True
                },
                'last_operations': historico[:3]
            }
        else:
            logger.info(f"[{strategy_name}] FILTRO REJEITADO! {losses_nas_20} losses > 10. Não operando.")
            return {
                'should_operate': False,
                'reason': f"LLL detectado mas filtro rejeitado ({losses_nas_20}/20 losses > 10)",
                'last_operations': historico[:3],
                'pattern_details': {
                    'trigger': 'LLL',
                    'losses_in_20': losses_nas_20,
                    'filter_passed': False
                }
            }
    
    # Se não é LLL, retorna aguardando
    ultimas_ops = historico[:3]
    # CORREÇÃO: Inverte a ordem para mostrar da mais antiga para mais recente (cronológica)
    ultimas_ops_cronologica = list(reversed(ultimas_ops))
    padrao_atual = ''.join(['L' if op == 'LOSS' else 'W' if op == 'WIN' else 'X' for op in ultimas_ops_cronologica])
    
    return {
        'should_operate': False,
        'reason': f"Esperando patrón LLL. Patrón actual: {padrao_atual} (cronológico: {' -> '.join(ultimas_ops_cronologica)})",
        'last_operations': ultimas_ops
    }

@retry_supabase_operation()
def enviar_sinal_supabase(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envia o sinal para a tabela do Supabase."""
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
            logger.info(f"Sinal enviado com sucesso para Supabase. ID: {signal_id}")
            return signal_id
        return None
    except Exception as e:
        logger.error(f"Falha ao enviar sinal para Supabase: {e}", exc_info=True)
        return None

@retry_supabase_operation()
def enviar_para_strategy_execution_logs(supabase: Client, signal_data: Dict) -> Optional[int]:
    """Envia o resultado da operação após o padrão LLL para a tabela strategy_execution_logs."""
    try:
        # Mapeia o resultado da operação para o formato esperado pela tabela
        resultado_operacion = signal_data.get('resultado_operacion')
        operation_1_result = None
        final_result = None
        
        if resultado_operacion == "GANADA":
            operation_1_result = "WIN"
            final_result = "WIN"
        elif resultado_operacion == "PERDIDA":
            operation_1_result = "LOSS"
            final_result = "LOSS"
        
        if not operation_1_result or not final_result:
            logger.warning(f"Resultado da operação não mapeável: {resultado_operacion}")
            return None
        
        # Cria o registro para a tabela strategy_execution_logs
        record = {
            'bot_name': BOT_NAME,
            'strategy_name': signal_data.get('strategy', 'Quantum+ (Modo LLL Puro)'),
            'confidence_level': signal_data.get('confidence', 0),
            'trigger_type': 'LLL',
            'pattern_detected_at': datetime.now().isoformat(),
            'operation_1_result': operation_1_result,
            'operation_1_completed_at': datetime.now().isoformat(),
            'final_result': final_result,
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat()
        }
        
        response = supabase.table('strategy_execution_logs').insert(record).execute()
        
        if response.data and len(response.data) > 0:
            record_id = response.data[0]['id']
            logger.info(f"Resultado enviado com sucesso para strategy_execution_logs. ID: {record_id}")
            return record_id
        else:
            logger.error("Falha ao enviar resultado para strategy_execution_logs: Resposta vazia")
            return None
    except Exception as e:
        logger.error(f"Falha ao enviar resultado para strategy_execution_logs: {e}", exc_info=True)
        return None

def main_loop():
    logger.info("=== INICIANDO TUNDER BOT COM ESTRATÉGIA LLL SIMPLIFICADA ===")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Falha fatal ao conectar com Supabase. Encerrando.")
        return

    logger.info("Bot inicializado com sucesso.")
    print("\n🚀 TUNDER BOT (MODO LLL COM FILTRO) ACTIVO")
    print("🎯 Estrategia: Detectar 3 pérdidas (LLL) consecutivas + Filtro")
    print("🔍 Filtro: Máximo 8 losses nas últimas 20 operações")
    print("⏱️  Análisis cada 5 segundos.")
    print("🔍 Rastreando resultado de la operación después del patrón LLL")
    print("📊 Enviando resultados para strategy_execution_logs (final_result e operation_1)")
    print("\nPresione Ctrl+C para detener.\n")

    last_processed_id = None  # Controle para evitar sinais duplicados
    last_update_time = 0  # Controle para atualizações regulares
    padrao_estado = PADRAO_NAO_ENCONTRADO  # Estado inicial do rastreamento de padrão
    padrao_id = None  # ID da operação onde o padrão foi encontrado
    ultima_operacao = None  # Última operação analisada

    while True:
        try:
            current_time = time.time()
            historico, timestamps, latest_id = buscar_operacoes_historico(supabase)
            
            if not historico:
                print("Esperando datos del histórico...")
                time.sleep(ANALISE_INTERVALO)
                continue

            # Analisa sempre, mas só atualiza o ID se houver novas operações
            resultado_analise = analisar_estrategia_simplificada_lll(historico)
            is_new_operation = (latest_id != last_processed_id)
            
            # Rastreamento da próxima operação após o padrão LLL
            if padrao_estado == PADRAO_ENCONTRADO and is_new_operation:
                # Temos uma nova operação após encontrar o padrão
                resultado_operacao = "GANADA" if historico[0] == "WIN" else "PERDIDA"
                print(f"\n🔍 Resultado de la operación después del patrón LLL: {resultado_operacao}")
                
                # Atualiza o resultado_analise com o resultado da operação
                resultado_analise['resultado_operacion'] = resultado_operacao
                
                # Envia o resultado para o Supabase (tabela radar_de_apalancamiento_signals)
                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                
                # Envia o resultado para a tabela strategy_execution_logs
                strategy_log_id = enviar_para_strategy_execution_logs(supabase, resultado_analise)
                
                if signal_id and strategy_log_id:
                    print(f"✅ Resultado enviado con ID: {signal_id} y registrado en strategy_execution_logs con ID: {strategy_log_id}")
                elif signal_id and not strategy_log_id:
                    print(f"✅ Resultado enviado con ID: {signal_id}, pero falló el registro en strategy_execution_logs")
                elif not signal_id and strategy_log_id:
                    print(f"✅ Registrado en strategy_execution_logs con ID: {strategy_log_id}, pero falló el envío del señal")
                else:
                    print("❌ Error al enviar resultado")
                
                # Marca como registrado independentemente do sucesso
                padrao_estado = PADRAO_RESULTADO_REGISTRADO
                last_processed_id = latest_id
                last_update_time = current_time
            
            # Sempre envia atualizações para o Supabase a cada 5 segundos
            should_update = (current_time - last_update_time >= ANALISE_INTERVALO)
            
            if resultado_analise['should_operate']:
                print(f"\n🎯 {resultado_analise['reason']}")
                print(f"📊 Últimas 3 operaciones: {historico[:3]}")
                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                if signal_id:
                    print(f"✅ Señal enviada con ID: {signal_id}")
                    padrao_estado = PADRAO_ENCONTRADO  # Marca que encontramos o padrão
                    padrao_id = latest_id  # Guarda o ID onde o padrão foi encontrado
                    last_processed_id = latest_id  # Atualiza para evitar duplicatas
                    last_update_time = current_time
                else:
                    print("❌ Error al enviar señal")
            elif should_update or is_new_operation:
                # Envia atualizações regulares mesmo sem padrão LLL
                print(f"⏳ {resultado_analise['reason']}")
                print(f"📊 Últimas 3 operaciones: {historico[:3]}")
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
                print(f"📊 Últimas 3 operaciones: {historico[:3]}")
            
            time.sleep(ANALISE_INTERVALO)
            
        except KeyboardInterrupt:
            logger.info("Bot interrompido pelo usuário.")
            print("\n🛑 Bot parado pelo usuário.")
            break
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}", exc_info=True)
            print(f"❌ Erro: {e}")
            time.sleep(ANALISE_INTERVALO)

if __name__ == "__main__":
    main_loop()