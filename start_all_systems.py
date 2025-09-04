#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================
START ALL SYSTEMS - INICIALIZADOR UNIFICADO
=====================================================
Este script inicia todos os sistemas de trading:
- bot_trading_system.py (Sistema principal)
- accumulator_standalone.py (Accumulator antigo)
- radar_analyzer.py (Analisador de radar)
- orchestrator.py (Nova geração de robôs)
=====================================================
"""

import os
import sys
import time
import subprocess
import signal
import threading
from datetime import datetime
from typing import List, Dict

class SystemManager:
    """
    Gerenciador unificado de todos os sistemas de trading
    """
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        
        # Configuração dos sistemas
        self.systems = {
            'bot_trading_system': {
                'command': ['python', 'bot_trading_system.py'],
                'description': '🤖 Sistema Principal de Trading',
                'delay': 0
            },
            'accumulator_standalone': {
                'command': ['python', 'accumulator_standalone.py'],
                'description': '💰 Accumulator Bot (Standalone)',
                'delay': 5
            },
            'radar_analyzer': {
                'command': ['python', 'radar_analyzer.py'],
                'description': '📡 Radar Analyzer',
                'delay': 10
            },
            'orchestrator': {
                'command': ['python', 'orchestrator.py'],
                'description': '🎯 Orchestrator (Nova Geração)',
                'delay': 15
            }
        }
        
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handler para sinais de interrupção"""
        print(f"\n🛑 Sinal {signum} recebido. Finalizando todos os sistemas...")
        self.shutdown_all()
    
    def check_file_exists(self, filename: str) -> bool:
        """Verifica se o arquivo existe"""
        return os.path.isfile(filename)
    
    def start_system(self, name: str, config: dict) -> bool:
        """Inicia um sistema específico"""
        try:
            script_name = config['command'][1]
            
            # Verificar se o arquivo existe
            if not self.check_file_exists(script_name):
                print(f"❌ {config['description']}: Arquivo {script_name} não encontrado")
                return False
            
            print(f"🚀 Iniciando {config['description']}...")
            
            # Iniciar processo
            process = subprocess.Popen(
                config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[name] = process
            
            # Verificar se o processo iniciou corretamente
            time.sleep(2)
            if process.poll() is None:
                print(f"✅ {config['description']}: Iniciado com sucesso (PID: {process.pid})")
                
                # Iniciar thread para monitorar output
                threading.Thread(
                    target=self.monitor_process_output,
                    args=(name, process),
                    daemon=True
                ).start()
                
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {config['description']}: Falhou ao iniciar")
                if stderr:
                    print(f"   Erro: {stderr.strip()}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao iniciar {config['description']}: {e}")
            return False
    
    def monitor_process_output(self, name: str, process: subprocess.Popen):
        """Monitora output do processo"""
        try:
            while process.poll() is None and self.running:
                line = process.stdout.readline()
                if line:
                    print(f"[{name.upper()}] {line.strip()}")
                time.sleep(0.1)
        except Exception as e:
            print(f"❌ Erro no monitoramento de {name}: {e}")
    
    def check_processes(self) -> Dict[str, bool]:
        """Verifica status de todos os processos"""
        status = {}
        for name, process in self.processes.items():
            if process.poll() is None:
                status[name] = True  # Rodando
            else:
                status[name] = False  # Parado
        return status
    
    def restart_failed_processes(self):
        """Reinicia processos que falharam"""
        status = self.check_processes()
        
        for name, is_running in status.items():
            if not is_running and name in self.systems:
                print(f"🔄 Reiniciando {self.systems[name]['description']}...")
                self.start_system(name, self.systems[name])
                time.sleep(5)  # Aguardar antes do próximo
    
    def show_status(self):
        """Mostra status de todos os sistemas"""
        print("\n" + "="*60)
        print(f"📊 STATUS DOS SISTEMAS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        status = self.check_processes()
        
        for name, config in self.systems.items():
            if name in self.processes:
                is_running = status.get(name, False)
                status_icon = "🟢" if is_running else "🔴"
                pid = self.processes[name].pid if is_running else "N/A"
                print(f"{status_icon} {config['description']} (PID: {pid})")
            else:
                print(f"⚪ {config['description']} (Não iniciado)")
        
        print("="*60)
    
    def shutdown_all(self):
        """Finaliza todos os processos"""
        self.running = False
        
        print("\n🛑 Finalizando todos os sistemas...")
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    print(f"   Finalizando {name}...")
                    process.terminate()
                    
                    # Aguardar finalização graceful
                    try:
                        process.wait(timeout=10)
                        print(f"   ✅ {name} finalizado")
                    except subprocess.TimeoutExpired:
                        print(f"   ⚠️ {name} não respondeu, forçando finalização...")
                        process.kill()
                        process.wait()
                        print(f"   ✅ {name} finalizado (forçado)")
            except Exception as e:
                print(f"   ❌ Erro ao finalizar {name}: {e}")
        
        print("✅ Todos os sistemas finalizados")
        sys.exit(0)
    
    def start_all(self):
        """Inicia todos os sistemas"""
        print("")
        print("="*60)
        print("🚀 INICIALIZADOR UNIFICADO DE SISTEMAS")
        print("="*60)
        print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60)
        print("")
        
        # Verificar arquivos
        missing_files = []
        for name, config in self.systems.items():
            script_name = config['command'][1]
            if not self.check_file_exists(script_name):
                missing_files.append(script_name)
        
        if missing_files:
            print("❌ Arquivos não encontrados:")
            for file in missing_files:
                print(f"   • {file}")
            print("\n⚠️ Alguns sistemas não poderão ser iniciados.")
            print("")
        
        # Iniciar sistemas com delay
        started_count = 0
        for name, config in self.systems.items():
            if config['delay'] > 0:
                print(f"⏳ Aguardando {config['delay']} segundos antes de iniciar {config['description']}...")
                time.sleep(config['delay'])
            
            if self.start_system(name, config):
                started_count += 1
            
            print("")
        
        print(f"✅ {started_count}/{len(self.systems)} sistemas iniciados com sucesso")
        print("")
        
        # Loop de monitoramento
        self.monitoring_loop()
    
    def monitoring_loop(self):
        """Loop principal de monitoramento"""
        print("👁️ Iniciando monitoramento dos sistemas...")
        print("💡 Pressione Ctrl+C para finalizar todos os sistemas")
        print("")
        
        last_status_time = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # Mostrar status a cada 60 segundos
                if current_time - last_status_time >= 60:
                    self.show_status()
                    last_status_time = current_time
                
                # Verificar e reiniciar processos falhos a cada 30 segundos
                if int(current_time) % 30 == 0:
                    self.restart_failed_processes()
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⌨️ Interrupção manual detectada")
        except Exception as e:
            print(f"\n❌ Erro no monitoramento: {e}")
        finally:
            self.shutdown_all()

def main():
    """Função principal"""
    try:
        manager = SystemManager()
        manager.start_all()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()