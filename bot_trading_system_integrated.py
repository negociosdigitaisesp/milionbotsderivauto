#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE TRADING AUTOMATIZADO COM SUPERVISÃO INTEGRADA
Versão: 3.0 - Integrada com Supervisor
Data: 2024

Características:
- Sistema de supervisão integrado
- Correção de erros WebSocket "no close frame received or sent"
- Pool de conexões com failover automático
- Rate limiting distribuído inteligente
- Reconexão automática robusta
- Monitoramento em tempo real
"""

import asyncio
import subprocess
import sys
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from deriv_api import DerivAPI
from supabase import create_client, Client
import json
import random

# Importações condicionais dos bots
try:
    from bot_scale import bot_scale
except ImportError:
    print("⚠️ bot_scale não encontrado")
    bot_scale = None

try:
    from bot_gold import bot_gold
except ImportError:
    print("⚠️ bot_gold não encontrado")
    bot_gold = None

# ============================================================================
# 1. CLASSES DE GERENCIAMENTO DE CONEXÃO E RATE LIMITING
# ============================================================================

class AdvancedRateLimiter:
    """Rate limiter avançado com jitter e controle inteligente"""
    
    def __init__(self):
        self.call_tracker = defaultdict(list)
        self.lock = asyncio.Lock()
        self.config = {
            'buy': {'max_calls': 3, 'window_seconds': 60},
            'ticks_history': {'max_calls': 8, 'window_seconds': 60},
            'proposal_open_contract': {'max_calls': 15, 'window_seconds': 60},
            'proposal': {'max_calls': 10, 'window_seconds': 60}
        }
    
    async def wait_for_rate_limit(self, endpoint):
        """Controla rate limiting com jitter para evitar thundering herd"""
        async with self.lock:
            now = datetime.now()
            config = self.config.get(endpoint, {'max_calls': 5, 'window_seconds': 60})
            
            # Limpar chamadas antigas
            cutoff_time = now - timedelta(seconds=config['window_seconds'])
            self.call_tracker[endpoint] = [
                call_time for call_time in self.call_tracker[endpoint] 
                if call_time > cutoff_time
            ]
            
            # Verificar se excedeu o limite
            if len(self.call_tracker[endpoint]) >= config['max_calls']:
                oldest_call = min(self.call_tracker[endpoint])
                wait_time = (oldest_call + timedelta(seconds=config['window_seconds']) - now).total_seconds()
                
                # Adicionar jitter para evitar sincronização
                jitter = random.uniform(0.5, 2.0)
                total_wait = max(0, wait_time + jitter)
                
                if total_wait > 0:
                    print(f"⏳ Rate limit atingido para {endpoint}. Aguardando {total_wait:.1f}s...")
                    await asyncio.sleep(total_wait)
            
            # Registrar a chamada
            self.call_tracker[endpoint].append(now)

class ConnectionPool:
    """Pool de conexões WebSocket com failover automático"""
    
    def __init__(self, app_id, token, pool_size=3):
        self.app_id = app_id
        self.token = token
        self.pool_size = pool_size
        self.connections = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.rate_limiter = AdvancedRateLimiter()
    
    async def initialize(self):
        """Inicializa o pool de conexões"""
        print(f"🔌 Inicializando pool de {self.pool_size} conexões...")
        
        for i in range(self.pool_size):
            try:
                api = DerivAPI(app_id=self.app_id)
                await api.authorize(self.token)
                self.connections.append(api)
                print(f"✅ Conexão {i+1}/{self.pool_size} estabelecida")
                await asyncio.sleep(1)  # Delay entre conexões
            except Exception as e:
                print(f"❌ Erro ao criar conexão {i+1}: {e}")
        
        if not self.connections:
            raise Exception("Falha ao estabelecer qualquer conexão")
        
        print(f"🎯 Pool inicializado com {len(self.connections)} conexões")
    
    async def get_connection(self):
        """Obtém uma conexão saudável do pool"""
        async with self.lock:
            for _ in range(len(self.connections)):
                api = self.connections[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.connections)
                
                # Verificar se a conexão está saudável
                try:
                    # Teste simples de conectividade
                    await asyncio.wait_for(api.ping(), timeout=5)
                    return api
                except Exception as e:
                    print(f"⚠️ Conexão {self.current_index} não responsiva: {e}")
                    # Tentar reconectar esta conexão
                    await self._reconnect_connection(self.current_index)
            
            # Se chegou aqui, todas as conexões falharam
            raise Exception("Todas as conexões do pool falharam")
    
    async def _reconnect_connection(self, index):
        """Reconecta uma conexão específica"""
        try:
            print(f"🔄 Reconectando conexão {index+1}...")
            old_api = self.connections[index]
            
            # Fechar conexão antiga
            try:
                await old_api.disconnect()
            except:
                pass
            
            # Criar nova conexão
            new_api = DerivAPI(app_id=self.app_id)
            await new_api.authorize(self.token)
            self.connections[index] = new_api
            print(f"✅ Conexão {index+1} reconectada")
            
        except Exception as e:
            print(f"❌ Falha ao reconectar conexão {index+1}: {e}")
    
    async def safe_api_call(self, method_name, params=None, max_retries=3):
        """Chamada segura à API com failover automático"""
        for attempt in range(max_retries):
            try:
                # Aguardar rate limit
                await self.rate_limiter.wait_for_rate_limit(method_name)
                
                # Obter conexão saudável
                api = await self.get_connection()
                
                # Fazer a chamada
                method = getattr(api, method_name)
                if params:
                    result = await asyncio.wait_for(method(params), timeout=10)
                else:
                    result = await asyncio.wait_for(method(), timeout=10)
                
                return result
                
            except asyncio.TimeoutError:
                print(f"⏰ Timeout na chamada {method_name} (tentativa {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                else:
                    raise Exception(f"Timeout persistente em {method_name}")
            
            except Exception as e:
                error_str = str(e).lower()
                is_connection_error = any(keyword in error_str for keyword in [
                    'no close frame received',
                    'connection closed',
                    'websocket',
                    'connection lost',
                    'connection reset'
                ])
                
                if is_connection_error and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"🔌 Erro de conexão em {method_name}: {e}")
                    print(f"🔄 Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise e
    
    async def close_all(self):
        """Fecha todas as conexões do pool"""
        print("🔌 Fechando todas as conexões...")
        for i, api in enumerate(self.connections):
            try:
                await api.disconnect()
                print(f"✅ Conexão {i+1} fechada")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão {i+1}: {e}")

# ============================================================================
# 2. SISTEMA DE SUPERVISÃO INTEGRADO
# ============================================================================

class SupervisorStats:
    """Classe para monitorar estatísticas do supervisor"""
    
    def __init__(self):
        self.inicio_supervisor = datetime.now()
        self.ciclos_executados = 0
        self.reinicios_programados = 0
        self.reinicios_por_falha = 0
        self.ultimo_reinicio = None
        self.tempo_execucao_antes_falha = 0
    
    def registrar_ciclo(self):
        self.ciclos_executados += 1
    
    def registrar_reinicio_programado(self):
        self.reinicios_programados += 1
        self.ultimo_reinicio = datetime.now()
    
    def registrar_reinicio_por_falha(self, tempo_execucao):
        self.reinicios_por_falha += 1
        self.tempo_execucao_antes_falha = tempo_execucao
        self.ultimo_reinicio = datetime.now()
    
    def get_tempo_ativo(self):
        return datetime.now() - self.inicio_supervisor
    
    def exibir_estatisticas(self):
        tempo_ativo = self.get_tempo_ativo()
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DO SUPERVISOR")
        print("="*60)
        print(f"⏰ Tempo ativo: {tempo_ativo}")
        print(f"🔄 Ciclos executados: {self.ciclos_executados}")
        print(f"⏲️  Reinícios programados: {self.reinicios_programados}")
        print(f"⚠️ Reinícios por falha: {self.reinicios_por_falha}")
        if self.ultimo_reinicio:
            print(f"🕐 Último reinício: {self.ultimo_reinicio.strftime('%H:%M:%S')}")
        print("="*60 + "\n")

class IntegratedSupervisor:
    """Sistema de supervisão integrado"""
    
    def __init__(self, execution_time_seconds=3600, pause_between_restarts=15):
        self.execution_time = execution_time_seconds
        self.pause_time = pause_between_restarts
        self.stats = SupervisorStats()
        self.running = False
    
    async def run_supervised_trading(self):
        """Executa o sistema de trading com supervisão integrada"""
        print("🎯 SISTEMA DE TRADING COM SUPERVISÃO INTEGRADA")
        print("="*60)
        
        self.running = True
        
        while self.running:
            try:
                self.stats.registrar_ciclo()
                inicio_ciclo = datetime.now()
                
                print(f"\n🚀 Iniciando ciclo {self.stats.ciclos_executados}")
                print(f"⏰ Duração programada: {self.execution_time}s")
                
                # Executar sistema de trading
                await asyncio.wait_for(
                    self.execute_trading_system(),
                    timeout=self.execution_time
                )
                
                # Se chegou aqui, foi reinício programado
                self.stats.registrar_reinicio_programado()
                print(f"⏰ Reinício programado após {self.execution_time}s")
                
            except asyncio.TimeoutError:
                # Reinício programado por timeout
                self.stats.registrar_reinicio_programado()
                print(f"⏰ Reinício programado após {self.execution_time}s")
                
            except KeyboardInterrupt:
                print("\n⏹️ Interrupção manual detectada...")
                self.running = False
                break
                
            except Exception as e:
                # Reinício por falha
                tempo_execucao = (datetime.now() - inicio_ciclo).total_seconds()
                self.stats.registrar_reinicio_por_falha(tempo_execucao)
                
                print(f"❌ Erro no sistema de trading: {e}")
                print(f"⚠️ Sistema executou por {tempo_execucao:.1f}s antes da falha")
                print(f"🔄 Reiniciando sistema...")
            
            # Exibir estatísticas a cada 5 ciclos
            if self.stats.ciclos_executados % 5 == 0:
                self.stats.exibir_estatisticas()
            
            # Pausa entre reinícios (se ainda estiver rodando)
            if self.running:
                print(f"⏸️ Aguardando {self.pause_time}s antes do próximo ciclo...")
                await asyncio.sleep(self.pause_time)
        
        # Exibir estatísticas finais
        print("\n🏁 SUPERVISOR ENCERRADO")
        self.stats.exibir_estatisticas()
    
    async def execute_trading_system(self):
        """Executa o sistema principal de trading"""
        # Carregar variáveis de ambiente
        load_dotenv()
        
        DERIV_APP_ID = os.getenv("DERIV_APP_ID")
        DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
            raise Exception("Variáveis de ambiente não configuradas")
        
        # Inicializar pool de conexões
        pool = ConnectionPool(DERIV_APP_ID, DERIV_API_TOKEN, pool_size=2)
        await pool.initialize()
        
        # Inicializar Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        try:
            # Verificar conexão com Supabase
            supabase.table('operacoes').select("*").limit(1).execute()
            print("✅ Conexão com Supabase verificada!")
        except Exception as e:
            print(f"⚠️ Aviso: Problema na conexão com Supabase: {e}")
        
        print("\n🤖 Iniciando execução dos bots...")
        
        # Lista de bots disponíveis
        available_bots = []
        
        if bot_gold:
            available_bots.append(("GoldBot_Integrated", self.create_gold_bot_integrated(pool, supabase)))
        
        # Adicionar bot simples para teste
        available_bots.append(("SimpleBot_Integrated", self.create_simple_bot_integrated(pool, supabase)))
        
        if not available_bots:
            raise Exception("Nenhum bot disponível para execução")
        
        # Criar tarefas com delays escalonados
        tasks = []
        for i, (bot_name, bot_func) in enumerate(available_bots):
            delay = i * 3  # 3 segundos entre cada bot
            task = asyncio.create_task(self.delayed_bot_execution(bot_func, delay, bot_name))
            tasks.append(task)
        
        print(f"📈 {len(tasks)} bots configurados para execução")
        
        try:
            # Executar todos os bots em paralelo
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Fechar pool de conexões
            await pool.close_all()
    
    async def delayed_bot_execution(self, bot_func, delay, bot_name):
        """Executa um bot com delay inicial"""
        await asyncio.sleep(delay)
        print(f"🚀 Iniciando {bot_name}...")
        await bot_func()
    
    def create_gold_bot_integrated(self, pool, supabase):
        """Cria uma versão integrada do GoldBot"""
        async def gold_bot_integrated():
            nome_bot = "GoldBot_Integrated"
            stake_inicial = 1.0
            stake_atual = stake_inicial
            total_profit = 0.0
            
            print(f"🥇 {nome_bot}: Iniciado com stake ${stake_inicial}")
            
            while True:
                try:
                    # Obter histórico de ticks
                    ticks_response = await pool.safe_api_call('ticks_history', {
                        "ticks_history": "R_100",
                        "count": 1,
                        "end": "latest"
                    })
                    
                    if 'error' in ticks_response:
                        print(f"❌ {nome_bot}: Erro ao obter ticks: {ticks_response['error']['message']}")
                        await asyncio.sleep(2)
                        continue
                    
                    # Estratégia: DIGITOVER simples
                    proposta = {
                        "proposal": 1,
                        "amount": stake_atual,
                        "basis": "stake",
                        "contract_type": "DIGITOVER",
                        "barrier": "5",
                        "currency": "USD",
                        "symbol": "R_100",
                        "duration": 5,
                        "duration_unit": "t"
                    }
                    
                    proposal_response = await pool.safe_api_call('proposal', proposta)
                    
                    if 'error' in proposal_response:
                        print(f"❌ {nome_bot}: Erro na proposta: {proposal_response['error']['message']}")
                        await asyncio.sleep(2)
                        continue
                    
                    # Comprar contrato
                    buy_response = await pool.safe_api_call('buy', {
                        "buy": proposal_response['proposal']['id'],
                        "price": float(stake_atual)
                    })
                    
                    if 'error' in buy_response:
                        print(f"❌ {nome_bot}: Erro na compra: {buy_response['error']['message']}")
                        await asyncio.sleep(2)
                        continue
                    
                    contract_id = buy_response['buy']['contract_id']
                    print(f"📋 {nome_bot}: Contrato ativo - ID: {contract_id}")
                    
                    # Aguardar resultado
                    await self.wait_for_contract_result(pool, contract_id, nome_bot, supabase)
                    
                    await asyncio.sleep(5)  # Pausa entre trades
                    
                except Exception as e:
                    print(f"❌ Erro no {nome_bot}: {e}")
                    await asyncio.sleep(5)
        
        return gold_bot_integrated
    
    def create_simple_bot_integrated(self, pool, supabase):
        """Cria um bot simples para teste"""
        async def simple_bot_integrated():
            nome_bot = "SimpleBot_Integrated"
            stake = 1.0
            
            print(f"🤖 {nome_bot}: Iniciado com stake ${stake}")
            
            while True:
                try:
                    # Estratégia: DIGITOVER simples
                    proposta = {
                        "proposal": 1,
                        "amount": stake,
                        "basis": "stake",
                        "contract_type": "DIGITOVER",
                        "barrier": "5",
                        "currency": "USD",
                        "symbol": "R_100",
                        "duration": 5,
                        "duration_unit": "t"
                    }
                    
                    proposal_response = await pool.safe_api_call('proposal', proposta)
                    
                    if 'error' in proposal_response:
                        print(f"❌ {nome_bot}: Erro na proposta: {proposal_response['error']['message']}")
                        await asyncio.sleep(3)
                        continue
                    
                    # Comprar contrato
                    buy_response = await pool.safe_api_call('buy', {
                        "buy": proposal_response['proposal']['id'],
                        "price": float(stake)
                    })
                    
                    if 'error' in buy_response:
                        print(f"❌ {nome_bot}: Erro na compra: {buy_response['error']['message']}")
                        await asyncio.sleep(3)
                        continue
                    
                    contract_id = buy_response['buy']['contract_id']
                    print(f"📋 {nome_bot}: Contrato ativo - ID: {contract_id}")
                    
                    # Aguardar resultado
                    await self.wait_for_contract_result(pool, contract_id, nome_bot, supabase)
                    
                    await asyncio.sleep(7)  # Pausa entre trades
                    
                except Exception as e:
                    print(f"❌ Erro no {nome_bot}: {e}")
                    await asyncio.sleep(5)
        
        return simple_bot_integrated
    
    async def wait_for_contract_result(self, pool, contract_id, nome_bot, supabase):
        """Aguarda o resultado de um contrato"""
        contract_finalizado = False
        tentativas = 0
        max_tentativas = 30
        
        while not contract_finalizado and tentativas < max_tentativas:
            await asyncio.sleep(1)
            tentativas += 1
            
            try:
                contract_status = await pool.safe_api_call('proposal_open_contract', {
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                })
                
                if 'error' in contract_status:
                    continue
                
                contract_info = contract_status['proposal_open_contract']
                
                if contract_info.get('is_sold', False):
                    contract_finalizado = True
                    lucro = float(contract_info.get('profit', 0))
                    
                    # Salvar operação
                    await self.salvar_operacao_async(supabase, nome_bot, lucro)
                    
                    if lucro > 0:
                        print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f}")
                    else:
                        print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f}")
                    break
                    
            except Exception as e:
                print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s)")
        
        if not contract_finalizado:
            print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
    
    async def salvar_operacao_async(self, supabase, nome_bot, lucro):
        """Salva operação no Supabase de forma assíncrona"""
        try:
            def save_operation():
                return supabase.table('operacoes').insert({
                    'bot_name': nome_bot,
                    'profit': lucro,
                    'timestamp': datetime.now().isoformat()
                }).execute()
            
            # Executar em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, save_operation)
            
        except Exception as e:
            print(f"⚠️ Erro ao salvar operação: {e}")

# ============================================================================
# 3. PONTO DE ENTRADA PRINCIPAL
# ============================================================================

async def main():
    """Função principal do sistema integrado"""
    supervisor = IntegratedSupervisor(
        execution_time_seconds=3600,  # 1 hora por ciclo
        pause_between_restarts=15     # 15 segundos entre reinícios
    )
    
    await supervisor.run_supervised_trading()

if __name__ == "__main__":
    print("🎯 SISTEMA DE TRADING AUTOMATIZADO COM SUPERVISÃO INTEGRADA")
    print("🔧 Versão 3.0 - Correção WebSocket + Supervisão")
    print("="*60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Sistema interrompido pelo usuário (Ctrl+C)")
        print("✅ Sistema encerrado com segurança!")
    except Exception as e:
        print(f"\n❌ Erro crítico no sistema: {e}")
        print("🔧 Verifique as configurações e tente novamente.")