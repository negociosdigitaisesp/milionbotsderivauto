#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTOR SISTEMA COMPLETO - Orquestrador de Bots de Trading

Este script executa simultaneamente os três bots de trading estratégico:
- radartunder3.5.py (Bot principal de análise)
- executor_reversao_calma_v1.py (Estratégia Reversión-Calma)
- executor_momentum_medio_v1.py (Estratégia Momentum-Medio)

Características:
- Execução simultânea de múltiplos processos
- Tratamento robusto de erros e reinicialização automática
- Monitoramento de saúde dos processos
- Logging centralizado
- Graceful shutdown
- Sistema de retry inteligente

Autor: Sistema de Trading Automatizado
Versão: 1.0 - Sistema Completo
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Configuração de logging centralizado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('executor_sistema_completo.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ORQUESTRADOR')

# Configurações do sistema
CLASS_CONFIG = {
    'max_retries': 5,
    'retry_delay': 10,  # segundos
    'health_check_interval': 30,  # segundos
    'restart_cooldown': 60,  # segundos entre reinicializações
    'graceful_shutdown_timeout': 30  # segundos
}

# Scripts a serem executados
SCRIPTS = [
    {
        'name': 'RadarTunder',
        'script': 'radartunder3.5.py',
        'description': 'Bot principal de análise de trading',
        'critical': True  # Script crítico - sistema para se este falhar muito
    },
    {
        'name': 'ReversaoCalma',
        'script': 'executor_reversao_calma_v1.py',
        'description': 'Estratégia Reversión-Calma (LL)',
        'critical': False
    },
    {
        'name': 'MomentumMedio',
        'script': 'executor_momentum_medio_v1.py',
        'description': 'Estratégia Momentum-Medio (WW)',
        'critical': False
    }
]

