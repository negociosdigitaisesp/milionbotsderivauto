#!/usr/bin/env python3
"""
Sistema de Gerenciamento de Bots - Versão Aprimorada
Versão com melhor captura de erros e logging detalhado
"""

import os
import sys
import asyncio
import subprocess
import signal
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Any
from pathlib import Path

# Configuração de logging aprimorada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_manager_enhanced.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('BotManagerEnhanced')

class BotStatus(Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    RESTARTING = "RESTARTING"

@dataclass
class BotInfo:
    name: str
    script_path: str
    status: BotStatus = BotStatus.STOPPED
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    error_count: int = 0
    restart_count: int = 0
    last_error: Optional[str] = None
    exit_code: Optional[int] = None
    stdout_log: List[str] = None
    stderr_log: List[str] = None
    
    def __post_init__(self):
        if self.stdout_log is None:
            self.stdout_log = []
        if self.stderr_log is None:
            self.stderr_log = []

class EnhancedBotManager:
    def __init__(self):
        self.bots: Dict[str, BotInfo] = {}
        self.running = False
        self.max_restart_attempts = 3
        self.restart_cooldown = 5  # segundos
        self.health_check_interval = 10  # segundos
        self.log_buffer_size = 100  # linhas de log por bot
        
        # Configurar bots
        self._setup_bots()
        
        # Configurar handlers de sinal
        self._setup_signal_handlers()
    
    def _setup_bots(self):
        """Configura os bots disponíveis"""
        bot_configs = [
            {
                'key': 'tunder_bot',
                'name': 'Tunder Bot Enhanced',
                'script': 'tunderbot.py'
            },
            {
                'key': 'accumulator_bot',
                'name': 'Accumulator Bot Enhanced',
                'script': 'accumulator_standalone.py'
            }
        ]
        
        for config in bot_configs:
            script_path = Path(config['script'])
            if script_path.exists():
                self.bots[config['key']] = BotInfo(
                    name=config['name'],
                    script_path=str(script_path.absolute())
                )
                logger.info(f"✅ Bot configurado: {config['name']} -> {script_path}")
            else:
                logger.error(f"❌ Script não encontrado: {script_path}")
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Sinal recebido: {signum}")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_bot(self, bot_key: str) -> bool:
        """Inicia um bot específico com logging detalhado"""
        if bot_key not in self.bots:
            logger.error(f"❌ Bot não encontrado: {bot_key}")
            return False
        
        bot = self.bots[bot_key]
        
        if bot.status in [BotStatus.RUNNING, BotStatus.STARTING]:
            logger.warning(f"⚠️ {bot.name} já está rodando ou iniciando")
            return True
        
        try:
            logger.info(f"🚀 Iniciando {bot.name}...")
            bot.status = BotStatus.STARTING
            bot.start_time = datetime.now()
            bot.last_heartbeat = datetime.now()
            
            # Criar processo com captura detalhada de logs
            process = subprocess.Popen(
                [sys.executable, bot.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=os.getcwd()
            )
            
            bot.process = process
            bot.pid = process.pid
            bot.status = BotStatus.RUNNING
            
            logger.info(f"✅ {bot.name} iniciado - PID: {bot.pid}")
            
            # Iniciar monitoramento do processo
            asyncio.create_task(self._monitor_bot_process(bot_key))
            asyncio.create_task(self._capture_bot_logs(bot_key))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar {bot.name}: {e}")
            bot.status = BotStatus.ERROR
            bot.last_error = str(e)
            bot.error_count += 1
            return False
    
    async def _capture_bot_logs(self, bot_key: str):
        """Captura logs detalhados do bot"""
        bot = self.bots[bot_key]
        
        if not bot.process:
            return
        
        try:
            # Capturar stdout
            async def read_stdout():
                while bot.process and bot.process.poll() is None:
                    try:
                        line = bot.process.stdout.readline()
                        if line:
                            bot.stdout_log.append(f"[{datetime.now()}] {line.strip()}")
                            if len(bot.stdout_log) > self.log_buffer_size:
                                bot.stdout_log.pop(0)
                            logger.debug(f"[{bot.name} STDOUT] {line.strip()}")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"❌ Erro lendo stdout de {bot.name}: {e}")
                        break
            
            # Capturar stderr
            async def read_stderr():
                while bot.process and bot.process.poll() is None:
                    try:
                        line = bot.process.stderr.readline()
                        if line:
                            stripped_line = line.strip()
                            bot.stderr_log.append(f"[{datetime.now()}] {stripped_line}")
                            if len(bot.stderr_log) > self.log_buffer_size:
                                bot.stderr_log.pop(0)
                            logger.error(f"[{bot.name} STDERR] {stripped_line}")
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"❌ Erro lendo stderr de {bot.name}: {e}")
                        break
            
            # Executar ambos em paralelo
            await asyncio.gather(
                read_stdout(),
                read_stderr(),
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na captura de logs de {bot.name}: {e}")
    
    async def _monitor_bot_process(self, bot_key: str):
        """Monitora o processo do bot"""
        bot = self.bots[bot_key]
        
        while bot.status == BotStatus.RUNNING and bot.process:
            try:
                # Verificar se o processo ainda está rodando
                exit_code = bot.process.poll()
                
                if exit_code is not None:
                    # Processo terminou
                    bot.exit_code = exit_code
                    bot.status = BotStatus.ERROR
                    
                    logger.error(f"💀 {bot.name} terminou - Exit Code: {exit_code}")
                    
                    # Capturar logs finais
                    if bot.stderr_log:
                        logger.error(f"📋 Últimos erros de {bot.name}:")
                        for log_line in bot.stderr_log[-5:]:
                            logger.error(f"  {log_line}")
                    
                    if bot.stdout_log:
                        logger.info(f"📋 Últimas saídas de {bot.name}:")
                        for log_line in bot.stdout_log[-5:]:
                            logger.info(f"  {log_line}")
                    
                    # Tentar restart se não excedeu o limite
                    if bot.restart_count < self.max_restart_attempts:
                        logger.info(f"🔄 Tentando restart de {bot.name} (tentativa {bot.restart_count + 1})...")
                        await asyncio.sleep(self.restart_cooldown)
                        await self.restart_bot(bot_key)
                    else:
                        logger.error(f"❌ {bot.name} excedeu limite de restarts ({self.max_restart_attempts})")
                    
                    break
                
                # Atualizar heartbeat
                bot.last_heartbeat = datetime.now()
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento de {bot.name}: {e}")
                await asyncio.sleep(5)
    
    async def stop_bot(self, bot_key: str) -> bool:
        """Para um bot específico"""
        if bot_key not in self.bots:
            logger.error(f"❌ Bot não encontrado: {bot_key}")
            return False
        
        bot = self.bots[bot_key]
        
        if bot.status == BotStatus.STOPPED:
            logger.info(f"ℹ️ {bot.name} já está parado")
            return True
        
        try:
            logger.info(f"🛑 Parando {bot.name}...")
            
            if bot.process and bot.process.poll() is None:
                # Tentar parada graceful
                bot.process.terminate()
                
                # Aguardar um pouco
                await asyncio.sleep(3)
                
                # Se ainda estiver rodando, forçar
                if bot.process.poll() is None:
                    logger.warning(f"⚠️ Forçando parada de {bot.name}")
                    bot.process.kill()
                    await asyncio.sleep(1)
            
            bot.status = BotStatus.STOPPED
            bot.process = None
            bot.pid = None
            
            logger.info(f"✅ {bot.name} parado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar {bot.name}: {e}")
            return False
    
    async def restart_bot(self, bot_key: str) -> bool:
        """Reinicia um bot específico"""
        if bot_key not in self.bots:
            logger.error(f"❌ Bot não encontrado: {bot_key}")
            return False
        
        bot = self.bots[bot_key]
        bot.restart_count += 1
        
        # Parar o bot
        await self.stop_bot(bot_key)
        
        # Aguardar cooldown
        await asyncio.sleep(self.restart_cooldown)
        
        # Iniciar novamente
        return await self.start_bot(bot_key)
    
    async def start_all_bots(self):
        """Inicia todos os bots"""
        logger.info(f"🚀 Iniciando todos os bots ({len(self.bots)})...")
        
        results = []
        for bot_key in self.bots.keys():
            result = await self.start_bot(bot_key)
            results.append(result)
        
        success_count = sum(results)
        logger.info(f"✅ {success_count}/{len(self.bots)} bots iniciados com sucesso")
        
        return success_count == len(self.bots)
    
    async def stop_all_bots(self):
        """Para todos os bots"""
        logger.info("🛑 Parando todos os bots...")
        
        tasks = []
        for bot_key in self.bots.keys():
            tasks.append(self.stop_bot(bot_key))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ Todos os bots parados")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status detalhado de todos os bots"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "manager_status": "RUNNING" if self.running else "STOPPED",
            "bots": {}
        }
        
        for bot_key, bot in self.bots.items():
            uptime = 0
            if bot.start_time:
                uptime = (datetime.now() - bot.start_time).total_seconds()
            
            status["bots"][bot_key] = {
                "name": bot.name,
                "status": bot.status.value,
                "pid": bot.pid,
                "uptime_seconds": uptime,
                "error_count": bot.error_count,
                "restart_count": bot.restart_count,
                "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None,
                "last_error": bot.last_error,
                "exit_code": bot.exit_code,
                "recent_stdout": bot.stdout_log[-3:] if bot.stdout_log else [],
                "recent_stderr": bot.stderr_log[-3:] if bot.stderr_log else []
            }
        
        return status
    
    async def health_check_loop(self):
        """Loop de verificação de saúde"""
        while self.running:
            try:
                status = self.get_status()
                logger.info(f"📊 STATUS: {json.dumps(status, indent=2, ensure_ascii=False)}")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"❌ Erro no health check: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Executa o gerenciador de bots"""
        try:
            logger.info("🚀 Bot Manager Enhanced inicializado")
            self.running = True
            
            # Iniciar todos os bots
            await self.start_all_bots()
            
            # Iniciar loop de health check
            await self.health_check_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Interrupção solicitada")
        except Exception as e:
            logger.error(f"❌ Erro crítico: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Encerra o gerenciador graciosamente"""
        logger.info("🔄 Iniciando shutdown...")
        self.running = False
        
        await self.stop_all_bots()
        
        logger.info("✅ Shutdown concluído")

async def main():
    """Função principal"""
    try:
        # Banner
        print("="*60)
        print("🤖 BOT MANAGER ENHANCED")
        print("="*60)
        print("🎯 Recursos Aprimorados:")
        print("   • Captura detalhada de logs")
        print("   • Monitoramento de exit codes")
        print("   • Análise de erros em tempo real")
        print("   • Sistema de restart inteligente")
        print("   • Logging persistente")
        print("="*60)
        
        manager = EnhancedBotManager()
        await manager.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Programa interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ ERRO FATAL: {e}")
        logger.error(f"📋 Tipo: {type(e).__name__}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO: {e}")
        sys.exit(1)