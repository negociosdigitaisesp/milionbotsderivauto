#!/usr/bin/env python3
"""
Gerenciador Principal de Bots
Controla e monitora ambos os bots (Tunder Bot e Accumulator Bot) simultaneamente
Com sistema robusto de tratamento de erros e recuperação automática
"""

import os
import sys
import asyncio
import logging
import signal
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# Importar sistema de tratamento de erros
from error_handler import RobustErrorHandler, ErrorSeverity, ErrorType, with_error_handling

class BotStatus(Enum):
    """Status dos bots"""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    RECOVERING = "RECOVERING"
    SHUTDOWN = "SHUTDOWN"

@dataclass
class BotInfo:
    """Informações de um bot"""
    name: str
    module_name: str
    process: Optional[asyncio.subprocess.Process] = None
    status: BotStatus = BotStatus.STOPPED
    last_heartbeat: Optional[datetime] = None
    error_count: int = 0
    restart_count: int = 0
    start_time: Optional[datetime] = None
    pid: Optional[int] = None

class BotManager:
    """Gerenciador principal dos bots com tratamento robusto de erros"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.error_handler = RobustErrorHandler("BotManager")
        
        # Configuração dos bots
        self.bots: Dict[str, BotInfo] = {
            "tunder_bot": BotInfo(
                name="Tunder Bot",
                module_name="tunderbot.py"
            ),
            "accumulator_bot": BotInfo(
                name="Accumulator Bot",
                module_name="accumulator_standalone.py"
            )
        }
        
        # Configurações de monitoramento
        self.monitoring_interval = 30  # segundos
        self.max_restart_attempts = 5
        self.restart_cooldown = 60  # segundos entre restarts
        
        # Estado do gerenciador
        self.running = False
        self.shutdown_requested = False
        
        # Configurar handlers de sinal
        self._setup_signal_handlers()
        
        self.logger.info("🚀 Bot Manager inicializado")
    
    def _setup_logging(self) -> logging.Logger:
        """Configura sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot_manager.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('BotManager')
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            self.logger.info(f"📡 Sinal {signum} recebido - Iniciando shutdown graceful...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    @with_error_handling(ErrorType.SYSTEM, ErrorSeverity.HIGH)
    async def start_bot(self, bot_key: str) -> bool:
        """Inicia um bot específico"""
        bot = self.bots[bot_key]
        
        if bot.status == BotStatus.RUNNING:
            self.logger.warning(f"⚠️ {bot.name} já está rodando")
            return True
        
        try:
            bot.status = BotStatus.STARTING
            self.logger.info(f"🚀 Iniciando {bot.name}...")
            
            # Comando para executar o bot
            cmd = [sys.executable, bot.module_name]
            
            # Criar processo
            bot.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            bot.pid = bot.process.pid
            bot.start_time = datetime.now()
            bot.status = BotStatus.RUNNING
            bot.last_heartbeat = datetime.now()
            
            self.logger.info(f"✅ {bot.name} iniciado com sucesso - PID: {bot.pid}")
            
            # Iniciar monitoramento do processo
            asyncio.create_task(self._monitor_bot_process(bot_key))
            
            return True
            
        except Exception as e:
            bot.status = BotStatus.ERROR
            bot.error_count += 1
            self.logger.error(f"❌ Erro ao iniciar {bot.name}: {e}")
            return False
    
    @with_error_handling(ErrorType.SYSTEM, ErrorSeverity.MEDIUM)
    async def stop_bot(self, bot_key: str, force: bool = False) -> bool:
        """Para um bot específico"""
        bot = self.bots[bot_key]
        
        if bot.status == BotStatus.STOPPED:
            self.logger.warning(f"⚠️ {bot.name} já está parado")
            return True
        
        try:
            self.logger.info(f"🛑 Parando {bot.name}...")
            
            if bot.process:
                if force:
                    bot.process.kill()
                    self.logger.info(f"💀 {bot.name} terminado forçadamente")
                else:
                    bot.process.terminate()
                    try:
                        await asyncio.wait_for(bot.process.wait(), timeout=10)
                        self.logger.info(f"✅ {bot.name} parado graciosamente")
                    except asyncio.TimeoutError:
                        self.logger.warning(f"⏰ Timeout ao parar {bot.name} - Forçando...")
                        bot.process.kill()
                        await bot.process.wait()
            
            bot.status = BotStatus.STOPPED
            bot.process = None
            bot.pid = None
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao parar {bot.name}: {e}")
            return False
    
    @with_error_handling(ErrorType.SYSTEM, ErrorSeverity.HIGH)
    async def restart_bot(self, bot_key: str) -> bool:
        """Reinicia um bot específico"""
        bot = self.bots[bot_key]
        
        # Verificar limite de restarts
        if bot.restart_count >= self.max_restart_attempts:
            self.logger.critical(
                f"💀 {bot.name} excedeu limite de restarts ({self.max_restart_attempts})"
            )
            return False
        
        # Verificar se já está em processo de restart
        if bot.status == BotStatus.STARTING:
            self.logger.warning(f"⚠️ {bot.name} já está sendo reiniciado")
            return False
        
        self.logger.info(f"🔄 Reiniciando {bot.name} (tentativa {bot.restart_count + 1})...")
        
        # Parar bot
        stop_success = await self.stop_bot(bot_key, force=True)
        if not stop_success:
            self.logger.error(f"❌ Falha ao parar {bot.name} para restart")
            return False
        
        # Aguardar cooldown
        await asyncio.sleep(self.restart_cooldown)
        
        # Iniciar bot
        success = await self.start_bot(bot_key)
        
        if success:
            bot.restart_count += 1
            self.logger.info(f"✅ {bot.name} reiniciado com sucesso")
        else:
            self.logger.error(f"❌ Falha ao reiniciar {bot.name}")
        
        return success
    
    async def _monitor_bot_process(self, bot_key: str):
        """Monitora processo de um bot específico"""
        bot = self.bots[bot_key]
        restart_in_progress = False
        
        while bot.status == BotStatus.RUNNING and not self.shutdown_requested:
            try:
                if bot.process:
                    # Verificar se processo ainda está rodando
                    return_code = bot.process.returncode
                    
                    if return_code is not None and not restart_in_progress:
                        # Processo terminou
                        self.logger.error(
                            f"💀 {bot.name} terminou inesperadamente - Código: {return_code}"
                        )
                        
                        bot.status = BotStatus.ERROR
                        bot.error_count += 1
                        restart_in_progress = True
                        
                        # Tentar restart automático apenas se não excedeu limite
                        if bot.restart_count < self.max_restart_attempts:
                            self.logger.info(f"🔄 Tentando restart automático de {bot.name}...")
                            
                            # Aguardar um pouco antes do restart
                            await asyncio.sleep(2)
                            
                            success = await self.restart_bot(bot_key)
                            if success:
                                restart_in_progress = False
                                # Reiniciar monitoramento após restart bem-sucedido
                                continue
                            else:
                                self.logger.error(f"❌ Falha no restart de {bot.name}")
                                break
                        else:
                            self.logger.critical(
                                f"💀 {bot.name} não será reiniciado - Limite excedido ({self.max_restart_attempts})"
                            )
                            break
                    
                    # Atualizar heartbeat apenas se processo está rodando
                    if return_code is None:
                        bot.last_heartbeat = datetime.now()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Erro no monitoramento de {bot.name}: {e}")
                await asyncio.sleep(5)
                restart_in_progress = False
    
    async def _health_check_loop(self):
        """Loop de verificação de saúde dos bots"""
        while self.running and not self.shutdown_requested:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                await self.error_handler.handle_error(e, "health_check")
                await asyncio.sleep(10)
    
    async def _perform_health_check(self):
        """Executa verificação de saúde dos bots"""
        current_time = datetime.now()
        
        for bot_key, bot in self.bots.items():
            if bot.status == BotStatus.RUNNING:
                # Verificar se bot rodou tempo suficiente para resetar contador de restart
                if bot.start_time:
                    uptime = (current_time - bot.start_time).total_seconds()
                    # Reset contador se bot rodou por mais de 5 minutos sem problemas
                    if uptime > 300 and bot.restart_count > 0:
                        self.logger.info(f"🔄 Resetando contador de restart de {bot.name} - Uptime: {uptime:.0f}s")
                        bot.restart_count = 0
                
                # Verificar se bot está responsivo
                if bot.last_heartbeat:
                    time_since_heartbeat = (current_time - bot.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > (self.monitoring_interval * 3):
                        self.logger.warning(
                            f"⚠️ {bot.name} não responde há {time_since_heartbeat:.1f}s"
                        )
                        
                        # Verificar se processo ainda existe
                        if bot.process and bot.process.returncode is None:
                            self.logger.info(f"🔄 {bot.name} ainda rodando - Aguardando...")
                        else:
                            self.logger.error(f"💀 {bot.name} processo morto - Reiniciando...")
                            await self.restart_bot(bot_key)
    
    async def start_all_bots(self):
        """Inicia todos os bots"""
        self.logger.info("🚀 Iniciando todos os bots...")
        
        tasks = []
        for bot_key in self.bots.keys():
            task = asyncio.create_task(self.start_bot(bot_key))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for result in results if result is True)
        self.logger.info(f"✅ {success_count}/{len(self.bots)} bots iniciados com sucesso")
        
        return success_count == len(self.bots)
    
    async def stop_all_bots(self, force: bool = False):
        """Para todos os bots"""
        self.logger.info("🛑 Parando todos os bots...")
        
        tasks = []
        for bot_key in self.bots.keys():
            task = asyncio.create_task(self.stop_bot(bot_key, force))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info("✅ Todos os bots parados")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Gera relatório de status dos bots"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "manager_status": "RUNNING" if self.running else "STOPPED",
            "bots": {},
            "error_stats": self.error_handler.get_error_stats()
        }
        
        for bot_key, bot in self.bots.items():
            uptime = None
            if bot.start_time:
                uptime = (datetime.now() - bot.start_time).total_seconds()
            
            report["bots"][bot_key] = {
                "name": bot.name,
                "status": bot.status.value,
                "pid": bot.pid,
                "uptime_seconds": uptime,
                "error_count": bot.error_count,
                "restart_count": bot.restart_count,
                "last_heartbeat": bot.last_heartbeat.isoformat() if bot.last_heartbeat else None
            }
        
        return report
    
    async def run(self):
        """Executa o gerenciador principal"""
        try:
            self.running = True
            self.logger.info("🎯 Bot Manager iniciado")
            
            # Iniciar todos os bots
            await self.start_all_bots()
            
            # Iniciar loop de monitoramento
            health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Loop principal
            while self.running and not self.shutdown_requested:
                # Exibir status a cada minuto
                report = self.get_status_report()
                self.logger.info(f"📊 STATUS: {json.dumps(report, indent=2)}")
                
                await asyncio.sleep(60)
            
            # Cancelar task de monitoramento
            health_check_task.cancel()
            
        except Exception as e:
            self.logger.critical(f"💀 Erro crítico no Bot Manager: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown graceful do gerenciador"""
        self.logger.info("🛑 Iniciando shutdown do Bot Manager...")
        
        self.running = False
        
        # Parar todos os bots
        await self.stop_all_bots(force=True)
        
        self.logger.info("✅ Bot Manager finalizado")

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================
async def main():
    """Função principal do gerenciador"""
    print("\n" + "="*60)
    print("🤖 BOT MANAGER - Sistema de Gerenciamento de Bots")
    print("="*60)
    print("📋 Bots Gerenciados:")
    print("   • Tunder Bot (tunderbot.py)")
    print("   • Accumulator Bot (accumulator_standalone.py)")
    print("🔧 Recursos:")
    print("   • Monitoramento em tempo real")
    print("   • Restart automático em caso de falha")
    print("   • Tratamento robusto de erros")
    print("   • Circuit breakers para prevenção de falhas")
    print("   • Logs detalhados e relatórios de status")
    print("="*60)
    
    # Criar e executar gerenciador
    manager = BotManager()
    await manager.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutdown solicitado pelo usuário")
    except Exception as e:
        print(f"💀 Erro crítico: {e}")
        sys.exit(1)