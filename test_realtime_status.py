#!/usr/bin/env python3
"""
Script de Teste para Sistema de Status em Tempo Real

Este script verifica se os dados estão sendo salvos corretamente
na tabela radar_de_apalancamiento_signals com UPSERT e todos os campos obrigatórios.
"""

import os
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

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

def verificar_estrutura_tabela(supabase):
    """Verifica a estrutura da tabela radar_de_apalancamiento_signals"""
    try:
        print("\n🔍 Verificando estrutura da tabela...")
        
        # Tentar buscar um registro para ver quais campos existem
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .limit(1) \
            .execute()
        
        if response.data:
            campos_existentes = list(response.data[0].keys())
            print(f"✅ Campos encontrados na tabela: {', '.join(campos_existentes)}")
            return campos_existentes
        else:
            print("⚠️ Tabela vazia, não foi possível verificar estrutura")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura da tabela: {e}")
        return []

def buscar_registros_atuais(supabase):
    """Busca registros atuais na tabela"""
    try:
        print("\n📊 Buscando registros atuais...")
        
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        
        if response.data:
            print(f"✅ Encontrados {len(response.data)} registros")
            
            for i, record in enumerate(response.data[:5]):  # Mostrar apenas os 5 mais recentes
                print(f"\n📋 Registro {i+1}:")
                print(f"   ID: {record.get('id')}")
                print(f"   Bot: {record.get('bot_name')}")
                print(f"   Seguro: {record.get('is_safe_to_operate')}")
                print(f"   Motivo: {record.get('reason', 'N/A')[:50]}...")
                print(f"   Operações após padrão: {record.get('operations_after_pattern', 'N/A')}")
                print(f"   Criado em: {record.get('created_at')}")
                
                # Campos específicos do Tunder Bot
                if record.get('last_pattern_found'):
                    print(f"   Último padrão: {record.get('last_pattern_found')}")
                if record.get('historical_accuracy') is not None:
                    print(f"   Precisão histórica: {record.get('historical_accuracy')}")
            
            return response.data
        else:
            print("⚠️ Nenhum registro encontrado")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao buscar registros: {e}")
        return []

def testar_upsert_scalping_bot(supabase):
    """Testa UPSERT para Scalping Bot"""
    try:
        print("\n🧪 Testando UPSERT para Scalping Bot...")
        
        data = {
            'bot_name': 'Scalping Bot',
            'is_safe_to_operate': True,
            'reason': 'TESTE: Scalping Bot operando com segurança',
            'operations_after_pattern': 1,
            'created_at': datetime.now().isoformat(),
            'pattern_found_at': datetime.now().isoformat()
        }
        
        response = supabase.table('radar_de_apalancamiento_signals') \
            .upsert(data, on_conflict='bot_name') \
            .execute()
        
        if response.data:
            print(f"✅ UPSERT Scalping Bot bem-sucedido! ID: {response.data[0]['id']}")
            return True
        else:
            print("❌ UPSERT Scalping Bot falhou - resposta vazia")
            return False
            
    except Exception as e:
        print(f"❌ Erro no UPSERT Scalping Bot: {e}")
        return False

def testar_upsert_tunder_bot(supabase):
    """Testa UPSERT para Tunder Bot"""
    try:
        print("\n🧪 Testando UPSERT para Tunder Bot...")
        
        data = {
            'bot_name': 'Tunder Bot',
            'is_safe_to_operate': False,
            'reason': 'TESTE: Tunder Bot aguardando padrão V-D-V',
            'operations_after_pattern': 0,
            'created_at': datetime.now().isoformat(),
            'pattern_found_at': None,
            'last_pattern_found': 'Aguardando',
            'losses_in_last_10_ops': 2,
            'wins_in_last_5_ops': 3,
            'historical_accuracy': 0.75,
            'auto_disable_after_ops': 3
        }
        
        response = supabase.table('radar_de_apalancamiento_signals') \
            .upsert(data, on_conflict='bot_name') \
            .execute()
        
        if response.data:
            print(f"✅ UPSERT Tunder Bot bem-sucedido! ID: {response.data[0]['id']}")
            return True
        else:
            print("❌ UPSERT Tunder Bot falhou - resposta vazia")
            return False
            
    except Exception as e:
        print(f"❌ Erro no UPSERT Tunder Bot: {e}")
        return False

