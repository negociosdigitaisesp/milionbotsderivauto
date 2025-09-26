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
        logging.FileHandler('radarscalpingreversion_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

for lib in ['httpx', 'httpcore', 'supabase', 'postgrest']:
    logging.getLogger(lib).setLevel(logging.WARNING)

BOT_NAME = 'Scalping Reversion'
ANALISE_INTERVALO = 5
OPERACOES_HISTORICO = 35
OPERACOES_MINIMAS = 2  # Requisito mínimo para padrão LL

# Estados de rastreamento de patrón
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
                    if attempt == max_retries - 1:
                        logger.error(f"Falha definitiva em {func.__name__} após {max_retries} tentativas: {e}")
                        raise
                    logger.warning(f"Tentativa {attempt + 1} falhou em {func.__name__}: {e}. Tentando novamente em {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_supabase_operation(max_retries=3, delay=2)
def buscar_operacoes_historico(supabase: Client) -> Tuple[List[str], List[str], Optional[str]]:
    try:
        response = supabase.table('scalping_accumulator_bot_logs').select('*').order('timestamp', desc=True).limit(OPERACOES_HISTORICO).execute()
        
        if not response.data:
            logger.warning("Nenhum dado encontrado na tabela scalping_accumulator_bot_logs")
            return [], [], None
        
        historico = []
        timestamps = []
        latest_id = None
        
        for record in response.data:
            resultado = record.get('operation_result', '').upper()
            if resultado in ['WIN', 'LOSS']:
                historico.append(resultado)
                timestamps.append(record.get('timestamp', ''))
                if latest_id is None:
                    latest_id = str(record.get('id', ''))
        
        logger.info(f"Carregadas {len(historico)} operações da tabela scalping_accumulator_bot_logs")
        return historico, timestamps, latest_id
    
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        return [], [], None

def analisar_estrategia_ll_pattern(historico: List[str]) -> Dict:
    if len(historico) < OPERACOES_MINIMAS:
        return {
            'should_operate': False,
            'reason': 'Esperando Patrón Asertivo',
            'padrao_atual': 'INSUFICIENTE',
            'bot_name': BOT_NAME,
            'resultado_operacion': 'PENDING'
        }
    
    # Verifica se as duas últimas operações são LOSS-LOSS
    ultimas_2 = historico[:2]
    
    if ultimas_2 == ['LOSS', 'LOSS']:
        # Padrão LL detectado - deve operar
        return {
            'should_operate': True,
            'reason': 'PATRÓN LL DETECTADO - Dos pérdidas consecutivas identificadas',
            'padrao_atual': 'LL',
            'bot_name': BOT_NAME,
            'resultado_operacion': 'PENDING',
            'ultimas_operacoes': ' -> '.join(reversed(ultimas_2))
        }
    else:
        # Padrão LL não encontrado
        padrao_atual = ' -> '.join(reversed(ultimas_2))
        return {
            'should_operate': False,
            'reason': 'Esperando Patrón Asertivo',
            'padrao_atual': padrao_atual,
            'bot_name': BOT_NAME,
            'resultado_operacion': 'PENDING'
        }

@retry_supabase_operation()
def enviar_sinal_supabase(supabase: Client, signal_data: Dict) -> Optional[int]:
    try:
        record = {
            'bot_name': signal_data.get('bot_name', BOT_NAME),
            'is_safe_to_operate': signal_data.get('should_operate', False),
            'reason': signal_data.get('reason', ''),
            'last_pattern_found': signal_data.get('padrao_atual', ''),
            'pattern_found_at': signal_data.get('pattern_detected_at'),
            'strategy_used': 'LL Pattern',
            'strategy_confidence': 85.0 if signal_data.get('should_operate', False) else 0.0,
            'strategy_details': f"Padrão LL - {signal_data.get('reason', '')}",
            'last_update': datetime.now().isoformat()
        }
        
        response = supabase.table('radar_de_apalancamiento_signals').update(record).eq('bot_name', BOT_NAME).execute()
        
        if response.data:
            record_id = response.data[0]['id']
            logger.info(f"Sinal enviado para radar_de_apalancamiento_signals. ID: {record_id}")
            return record_id
        return None
    except Exception as e:
        logger.error(f"Error al enviar señal: {e}")
        return None

@retry_supabase_operation()
def enviar_para_strategy_execution_logs(supabase: Client, signal_data: Dict) -> Optional[int]:
    try:
        record = {
            'bot_name': signal_data.get('bot_name', BOT_NAME),
            'should_operate': signal_data.get('should_operate', False),
            'reason': signal_data.get('reason', ''),
            'padrao_atual': signal_data.get('padrao_atual', ''),
            'pattern_detected_at': signal_data.get('pattern_detected_at'),
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
    logger.info("=== INICIANDO SCALPING REVERSION CON ESTRATEGIA LL PATTERN ===")
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    if not supabase:
        logger.critical("Error fatal al conectar con Supabase. Cerrando.")
        return

    logger.info("Bot inicializado con éxito.")
    print("\n🚀 SCALPING REVERSION ACTIVO")
    print("🥈 ESTRATEGIA: LL PATTERN (LOSS-LOSS REVERSION)")
    print("🎯 Disparador: Detectar 2 LOSS consecutivos")
    print("📊 Reversión después de doble pérdida")
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
            
            # PASO 1: MODIFICAR LA LÓGICA PRINCIPAL - Saltar análisis cuando rastreando
            if padrao_estado != PADRAO_NAO_ENCONTRADO:
                # Cuando esté rastreando, NO analiza nuevos patrones
                print(f"🔍 Rastreando operaciones... Estado: {padrao_estado}")
            
            # Rastreo de las dos operaciones después del patrón
            if padrao_estado == PADRAO_ENCONTRADO and is_new_operation:
                # Primera operación después de encontrar el patrón
                operation_1_result = "WIN" if historico[0] == "WIN" else "LOSS"
                operation_1_completed_at = datetime.now().isoformat()
                print(f"\n🔍 Primera operación después del patrón: {operation_1_result}")
                
                # Actualiza el reason para mostrar progreso
                resultado_analise['reason'] = f"Patrón encontrado + resta apenas 1 operación (1ª: {operation_1_result})"
                
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
                
                # PASO 3: ELIMINAR ESTADO REDUNDANTE - Reset directo para PADRAO_NAO_ENCONTRADO
                padrao_estado = PADRAO_NAO_ENCONTRADO
                last_processed_id = latest_id
                last_update_time = current_time
                
                # Limpia variables para próximo patrón
                operation_1_result = None
                operation_1_completed_at = None
                operation_2_result = None
                operation_2_completed_at = None
                pattern_detected_at = None
            
            # PASO 2: REORGANIZAR EL FLUJO - SOLO analiza cuando no esté rastreando
            elif padrao_estado == PADRAO_NAO_ENCONTRADO:
                # SOLO AQUÍ analiza nuevos patrones
                resultado_analise = analisar_estrategia_ll_pattern(historico)
                should_update = (current_time - last_update_time >= ANALISE_INTERVALO)
                
                if resultado_analise['should_operate']:
                    print(f"\n🎯 {resultado_analise['reason']}")
                    print(f"📊 Últimas 5 operaciones: {historico[:5]}")
                    signal_id = enviar_sinal_supabase(supabase, resultado_analise)
                    if signal_id:
                        print(f"✅ Patrón detectado - Señal enviada con ID: {signal_id}")
                        padrao_estado = PADRAO_ENCONTRADO  # Detectó patrón, cambia estado
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
            print("\n🛑 Bot detenido por el usuario.")
            break
        except Exception as e:
            logger.error(f"Error en el bucle principal: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            time.sleep(ANALISE_INTERVALO)

if __name__ == "__main__":
    main_loop()