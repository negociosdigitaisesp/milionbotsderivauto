#!/usr/bin/env python3
"""
Teste final para verificar se ambos os radares estão enviando os nomes corretos dos bots
"""

import os
import subprocess
import time
import threading
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def executar_radar_original():
    """Executa o radar original por alguns segundos"""
    try:
        print("🔄 Iniciando Radar Original (Scalping Bot)...")
        process = subprocess.Popen(['python', 'radar_analyzer.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Deixar rodar por 10 segundos
        time.sleep(10)
        process.terminate()
        print("✅ Radar Original finalizado")
        
    except Exception as e:
        print(f"❌ Erro no Radar Original: {e}")

def executar_radar_tunder():
    """Executa o radar do Tunder Bot por alguns segundos"""
    try:
        print("🔄 Iniciando Radar Tunder Bot...")
        process = subprocess.Popen(['python', 'radar_analyzer_tunder.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Deixar rodar por 10 segundos
        time.sleep(10)
        process.terminate()
        print("✅ Radar Tunder Bot finalizado")
        
    except Exception as e:
        print(f"❌ Erro no Radar Tunder Bot: {e}")

def verificar_resultados():
    """Verifica os resultados na tabela"""
    try:
        # Conectar ao Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Credenciais do Supabase não encontradas")
            return
        
        supabase: Client = create_client(supabase_url, supabase_key)
        print("\n🔍 Verificando resultados na tabela...")
        
        # Buscar os últimos registros
        response = supabase.table('radar_de_apalancamiento_signals') \
            .select('bot_name, id, created_at, is_safe_to_operate') \
            .order('created_at', desc=True) \
            .limit(20) \
            .execute()
        
        if response.data:
            scalping_count = 0
            tunder_count = 0
            incorrect_count = 0
            
            print("\n📊 Últimos registros:")
            print("=" * 70)
            
            for record in response.data:
                bot_name = record.get('bot_name', 'N/A')
                record_id = record.get('id', 'N/A')
                created_at = record.get('created_at', 'N/A')[:19] if record.get('created_at') else 'N/A'
                
                if bot_name == 'Scalping Bot':
                    status = "✅ CORRETO"
                    scalping_count += 1
                elif bot_name == 'Tunder Bot':
                    status = "✅ CORRETO"
                    tunder_count += 1
                else:
                    status = "❌ INCORRETO"
                    incorrect_count += 1
                
                print(f"{status} | ID: {record_id} | Bot: '{bot_name}' | {created_at}")
            
            print("\n📈 RESUMO DOS RESULTADOS:")
            print("=" * 50)
            print(f"✅ Scalping Bot (correto): {scalping_count} registros")
            print(f"✅ Tunder Bot (correto): {tunder_count} registros")
            print(f"❌ Nomes incorretos: {incorrect_count} registros")
            
            if incorrect_count == 0:
                print("\n🎉 SUCESSO! Todos os nomes estão corretos!")
            else:
                print(f"\n⚠️ Ainda existem {incorrect_count} registros com nomes incorretos (provavelmente antigos)")
                
        else:
            print("⚠️ Nenhum registro encontrado")
        
    except Exception as e:
        print(f"❌ Erro ao verificar resultados: {e}")

def main():
    """Função principal"""
    print("🚀 TESTE FINAL - VERIFICAÇÃO DOS NOMES DOS BOTS")
    print("=" * 60)
    
    # Executar ambos os radares em paralelo
    thread1 = threading.Thread(target=executar_radar_original)
    thread2 = threading.Thread(target=executar_radar_tunder)
    
    print("⏳ Executando ambos os radares por 10 segundos...")
    
    thread1.start()
    thread2.start()
    
    # Aguardar ambos terminarem
    thread1.join()
    thread2.join()
    
    print("\n⏳ Aguardando 2 segundos para sincronização...")
    time.sleep(2)
    
    # Verificar resultados
    verificar_resultados()
    
    print("\n✅ Teste finalizado!")

if __name__ == "__main__":
    main()