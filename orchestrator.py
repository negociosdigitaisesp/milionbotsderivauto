#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================
ORCHESTRATOR - GERENTE DA NOVA GERAÇÃO DE ROBÔS
=====================================================
Este script gerencia exclusivamente os robôs definidos
na tabela bot_configurations do Supabase.

Robôs Controlados:
- Accumulator
- Speed Bot

Outros scripts de robôs na VPS são ignorados.
=====================================================
"""

import os
import sys
import time
import signal
import subprocess
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ORCHESTRATOR] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
except ImportError as e:
    logger.error(f"Dependências não encontradas: {e}")
    logger.error("Execute: pip install supabase python-dotenv")
    sys.exit(1)

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

class BotOrchestrator:
    """
    Orquestrador principal para gerenciar a nova geração de robôs
    """
    
    def __init__(self):
        self.supabase = self._init_supabase()
        self.active_processes: Dict[str, subprocess.Popen] = {}  # Mudança: usar bot_id como chave
        self.bot_configs: Dict[str, dict] = {}
        self.bot_health_status: Dict[str, str] = {}  # Novo: rastrear status de saúde
        self.recently_started: Dict[str, float] = {}  # Novo: rastrear processos recém-iniciados
        self.shutdown_requested = False
        self.sync_interval = 60  # segundos
        self.heartbeat_timeout = 180  # 3 minutos
        self.startup_delay = 5  # segundos entre inicializações
        self.startup_grace_period = 30  # segundos de graça para novos processos
        
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("[ORCHESTRATOR] Orchestrator inicializado")
    
    def _init_supabase(self) -> Client:
        """Inicializa conexão com Supabase"""
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_ANON_KEY')
            
            if not url or not key:
                raise ValueError("SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidas no .env.accumulator")
            
            supabase = create_client(url, key)
            
            # Testar conexão
            test_response = supabase.table('bot_configurations').select('count').execute()
            logger.info("[SUPABASE] Conexão com Supabase estabelecida")
            
            return supabase
            
        except Exception as e:
            logger.error(f"[ERROR] Erro ao conectar com Supabase: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de shutdown"""
        logger.info(f"[SIGNAL] Sinal {signum} recebido. Iniciando shutdown graceful...")
        self.shutdown_requested = True
    
    def sync_with_database(self) -> bool:
        """Sincroniza estado com a tabela bot_configurations"""
        try:
            logger.info("[SYNC] Sincronizando com banco de dados...")
            # Sincronização com banco de dados
            
            # Buscar configurações ativas
            response = self.supabase.table('bot_configurations') \
                .select('*') \
                .eq('is_active', True) \
                .execute()
            
            if not response.data:
                logger.warning("[WARNING] Nenhum robô ativo encontrado na configuração")
                return True
            
            # Atualizar configurações locais
            new_configs = {}
            for config in response.data:
                bot_id = str(config['id'])  # Usar bot_id como chave principal
                bot_name = config['bot_name']
                new_configs[bot_id] = config
                
                # Log das configurações carregadas (com verificação de campos)
                stake = config.get('param_stake_inicial', 'N/A')
                take_profit = config.get('param_take_profit', 'N/A')
                status = config.get('status', 'stopped')
                
                logger.info(f"[CONFIG] {bot_name} (ID: {bot_id}): stake={stake}, "
                          f"take_profit={take_profit}, "
                          f"status={status}")
            
            self.bot_configs = new_configs
            # Sincronização concluída
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Erro na sincronização: {e}")
            return False
    
    def check_process_health(self):
        """ETAPA 1: Verifica a saúde real de todos os processos"""
        try:
            logger.info("[HEALTH] === VERIFICAÇÃO DE SAÚDE DOS PROCESSOS ===")
            logger.info(f"[HEALTH] Processos ativos rastreados: {len(self.active_processes)}")
            logger.info(f"[HEALTH] Bot IDs ativos: {list(self.active_processes.keys())}")
            current_time = datetime.now()
            
            # Loop 1: Verificar saúde de cada robô
            for bot_id, config in self.bot_configs.items():
                bot_name = config['bot_name']
                logger.info(f"[HEALTH] Verificando {bot_name} (ID: {bot_id})")
                
                # Verificar se deveria estar rodando
                if bot_id in self.active_processes:
                    process = self.active_processes[bot_id]
                    
                    # Verificar se processo ainda está vivo
                    if process.poll() is not None:
                        logger.warning(f"[DEAD] {bot_name}: Processo morreu (PID: {process.pid})")
                        del self.active_processes[bot_id]
                        self.bot_health_status[bot_id] = 'dead'
                        continue
                    
                    # Verificar heartbeat para detectar zumbis
                    last_heartbeat = config.get('last_heartbeat')
                    if last_heartbeat:
                        try:
                            if isinstance(last_heartbeat, str):
                                last_heartbeat = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                            
                            time_diff = current_time - last_heartbeat.replace(tzinfo=None)
                            
                            if time_diff.total_seconds() > self.heartbeat_timeout:
                                logger.warning(f"[ZOMBIE] {bot_name}: Heartbeat expirado ({time_diff.total_seconds():.0f}s)")
                                
                                # Matar processo zumbi
                                try:
                                    process.kill()
                                    process.wait(timeout=5)
                                except Exception as e:
                                    logger.error(f"[ERROR] Erro ao matar processo zumbi {bot_name}: {e}")
                                
                                del self.active_processes[bot_id]
                                self.bot_health_status[bot_id] = 'dead'
                                continue
                        except Exception as e:
                            logger.error(f"[ERROR] Erro ao verificar heartbeat de {bot_name}: {e}")
                    
                    # Se chegou até aqui, processo está saudável
                    self.bot_health_status[bot_id] = 'healthy'
                    logger.debug(f"[HEALTHY] {bot_name}: Processo saudável (PID: {process.pid})")
                    
                else:
                    # Não está na lista de processos ativos
                    self.bot_health_status[bot_id] = 'stopped'
                    logger.debug(f"[STOPPED] {bot_name}: Não está rodando")
                    
        except Exception as e:
            logger.error(f"[ERROR] Erro na verificação de saúde: {e}")
    
    def manage_bot_processes(self):
        """ETAPA 2: Decide quais processos iniciar/parar baseado na saúde atual"""
        try:
            logger.info("[MANAGE] === GERENCIAMENTO DE PROCESSOS ===")
            
            # Loop 2: Decidir ações baseado no status de saúde atualizado
            for bot_id, config in self.bot_configs.items():
                bot_name = config['bot_name']
                database_status = config.get('status', 'stopped')
                health_status = self.bot_health_status.get(bot_id, 'unknown')
                
                logger.info(f"[DECISION] {bot_name}: DB_Status={database_status}, Health={health_status}")
                
                # Lógica de decisão baseada no estado real
                if health_status in ['dead', 'stopped']:
                    if database_status in ['running', 'starting']:
                        logger.info(f"[ACTION] {bot_name}: Precisa ser iniciado (morto/parado mas deveria estar rodando)")
                        self._start_bot_process(bot_id, bot_name)
                    else:
                        logger.debug(f"[ACTION] {bot_name}: Mantém parado (status correto)")
                        
                elif health_status == 'healthy':
                    if database_status == 'stopped':
                        logger.info(f"[ACTION] {bot_name}: Precisa ser parado (rodando mas deveria estar parado)")
                        self._terminate_bot_process(bot_id, bot_name)
                    else:
                        logger.debug(f"[ACTION] {bot_name}: Mantém rodando (status correto)")
                        
                else:
                    logger.warning(f"[ACTION] {bot_name}: Status desconhecido - investigar")
                    
        except Exception as e:
            logger.error(f"[ERROR] Erro no gerenciamento de processos: {e}")
    
    def _start_bot_process(self, bot_id: str, bot_name: str):
        """Inicia um processo de robô"""
        try:
            logger.info(f"[START] Iniciando {bot_name} (ID: {bot_id})...")
            
            # Comando para iniciar o bot_instance.py
            cmd = [sys.executable, 'bot_instance.py', '--bot_id', bot_id]
            
            # Iniciar processo (sem capturar stdout/stderr para evitar buffer overflow)
            process = subprocess.Popen(
                cmd,
                cwd=os.getcwd()
            )
            
            # Registrar processo na lista ativa
            self.active_processes[bot_id] = process
            self.bot_health_status[bot_id] = 'starting'
            self.recently_started[bot_id] = time.time()  # Registrar tempo de início
            
            # Processo adicionado à lista ativa
            
            # Atualizar status no banco
            self._update_bot_status(bot_id, 'starting', process.pid)
            
            logger.info(f"[SUCCESS] {bot_name}: Processo iniciado (PID: {process.pid})")
            
            # Delay para não sobrecarregar APIs
            time.sleep(self.startup_delay)
            
        except Exception as e:
            logger.error(f"[ERROR] Erro ao iniciar {bot_name}: {e}")
            self._update_bot_status(bot_id, 'error', None)
            self.bot_health_status[bot_id] = 'error'
    
    def _terminate_bot_process(self, bot_id: str, bot_name: str):
        """Termina um processo de robô"""
        try:
            if bot_id in self.active_processes:
                process = self.active_processes[bot_id]
                
                logger.info(f"[TERMINATE] Terminando {bot_name} (PID: {process.pid})...")
                
                # Tentar terminar graciosamente
                process.terminate()
                
                # Aguardar até 10 segundos
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Forçar kill se não terminar
                    logger.warning(f"[KILL] Forçando kill do {bot_name}")
                    process.kill()
                    process.wait()
                
                # Remover da lista ativa
                del self.active_processes[bot_id]
                self.bot_health_status[bot_id] = 'stopped'
                
                # Atualizar status no banco
                self._update_bot_status(bot_id, 'stopped', None)
                
                logger.info(f"[SUCCESS] {bot_name}: Processo terminado")
                
        except Exception as e:
            logger.error(f"[ERROR] Erro ao terminar {bot_name}: {e}")
    
    def _is_bot_process_running(self, bot_id: str) -> bool:
        """Verifica se um processo de bot ainda está rodando"""
        if bot_id not in self.active_processes:
            return False
        
        process = self.active_processes[bot_id]
        return process.poll() is None
    
    def _update_bot_status(self, bot_id: str, status: str, process_id: Optional[int]):
        """Atualiza status do robô no banco de dados"""
        try:
            update_data = {
                'status': status
            }
            
            if process_id is not None:
                update_data['process_id'] = process_id
            
            self.supabase.table('bot_configurations') \
                .update(update_data) \
                .eq('id', bot_id) \
                .execute()
                
        except Exception as e:
            logger.error(f"[ERROR] Erro ao atualizar status: {e}")
    
    def cleanup_dead_processes(self):
        """Remove processos mortos da lista ativa"""
        current_time = time.time()
        dead_bot_ids = []
        
        for bot_id, process in self.active_processes.items():
            if process.poll() is not None:
                # Verificar se o processo foi iniciado recentemente
                start_time = self.recently_started.get(bot_id, 0)
                time_since_start = current_time - start_time
                
                if time_since_start < self.startup_grace_period:
                    continue  # Ignorar durante período de graça
                
                dead_bot_ids.append(bot_id)
        
        for bot_id in dead_bot_ids:
            del self.active_processes[bot_id]
            self.bot_health_status[bot_id] = 'dead'
            # Remover do registro de recém-iniciados
            if bot_id in self.recently_started:
                del self.recently_started[bot_id]
        
        if dead_bot_ids:
            logger.info(f"[CLEANUP] Processos mortos removidos: {dead_bot_ids}")
    
    def print_status_report(self):
        """Imprime relatório de status"""
        logger.info("[REPORT] === STATUS REPORT ===")
        logger.info(f"[REPORT] Robôs configurados: {len(self.bot_configs)}")
        logger.info(f"[REPORT] Processos ativos: {len(self.active_processes)}")
        
        for bot_id, config in self.bot_configs.items():
            bot_name = config['bot_name']
            db_status = config['status']
            health_status = self.bot_health_status.get(bot_id, 'unknown')
            process_id = config.get('process_id')
            last_heartbeat = config.get('last_heartbeat', 'Nunca')
            
            # Mostrar PID real se processo estiver ativo
            real_pid = None
            if bot_id in self.active_processes:
                real_pid = self.active_processes[bot_id].pid
            
            logger.info(f"  [BOT] {bot_name} (ID: {bot_id}):")
            logger.info(f"        DB_Status: {db_status} | Health: {health_status}")
            logger.info(f"        PID_DB: {process_id} | PID_Real: {real_pid}")
            logger.info(f"        Heartbeat: {last_heartbeat}")
        
        logger.info("[REPORT] === FIM REPORT ===")
    
    def run(self):
        """Loop principal do orquestrador"""
        logger.info("[MAIN] Iniciando loop principal do Orchestrator")
        logger.info(f"[CONFIG] Intervalo de sincronização: {self.sync_interval}s")
        logger.info(f"[CONFIG] Timeout de heartbeat: {self.heartbeat_timeout}s")
        
        cycle_count = 0
        
        try:
            while not self.shutdown_requested:
                cycle_count += 1
                logger.info(f"[CYCLE] === CICLO {cycle_count} ===")
                
                # 1. Sincronizar com banco de dados
                if not self.sync_with_database():
                    logger.error("[ERROR] Falha na sincronização. Tentando novamente...")
                    time.sleep(10)
                    continue
                
                # 2. ETAPA 1: Verificar saúde real dos processos
                self.check_process_health()
                
                # 3. ETAPA 2: Gerenciar processos baseado na saúde atual
                self.manage_bot_processes()
                
                # 4. Limpar processos mortos
                self.cleanup_dead_processes()
                
                # 5. Relatório de status (a cada 5 ciclos)
                if cycle_count % 5 == 0:
                    self.print_status_report()
                
                # 6. Aguardar próximo ciclo
                logger.info(f"[WAIT] Aguardando {self.sync_interval}s para próximo ciclo...")
                time.sleep(self.sync_interval)
                
        except KeyboardInterrupt:
            logger.info("[INTERRUPT] Interrupção manual detectada")
        except Exception as e:
            logger.error(f"[ERROR] Erro crítico no loop principal: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown graceful do orquestrador"""
        logger.info("[SHUTDOWN] Iniciando shutdown do Orchestrator...")
        
        # Terminar todos os processos ativos
        for bot_id, process in list(self.active_processes.items()):
            try:
                logger.info(f"[SHUTDOWN] Terminando processo Bot ID {bot_id} (PID: {process.pid})...")
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"[KILL] Forçando kill do processo Bot ID {bot_id}")
                process.kill()
                process.wait()
            except Exception as e:
                logger.error(f"[ERROR] Erro ao terminar processo Bot ID {bot_id}: {e}")
        
        # Atualizar status no banco
        try:
            for bot_id, config in self.bot_configs.items():
                self._update_bot_status(bot_id, 'stopped', None)
        except Exception as e:
            logger.error(f"[ERROR] Erro ao atualizar status final: {e}")
        
        logger.info("[SHUTDOWN] Orchestrator finalizado")

def main():
    """
    Função principal
    """
    print("")
    print("="*70)
    print("[ORCHESTRATOR] GERENTE DA NOVA GERACAO DE ROBOS")
    print("="*70)
    print("[ROBOS] Gerenciados: Accumulator, Speed Bot")
    print("[SYNC] Sincronizacao: A cada 60 segundos")
    print("[HEARTBEAT] Timeout de 3 minutos")
    print("[INIT] Inicializacao: Delay de 5 segundos entre robos")
    print("="*70)
    print("")
    
    try:
        orchestrator = BotOrchestrator()
        orchestrator.run()
    except Exception as e:
        logger.error(f"[FATAL] Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()