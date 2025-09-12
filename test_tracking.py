#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste do Sistema de Tracking
Testa a funcionalidade completa do sistema de rastreamento de sinais
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inicializar_supabase():
    """Inicializa conexão com Supabase"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Credenciais do Supabase não encontradas no arquivo .env")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conexão com Supabase estabelecida com sucesso")
        return supabase
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Supabase: {e}")
        return None

def enviar_sinal_supabase_corrigido(supabase, signal_data):
    """Envia sinal para Supabase - versão de teste"""
    try:
        # Preparar dados do sinal
        sinal_dados = {
            'bot_name': 'Tunder Bot',
            'strategy_used': signal_data.get('strategy', 'Quantum+'),
            'strategy_confidence': signal_data.get('confidence', 71.98),
            'reason': signal_data.get('reason', 'Teste do sistema de tracking'),
            'is_safe_to_operate': signal_data.get('should_operate', True),
            'losses_in_last_10_ops': signal_data.get('losses_in_last_10_ops', 2),
            'wins_in_last_5_ops': signal_data.get('wins_in_last_5_ops', 4),
            'historical_accuracy': signal_data.get('historical_accuracy', 0.935),
            'operations_after_pattern': signal_data.get('operations_after_pattern', 0),
            'auto_disable_after_ops': signal_data.get('auto_disable_after_ops', 2)
        }
        
        # Inserir no Supabase
        response = supabase.table('radar_de_apalancamiento_signals').insert(sinal_dados).execute()
        
        if response.data and len(response.data) > 0:
            signal_id = response.data[0]['id']
            logger.info(f"[SIGNAL_SENT] Sinal enviado com ID: {signal_id}")
            return signal_id
        else:
            logger.error("[SIGNAL_ERROR] Resposta vazia do Supabase")
            return None
            
    except Exception as e:
        logger.error(f"[SIGNAL_ERROR] Erro ao enviar sinal: {e}")
        return None

def criar_registro_de_rastreamento_linkado(supabase, strategy_name, confidence, signal_id):
    """Cria registro de rastreamento linkado ao sinal - versão de teste (evitando campos duplicados)"""
    try:
        tracking_data = {
            'signal_id': signal_id,
            'strategy_name': strategy_name,
            'strategy_confidence': confidence,  # CORRETO: usar strategy_confidence
            'operation_1_result': None,  # Usar este em vez de next_operation_1_result
            'operation_2_result': None,
            'pattern_success': None,
            'status': 'ACTIVE',  # Usar este em vez de tracking_status
            'pattern_detected_at': datetime.now().isoformat(),  # Usar este em vez de pattern_found_at
            'operations_completed': 0,
            'validation_complete': False
        }
        
        response = supabase.table('strategy_results_tracking').insert(tracking_data).execute()
        
        if response.data and len(response.data) > 0:
            tracking_id = response.data[0]['id']
            logger.info(f"[TRACKING] Registro criado com ID: {tracking_id} linkado ao signal_id: {signal_id}")
            return tracking_id
        else:
            logger.error("[TRACKING_ERROR] Falha ao criar registro")
            return None
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro ao criar rastreamento: {e}")
        return None

def finalizar_registro_de_rastreamento(supabase, tracking_id, resultados):
    """Finaliza registro de rastreamento com resultados - versão de teste"""
    try:
        if len(resultados) < 2:
            logger.warning(f"[TRACKING] Resultados insuficientes: {resultados}")
            return False
            
        # Determinar sucesso do padrão (ambos WIN para sucesso)
        pattern_success = all(resultado == 'V' for resultado in resultados[:2])
        
        update_data = {
            'operation_1_result': resultados[0],
            'operation_2_result': resultados[1],
            'pattern_success': pattern_success,
            'status': 'COMPLETED',
            'completed_at': datetime.now().isoformat()
        }
        
        response = supabase.table('strategy_results_tracking') \
            .update(update_data) \
            .eq('id', tracking_id) \
            .execute()
        
        if response.data:
            logger.info(f"[TRACKING] Registro {tracking_id} finalizado: {resultados} -> Sucesso: {pattern_success}")
            return True
        else:
            logger.error(f"[TRACKING] Falha ao finalizar registro {tracking_id}")
            return False
            
    except Exception as e:
        logger.error(f"[TRACKING_ERROR] Erro ao finalizar: {e}")
        return False

def testar_sistema_tracking():
    """Teste para verificar se o tracking está funcionando"""
    print("\n=== TESTE DO SISTEMA DE TRACKING ===")
    print("Iniciando teste completo...\n")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    
    if not supabase:
        print("❌ ERRO: Falha na conexão Supabase")
        return False
    
    try:
        # 1. Testar criação de sinal
        print("📡 Testando criação de sinal...")
        signal_data = {
            'should_operate': True,
            'strategy': 'Quantum+',
            'confidence': 71.98,
            'reason': 'Teste do sistema de tracking',
            'losses_in_last_10_ops': 2,
            'wins_in_last_5_ops': 4,
            'historical_accuracy': 0.935,
            'operations_after_pattern': 0,
            'auto_disable_after_ops': 2
        }
        
        signal_id = enviar_sinal_supabase_corrigido(supabase, signal_data)
        
        if signal_id:
            print(f"✅ Signal ID criado: {signal_id}")
        else:
            print("❌ Falha ao criar sinal")
            return False
        
        # 2. Testar criação de tracking
        print("\n📊 Testando criação de tracking...")
        tracking_id = criar_registro_de_rastreamento_linkado(
            supabase, 'Quantum+', 71.98, signal_id
        )
        
        if tracking_id:
            print(f"✅ Tracking ID criado: {tracking_id}")
        else:
            print("❌ Falha ao criar tracking")
            return False
        
        # 3. Testar finalização
        print("\n🏁 Testando finalização...")
        resultados_teste = ['V', 'D']  # Simular: WIN, LOSS
        sucesso = finalizar_registro_de_rastreamento(
            supabase, tracking_id, resultados_teste
        )
        
        if sucesso:
            print(f"✅ Finalização: Sucesso")
            print(f"📋 Resultados simulados: {resultados_teste}")
        else:
            print("❌ Finalização: Falha")
            return False
        
        # 4. Verificar dados na tabela
        print("\n🔍 Verificando dados na tabela...")
        response = supabase.table('strategy_results_tracking') \
            .select('*') \
            .eq('id', tracking_id) \
            .execute()
        
        if response.data:
            registro = response.data[0]
            print(f"📊 Registro encontrado:")
            print(f"   - ID: {registro['id']}")
            print(f"   - Signal ID: {registro['signal_id']}")
            print(f"   - Estratégia: {registro['strategy_name']}")
            print(f"   - Operação 1: {registro['operation_1_result']}")
            print(f"   - Operação 2: {registro['operation_2_result']}")
            print(f"   - Sucesso do Padrão: {registro['pattern_success']}")
            print(f"   - Status: {registro['status']}")
        
        print("\n🎉 TESTE COMPLETO: SUCESSO!")
        print("✅ Todas as funcionalidades estão operacionais")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE: {e}")
        return False

def verificar_tabelas_existem(supabase):
    """Verifica se as tabelas necessárias existem"""
    try:
        print("\n🔍 Verificando tabelas...")
        
        # Testar tabela de sinais
        response1 = supabase.table('radar_de_apalancamiento_signals').select('id').limit(1).execute()
        print("✅ Tabela 'radar_de_apalancamiento_signals' existe")
        
        # Testar tabela de tracking
        response2 = supabase.table('strategy_results_tracking').select('id').limit(1).execute()
        print("✅ Tabela 'strategy_results_tracking' existe")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste do sistema de tracking...")
    
    # Verificar tabelas primeiro
    supabase = inicializar_supabase()
    if supabase and verificar_tabelas_existem(supabase):
        # Executar teste completo
        sucesso = testar_sistema_tracking()
        
        if sucesso:
            print("\n🎯 RESULTADO FINAL: SISTEMA FUNCIONANDO PERFEITAMENTE!")
            print("\n📋 Próximos passos:")
            print("   1. Execute o bot principal")
            print("   2. Observe os logs para sinais [SIGNAL_SENT] e [TRACKING]")
            print("   3. Verifique a tabela strategy_results_tracking no Supabase")
        else:
            print("\n⚠️  RESULTADO FINAL: PROBLEMAS DETECTADOS")
            print("   Verifique os logs de erro acima")
    else:
        print("\n❌ Falha na verificação inicial das tabelas")