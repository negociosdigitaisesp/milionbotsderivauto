#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Tracking - Versão com Tabelas Existentes
Testa a funcionalidade usando as tabelas já disponíveis no projeto
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

def verificar_tabelas_existentes(supabase):
    """Verifica quais tabelas existem no projeto"""
    tabelas_para_testar = [
        'scalping_accumulator_bot_logs',
        'bot_operation_logs', 
        'bot_configurations',
        'radar_de_apalancamiento_signals'
    ]
    
    tabelas_existentes = []
    
    print("\n🔍 Verificando tabelas existentes...")
    
    for tabela in tabelas_para_testar:
        try:
            response = supabase.table(tabela).select('id').limit(1).execute()
            print(f"✅ Tabela '{tabela}' existe")
            tabelas_existentes.append(tabela)
        except Exception as e:
            print(f"❌ Tabela '{tabela}' não existe: {str(e)[:50]}...")
    
    return tabelas_existentes

def testar_funcoes_tracking_basicas():
    """Testa as funções básicas de tracking usando tabelas existentes"""
    print("\n=== TESTE DAS FUNÇÕES DE TRACKING BÁSICAS ===")
    
    # Importar funções do bot principal
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Simular as funções principais
        def simular_envio_sinal(supabase, signal_data):
            """Simula envio de sinal usando tabela existente"""
            try:
                # Usar tabela de logs como alternativa
                log_data = {
                    'bot_name': 'Scalping Bot - Teste',
                    'operation_type': 'SIGNAL',
                    'status': 'info',
                    'result_details': {
                        'strategy': signal_data.get('strategy'),
                        'confidence': signal_data.get('confidence'),
                        'reason': signal_data.get('reason')
                    }
                }
                
                response = supabase.table('bot_operation_logs').insert(log_data).execute()
                
                if response.data:
                    signal_id = response.data[0]['id']
                    logger.info(f"[SIGNAL_SENT] Sinal simulado com ID: {signal_id}")
                    return signal_id
                return None
                
            except Exception as e:
                logger.error(f"[SIGNAL_ERROR] Erro ao simular sinal: {e}")
                return None
        
        def simular_tracking(supabase, strategy_name, confidence, signal_id):
            """Simula criação de tracking usando tabela existente"""
            try:
                tracking_data = {
                    'bot_name': 'Scalping Bot - Tracking',
                    'operation_type': 'TRACKING_START',
                    'status': 'info',
                    'result_details': {
                        'signal_id': signal_id,
                        'strategy_name': strategy_name,
                        'confidence_level': confidence,
                        'status': 'ACTIVE'
                    }
                }
                
                response = supabase.table('bot_operation_logs').insert(tracking_data).execute()
                
                if response.data:
                    tracking_id = response.data[0]['id']
                    logger.info(f"[TRACKING] Registro simulado com ID: {tracking_id} linkado ao signal_id: {signal_id}")
                    return tracking_id
                return None
                
            except Exception as e:
                logger.error(f"[TRACKING_ERROR] Erro ao simular tracking: {e}")
                return None
        
        def simular_finalizacao(supabase, tracking_id, resultados):
            """Simula finalização de tracking"""
            try:
                pattern_success = all(resultado == 'V' for resultado in resultados[:2])
                
                finalizacao_data = {
                    'bot_name': 'Scalping Bot - Finalização',
                    'operation_type': 'TRACKING_END',
                    'status': 'info',
                    'result_details': {
                        'tracking_id': tracking_id,
                        'operation_1_result': resultados[0] if len(resultados) > 0 else None,
                        'operation_2_result': resultados[1] if len(resultados) > 1 else None,
                        'pattern_success': pattern_success,
                        'status': 'COMPLETED'
                    }
                }
                
                response = supabase.table('bot_operation_logs').insert(finalizacao_data).execute()
                
                if response.data:
                    logger.info(f"[TRACKING] Registro {tracking_id} finalizado: {resultados} -> Sucesso: {pattern_success}")
                    return True
                return False
                
            except Exception as e:
                logger.error(f"[TRACKING_ERROR] Erro ao finalizar: {e}")
                return False
        
        return simular_envio_sinal, simular_tracking, simular_finalizacao
        
    except Exception as e:
        print(f"❌ Erro ao importar funções: {e}")
        return None, None, None

