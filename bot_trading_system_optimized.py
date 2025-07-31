#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE TRADING OTIMIZADO - EXECUÇÃO PARALELA EFICAZ

Melhorias implementadas:
1. Rate limiting distribuído por bot
2. Pool de conexões API
3. Execução assíncrona verdadeira
4. Sistema de filas inteligente
5. Monitoramento em tempo real
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

class BotRateLimiter:
    """Rate limiter individual por bot"""
    
    def __init__(self, bot_name: str):
        self.bot_name = bot_name
        self.call_tracker = defaultdict(list)
        self.lock = asyncio.Lock()
        
        # Configuração específica por bot (distribuída)
        self.config = {
            'buy': {'max_calls': 2, 'window_seconds': 60},  # 2 compras por bot por minuto
            'ticks_history': {'max_calls': 5, 'window_seconds': 60},  # 5 históricos por bot
            'proposal_open_contract': {'max_calls': 10, 'window_seconds': 60}  # 10 verificações por bot
        }
    
    async def wait_for_limit(self, endpoint: str) -> None:
        """Controle de rate limiting específico do bot"""
        async with self.lock:
            now = datetime.now()
            config = self.config.get(endpoint, {'max_calls': 5, 'window_seconds': 60})
            
            # Limpar chamadas antigas
            cutoff_time = now - timedelta(seconds=config['window_seconds'])
            self.call_tracker[endpoint] = [
                call_time for call_time in self.call_tracker[endpoint] 
                if call_time > cutoff_time
            ]
            
            # Verificar limite
            if len(self.call_tracker[endpoint]) >= config['max_calls']:
                oldest_call = min(self.call_tracker[endpoint])
                wait_time = config['window_seconds'] - (now - oldest_call).total_seconds()
                
                if wait_time > 0:
                    print(f"⏳ {self.bot_name}: Rate limit. Aguardando {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time + 0.5)
            
            # Registrar nova chamada
            self.call_tracker[endpoint].append(now)

class APIConnectionPool:
    """Pool de conexões API para distribuir carga"""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.connections: List[DerivAPI] = []
        self.current_index = 0
        self.lock = asyncio.Lock()
    
    async def initialize(self):
        """Inicializar pool de conexões"""
        for i in range(self.pool_size):
            try:
                api = DerivAPI(app_id=DERIV_APP_ID)
                await api.authorize(DERIV_API_TOKEN)
                self.connections.append(api)
                print(f"✅ Conexão API {i+1}/{self.pool_size} estabelecida")
            except Exception as e:
                print(f"⚠️ Erro na conexão {i+1}: {e}")
    
    async def get_connection(self) -> DerivAPI:
        """Obter conexão disponível do pool"""
        async with self.lock:
            if not self.connections:
                raise Exception("Nenhuma conexão disponível no pool")
            
            connection = self.connections[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.connections)
            return connection

class OperationQueue:
    """Sistema de filas para diferentes tipos de operação"""
    
    def __init__(self):
        self.buy_queue = asyncio.Queue(maxsize=20)
        self.check_queue = asyncio.Queue(maxsize=50)
        self.history_queue = asyncio.Queue(maxsize=30)
        
        # Workers para processar filas
        self.workers_running = False
    
    async def start_workers(self, api_pool: APIConnectionPool):
        """Iniciar workers para processar filas"""
        self.workers_running = True
        
        # Worker para compras
        asyncio.create_task(self._buy_worker(api_pool))
        
        # Worker para verificações
        asyncio.create_task(self._check_worker(api_pool))
        
        # Worker para históricos
        asyncio.create_task(self._history_worker(api_pool))
    
    async def _buy_worker(self, api_pool: APIConnectionPool):
        """Worker dedicado para operações de compra"""
        while self.workers_running:
            try:
                operation = await asyncio.wait_for(self.buy_queue.get(), timeout=1.0)
                api = await api_pool.get_connection()
                
                # Processar operação de compra
                result = await self._execute_buy(api, operation)
                operation['callback'](result)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Erro no buy_worker: {e}")
    
    async def _check_worker(self, api_pool: APIConnectionPool):
        """Worker dedicado para verificações de contrato"""
        while self.workers_running:
            try:
                operation = await asyncio.wait_for(self.check_queue.get(), timeout=1.0)
                api = await api_pool.get_connection()
                
                # Processar verificação
                result = await self._execute_check(api, operation)
                operation['callback'](result)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Erro no check_worker: {e}")
    
    async def _history_worker(self, api_pool: APIConnectionPool):
        """Worker dedicado para históricos"""
        while self.workers_running:
            try:
                operation = await asyncio.wait_for(self.history_queue.get(), timeout=1.0)
                api = await api_pool.get_connection()
                
                # Processar histórico
                result = await self._execute_history(api, operation)
                operation['callback'](result)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Erro no history_worker: {e}")
    
    async def _execute_buy(self, api: DerivAPI, operation: dict):
        """Executar operação de compra"""
        try:
            method = getattr(api, operation['method'])
            return await method(operation['params'])
        except Exception as e:
            return {'error': {'message': str(e)}}
    
    async def _execute_check(self, api: DerivAPI, operation: dict):
        """Executar verificação de contrato"""
        try:
            method = getattr(api, operation['method'])
            return await method(operation['params'])
        except Exception as e:
            return {'error': {'message': str(e)}}
    
    async def _execute_history(self, api: DerivAPI, operation: dict):
        """Executar busca de histórico"""
        try:
            method = getattr(api, operation['method'])
            return await method(operation['params'])
        except Exception as e:
            return {'error': {'message': str(e)}}

class BotManager:
    """Gerenciador principal dos bots com execução otimizada"""
    
    def __init__(self):
        self.api_pool = APIConnectionPool(pool_size=4)
        self.operation_queue = OperationQueue()
        self.bot_metrics: Dict[str, BotMetrics] = {}
        self.rate_limiters: Dict[str, BotRateLimiter] = {}
        
        # Semáforo para controlar concorrência
        self.operation_semaphore = asyncio.Semaphore(8)  # Max 8 operações simultâneas
    
    async def initialize(self):
        """Inicializar sistema"""
        print("🚀 Inicializando sistema otimizado...")
        
        # Inicializar pool de conexões
        await self.api_pool.initialize()
        
        # Iniciar workers das filas
        await self.operation_queue.start_workers(self.api_pool)
        
        print("✅ Sistema otimizado inicializado!")
    
    def register_bot(self, bot_name: str):
        """Registrar novo bot no sistema"""
        self.bot_metrics[bot_name] = BotMetrics(name=bot_name)
        self.rate_limiters[bot_name] = BotRateLimiter(bot_name)
    
    async def safe_api_call(self, bot_name: str, method_name: str, params: dict, max_retries: int = 2):
        """Chamada segura da API com rate limiting distribuído"""
        rate_limiter = self.rate_limiters[bot_name]
        
        for attempt in range(max_retries):
            try:
                # Aguardar rate limit específico do bot
                await rate_limiter.wait_for_limit(method_name)
                
                # Usar semáforo para controlar concorrência global
                async with self.operation_semaphore:
                    # Obter conexão do pool
                    api = await self.api_pool.get_connection()
                    
                    # Executar chamada
                    method = getattr(api, method_name)
                    result = await method(params)
                    
                    # Atualizar métricas
                    self.bot_metrics[bot_name].last_operation = datetime.now()
                    
                    return result
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1.5
                    print(f"⚠️ {bot_name}: Retry {attempt + 1}/{max_retries} em {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
    
    async def execute_bot_optimized(self, bot_func, bot_name: str):
        """Executar bot com otimizações"""
        self.register_bot(bot_name)
        
        try:
            self.bot_metrics[bot_name].status = "running"
            
            # Criar contexto isolado para o bot
            bot_context = {
                'manager': self,
                'bot_name': bot_name,
                'start_time': datetime.now()
            }
            
            # Executar bot com contexto
            await bot_func(bot_context)
            
        except Exception as e:
            print(f"❌ Erro no {bot_name}: {e}")
            self.bot_metrics[bot_name].status = "error"
        finally:
            self.bot_metrics[bot_name].status = "idle"
    
    def get_performance_report(self) -> dict:
        """Gerar relatório de performance"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_bots': len(self.bot_metrics),
            'active_bots': sum(1 for m in self.bot_metrics.values() if m.status == 'running'),
            'total_operations': sum(m.operations_count for m in self.bot_metrics.values()),
            'total_profit': sum(m.total_profit for m in self.bot_metrics.values()),
            'bots': {}
        }
        
        for bot_name, metrics in self.bot_metrics.items():
            report['bots'][bot_name] = {
                'operations': metrics.operations_count,
                'profit': metrics.total_profit,
                'success_rate': metrics.success_rate,
                'status': metrics.status,
                'last_operation': metrics.last_operation.isoformat() if metrics.last_operation else None
            }
        
        return report

# Função para salvar operação otimizada
async def salvar_operacao_async(nome_bot: str, lucro: float):
    """Versão assíncrona para salvar operação"""
    try:
        data = {
            'nome_bot': nome_bot,
            'lucro': lucro,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Usar ThreadPoolExecutor para operação de I/O
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: supabase.table('operacoes').insert(data).execute()
            )
        
        print(f"✅ {nome_bot}: Operação salva - Lucro: ${lucro:.2f}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar {nome_bot}: {e}")

# Exemplo de bot otimizado
async def bot_gold_optimized(context):
    """GoldBot otimizado para execução paralela"""
    manager = context['manager']
    bot_name = context['bot_name']
    
    # Configurações
    stake_inicial = 2.0
    martingale_fator = 2.0
    stake_atual = stake_inicial
    total_profit = 0.0
    
    print(f"🥇 {bot_name}: Iniciado com execução otimizada")
    
    while True:
        try:
            manager.bot_metrics[bot_name].status = "running"
            
            # Obter último dígito
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
            
            print(f"🔍 {bot_name}: Dígito: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Preparar compra DIGITDIFF
            buy_params = {
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
            
            # Fazer proposta
            proposal_response = await manager.safe_api_call(bot_name, 'proposal', buy_params)
            
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
            print(f"📈 {bot_name}: DIGITDIFF {ultimo_digito} comprado | Stake: ${stake_atual:.2f}")
            
            # Aguardar resultado de forma não-bloqueante
            manager.bot_metrics[bot_name].status = "waiting"
            
            contract_finalizado = False
            tentativas = 0
            max_tentativas = 20
            
            while not contract_finalizado and tentativas < max_tentativas:
                await asyncio.sleep(0.5)  # Intervalo menor para melhor responsividade
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
                        total_profit += lucro
                        
                        # Salvar operação de forma assíncrona
                        asyncio.create_task(salvar_operacao_async(bot_name, lucro))
                        
                        # Atualizar métricas
                        manager.bot_metrics[bot_name].operations_count += 1
                        manager.bot_metrics[bot_name].total_profit = total_profit
                        
                        if lucro > 0:
                            print(f"✅ {bot_name}: VITÓRIA! +${lucro:.2f} | Total: ${total_profit:.2f}")
                            stake_atual = stake_inicial  # Reset stake
                        else:
                            print(f"❌ {bot_name}: DERROTA! ${lucro:.2f} | Total: ${total_profit:.2f}")
                            stake_atual = abs(lucro) * martingale_fator  # Martingale
                            print(f"🔄 {bot_name}: Próximo stake: ${stake_atual:.2f}")
                        
                        break
                        
                except Exception as e:
                    print(f"⏳ {bot_name}: Verificando resultado... ({tentativas}/20)")
            
            # Pausa mínima entre operações
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"❌ {bot_name}: Erro: {e}")
            manager.bot_metrics[bot_name].status = "error"
            await asyncio.sleep(5)

async def main_optimized():
    """Função principal otimizada"""
    print("🚀 SISTEMA DE TRADING OTIMIZADO - EXECUÇÃO PARALELA EFICAZ")
    print("============================================================")
    
    # Inicializar gerenciador
    manager = BotManager()
    await manager.initialize()
    
    # Lista de bots para execução
    bot_configs = [
        ('GoldBot_1', bot_gold_optimized),
        ('GoldBot_2', bot_gold_optimized),
        ('GoldBot_3', bot_gold_optimized),
        # Adicionar mais bots conforme necessário
    ]
    
    # Criar tarefas otimizadas
    tasks = []
    for bot_name, bot_func in bot_configs:
        task = asyncio.create_task(
            manager.execute_bot_optimized(bot_func, bot_name)
        )
        tasks.append(task)
        
        # Delay mínimo entre inicializações
        await asyncio.sleep(0.2)
    
    print(f"📈 {len(tasks)} bots configurados para execução paralela otimizada")
    
    # Task para relatórios periódicos
    async def report_task():
        while True:
            await asyncio.sleep(30)  # Relatório a cada 30 segundos
            report = manager.get_performance_report()
            print(f"\n📊 RELATÓRIO: {report['active_bots']}/{report['total_bots']} bots ativos")
            print(f"💰 Profit total: ${report['total_profit']:.2f}")
            print(f"📈 Operações: {report['total_operations']}")
    
    tasks.append(asyncio.create_task(report_task()))
    
    try:
        # Executar todas as tarefas
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupção manual detectada...")
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main_optimized())
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")