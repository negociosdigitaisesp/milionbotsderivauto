#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 SCRIPT DE MIGRAÇÃO PARA SISTEMA OTIMIZADO

Este script aplica as otimizações ao sistema existente mantendo:
- Todas as funções de bot existentes
- Configurações atuais
- Compatibilidade total
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Imports externos
from deriv_api import DerivAPI
from supabase import create_client, Client
from dotenv import load_dotenv
import random

# Importar bots existentes
try:
    from bot_trading_system_fixed import bot_gold
except ImportError:
    print("⚠️ bot_gold não encontrado, usando versão local")
    bot_gold = None

try:
    from trading_system.bots.scale_bot import bot_scale
except ImportError:
    print("⚠️ bot_scale não encontrado")
    bot_scale = None

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("❌ Variáveis de ambiente não encontradas")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@dataclass
class BotMetrics:
    """Métricas de performance por bot"""
    name: str
    operations_count: int = 0
    total_profit: float = 0.0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    last_operation: Optional[datetime] = None
    status: str = "idle"  # idle, running, waiting, error
    wins: int = 0
    losses: int = 0
    current_stake: float = 0.0

class OptimizedRateLimiter:
    """Rate limiter otimizado com distribuição inteligente"""
    
    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.call_tracker = defaultdict(list)
        self.lock = asyncio.Lock()
        
        # Configuração distribuída por tipo de operação
        self.config = {
            'buy': {'max_calls': 3, 'window_seconds': 60},
            'ticks_history': {'max_calls': 8, 'window_seconds': 60},
            'proposal_open_contract': {'max_calls': 15, 'window_seconds': 60},
            'proposal': {'max_calls': 5, 'window_seconds': 60}
        }
    
    async def wait_for_limit(self, endpoint: str) -> None:
        """Controle inteligente de rate limiting"""
        async with self.lock:
            now = datetime.now()
            config = self.config.get(endpoint, {'max_calls': 5, 'window_seconds': 60})
            
            # Limpar chamadas antigas
            cutoff_time = now - timedelta(seconds=config['window_seconds'])
            self.call_tracker[endpoint] = [
                call_time for call_time in self.call_tracker[endpoint] 
                if call_time > cutoff_time
            ]
            
            # Verificar limite com margem de segurança
            current_calls = len(self.call_tracker[endpoint])
            if current_calls >= config['max_calls']:
                oldest_call = min(self.call_tracker[endpoint])
                wait_time = config['window_seconds'] - (now - oldest_call).total_seconds()
                
                if wait_time > 0:
                    # Adicionar jitter para evitar thundering herd
                    jitter = random.uniform(0.1, 0.5)
                    total_wait = wait_time + jitter
                    print(f"⏳ {self.bot_name}: Rate limit {endpoint}. Aguardando {total_wait:.1f}s...")
                    await asyncio.sleep(total_wait)
            
            # Registrar nova chamada
            self.call_tracker[endpoint].append(now)

class ConnectionManager:
    """Gerenciador de conexões com failover automático"""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.connections: List[DerivAPI] = []
        self.connection_health: List[bool] = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.last_health_check = datetime.now()
    
    async def initialize(self):
        """Inicializar pool com verificação de saúde"""
        print(f"🔗 Inicializando pool de {self.pool_size} conexões...")
        
        for i in range(self.pool_size):
            try:
                api = DerivAPI(app_id=DERIV_APP_ID)
                await api.authorize(DERIV_API_TOKEN)
                self.connections.append(api)
                self.connection_health.append(True)
                print(f"✅ Conexão {i+1}/{self.pool_size} estabelecida")
                
                # Delay entre conexões para evitar rate limit
                if i < self.pool_size - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                print(f"⚠️ Erro na conexão {i+1}: {e}")
                self.connection_health.append(False)
    
    async def get_healthy_connection(self) -> DerivAPI:
        """Obter conexão saudável com failover"""
        async with self.lock:
            # Verificar saúde das conexões periodicamente
            if (datetime.now() - self.last_health_check).seconds > 300:  # 5 minutos
                await self._health_check()
            
            # Encontrar conexão saudável
            healthy_connections = [
                (i, conn) for i, (conn, healthy) in 
                enumerate(zip(self.connections, self.connection_health)) 
                if healthy
            ]
            
            if not healthy_connections:
                raise Exception("Nenhuma conexão saudável disponível")
            
            # Rotacionar entre conexões saudáveis
            index, connection = healthy_connections[self.current_index % len(healthy_connections)]
            self.current_index += 1
            
            return connection
    
    async def _health_check(self):
        """Verificar saúde das conexões"""
        self.last_health_check = datetime.now()
        
        for i, connection in enumerate(self.connections):
            try:
                # Teste simples de conectividade
                await connection.ping()
                self.connection_health[i] = True
            except:
                self.connection_health[i] = False
                print(f"⚠️ Conexão {i+1} não responsiva")

