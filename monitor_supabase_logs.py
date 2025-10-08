#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de Logs do Supabase em Tempo Real
=========================================

Este script monitora em tempo real se o Tunder Bot está enviando dados 
corretamente para a tabela 'tunder_bot_logs' no Supabase.
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

class SupabaseLogMonitor:
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        self.last_check_time = datetime.now()
        self.last_record_id = None
        self.total_records_seen = 0
        
    def get_latest_records(self):
        """Busca os registros mais recentes"""
        try:
            response = self.supabase.table('tunder_bot_logs') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(5) \
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Erro ao buscar registros: {e}")
            return []
    
    def check_for_new_records(self):
        """Verifica se há novos registros desde a última verificação"""
        records = self.get_latest_records()
        
        if not records:
            return []
        
        # Se é a primeira verificação, apenas armazena o ID mais recente
        if self.last_record_id is None:
            self.last_record_id = records[0]['id']
            return []
        
        # Verifica se há registros mais novos que o último visto
        new_records = []
        for record in records:
            if record['id'] > self.last_record_id:
                new_records.append(record)
        
        # Atualiza o último ID visto
        if new_records:
            self.last_record_id = max(record['id'] for record in new_records)
        
        return new_records
    
    def format_record(self, record):
        """Formata um registro para exibição"""
        created_at = record.get('created_at', 'N/A')
        operation_result = record.get('operation_result', 'N/A')
        profit_percentage = record.get('profit_percentage', 0)
        stake_value = record.get('stake_value', 0)
        account_name = record.get('account_name', 'N/A')
        bot_name = record.get('bot_name', 'N/A')
        
        # Calcular lucro real
        profit_real = (stake_value * profit_percentage / 100)
        
        return f"""
   📊 NOVO REGISTRO (ID: {record.get('id', 'N/A')})
      🕐 Data/Hora: {created_at}
      🎯 Resultado: {operation_result}
      💰 Stake: ${stake_value}
      📈 Profit %: {profit_percentage:.2f}%
      💵 Profit $: ${profit_real:.2f}
      👤 Conta: {account_name}
      🤖 Bot: {bot_name}"""
    
    def run_monitor(self):
        """Executa o monitor em tempo real"""
        print("🔍 MONITOR DE LOGS SUPABASE - TEMPO REAL")
        print("=" * 50)
        print("⏰ Monitorando novos registros na tabela 'tunder_bot_logs'...")
        print("🔄 Verificando a cada 5 segundos...")
        print("❌ Pressione Ctrl+C para parar")
        print("=" * 50)
        
        # Inicializar com registros atuais
        initial_records = self.get_latest_records()
        if initial_records:
            self.last_record_id = initial_records[0]['id']
            print(f"✅ Monitor inicializado - Último ID: {self.last_record_id}")
        else:
            print("⚠️ Nenhum registro encontrado na tabela")
        
        try:
            while True:
                current_time = datetime.now()
                
                # Verificar novos registros
                new_records = self.check_for_new_records()
                
                if new_records:
                    print(f"\n🆕 {len(new_records)} NOVO(S) REGISTRO(S) DETECTADO(S)!")
                    print("=" * 50)
                    
                    for record in reversed(new_records):  # Mostrar do mais antigo para o mais novo
                        print(self.format_record(record))
                        self.total_records_seen += 1
                    
                    print("=" * 50)
                    print(f"📊 Total de registros monitorados: {self.total_records_seen}")
                
                # Status a cada minuto
                if (current_time - self.last_check_time).total_seconds() >= 60:
                    print(f"\n⏰ {current_time.strftime('%H:%M:%S')} - Monitor ativo (Total: {self.total_records_seen} registros)")
                    self.last_check_time = current_time
                
                time.sleep(5)  # Verificar a cada 5 segundos
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Monitor interrompido pelo usuário")
            print(f"📊 Total de registros monitorados: {self.total_records_seen}")
            print("✅ Monitor finalizado")

def main():
    """Função principal"""
    try:
        monitor = SupabaseLogMonitor()
        monitor.run_monitor()
    except Exception as e:
        print(f"❌ Erro fatal no monitor: {e}")

if __name__ == "__main__":
    main()