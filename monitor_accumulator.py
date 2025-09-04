#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor para o Accumulator Bot Standalone
Script para monitorar o desempenho e status do bot em execução.
"""

import os
import time
import psutil
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class AccumulatorMonitor:
    """Monitor para acompanhar o Accumulator bot"""
    
    def __init__(self, db_path="trading_data.db"):
        self.db_path = db_path
        self.start_time = datetime.now()
        
    def check_bot_process(self):
        """Verifica se o bot está rodando"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'accumulator_standalone.py' in ' '.join(proc.info['cmdline'] or []):
                    return {
                        'running': True,
                        'pid': proc.info['pid'],
                        'memory': proc.memory_info().rss / 1024 / 1024,  # MB
                        'cpu': proc.cpu_percent()
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {'running': False}
    
    def get_trading_stats(self, hours=24):
        """Obtém estatísticas de trading das últimas horas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Data limite
            since = datetime.now() - timedelta(hours=hours)
            since_str = since.strftime('%Y-%m-%d %H:%M:%S')
            
            # Buscar operações do Accumulator bot
            cursor.execute("""
                SELECT profit, timestamp 
                FROM trading_operations 
                WHERE bot_name LIKE '%Accumulator%' 
                AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (since_str,))
            
            operations = cursor.fetchall()
            conn.close()
            
            if not operations:
                return {
                    'total_operations': 0,
                    'total_profit': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0,
                    'last_operation': None
                }
            
            # Calcular estatísticas
            total_profit = sum(float(op[0]) for op in operations)
            wins = sum(1 for op in operations if float(op[0]) > 0)
            losses = len(operations) - wins
            win_rate = (wins / len(operations)) * 100 if operations else 0
            
            return {
                'total_operations': len(operations),
                'total_profit': round(total_profit, 2),
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 1),
                'last_operation': operations[0][1] if operations else None
            }
            
        except Exception as e:
            print(f"Erro ao obter estatísticas: {e}")
            return None
    
    def get_hourly_performance(self, hours=24):
        """Obtém performance por hora"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            since_str = since.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as operations,
                    SUM(profit) as total_profit,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins
                FROM trading_operations 
                WHERE bot_name LIKE '%Accumulator%' 
                AND timestamp >= ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """, (since_str,))
            
            hourly_data = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'hour': f"{row[0]}:00",
                    'operations': row[1],
                    'profit': round(float(row[2]), 2),
                    'wins': row[3],
                    'win_rate': round((row[3] / row[1]) * 100, 1) if row[1] > 0 else 0
                }
                for row in hourly_data
            ]
            
        except Exception as e:
            print(f"Erro ao obter performance horária: {e}")
            return []
    
    def display_status(self):
        """Exibe status completo do bot"""
        print("\n" + "="*60)
        print("🎯 ACCUMULATOR BOT - STATUS MONITOR")
        print("="*60)
        print(f"⏰ Monitoramento iniciado: {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🕐 Hora atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Status do processo
        process_info = self.check_bot_process()
        if process_info['running']:
            print(f"✅ Bot Status: RODANDO (PID: {process_info['pid']})")
            print(f"💾 Memória: {process_info['memory']:.1f} MB")
            print(f"⚡ CPU: {process_info.get('cpu', 0):.1f}%")
        else:
            print("❌ Bot Status: NÃO RODANDO")
        
        print("-" * 60)
        
        # Estatísticas de trading (últimas 24h)
        stats = self.get_trading_stats(24)
        if stats:
            print("📊 ESTATÍSTICAS (Últimas 24h):")
            print(f"   🎯 Total de operações: {stats['total_operations']}")
            print(f"   💰 Lucro total: ${stats['total_profit']}")
            print(f"   ✅ Vitórias: {stats['wins']}")
            print(f"   ❌ Derrotas: {stats['losses']}")
            print(f"   📈 Taxa de vitória: {stats['win_rate']}%")
            if stats['last_operation']:
                print(f"   🕐 Última operação: {stats['last_operation']}")
        else:
            print("📊 Nenhuma operação encontrada nas últimas 24h")
        
        print("-" * 60)
        
        # Performance por hora (últimas 12h)
        hourly = self.get_hourly_performance(12)
        if hourly:
            print("📈 PERFORMANCE POR HORA (Últimas 12h):")
            for hour_data in hourly[-6:]:  # Últimas 6 horas
                print(f"   {hour_data['hour']}: {hour_data['operations']} ops | "
                      f"${hour_data['profit']} | {hour_data['win_rate']}% vitórias")
        
        print("="*60)
    
    def monitor_continuous(self, interval=300):
        """Monitor contínuo com atualizações periódicas"""
        print(f"🔄 Iniciando monitoramento contínuo (atualização a cada {interval}s)")
        print("💡 Pressione Ctrl+C para parar")
        
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # Limpar tela
                self.display_status()
                
                print(f"\n⏳ Próxima atualização em {interval} segundos...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoramento interrompido pelo usuário")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor do Accumulator Bot')
    parser.add_argument('--continuous', '-c', action='store_true',
                       help='Monitoramento contínuo')
    parser.add_argument('--interval', '-i', type=int, default=300,
                       help='Intervalo de atualização em segundos (padrão: 300)')
    parser.add_argument('--hours', type=int, default=24,
                       help='Horas para análise de estatísticas (padrão: 24)')
    
    args = parser.parse_args()
    
    monitor = AccumulatorMonitor()
    
    if args.continuous:
        monitor.monitor_continuous(args.interval)
    else:
        monitor.display_status()

if __name__ == "__main__":
    main()