def testar_atualizacao_sequencial(supabase):
    """Testa múltiplas atualizações sequenciais para simular realtime"""
    try:
        print("\n🔄 Testando atualizações sequenciais...")
        
        # Teste 1: Scalping Bot muda para RISCO
        data1 = {
            'bot_name': 'Scalping Bot',
            'is_safe_to_operate': False,
            'reason': 'TESTE: Scalping Bot detectou risco - 3 operações completadas',
            'operations_after_pattern': 3,
            'created_at': datetime.now().isoformat()
        }
        
        response1 = supabase.table('radar_de_apalancamiento_signals') \
            .upsert(data1, on_conflict='bot_name') \
            .execute()
        
        if response1.data:
            print(f"✅ Atualização 1 - Scalping Bot: ID {response1.data[0]['id']}")
        
        time.sleep(2)
        
        # Teste 2: Tunder Bot encontra padrão
        data2 = {
            'bot_name': 'Tunder Bot',
            'is_safe_to_operate': True,
            'reason': 'TESTE: Tunder Bot - Padrão V-D-V encontrado! Pode operar.',
            'operations_after_pattern': 0,
            'created_at': datetime.now().isoformat(),
            'pattern_found_at': datetime.now().isoformat(),
            'last_pattern_found': 'V-D-V',
            'losses_in_last_10_ops': 1,
            'wins_in_last_5_ops': 4,
            'historical_accuracy': 0.82
        }
        
        response2 = supabase.table('radar_de_apalancamiento_signals') \
            .upsert(data2, on_conflict='bot_name') \
            .execute()
        
        if response2.data:
            print(f"✅ Atualização 2 - Tunder Bot: ID {response2.data[0]['id']}")
        
        time.sleep(2)
        
        # Teste 3: Scalping Bot volta ao normal
        data3 = {
            'bot_name': 'Scalping Bot',
            'is_safe_to_operate': True,
            'reason': 'TESTE: Scalping Bot - Novo padrão encontrado, operando normalmente',
            'operations_after_pattern': 0,
            'created_at': datetime.now().isoformat(),
            'pattern_found_at': datetime.now().isoformat()
        }
        
        response3 = supabase.table('radar_de_apalancamiento_signals') \
            .upsert(data3, on_conflict='bot_name') \
            .execute()
        
        if response3.data:
            print(f"✅ Atualização 3 - Scalping Bot: ID {response3.data[0]['id']}")
        
        print("✅ Teste de atualizações sequenciais concluído")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de atualizações sequenciais: {e}")
        return False

def main():
    """Função principal do teste"""
    print("="*70)
    print("🧪 TESTE DO SISTEMA DE STATUS EM TEMPO REAL")
    print("="*70)
    
    # Inicializar Supabase
    supabase = inicializar_supabase()
    if not supabase:
        return
    
    # Verificar estrutura da tabela
    campos = verificar_estrutura_tabela(supabase)
    
    # Buscar registros atuais
    registros_antes = buscar_registros_atuais(supabase)
    
    # Testar UPSERT para ambos os bots
    sucesso_scalping = testar_upsert_scalping_bot(supabase)
    sucesso_tunder = testar_upsert_tunder_bot(supabase)
    
    # Testar atualizações sequenciais
    sucesso_sequencial = testar_atualizacao_sequencial(supabase)
    
    # Verificar registros após os testes
    print("\n📊 Registros após os testes:")
    registros_depois = buscar_registros_atuais(supabase)
    
    # Resumo final
    print("\n" + "="*70)
    print("📋 RESUMO DOS TESTES")
    print("="*70)
    print(f"✅ Conexão Supabase: {'OK' if supabase else 'FALHOU'}")
    print(f"✅ Estrutura da tabela: {'OK' if campos else 'FALHOU'}")
    print(f"✅ UPSERT Scalping Bot: {'OK' if sucesso_scalping else 'FALHOU'}")
    print(f"✅ UPSERT Tunder Bot: {'OK' if sucesso_tunder else 'FALHOU'}")
    print(f"✅ Atualizações sequenciais: {'OK' if sucesso_sequencial else 'FALHOU'}")
    print(f"📊 Registros antes: {len(registros_antes)}")
    print(f"📊 Registros depois: {len(registros_depois)}")
    
    if all([supabase, campos, sucesso_scalping, sucesso_tunder, sucesso_sequencial]):
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema de realtime está funcionando.")
        print("\n💡 Próximos passos:")
        print("   1. Configure o frontend com o hook useRealtimeRadarStatus.js")
        print("   2. Implemente o componente BotStatusCards.jsx")
        print("   3. Configure as variáveis de ambiente do Supabase no frontend")
        print("   4. Teste a subscription em tempo real no navegador")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM. Verifique os erros acima.")

if __name__ == "__main__":
    main()