class OptimizedBotManager:
    """Gerenciador otimizado com todas as melhorias"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager(pool_size=4)
        self.bot_metrics: Dict[str, BotMetrics] = {}
        self.rate_limiters: Dict[str, OptimizedRateLimiter] = {}
        
        # Controle de concorrência inteligente
        self.global_semaphore = asyncio.Semaphore(10)  # Max 10 operações globais
        self.buy_semaphore = asyncio.Semaphore(3)      # Max 3 compras simultâneas
        self.check_semaphore = asyncio.Semaphore(8)    # Max 8 verificações simultâneas
        
        # Estatísticas globais
        self.start_time = datetime.now()
        self.total_api_calls = 0
        self.total_errors = 0
    
    async def initialize(self):
        """Inicializar sistema otimizado"""
        print("🚀 Inicializando sistema otimizado com failover...")
        await self.connection_manager.initialize()
        print("✅ Sistema otimizado pronto!")
    
    def register_bot(self, bot_name: str):
        """Registrar bot com métricas"""
        if bot_name not in self.bot_metrics:
            self.bot_metrics[bot_name] = BotMetrics(name=bot_name)
            self.rate_limiters[bot_name] = OptimizedRateLimiter(bot_name)
            print(f"📝 Bot {bot_name} registrado")
    
    async def safe_api_call(self, bot_name: str, method_name: str, params: dict, max_retries: int = 3):
        """Chamada API otimizada com retry inteligente"""
        self.register_bot(bot_name)
        rate_limiter = self.rate_limiters[bot_name]
        
        # Selecionar semáforo apropriado
        if method_name == 'buy':
            semaphore = self.buy_semaphore
        elif method_name == 'proposal_open_contract':
            semaphore = self.check_semaphore
        else:
            semaphore = self.global_semaphore
        
        for attempt in range(max_retries):
            try:
                # Rate limiting específico do bot
                await rate_limiter.wait_for_limit(method_name)
                
                # Controle de concorrência
                async with semaphore:
                    # Obter conexão saudável
                    api = await self.connection_manager.get_healthy_connection()
                    
                    # Executar chamada
                    start_time = time.time()
                    method = getattr(api, method_name)
                    result = await method(params)
                    response_time = time.time() - start_time
                    
                    # Atualizar estatísticas
                    self.total_api_calls += 1
                    self.bot_metrics[bot_name].last_operation = datetime.now()
                    self.bot_metrics[bot_name].avg_response_time = (
                        (self.bot_metrics[bot_name].avg_response_time + response_time) / 2
                    )
                    
                    return result
                    
            except Exception as e:
                self.total_errors += 1
                error_msg = str(e)
                
                if attempt < max_retries - 1:
                    # Retry com backoff exponencial + jitter
                    wait_time = (2 ** attempt) + random.uniform(0.1, 1.0)
                    print(f"⚠️ {bot_name}: Retry {attempt + 1}/{max_retries} em {wait_time:.1f}s - {error_msg[:50]}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ {bot_name}: Falha após {max_retries} tentativas - {error_msg}")
                    raise e
    
    async def execute_bot_with_monitoring(self, bot_func, bot_name: str, delay: float = 0):
        """Executar bot com monitoramento completo"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        self.register_bot(bot_name)
        
        try:
            self.bot_metrics[bot_name].status = "running"
            print(f"🤖 {bot_name}: Iniciado")
            
            # Executar bot com contexto otimizado
            await bot_func(self, bot_name)
            
        except Exception as e:
            print(f"❌ {bot_name}: Erro crítico - {e}")
            self.bot_metrics[bot_name].status = "error"
        finally:
            self.bot_metrics[bot_name].status = "idle"
    
    def get_comprehensive_report(self) -> dict:
        """Relatório completo de performance"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        active_bots = sum(1 for m in self.bot_metrics.values() if m.status == 'running')
        total_operations = sum(m.operations_count for m in self.bot_metrics.values())
        total_profit = sum(m.total_profit for m in self.bot_metrics.values())
        total_wins = sum(m.wins for m in self.bot_metrics.values())
        total_losses = sum(m.losses for m in self.bot_metrics.values())
        
        success_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime,
            'system_stats': {
                'total_bots': len(self.bot_metrics),
                'active_bots': active_bots,
                'total_operations': total_operations,
                'total_profit': round(total_profit, 2),
                'success_rate': round(success_rate, 2),
                'api_calls': self.total_api_calls,
                'errors': self.total_errors,
                'error_rate': round((self.total_errors / max(self.total_api_calls, 1)) * 100, 2)
            },
            'bots': {}
        }
        
        for bot_name, metrics in self.bot_metrics.items():
            bot_success_rate = (metrics.wins / (metrics.wins + metrics.losses) * 100) if (metrics.wins + metrics.losses) > 0 else 0
            
            report['bots'][bot_name] = {
                'status': metrics.status,
                'operations': metrics.operations_count,
                'profit': round(metrics.total_profit, 2),
                'wins': metrics.wins,
                'losses': metrics.losses,
                'success_rate': round(bot_success_rate, 2),
                'current_stake': round(metrics.current_stake, 2),
                'avg_response_time': round(metrics.avg_response_time, 3),
                'last_operation': metrics.last_operation.isoformat() if metrics.last_operation else None
            }
        
        return report

# Função otimizada para salvar operações
async def salvar_operacao_optimized(nome_bot: str, lucro: float, manager: OptimizedBotManager):
    """Salvar operação de forma otimizada e assíncrona"""
    try:
        data = {
            'nome_bot': nome_bot,
            'lucro': lucro,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Usar ThreadPoolExecutor para não bloquear
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: supabase.table('operacoes').insert(data).execute()
            )
        
        # Atualizar métricas
        if lucro > 0:
            manager.bot_metrics[nome_bot].wins += 1
        else:
            manager.bot_metrics[nome_bot].losses += 1
        
        manager.bot_metrics[nome_bot].total_profit += lucro
        manager.bot_metrics[nome_bot].operations_count += 1
        
        print(f"✅ {nome_bot}: Operação salva - Lucro: ${lucro:.2f}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar {nome_bot}: {e}")

# Bot Gold otimizado mantendo compatibilidade
async def bot_gold_optimized_compatible(manager: OptimizedBotManager, bot_name: str):
    """GoldBot otimizado mantendo lógica original"""
    # Configurações originais
    stake_inicial = 2.0
    martingale_fator = 2.0
    stake_atual = stake_inicial
    
    print(f"🥇 {bot_name}: Iniciado (Stake: ${stake_inicial}, Martingale: {martingale_fator}x)")
    
    while True:
        try:
            manager.bot_metrics[bot_name].status = "running"
            manager.bot_metrics[bot_name].current_stake = stake_atual
            
            # Obter último dígito com retry otimizado
            ticks_response = await manager.safe_api_call(
                bot_name, 'ticks_history', {
                    "ticks_history": "R_100",
                    "count": 1,
                    "end": "latest"
                }
            )
            
            if 'error' in ticks_response:
                print(f"❌ {bot_name}: Erro nos ticks: {ticks_response['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            ultimo_tick = ticks_response['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"🔍 {bot_name}: Dígito: {ultimo_digito} | Profit: ${manager.bot_metrics[bot_name].total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Fazer proposta DIGITDIFF
            proposal_params = {
                "proposal": 1,
                "amount": stake_atual,
                "basis": "stake",
                "contract_type": "DIGITDIFF",
                "currency": "USD",
                "symbol": "R_100",
                "duration": 1,
                "duration_unit": "t",
                "barrier": str(ultimo_digito)
            }
            
            proposal_response = await manager.safe_api_call(bot_name, 'proposal', proposal_params)
            
            if 'error' in proposal_response:
                print(f"❌ {bot_name}: Erro na proposta: {proposal_response['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            # Comprar contrato
            buy_response = await manager.safe_api_call(
                bot_name, 'buy', {
                    "buy": proposal_response['proposal']['id'],
                    "price": stake_atual
                }
            )
            
            if 'error' in buy_response:
                print(f"❌ {bot_name}: Erro na compra: {buy_response['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"📈 {bot_name}: DIGITDIFF {ultimo_digito} comprado | ID: {contract_id}")
            
            # Aguardar resultado de forma otimizada
            manager.bot_metrics[bot_name].status = "waiting"
            
            contract_finalizado = False
            tentativas = 0
            max_tentativas = 25
            
            while not contract_finalizado and tentativas < max_tentativas:
                await asyncio.sleep(0.4)  # Intervalo otimizado
                tentativas += 1
                
                try:
                    contract_status = await manager.safe_api_call(
                        bot_name, 'proposal_open_contract', {
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        }
                    )
                    
                    if 'error' in contract_status:
                        continue
                    
                    contract_info = contract_status['proposal_open_contract']
                    
                    if contract_info.get('is_sold', False):
                        contract_finalizado = True
                        lucro = float(contract_info.get('profit', 0))
                        
                        # Salvar operação de forma assíncrona
                        asyncio.create_task(salvar_operacao_optimized(bot_name, lucro, manager))
                        
                        if lucro > 0:
                            print(f"✅ {bot_name}: VITÓRIA! +${lucro:.2f} | Total: ${manager.bot_metrics[bot_name].total_profit + lucro:.2f}")
                            stake_atual = stake_inicial  # Reset stake
                        else:
                            print(f"❌ {bot_name}: DERROTA! ${lucro:.2f} | Total: ${manager.bot_metrics[bot_name].total_profit + lucro:.2f}")
                            stake_atual = abs(lucro) * martingale_fator  # Martingale
                            print(f"🔄 {bot_name}: Próximo stake: ${stake_atual:.2f}")
                        
                        break
                        
                except Exception as e:
                    if tentativas % 5 == 0:  # Log a cada 5 tentativas
                        print(f"⏳ {bot_name}: Verificando resultado... ({tentativas}/{max_tentativas})")
            
            if not contract_finalizado:
                print(f"⚠️ {bot_name}: Timeout na verificação do contrato")
            
            # Pausa otimizada entre operações
            await asyncio.sleep(0.3)
            
        except Exception as e:
            print(f"❌ {bot_name}: Erro: {e}")
            manager.bot_metrics[bot_name].status = "error"
            await asyncio.sleep(3)

# Wrapper para bots existentes
async def wrap_existing_bot(manager: OptimizedBotManager, bot_name: str, original_bot_func):
    """Wrapper para integrar bots existentes ao sistema otimizado"""
    if original_bot_func is None:
        print(f"⚠️ {bot_name}: Função não disponível")
        return
    
    try:
        # Criar uma API mock que usa o manager otimizado
        class OptimizedAPIWrapper:
            def __init__(self, manager, bot_name):
                self.manager = manager
                self.bot_name = bot_name
            
            async def __getattr__(self, method_name):
                async def api_call(params):
                    return await self.manager.safe_api_call(self.bot_name, method_name, params)
                return api_call
        
        api_wrapper = OptimizedAPIWrapper(manager, bot_name)
        await original_bot_func(api_wrapper)
        
    except Exception as e:
        print(f"❌ {bot_name}: Erro no wrapper - {e}")

async def main_migrated():
    """Função principal com sistema migrado"""
    print("🔄 SISTEMA MIGRADO - EXECUÇÃO PARALELA OTIMIZADA")
    print("=================================================")
    
    # Inicializar gerenciador otimizado
    manager = OptimizedBotManager()
    await manager.initialize()
    
    # Configurar bots com delays escalonados
    bot_configs = [
        ('GoldBot_Optimized_1', bot_gold_optimized_compatible, 0.0),
        ('GoldBot_Optimized_2', bot_gold_optimized_compatible, 0.5),
        ('GoldBot_Optimized_3', bot_gold_optimized_compatible, 1.0),
        ('GoldBot_Optimized_4', bot_gold_optimized_compatible, 1.5),
    ]
    
    # Adicionar bots existentes se disponíveis
    if bot_gold:
        bot_configs.append(('GoldBot_Original', lambda m, n: wrap_existing_bot(m, n, bot_gold), 2.0))
    
    if bot_scale:
        bot_configs.append(('ScaleBot_Original', lambda m, n: wrap_existing_bot(m, n, bot_scale), 2.5))
    
    # Criar tarefas otimizadas
    tasks = []
    for bot_name, bot_func, delay in bot_configs:
        task = asyncio.create_task(
            manager.execute_bot_with_monitoring(bot_func, bot_name, delay)
        )
        tasks.append(task)
    
    print(f"📈 {len(tasks)} bots configurados para execução paralela otimizada")
    
    # Task para relatórios em tempo real
    async def enhanced_report_task():
        while True:
            await asyncio.sleep(45)  # Relatório a cada 45 segundos
            report = manager.get_comprehensive_report()
            
            print(f"\n📊 RELATÓRIO DETALHADO - {datetime.now().strftime('%H:%M:%S')}")
            print(f"🤖 Bots: {report['system_stats']['active_bots']}/{report['system_stats']['total_bots']} ativos")
            print(f"💰 Profit Total: ${report['system_stats']['total_profit']}")
            print(f"📈 Operações: {report['system_stats']['total_operations']}")
            print(f"🎯 Taxa de Sucesso: {report['system_stats']['success_rate']}%")
            print(f"📡 API Calls: {report['system_stats']['api_calls']} (Erros: {report['system_stats']['error_rate']}%)")
            
            # Top 3 bots por profit
            top_bots = sorted(
                report['bots'].items(), 
                key=lambda x: x[1]['profit'], 
                reverse=True
            )[:3]
            
            print("🏆 Top Performers:")
            for i, (name, stats) in enumerate(top_bots, 1):
                print(f"  {i}. {name}: ${stats['profit']} ({stats['success_rate']}% win)")
    
    tasks.append(asyncio.create_task(enhanced_report_task()))
    
    try:
        # Executar todas as tarefas
        print("🚀 Iniciando execução paralela otimizada...")
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupção manual detectada...")
        final_report = manager.get_comprehensive_report()
        print(f"📊 Relatório Final: ${final_report['system_stats']['total_profit']} em {final_report['system_stats']['total_operations']} operações")
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main_migrated())
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")