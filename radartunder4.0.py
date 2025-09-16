#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radartunder4.0 - Sistema de Trading com Estratégia LL+ (2 Losses + Filtro)
Estratégia implementada:
- LL+ (2 Losses Consecutivos + Filtro de 4+ losses em 6 operações)
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
        logging.FileHandler('radartunder4.0_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

BOT_NAME = 'radartunder4.0'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 35
OPERACOES_MINIMAS = 6  # Requisito mínimo para LL+ (precisa de 6 operações para análise)

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

def analisar_estrategia_ll_plus(historico: List[str]) -> Dict:
    """ESTRATÉGIA LL+: 2 Losses consecutivos + ≥4 losses nas últimas 6 operações."""
    strategy_name = "LL+ (2 Losses + Filtro 4/6)"
    
    if len(historico) < OPERACOES_MINIMAS:
        return {
            'should_operate': False,
            'reason': f"Datos insuficientes ({len(historico)}/{OPERACOES_MINIMAS})",
            'last_operations': historico[:6] if len(historico) > 0 else []
        }

    # PASSO 1: Verifica se as 2 operações mais recentes são LL (em ordem cronológica)
    # Como o histórico vem em ordem DESC (mais recente primeiro), as 2 primeiras são as mais recentes
    ultimas_2 = historico[:2]
    ultimas_2_cronologica = list(reversed(ultimas_2))  # Inverte para ordem cronológica
    gatilho_ll = ['LOSS', 'LOSS']
    
    logger.info(f"[{strategy_name}] Verificando padrão LL: {' -> '.join(ultimas_2_cronologica)} (ordem cronológica)")
    
    if ultimas_2_cronologica == gatilho_ll:
        logger.info(f"[{strategy_name}] Padrão LL detectado! Verificando filtro das últimas 6 operações...")
        
        # PASSO 2: Aplica o filtro das últimas 6 operações
        ultimas_6 = historico[:6]
        losses_nas_6 = ultimas_6.count('LOSS')
        
        logger.info(f"[{strategy_name}] Losses nas últimas 6 operações: {losses_nas_6}")
        logger.info(f"[{strategy_name}] Últimas 6 ops: {' -> '.join(reversed(ultimas_6))} (cronológica)")
        
        if losses_nas_6 >= 4:
            logger.info(f"[{strategy_name}] FILTRO APROVADO! {losses_nas_6} losses ≥ 4. Ativando sinal.")
            return {
                'should_operate': True,
                'strategy': strategy_name,
                'confidence': 71.3,  # 71,3% de expectativa conforme especificado
                'reason': f"Patrón LL + Filtro OK ({losses_nas_6}/6 losses ≥ 4) - P(Win)=71.3%",
                'pattern_details': {
                    'trigger': 'LL',
                    'losses_in_6': losses_nas_6,
                    'filter_passed': True,
                    'win_probability': 71.3
                },
                'last_operations': ultimas_6
            }
        else:
            logger.info(f"[{strategy_name}] FILTRO REJEITADO! {losses_nas_6} losses < 4. Não operando.")
            return {
                'should_operate': False,
                'reason': f"LL detectado mas filtro rejeitado ({losses_nas_6}/6 losses < 4)",
                'last_operations': ultimas_6,
                'pattern_details': {
                    'trigger': 'LL',
                    'losses_in_6': losses_nas_6,
                    'filter_passed': False
                }
            }
    
    # Se não é LL, retorna aguardando
    ultimas_ops = historico[:6]
    # CORREÇÃO: Inverte a ordem para mostrar da mais antiga para mais recente (cronológica)
    ultimas_ops_cronologica = list(reversed(ultimas_ops))
    padrao_atual = ''.join(['L' if op == 'LOSS' else 'W' if op == 'WIN' else 'X' for op in ultimas_ops_cronologica])
    
    # Verifica quantos losses há nas últimas 6 para informar o progresso
    losses_atuais = ultimas_ops.count('LOSS')
    
    return {
        'should_operate': False,
        'reason': f"Esperando patrón LL. Actual: {padrao_atual[-2:]} ({losses_atuais}/6 losses)",
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
    """Envia para strategy_execution_logs quando padrão for detectado."""
    try:
        record = {
            'bot_name': BOT_NAME,
            'strategy_name': signal_data.get('strategy', 'LL+ (2 Losses + Filtro 4/6)'),
            'confidence_level': signal_data.get('confidence', 71.3),
            'trigger_type': 'LL',
            'pattern_detected_at': datetime.now().isoformat(),
            'status': 'WAITING'
        }
        
        response = supabase.table('strategy_execution_logs').insert(record).execute()
        
        if response.data:
            record_id = response.data[0]['id']
            logger.info(f"Padrão registrado em strategy_execution_logs. ID: {record_id}")
            return record_id
        return None
    except Exception as e:
        logger.error(f"Erro ao registrar padrão em strategy_execution_logs: {e}")
        return None

@retry_supabase_operation()
def atualizar_resultado_strategy_logs(supabase: Client, record_id: int, resultado: str) -> bool:
    """Atualiza resultado na strategy_execution_logs."""
    try:
        final_result = "WIN" if resultado == "GANADA" else "LOSS"
        now = datetime.now().isoformat()
        
        response = supabase.table('strategy_execution_logs').update({
            'operation_1_result': final_result,
            'operation_1_completed_at': now,
            'final_result': final_result,
            'pattern_success': resultado == "GANADA",
            'status': 'COMPLETED',
            'completed_at': now
        }).eq('id', record_id).execute()
        
        logger.info(f"Resultado {resultado} atualizado em strategy_execution_logs ID: {record_id}")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar resultado: {e}")
        return False

def main_loop():
    logger.info("=== INICIANDO TUNDER BOT 4.0 COM ESTRATÉGIA LL+ ===") 
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Falha fatal ao conectar com Supabase. Encerrando.")
        return

    logger.info("Bot inicializado com sucesso.")
    print("\n🚀 TUNDER BOT 4.0 (MODO LL+ COM FILTRO) ACTIVO")
    print("🎯 Estrategia: Detectar 2 pérdidas (LL) consecutivas + Filtro")
    print("🔍 Filtro: Mínimo 4 losses nas últimas 6 operações")
    print("⚡ Expectativa: 71,3% chance de WIN")
    print("⏱️  Análisis cada 5 segundos.")
    print("🔍 Rastreando resultado de la operación después del patrón LL")
    print("📊 Enviando resultados para strategy_execution_logs (final_result e operation_1)")
    print("\nPresione Ctrl+C para detener.\n")

    last_processed_id = None  # Controle para evitar sinais duplicados
    last_update_time = 0  # Controle para atualizações regulares
    padrao_estado = PADRAO_NAO_ENCONTRADO  # Estado inicial do rastreamento de padrão
    padrao_id = None  # ID da operação onde o padrão foi encontrado
    strategy_log_id = None  # ID do registro na strategy_execution_logs
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
            resultado_analise = analisar_estrategia_ll_plus(historico)
            is_new_operation = (latest_id != last_processed_id)
            
            # Rastreamento da próxima operação após o padrão LL
            if padrao_estado == PADRAO_ENCONTRADO and is_new_operation:
                # Temos uma nova operação após encontrar o padrão
                resultado_operacao = "GANADA" if historico[0] == "WIN" else "PERDIDA"
                print(f"\n🔍 Resultado de la operación después del patrón LL: {resultado_operacao}")
                
                # Atualiza o resultado_analise com o resultado da operação
                resultado_analise['resultado_operacion'] = resultado_operacao
                
                # Envia o resultado para o Supabase (tabela radar_de_apalancamiento_signals)
                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                
                # Atualiza o resultado na strategy_execution_logs
                if strategy_log_id:
                    resultado_atualizado = atualizar_resultado_strategy_logs(supabase, strategy_log_id, resultado_operacao)
                    if resultado_atualizado:
                        print(f"✅ Resultado {resultado_operacao} atualizado em strategy_execution_logs ID: {strategy_log_id}")
                    else:
                        print(f"❌ Erro ao atualizar resultado em strategy_execution_logs ID: {strategy_log_id}")
                
                if signal_id:
                    print(f"✅ Resultado enviado con ID: {signal_id}")
                else:
                    print("❌ Error al enviar resultado")
                
                # Marca como registrado independentemente do sucesso
                padrao_estado = PADRAO_RESULTADO_REGISTRADO
                strategy_log_id = None  # Reset para próximo padrão
                last_processed_id = latest_id
                last_update_time = current_time
            
            # Sempre envia atualizações para o Supabase a cada 5 segundos
            should_update = (current_time - last_update_time >= ANALISE_INTERVALO)
            
            if resultado_analise['should_operate']:
                print(f"\n🎯 {resultado_analise['reason']}")
                print(f"📊 Últimas 6 operaciones: {historico[:6]}")
                signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                
                # Registra o padrão detectado na strategy_execution_logs
                strategy_log_id = enviar_para_strategy_execution_logs(supabase, resultado_analise)
                
                if signal_id:
                    print(f"✅ Señal enviada con ID: {signal_id}")
                    if strategy_log_id:
                        print(f"✅ Padrón registrado en strategy_execution_logs con ID: {strategy_log_id}")
                    padrao_estado = PADRAO_ENCONTRADO  # Marca que encontramos o padrão
                    padrao_id = latest_id  # Guarda o ID onde o padrão foi encontrado
                    last_processed_id = latest_id  # Atualiza para evitar duplicatas
                    last_update_time = current_time
                else:
                    print("❌ Error al enviar señal")
            elif should_update or is_new_operation:
                # Envia atualizações regulares mesmo sem padrão LL
                print(f"⏳ {resultado_analise['reason']}")
                print(f"📊 Últimas 6 operaciones: {historico[:6]}")
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
                print(f"📊 Últimas 6 operaciones: {historico[:6]}")
            
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