def executar_teste_completo():
    """Executa o teste completo do sistema"""
    print("\n🚀 Iniciando teste do sistema de tracking...")
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    
    if not supabase:
        print("❌ ERRO: Falha na conexão Supabase")
        return False
    
    # Verificar tabelas existentes
    tabelas_existentes = verificar_tabelas_existentes(supabase)
    
    if not tabelas_existentes:
        print("\n❌ ERRO: Nenhuma tabela compatível encontrada")
        print("\n📋 SOLUÇÃO:")
        print("   1. Execute o script setup_tracking_tables.sql no Supabase")
        print("   2. Ou execute: python test_tracking.py (após criar as tabelas)")
        return False
    
    # Testar funções básicas
    enviar_sinal, criar_tracking, finalizar_tracking = testar_funcoes_tracking_basicas()
    
    if not all([enviar_sinal, criar_tracking, finalizar_tracking]):
        print("❌ ERRO: Falha ao carregar funções de tracking")
        return False
    
    try:
        print("\n📡 Testando simulação de sinal...")
        signal_data = {
            'strategy': 'PRECISION_SURGE',
            'confidence': 95.0,
            'reason': 'Teste de simulação do sistema'
        }
        
        signal_id = enviar_sinal(supabase, signal_data)
        
        if signal_id:
            print(f"✅ Signal ID simulado: {signal_id}")
        else:
            print("❌ Falha ao simular sinal")
            return False
        
        print("\n📊 Testando simulação de tracking...")
        tracking_id = criar_tracking(supabase, 'PRECISION_SURGE', 95.0, signal_id)
        
        if tracking_id:
            print(f"✅ Tracking ID simulado: {tracking_id}")
        else:
            print("❌ Falha ao simular tracking")
            return False
        
        print("\n🏁 Testando simulação de finalização...")
        resultados_teste = ['V', 'D']  # WIN, LOSS
        sucesso = finalizar_tracking(supabase, tracking_id, resultados_teste)
        
        if sucesso:
            print(f"✅ Finalização simulada: Sucesso")
            print(f"📋 Resultados: {resultados_teste}")
        else:
            print("❌ Finalização: Falha")
            return False
        
        print("\n🎉 TESTE DE SIMULAÇÃO: SUCESSO!")
        print("✅ Todas as funções básicas estão operacionais")
        
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Execute o script setup_tracking_tables.sql no Supabase")
        print("   2. Execute: python test_tracking.py (teste completo)")
        print("   3. Execute o bot: python radar_analisis_scalping_bot.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O TESTE: {e}")
        return False

def mostrar_logs_recentes(supabase):
    """Mostra logs recentes para verificar funcionamento"""
    try:
        print("\n📊 Logs recentes do sistema:")
        
        response = supabase.table('bot_operation_logs') \
            .select('*') \
            .order('created_at', desc=True) \
            .limit(5) \
            .execute()
        
        if response.data:
            for i, log in enumerate(response.data, 1):
                print(f"   {i}. [{log['operation_type']}] {log['bot_name']} - {log['status']}")
                if log.get('result_details'):
                    details = log['result_details']
                    if isinstance(details, dict):
                        for key, value in details.items():
                            print(f"      {key}: {value}")
        else:
            print("   Nenhum log encontrado")
            
    except Exception as e:
        print(f"   Erro ao buscar logs: {e}")

if __name__ == "__main__":
    print("🎯 TESTE DO SISTEMA DE TRACKING - VERSÃO COMPATÍVEL")
    print("📋 Este teste usa as tabelas existentes para demonstrar o funcionamento")
    
    sucesso = executar_teste_completo()
    
    if sucesso:
        # Mostrar logs recentes
        supabase = inicializar_supabase()
        if supabase:
            mostrar_logs_recentes(supabase)
        
        print("\n🎯 RESULTADO FINAL: SIMULAÇÃO FUNCIONANDO!")
        print("\n⚠️  IMPORTANTE:")
        print("   - Este foi um teste de simulação")
        print("   - Para o sistema completo, execute setup_tracking_tables.sql")
        print("   - Depois execute test_tracking.py para teste real")
    else:
        print("\n⚠️  RESULTADO FINAL: PROBLEMAS DETECTADOS")
        print("   Verifique os logs de erro acima")
        print("   Consulte o arquivo GUIA_CONFIGURACAO_TRACKING.md")