class ProcessManager:
    """Gerenciador de processos com tratamento robusto de erros."""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.retry_counts: Dict[str, int] = {}
        self.last_restart: Dict[str, float] = {}
        self.shutdown_requested = False
        self.health_monitor_thread = None
        
        # Configurar handlers de sinal para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handler para sinais de shutdown."""
        logger.info(f"Recebido sinal {signum}. Iniciando shutdown graceful...")
        self.shutdown_requested = True
        
    def start_script(self, script_config: Dict) -> bool:
        """Inicia um script específico."""
        script_name = script_config['name']
        script_file = script_config['script']
        
        try:
            # Verificar se o arquivo existe
            if not Path(script_file).exists():
                logger.error(f"Script {script_file} não encontrado!")
                return False
                
            # Verificar cooldown de reinicialização
            if script_name in self.last_restart:
                time_since_restart = time.time() - self.last_restart[script_name]
                if time_since_restart < CLASS_CONFIG['restart_cooldown']:
                    logger.warning(f"[COOLDOWN] Aguardando cooldown para {script_name}. Restam {CLASS_CONFIG['restart_cooldown'] - time_since_restart:.1f}s")
                    return False
            
            # Iniciar processo
            logger.info(f"Iniciando {script_name}: {script_config['description']}")
            process = subprocess.Popen(
                [sys.executable, script_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[script_name] = process
            self.last_restart[script_name] = time.time()
            
            logger.info(f"[OK] {script_name} iniciado com PID {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"[ERRO] Erro ao iniciar {script_name}: {e}")
            return False
    
    def check_process_health(self, script_name: str) -> bool:
        """Verifica se um processo está saudável."""
        if script_name not in self.processes:
            return False
            
        process = self.processes[script_name]
        
        # Verificar se o processo ainda está rodando
        if process.poll() is not None:
            # Processo terminou
            return_code = process.returncode
            logger.warning(f"[AVISO] {script_name} terminou com codigo {return_code}")
            
            # Capturar stderr se houver
            try:
                stderr_output = process.stderr.read()
                if stderr_output:
                    logger.error(f"Erro em {script_name}: {stderr_output}")
            except:
                pass
                
            # Remover processo morto
            del self.processes[script_name]
            return False
            
        return True
    
    def restart_script(self, script_config: Dict) -> bool:
        """Reinicia um script com controle de retry."""
        script_name = script_config['name']
        
        # Incrementar contador de retry
        self.retry_counts[script_name] = self.retry_counts.get(script_name, 0) + 1
        
        # Verificar limite de retries
        if self.retry_counts[script_name] > CLASS_CONFIG['max_retries']:
            logger.error(f"❌ {script_name} excedeu limite de {CLASS_CONFIG['max_retries']} tentativas")
            
            # Se for script crítico, parar todo o sistema
            if script_config.get('critical', False):
                logger.critical(f"Script crítico {script_name} falhou. Parando sistema.")
                self.shutdown_requested = True
            return False
        
        logger.info(f"[RETRY] Tentativa {self.retry_counts[script_name]}/{CLASS_CONFIG['max_retries']} para {script_name}")
        
        # Aguardar delay antes de reiniciar
        time.sleep(CLASS_CONFIG['retry_delay'])
        
        return self.start_script(script_config)
    
    def health_monitor(self):
        """Monitor de saúde que roda em thread separada."""
        logger.info("[MONITOR] Monitor de saude iniciado")
        
        while not self.shutdown_requested:
            try:
                for script_config in SCRIPTS:
                    script_name = script_config['name']
                    
                    if not self.check_process_health(script_name):
                        logger.warning(f"[AVISO] {script_name} nao esta saudavel. Tentando reiniciar...")
                        self.restart_script(script_config)
                    
                time.sleep(CLASS_CONFIG['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Erro no monitor de saúde: {e}")
                time.sleep(5)
    
    def start_all_scripts(self):
        """Inicia todos os scripts configurados."""
        logger.info("[INICIO] Iniciando todos os scripts...")
        
        success_count = 0
        for script_config in SCRIPTS:
            if self.start_script(script_config):
                success_count += 1
            else:
                logger.error(f"Falha ao iniciar {script_config['name']}")
        
        logger.info(f"[OK] {success_count}/{len(SCRIPTS)} scripts iniciados com sucesso")
        
        # Iniciar monitor de saúde
        self.health_monitor_thread = threading.Thread(target=self.health_monitor, daemon=True)
        self.health_monitor_thread.start()
    
    def stop_all_processes(self):
        """Para todos os processos gracefully."""
        logger.info("[STOP] Parando todos os processos...")
        
        # Enviar SIGTERM para todos os processos
        for script_name, process in self.processes.items():
            try:
                logger.info(f"Enviando SIGTERM para {script_name} (PID {process.pid})")
                process.terminate()
            except Exception as e:
                logger.error(f"Erro ao terminar {script_name}: {e}")
        
        # Aguardar término graceful
        start_time = time.time()
        while self.processes and (time.time() - start_time) < CLASS_CONFIG['graceful_shutdown_timeout']:
            for script_name in list(self.processes.keys()):
                if self.processes[script_name].poll() is not None:
                    logger.info(f"✅ {script_name} terminou gracefully")
                    del self.processes[script_name]
            time.sleep(1)
        
        # Forçar término dos processos restantes
        for script_name, process in list(self.processes.items()):
            try:
                logger.warning(f"Forçando término de {script_name}")
                process.kill()
                process.wait()
                logger.info(f"✅ {script_name} terminado forçadamente")
            except Exception as e:
                logger.error(f"Erro ao forçar término de {script_name}: {e}")
            finally:
                del self.processes[script_name]
    
    def run(self):
        """Executa o sistema completo."""
        logger.info("=== INICIANDO EXECUTOR SISTEMA COMPLETO ===")
        
        print("\n" + "="*60)
        print("[SISTEMA] EXECUTOR SISTEMA COMPLETO DE TRADING")
        print("="*60)
        print("[INFO] Scripts a serem executados:")
        for script in SCRIPTS:
            status = "[CRITICO]" if script.get('critical') else "[NORMAL]"
            print(f"   • {script['name']}: {script['description']} {status}")
        print("\n[CONFIG] Configuracoes:")
        print(f"   • Maximo de tentativas: {CLASS_CONFIG['max_retries']}")
        print(f"   • Intervalo de monitoramento: {CLASS_CONFIG['health_check_interval']}s")
        print(f"   • Cooldown de reinicializacao: {CLASS_CONFIG['restart_cooldown']}s")
        print("\n[AVISO] Pressione Ctrl+C para parar o sistema")
        print("="*60 + "\n")
        
        try:
            # Iniciar todos os scripts
            self.start_all_scripts()
            
            # Loop principal
            while not self.shutdown_requested:
                # Mostrar status dos processos
                running_count = len(self.processes)
                if running_count > 0:
                    process_names = list(self.processes.keys())
                    logger.info(f"[STATUS] Status: {running_count}/{len(SCRIPTS)} processos ativos: {', '.join(process_names)}")
                else:
                    logger.warning("[AVISO] Nenhum processo ativo!")
                
                time.sleep(60)  # Status report a cada minuto
                
        except KeyboardInterrupt:
            logger.info("Interrupção manual detectada")
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
        finally:
            self.stop_all_processes()
            logger.info("[OK] Sistema parado completamente")

def main():
    """Função principal."""
    try:
        # Verificar se estamos no diretório correto
        required_files = [script['script'] for script in SCRIPTS]
        missing_files = [f for f in required_files if not Path(f).exists()]
        
        if missing_files:
            logger.error(f"❌ Arquivos não encontrados: {missing_files}")
            logger.error("Certifique-se de estar no diretório correto com todos os scripts")
            return 1
        
        # Criar e executar o gerenciador
        manager = ProcessManager()
        manager.run()
        return 0
        
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)