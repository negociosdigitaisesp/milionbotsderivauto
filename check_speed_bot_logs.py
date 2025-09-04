#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar se o Speed Bot foi executado com o growth_rate corrigido
"""

import os
import glob
from datetime import datetime

def check_speed_bot_logs():
    print("🔍 VERIFICANDO LOGS DO SPEED BOT")
    print("=" * 50)
    
    # Buscar arquivos de log mais recentes
    log_patterns = [
        "logs/*.log",
        "*.log",
        "bot_*.log",
        "orchestrator*.log"
    ]
    
    log_files = []
    for pattern in log_patterns:
        log_files.extend(glob.glob(pattern))
    
    if not log_files:
        print("❌ Nenhum arquivo de log encontrado")
        return
    
    # Ordenar por data de modificação (mais recente primeiro)
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    print(f"📁 Encontrados {len(log_files)} arquivos de log")
    
    speed_bot_entries = []
    growth_rate_entries = []
    
    for log_file in log_files[:5]:  # Verificar apenas os 5 mais recentes
        print(f"\n📄 Verificando: {log_file}")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Buscar por entradas do Speed Bot
            for i, line in enumerate(lines):
                if 'Speed Bot' in line or 'f8eeac8d-64dd-4f6f-b73c-d6cc922422e8' in line:
                    speed_bot_entries.append((log_file, i+1, line.strip()))
                
                if 'Growth rate' in line or 'growth_rate' in line:
                    growth_rate_entries.append((log_file, i+1, line.strip()))
                    
        except Exception as e:
            print(f"   ❌ Erro ao ler {log_file}: {e}")
    
    # Mostrar entradas do Speed Bot
    print("\n🤖 ENTRADAS DO SPEED BOT:")
    print("=" * 40)
    if speed_bot_entries:
        for log_file, line_num, content in speed_bot_entries[-10:]:  # Últimas 10
            print(f"📍 {os.path.basename(log_file)}:{line_num}")
            print(f"   {content}")
            print()
    else:
        print("❌ Nenhuma entrada do Speed Bot encontrada")
    
    # Mostrar entradas de Growth Rate
    print("\n📈 ENTRADAS DE GROWTH RATE:")
    print("=" * 40)
    if growth_rate_entries:
        for log_file, line_num, content in growth_rate_entries[-10:]:  # Últimas 10
            print(f"📍 {os.path.basename(log_file)}:{line_num}")
            print(f"   {content}")
            print()
    else:
        print("❌ Nenhuma entrada de Growth Rate encontrada")
    
    # Verificar se há logs de hoje
    today = datetime.now().strftime('%Y-%m-%d')
    today_entries = [entry for entry in speed_bot_entries if today in entry[2]]
    
    print(f"\n📅 ENTRADAS DE HOJE ({today}):")
    print("=" * 40)
    if today_entries:
        for log_file, line_num, content in today_entries:
            print(f"📍 {os.path.basename(log_file)}:{line_num}")
            print(f"   {content}")
            print()
    else:
        print("❌ Nenhuma entrada do Speed Bot encontrada hoje")

if __name__ == "__main__":
    check_speed_bot_logs()