#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar se os bots estão conectados via WebSocket
e enviando dados para o Supabase corretamente
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

def main():
    print("🔍 VERIFICAÇÃO DE CONEXÃO WEBSOCKET E SUPABASE")
    print("=" * 60)
    
    try:
        # Conectar ao Supabase
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        supabase = create_client(url, key)
        
        print("✅ Conexão com Supabase estabelecida")
        
        # Verificar status dos bots
        response = supabase.table('bot_configurations') \
            .select('*') \
            .eq('is_active', True) \
            .execute()
        
        print(f"\n📊 BOTS ATIVOS: {len(response.data)}")
        print("-" * 40)
        
        current_time = datetime.now()
        
        for bot in response.data:
            bot_name = bot['bot_name']
            bot_id = bot['id']
            status = bot['status']
            last_heartbeat = bot.get('last_heartbeat')
            process_id = bot.get('process_id')
            
            print(f"\n🤖 {bot_name} (ID: {bot_id})")
            print(f"   📊 Status: {status}")
            print(f"   🔧 Process ID: {process_id}")
            
            if last_heartbeat:
                try:
                    heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                    time_diff = current_time - heartbeat_time.replace(tzinfo=None)
                    
                    if time_diff.total_seconds() < 180:  # Menos de 3 minutos
                        print(f"   💓 Heartbeat: ✅ Ativo ({time_diff.total_seconds():.0f}s atrás)")
                    else:
                        print(f"   💓 Heartbeat: ❌ Expirado ({time_diff.total_seconds():.0f}s atrás)")
                        
                except Exception as e:
                    print(f"   💓 Heartbeat: ❌ Erro ao processar: {e}")
            else:
                print(f"   💓 Heartbeat: ❌ Nunca enviado")
        
        # Verificar logs de operações recentes (últimos 10 minutos)
        print(f"\n📈 VERIFICANDO ATIVIDADE RECENTE...")
        print("-" * 40)
        
        try:
            # Tentar verificar se existe tabela de logs
            ten_minutes_ago = (current_time - timedelta(minutes=10)).isoformat()
            
            # Verificar se há atividade recente nos logs
            log_response = supabase.table('bot_operation_logs') \
                .select('bot_id, operation_result, timestamp') \
                .gte('timestamp', ten_minutes_ago) \
                .execute()
            
            if log_response.data:
                print(f"✅ {len(log_response.data)} operações registradas nos últimos 10 minutos")
                for log in log_response.data[-5:]:  # Mostrar últimas 5
                    print(f"   📝 Bot {log['bot_id']}: {log['operation_result']} em {log['timestamp']}")
            else:
                print("ℹ️ Nenhuma operação registrada nos últimos 10 minutos")
                
        except Exception as e:
            print(f"⚠️ Não foi possível verificar logs de operações: {e}")
        
        # Verificar conexão WebSocket (através dos logs)
        print(f"\n🌐 VERIFICANDO CONEXÃO WEBSOCKET...")
        print("-" * 40)
        
        # Ler últimas linhas do log para verificar atividade WebSocket
        try:
            with open('robust_order_system.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]  # Últimas 50 linhas
                
            websocket_activity = False
            tick_activity = False
            
            for line in lines:
                if 'WebSocket' in line or 'websocket' in line:
                    websocket_activity = True
                if 'tick' in line.lower() or 'quote' in line.lower():
                    tick_activity = True
            
            if websocket_activity:
                print("✅ Atividade WebSocket detectada nos logs")
            else:
                print("❌ Nenhuma atividade WebSocket detectada")
                
            if tick_activity:
                print("✅ Recebimento de ticks detectado")
            else:
                print("❌ Nenhum tick detectado")
                
        except Exception as e:
            print(f"⚠️ Erro ao verificar logs: {e}")
        
        print(f"\n🎯 RESUMO FINAL:")
        print("=" * 30)
        
        running_bots = [bot for bot in response.data if bot['status'] == 'running']
        healthy_bots = 0
        
        for bot in running_bots:
            if bot.get('last_heartbeat'):
                try:
                    heartbeat_time = datetime.fromisoformat(bot['last_heartbeat'].replace('Z', '+00:00'))
                    time_diff = current_time - heartbeat_time.replace(tzinfo=None)
                    if time_diff.total_seconds() < 180:
                        healthy_bots += 1
                except:
                    pass
        
        print(f"📊 Bots rodando: {len(running_bots)}/{len(response.data)}")
        print(f"💓 Bots com heartbeat saudável: {healthy_bots}/{len(running_bots)}")
        
        if healthy_bots == len(running_bots) and len(running_bots) > 0:
            print("\n🎉 SISTEMA FUNCIONANDO CORRETAMENTE!")
            print("   ✅ Todos os bots estão rodando")
            print("   ✅ Heartbeats estão sendo enviados")
            print("   ✅ Conexão com Supabase ativa")
        else:
            print("\n⚠️ PROBLEMAS DETECTADOS:")
            if len(running_bots) == 0:
                print("   ❌ Nenhum bot está rodando")
            elif healthy_bots < len(running_bots):
                print("   ❌ Alguns bots não estão enviando heartbeat")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())