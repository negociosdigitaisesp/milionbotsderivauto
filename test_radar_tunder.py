#!/usr/bin/env python3
"""
Teste do Radar Analyzer Tunder
Script para testar a funcionalidade do radar_analyzer_tunder.py
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

# Importar o radar analyzer tunder
try:
    from radar_analyzer_tunder import (
        inicializar_supabase,
        buscar_operacoes_historico,
        analisar_padroes,
        buscar_ultimo_sinal,
        enviar_sinal_para_supabase,
        analisar_e_enviar_sinal,
        BOT_NAME,
        TABELA_LOGS
    )
except ImportError as e:
    print(f"Erro ao importar radar_analyzer_tunder: {e}")
    exit(1)

def testar_conexao_supabase():
    """Testa a conexão com Supabase"""
    print("\n=== TESTE 1: Conexão com Supabase ===")
    supabase = inicializar_supabase()
    if supabase:
        print("✅ Conexão com Supabase estabelecida com sucesso")
        return supabase
    else:
        print("❌ Falha na conexão com Supabase")
        return None

def testar_tabela_logs(supabase):
    """Testa se a tabela tunder_bot_logs existe"""
    print(f"\n=== TESTE 2: Verificação da tabela {TABELA_LOGS} ===")
    try:
        response = supabase.table(TABELA_LOGS).select('*').limit(1).execute()
        print(f"✅ Tabela {TABELA_LOGS} existe e é acessível")
        if response.data:
            print(f"📊 Tabela contém dados: {len(response.data)} registro(s) encontrado(s)")
        else:
            print(f"⚠️ Tabela {TABELA_LOGS} existe mas está vazia")
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar tabela {TABELA_LOGS}: {e}")
        return False

def testar_tabela_sinais(supabase):
    """Testa se a tabela radar_de_apalancamiento_signals existe"""
    print("\n=== TESTE 3: Verificação da tabela radar_de_apalancamiento_signals ===")
    try:
        response = supabase.table('radar_de_apalancamiento_signals').select('*').limit(1).execute()
        print("✅ Tabela radar_de_apalancamiento_signals existe e é acessível")
        
        # Verificar se já existe sinal para o Tunder Bot
        tunder_signals = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .eq('bot_name', BOT_NAME) \
            .execute()
        
        if tunder_signals.data:
            print(f"📊 Encontrados {len(tunder_signals.data)} sinais existentes para {BOT_NAME}")
            for signal in tunder_signals.data:
                print(f"   • ID: {signal.get('id')}, Safe: {signal.get('is_safe_to_operate')}, Reason: {signal.get('reason')}")
        else:
            print(f"⚠️ Nenhum sinal existente encontrado para {BOT_NAME}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar tabela radar_de_apalancamiento_signals: {e}")
        return False

def testar_busca_operacoes(supabase):
    """Testa a busca de operações históricas"""
    print("\n=== TESTE 4: Busca de operações históricas ===")
    try:
        historico, timestamps = buscar_operacoes_historico(supabase)
        
        if historico:
            print(f"✅ Histórico obtido com sucesso: {len(historico)} operações")
            print(f"📊 Últimas 10 operações: {' '.join(historico[:10])}")
            
            # Estatísticas
            vitorias = historico.count('V')
            derrotas = historico.count('D')
            taxa_vitoria = (vitorias / len(historico)) * 100 if historico else 0
            
            print(f"📈 Estatísticas:")
            print(f"   • Total de operações: {len(historico)}")
            print(f"   • Vitórias: {vitorias}")
            print(f"   • Derrotas: {derrotas}")
            print(f"   • Taxa de vitória: {taxa_vitoria:.1f}%")
            
            return historico, timestamps
        else:
            print("⚠️ Nenhuma operação encontrada no histórico")
            return [], []
            
    except Exception as e:
        print(f"❌ Erro ao buscar operações: {e}")
        return [], []

def testar_analise_padroes(historico):
    """Testa a análise de padrões"""
    print("\n=== TESTE 5: Análise de padrões ===")
    try:
        if not historico:
            print("⚠️ Sem histórico para analisar")
            return False, "Sem dados"
        
        is_safe, reason = analisar_padroes(historico)
        
        print(f"📊 Resultado da análise:")
        print(f"   • Seguro para operar: {'✅ SIM' if is_safe else '❌ NÃO'}")
        print(f"   • Razão: {reason}")
        
        return is_safe, reason
        
    except Exception as e:
        print(f"❌ Erro na análise de padrões: {e}")
        return False, f"Erro: {e}"

def testar_envio_sinal(supabase, is_safe, reason):
    """Testa o envio de sinal para Supabase"""
    print("\n=== TESTE 6: Envio de sinal ===")
    try:
        pattern_found_at = datetime.now().isoformat() if is_safe else None
        operations_after_pattern = 0
        
        sucesso = enviar_sinal_para_supabase(
            supabase, 
            is_safe, 
            f"TESTE: {reason}", 
            pattern_found_at, 
            operations_after_pattern
        )
        
        if sucesso:
            print("✅ Sinal enviado com sucesso")
            
            # Verificar se foi salvo
            verificacao = supabase.table('radar_de_apalancamiento_signals') \
                .select('*') \
                .eq('bot_name', BOT_NAME) \
                .order('id', desc=True) \
                .limit(1) \
                .execute()
            
            if verificacao.data:
                signal = verificacao.data[0]
                print(f"📊 Sinal verificado na base:")
                print(f"   • ID: {signal.get('id')}")
                print(f"   • Bot: {signal.get('bot_name')}")
                print(f"   • Safe: {signal.get('is_safe_to_operate')}")
                print(f"   • Reason: {signal.get('reason')}")
                print(f"   • Created: {signal.get('created_at')}")
            
            return True
        else:
            print("❌ Falha no envio do sinal")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de envio: {e}")
        return False

def testar_ciclo_completo(supabase):
    """Testa um ciclo completo de análise"""
    print("\n=== TESTE 7: Ciclo completo de análise ===")
    try:
        print("🔄 Executando ciclo completo...")
        resultado = analisar_e_enviar_sinal(supabase)
        
        if resultado:
            is_safe, reason = resultado
            print(f"✅ Ciclo completo executado com sucesso")
            print(f"📊 Resultado final: {'SAFE' if is_safe else 'WAIT'} - {reason}")
            return True
        else:
            print("⚠️ Ciclo executado mas sem retorno")
            return True
            
    except Exception as e:
        print(f"❌ Erro no ciclo completo: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🤖 TESTE DO RADAR ANALYZER TUNDER BOT")
    print("=" * 50)
    print(f"Bot Name: {BOT_NAME}")
    print(f"Tabela de Logs: {TABELA_LOGS}")
    print(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)
    
    # Teste 1: Conexão
    supabase = testar_conexao_supabase()
    if not supabase:
        print("\n❌ TESTE ABORTADO: Falha na conexão com Supabase")
        return
    
    # Teste 2: Tabela de logs
    if not testar_tabela_logs(supabase):
        print(f"\n⚠️ AVISO: Tabela {TABELA_LOGS} não acessível")
    
    # Teste 3: Tabela de sinais
    if not testar_tabela_sinais(supabase):
        print("\n❌ TESTE ABORTADO: Tabela de sinais não acessível")
        return
    
    # Teste 4: Busca de operações
    historico, timestamps = testar_busca_operacoes(supabase)
    
    # Teste 5: Análise de padrões
    is_safe, reason = testar_analise_padroes(historico)
    
    # Teste 6: Envio de sinal
    testar_envio_sinal(supabase, is_safe, reason)
    
    # Teste 7: Ciclo completo
    testar_ciclo_completo(supabase)
    
    print("\n" + "=" * 50)
    print("🎉 TESTES CONCLUÍDOS")
    print("=" * 50)
    print("\n📋 Próximos passos:")
    print("1. Verificar se a tabela tunder_bot_logs tem dados")
    print("2. Executar o radar_analyzer_tunder.py em modo contínuo")
    print("3. Monitorar os sinais na tabela radar_de_apalancamiento_signals")
    print("4. Integrar com o tunderbot.py para receber os sinais")
    
    print("\n🚀 Para executar o radar em modo contínuo:")
    print("   python radar_analyzer_tunder.py")

if __name__ == "__main__":
    main()