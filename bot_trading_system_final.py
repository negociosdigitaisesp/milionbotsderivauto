#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Trading Automatizado - Versão Final Corrigida
Resolve todos os problemas identificados
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import random
from collections import defaultdict, deque
from deriv_api import DerivAPI
from supabase import create_client, Client
import threading
from concurrent.futures import ThreadPoolExecutor

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da API
DERIV_APP_ID = os.getenv('DERIV_APP_ID')
DERIV_API_TOKEN = os.getenv('DERIV_API_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Verificar se todas as variáveis estão definidas
if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Erro: Variáveis de ambiente não configuradas")
    sys.exit(1)

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurações de rate limiting otimizadas
RATE_LIMITS = {
    'buy': {'calls': 3, 'window': 60},
    'ticks_history': {'calls': 100, 'window': 60},
    'proposal_open_contract': {'calls': 100, 'window': 60},
    'proposal': {'calls': 50, 'window': 60}
}

class SmartRateLimiter:
    def __init__(self):
        self.call_tracker = defaultdict(lambda: deque())
        self.locks = defaultdict(threading.Lock)
    
    async def wait_for_rate_limit(self, method_name):
        """Rate limiting inteligente"""
        if method_name not in RATE_LIMITS:
            return
        
        config = RATE_LIMITS[method_name]
        now = time.time()
        
        with self.locks[method_name]:
            calls = self.call_tracker[method_name]
            
            # Remove chamadas antigas
            while calls and calls[0] <= now - config['window']:
                calls.popleft()
            
            # Verifica se precisa aguardar
            if len(calls) >= config['calls']:
                wait_time = calls[0] + config['window'] - now
                if wait_time > 0:
                    jitter = random.uniform(0.1, 0.3)
                    total_wait = wait_time + jitter
                    print(f"⏳ Rate limit {method_name}: aguardando {total_wait:.1f}s")
                    await asyncio.sleep(total_wait)
            
            # Registra a nova chamada
            calls.append(now)

class StableConnectionManager:
    def __init__(self, max_connections=2):
        self.max_connections = max_connections
        self.connections = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.rate_limiter = SmartRateLimiter()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
    
    async def initialize(self):
        """Inicializa conexões estáveis"""
        print(f"🔗 Inicializando {self.max_connections} conexões estáveis...")
        
        for i in range(self.max_connections):
            success = False
            for retry in range(3):
                try:
                    api = DerivAPI(app_id=DERIV_APP_ID)
                    await api.authorize(DERIV_API_TOKEN)
                    self.connections.append(api)
                    print(f"✅ Conexão {i+1} estabelecida")
                    success = True
                    break
                except Exception as e:
                    if retry < 2:
                        wait_time = (retry + 1) * 2
                        print(f"⚠️ Retry conexão {i+1}: {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ Falha conexão {i+1}: {e}")
            
            if not success:
                break
        
        if not self.connections:
            raise Exception("❌ Nenhuma conexão estabelecida")
        
        print(f"🎯 {len(self.connections)} conexões ativas")
    
    async def get_connection(self):
        """Obtém conexão com failover"""
        async with self.lock:
            if not self.connections:
                await self.reconnect()
            
            connection = self.connections[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.connections)
            return connection
    
    async def reconnect(self):
        """Reconecta em caso de falha"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            raise Exception("❌ Máximo de tentativas de reconexão atingido")
        
        self.reconnect_attempts += 1
        print(f"🔄 Tentativa de reconexão {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        # Limpar conexões antigas
        for api in self.connections:
            try:
                await api.disconnect()
            except:
                pass
        self.connections.clear()
        
        # Reestabelecer conexões
        await self.initialize()
    
    async def safe_api_call(self, method_name, params=None, max_retries=2):
        """Chamada segura com retry limitado"""
        await self.rate_limiter.wait_for_rate_limit(method_name)
        
        for attempt in range(max_retries):
            try:
                api = await self.get_connection()
                method = getattr(api, method_name)
                
                if params:
                    result = await method(params)
                else:
                    result = await method()
                
                # Reset contador de reconexão em caso de sucesso
                self.reconnect_attempts = 0
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Erros que indicam necessidade de reconexão
                if any(keyword in error_msg for keyword in ['close frame', 'connection', 'websocket']):
                    if attempt == 0:  # Só reconecta na primeira tentativa
                        try:
                            await self.reconnect()
                            continue
                        except:
                            pass
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1.5
                    print(f"⚠️ Retry {attempt+1}/{max_retries}: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Falha final: {e}")
                    raise e
    
    async def cleanup(self):
        """Limpa recursos"""
        for api in self.connections:
            try:
                await api.disconnect()
            except:
                pass
        self.connections.clear()

# Instância global
connection_manager = StableConnectionManager()
executor = ThreadPoolExecutor(max_workers=2)

async def salvar_operacao_async(bot_name, profit):
    """Salva operação de forma assíncrona"""
    def _salvar_sync():
        try:
            data = {
                'bot_name': bot_name,
                'profit': profit,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            supabase.table('operacoes').insert(data).execute()
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _salvar_sync)

async def bot_gold_stable(bot_name="GoldBot_Stable", stake_inicial=2.0, martingale_fator=2.0):
    """
    Bot Gold estável com contratos válidos
    """
    print(f"🚀 {bot_name}: Iniciando (Stake: ${stake_inicial:.2f})")
    
    stake_atual = stake_inicial
    total_profit = 0.0
    operacoes = 0
    vitorias = 0
    
    # Contratos válidos para R_100
    contract_types = [
        {'type': 'CALL', 'duration': 5, 'unit': 't'},
        {'type': 'PUT', 'duration': 5, 'unit': 't'},
        {'type': 'DIGITOVER', 'barrier': '5', 'duration': 1, 'unit': 't'},
        {'type': 'DIGITUNDER', 'barrier': '4', 'duration': 1, 'unit': 't'}
    ]
    
    while True:
        try:
            operacoes += 1
            
            # Selecionar contrato aleatório
            contract = random.choice(contract_types)
            
            print(f"📊 {bot_name}: Trade #{operacoes} | {contract['type']} | Stake: ${stake_atual:.2f}")
            
            # Criar proposta
            proposal_params = {
                'proposal': 1,
                'amount': stake_atual,
                'basis': 'stake',
                'contract_type': contract['type'],
                'currency': 'USD',
                'duration': contract['duration'],
                'duration_unit': contract['unit'],
                'symbol': 'R_100'
            }
            
            # Adicionar barrier se necessário
            if 'barrier' in contract:
                proposal_params['barrier'] = contract['barrier']
            
            proposal_response = await connection_manager.safe_api_call('proposal', proposal_params)
            
            if 'proposal' not in proposal_response:
                print(f"❌ {bot_name}: Proposta inválida")
                await asyncio.sleep(3)
                continue
            
            proposal_id = proposal_response['proposal']['id']
            payout = float(proposal_response['proposal']['payout'])
            
            print(f"📈 {bot_name}: Payout esperado: ${payout:.2f}")
            
            # Comprar contrato
            buy_params = {
                'buy': proposal_id,
                'price': stake_atual
            }
            
            buy_response = await connection_manager.safe_api_call('buy', buy_params)
            
            if 'buy' not in buy_response:
                print(f"❌ {bot_name}: Falha na compra")
                await asyncio.sleep(3)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"✅ {bot_name}: Contrato ativo - ID: {contract_id}")
            
            # Aguardar resultado com timeout
            max_wait = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    contract_response = await connection_manager.safe_api_call(
                        'proposal_open_contract',
                        {'proposal_open_contract': 1, 'contract_id': contract_id}
                    )
                    
                    if 'proposal_open_contract' in contract_response:
                        contract_data = contract_response['proposal_open_contract']
                        
                        if contract_data.get('is_settled'):
                            profit = float(contract_data.get('profit', 0))
                            total_profit += profit
                            
                            if profit > 0:
                                vitorias += 1
                                print(f"🎉 {bot_name}: VITÓRIA! +${profit:.2f} | Total: ${total_profit:.2f}")
                                stake_atual = stake_inicial  # Reset
                            else:
                                print(f"💸 {bot_name}: Derrota ${profit:.2f} | Total: ${total_profit:.2f}")
                                stake_atual = abs(profit) * martingale_fator  # Martingale
                            
                            # Salvar operação
                            await salvar_operacao_async(bot_name, profit)
                            
                            # Estatísticas
                            win_rate = (vitorias / operacoes) * 100
                            print(f"📊 {bot_name}: WR: {win_rate:.1f}% ({vitorias}/{operacoes}) | Próximo: ${stake_atual:.2f}")
                            
                            break
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️ {bot_name}: Erro verificação: {e}")
                    await asyncio.sleep(2)
                    break
            
            # Pausa entre trades
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ {bot_name}: Erro: {e}")
            print(f"⏳ {bot_name}: Aguardando 15s...")
            await asyncio.sleep(15)

async def bot_simple_call_put(bot_name="SimpleBot", stake=1.0):
    """
    Bot simples CALL/PUT para teste
    """
    print(f"🚀 {bot_name}: Bot simples iniciado")
    
    operacoes = 0
    total_profit = 0.0
    
    while True:
        try:
            operacoes += 1
            contract_type = random.choice(['CALL', 'PUT'])
            
            print(f"📊 {bot_name}: Trade #{operacoes} | {contract_type} | ${stake:.2f}")
            
            # Proposta
            proposal_params = {
                'proposal': 1,
                'amount': stake,
                'basis': 'stake',
                'contract_type': contract_type,
                'currency': 'USD',
                'duration': 5,
                'duration_unit': 't',
                'symbol': 'R_100'
            }
            
            proposal_response = await connection_manager.safe_api_call('proposal', proposal_params)
            
            if 'proposal' not in proposal_response:
                print(f"❌ {bot_name}: Proposta falhou")
                await asyncio.sleep(5)
                continue
            
            proposal_id = proposal_response['proposal']['id']
            
            # Compra
            buy_response = await connection_manager.safe_api_call('buy', {
                'buy': proposal_id,
                'price': stake
            })
            
            if 'buy' not in buy_response:
                print(f"❌ {bot_name}: Compra falhou")
                await asyncio.sleep(5)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"✅ {bot_name}: Contrato ativo")
            
            # Aguardar resultado
            for _ in range(15):
                try:
                    contract_response = await connection_manager.safe_api_call(
                        'proposal_open_contract',
                        {'proposal_open_contract': 1, 'contract_id': contract_id}
                    )
                    
                    if 'proposal_open_contract' in contract_response:
                        contract_data = contract_response['proposal_open_contract']
                        
                        if contract_data.get('is_settled'):
                            profit = float(contract_data.get('profit', 0))
                            total_profit += profit
                            
                            status = "VITÓRIA" if profit > 0 else "Derrota"
                            print(f"📈 {bot_name}: {status} ${profit:.2f} | Total: ${total_profit:.2f}")
                            
                            await salvar_operacao_async(bot_name, profit)
                            break
                    
                    await asyncio.sleep(1)
                except:
                    break
            
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"❌ {bot_name}: Erro: {e}")
            await asyncio.sleep(10)

async def main():
    """
    Sistema principal estável
    """
    print("🎯 SISTEMA DE TRADING ESTÁVEL - DERIV")
    print("🔧 Versão Final Corrigida")
    print("=" * 50)
    
    try:
        # Inicializar conexões
        await connection_manager.initialize()
        
        # Bots para execução paralela
        bots = [
            (bot_gold_stable, "GoldBot_1", 2.0, 2.0),
            (bot_gold_stable, "GoldBot_2", 2.0, 2.0),
            (bot_simple_call_put, "SimpleBot_1", 1.0),
            (bot_simple_call_put, "SimpleBot_2", 1.0)
        ]
        
        async def run_bot_delayed(bot_func, *args, delay=0):
            if delay > 0:
                await asyncio.sleep(delay)
            await bot_func(*args)
        
        # Criar tasks com delays
        tasks = []
        for i, bot_config in enumerate(bots):
            delay = i * 3  # 3 segundos entre cada bot
            task = asyncio.create_task(run_bot_delayed(*bot_config, delay=delay))
            tasks.append(task)
        
        print(f"🚀 Executando {len(tasks)} bots em paralelo...")
        
        # Executar todos os bots
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ Sistema interrompido")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
    finally:
        print("🧹 Finalizando...")
        await connection_manager.cleanup()
        executor.shutdown(wait=True)
        print("✅ Sistema finalizado")

if __name__ == "__main__":
    asyncio.run(main())