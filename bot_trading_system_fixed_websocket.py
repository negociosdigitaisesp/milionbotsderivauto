#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Trading Automatizado - Versão Corrigida WebSocket
Corrige problemas de conexão WebSocket e rate limiting
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

# Configurações de rate limiting melhoradas
RATE_LIMITS = {
    'buy': {'calls': 5, 'window': 60},
    'ticks_history': {'calls': 300, 'window': 60},
    'proposal_open_contract': {'calls': 300, 'window': 60}
}

class ImprovedRateLimiter:
    def __init__(self):
        self.call_tracker = defaultdict(lambda: deque())
        self.locks = defaultdict(threading.Lock)
    
    async def wait_for_rate_limit(self, method_name):
        """Rate limiting melhorado com jitter"""
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
                    # Adiciona jitter para evitar thundering herd
                    jitter = random.uniform(0.1, 0.5)
                    total_wait = wait_time + jitter
                    print(f"⏳ Rate limit atingido para {method_name}. Aguardando {total_wait:.1f}s...")
                    await asyncio.sleep(total_wait)
            
            # Registra a nova chamada
            calls.append(now)

class ConnectionManager:
    def __init__(self, max_connections=3):
        self.max_connections = max_connections
        self.connections = []
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.rate_limiter = ImprovedRateLimiter()
    
    async def initialize(self):
        """Inicializa pool de conexões com retry"""
        print(f"🔗 Inicializando pool de {self.max_connections} conexões...")
        
        for i in range(self.max_connections):
            max_retries = 3
            for retry in range(max_retries):
                try:
                    api = DerivAPI(app_id=DERIV_APP_ID)
                    await api.authorize(DERIV_API_TOKEN)
                    self.connections.append(api)
                    print(f"✅ Conexão {i+1}/{self.max_connections} estabelecida")
                    break
                except Exception as e:
                    if retry < max_retries - 1:
                        wait_time = (retry + 1) * 2
                        print(f"⚠️ Erro na conexão {i+1}, tentativa {retry+1}/{max_retries}. Aguardando {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ Falha ao estabelecer conexão {i+1} após {max_retries} tentativas")
        
        if not self.connections:
            raise Exception("❌ Nenhuma conexão estabelecida")
        
        print(f"🎯 Pool inicializado com {len(self.connections)} conexões")
    
    async def get_connection(self):
        """Obtém conexão com balanceamento de carga"""
        async with self.lock:
            if not self.connections:
                raise Exception("❌ Nenhuma conexão disponível")
            
            connection = self.connections[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.connections)
            return connection
    
    async def safe_api_call(self, method_name, params=None, max_retries=3):
        """Chamada segura à API com retry e failover"""
        await self.rate_limiter.wait_for_rate_limit(method_name)
        
        for attempt in range(max_retries):
            try:
                api = await self.get_connection()
                method = getattr(api, method_name)
                
                if params:
                    result = await method(params)
                else:
                    result = await method()
                
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Erro na API (tentativa {attempt+1}/{max_retries}): {e}")
                    print(f"   Aguardando {wait_time}s antes de tentar novamente...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Falha após {max_retries} tentativas: {e}")
                    raise e
    
    async def cleanup(self):
        """Limpa conexões"""
        for api in self.connections:
            try:
                await api.disconnect()
            except:
                pass
        self.connections.clear()

# Instância global do gerenciador de conexões
connection_manager = ConnectionManager()

# ThreadPoolExecutor para operações síncronas
executor = ThreadPoolExecutor(max_workers=4)

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
            print(f"❌ Erro ao salvar operação: {e}")
            return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _salvar_sync)

async def bot_gold_fixed(bot_name="GoldBot_Fixed", stake_inicial=2.0, martingale_fator=2.0, stop_loss=None, stop_win=None):
    """
    Bot Gold com correções de WebSocket e rate limiting
    """
    print(f"🚀 {bot_name}: Iniciando com stake inicial ${stake_inicial:.2f}")
    
    stake_atual = stake_inicial
    total_profit = 0.0
    operacoes = 0
    vitorias = 0
    
    while True:
        try:
            operacoes += 1
            
            # Obter último dígito para predição dinâmica
            try:
                ticks_response = await connection_manager.safe_api_call(
                    'ticks_history',
                    {
                        'ticks_history': 'R_100',
                        'adjust_start_time': 1,
                        'count': 1,
                        'end': 'latest',
                        'style': 'ticks'
                    }
                )
                
                if 'history' in ticks_response and 'prices' in ticks_response['history']:
                    ultimo_tick = float(ticks_response['history']['prices'][-1])
                    ultimo_digito = int(str(ultimo_tick).replace('.', '')[-1])
                    
                    # Predição dinâmica baseada no último dígito
                    if ultimo_digito <= 4:
                        prediction = random.choice([5, 6, 7, 8, 9])
                    else:
                        prediction = random.choice([0, 1, 2, 3, 4])
                    
                    print(f"🔍 {bot_name}: Último dígito: {ultimo_digito} | Predição: {prediction}")
                else:
                    prediction = random.randint(0, 9)
                    print(f"🎲 {bot_name}: Predição aleatória: {prediction}")
                    
            except Exception as e:
                prediction = random.randint(0, 9)
                print(f"⚠️ {bot_name}: Erro ao obter tick, usando predição aleatória: {prediction}")
            
            # Criar proposta
            proposal_params = {
                'proposal': 1,
                'amount': stake_atual,
                'barrier': str(prediction),
                'basis': 'stake',
                'contract_type': 'DIGITDIFF',
                'currency': 'USD',
                'duration': 1,
                'duration_unit': 't',
                'symbol': 'R_100'
            }
            
            proposal_response = await connection_manager.safe_api_call('proposal', proposal_params)
            
            if 'proposal' not in proposal_response:
                print(f"❌ {bot_name}: Erro na proposta")
                await asyncio.sleep(2)
                continue
            
            proposal_id = proposal_response['proposal']['id']
            payout = float(proposal_response['proposal']['payout'])
            
            print(f"📈 {bot_name}: Trade #{operacoes} | DIGITDIFF {prediction} | Stake: ${stake_atual:.2f} | Payout: ${payout:.2f}")
            
            # Comprar contrato
            buy_params = {
                'buy': proposal_id,
                'price': stake_atual
            }
            
            buy_response = await connection_manager.safe_api_call('buy', buy_params)
            
            if 'buy' not in buy_response:
                print(f"❌ {bot_name}: Erro na compra")
                await asyncio.sleep(2)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"✅ {bot_name}: Contrato comprado - ID: {contract_id}")
            
            # Aguardar resultado
            max_wait_time = 30
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    contract_response = await connection_manager.safe_api_call(
                        'proposal_open_contract',
                        {'proposal_open_contract': 1, 'contract_id': contract_id}
                    )
                    
                    if 'proposal_open_contract' in contract_response:
                        contract = contract_response['proposal_open_contract']
                        
                        if contract.get('is_settled'):
                            profit = float(contract.get('profit', 0))
                            total_profit += profit
                            
                            if profit > 0:
                                vitorias += 1
                                print(f"🎉 {bot_name}: VITÓRIA! Profit: ${profit:.2f} | Total: ${total_profit:.2f}")
                                stake_atual = stake_inicial  # Reset stake
                            else:
                                print(f"💸 {bot_name}: Derrota. Loss: ${profit:.2f} | Total: ${total_profit:.2f}")
                                stake_atual = abs(profit) * martingale_fator  # Martingale agressivo
                            
                            # Salvar operação
                            await salvar_operacao_async(bot_name, profit)
                            
                            # Estatísticas
                            win_rate = (vitorias / operacoes) * 100
                            print(f"📊 {bot_name}: Win Rate: {win_rate:.1f}% ({vitorias}/{operacoes}) | Próximo Stake: ${stake_atual:.2f}")
                            
                            # Verificar stop loss/win
                            if stop_loss and total_profit <= -stop_loss:
                                print(f"🛑 {bot_name}: Stop Loss atingido: ${total_profit:.2f}")
                                return
                            
                            if stop_win and total_profit >= stop_win:
                                print(f"🎯 {bot_name}: Stop Win atingido: ${total_profit:.2f}")
                                return
                            
                            break
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️ {bot_name}: Erro ao verificar resultado: {e}")
                    await asyncio.sleep(1)
            
            # Pausa entre operações
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro no {bot_name}: {e}")
            print(f"⏳ {bot_name}: Aguardando 10 segundos antes de tentar novamente...")
            await asyncio.sleep(10)

# Importar bots existentes
try:
    from bot_trading_system_fixed import (
        bot_ai_20, bot_apalancamiento, bk_bot_10, wolf_bot_20,
        sniper_bot_martingale, factor50x_conservador, tip_bot,
        alfa_bot, quantum_bot_fixed_stake, xtreme_bot
    )
    print("✅ Bots importados com sucesso!")
except ImportError as e:
    print(f"⚠️ Erro ao importar alguns bots: {e}")
    # Definir bots vazios como fallback
    async def bot_placeholder(name):
        print(f"⚠️ {name}: Bot não disponível")
        await asyncio.sleep(60)
    
    bot_ai_20 = lambda: bot_placeholder("BotAI_2.0")
    bot_apalancamiento = lambda: bot_placeholder("Bot_Apalancamiento")
    bk_bot_10 = lambda: bot_placeholder("BK_BOT_1.0")
    wolf_bot_20 = lambda: bot_placeholder("Wolf_Bot_2.0")
    sniper_bot_martingale = lambda: bot_placeholder("Sniper_Bot_Martingale")
    factor50x_conservador = lambda: bot_placeholder("Factor50X_Conservador")
    tip_bot = lambda: bot_placeholder("Tip_Bot")
    alfa_bot = lambda: bot_placeholder("Alfa_Bot")
    quantum_bot_fixed_stake = lambda: bot_placeholder("QuantumBot_FixedStake")
    xtreme_bot = lambda: bot_placeholder("XtremeBot")

# Importar bot_scale com fallback
try:
    from trading_system.bots.scale_bot import bot_scale
    print("✅ Scale Bot importado com sucesso!")
except ImportError:
    print("⚠️ Scale Bot não encontrado, usando versão local")
    async def bot_scale():
        print("⚠️ ScaleBot: Versão local não implementada")
        await asyncio.sleep(60)

async def main():
    """
    Função principal com execução paralela corrigida
    """
    print("🎯 SISTEMA DE TRADING AUTOMATIZADO - DERIV")
    print("⏰ Tempo de execução configurado: 3600 segundos")
    print("🔄 Rate limiting ativo para proteção da API")
    print("=" * 60)
    print("🔧 VERSÃO CORRIGIDA - WEBSOCKET ESTÁVEL")
    print("=" * 50)
    
    try:
        # Inicializar gerenciador de conexões
        await connection_manager.initialize()
        
        # Lista de bots com delays escalonados
        bots = [
            (bot_gold_fixed, "GoldBot_Fixed_1", 2.0, 2.0, None, None, 0),
            (bot_gold_fixed, "GoldBot_Fixed_2", 2.0, 2.0, None, None, 2),
            (bot_gold_fixed, "GoldBot_Fixed_3", 2.0, 2.0, None, None, 4),
            (bot_ai_20, None, None, None, None, None, 6),
            (bot_apalancamiento, None, None, None, None, None, 8),
            (bk_bot_10, None, None, None, None, None, 10),
            (wolf_bot_20, None, None, None, None, None, 12),
            (sniper_bot_martingale, None, None, None, None, None, 14),
            (factor50x_conservador, None, None, None, None, None, 16),
            (tip_bot, None, None, None, None, None, 18),
            (alfa_bot, None, None, None, None, None, 20),
            (quantum_bot_fixed_stake, None, None, None, None, None, 22),
            (xtreme_bot, None, None, None, None, None, 24),
            (bot_scale, None, None, None, None, None, 26)
        ]
        
        async def run_bot_with_delay(bot_func, *args):
            """Executa bot com delay inicial"""
            delay = args[-1] if args and isinstance(args[-1], (int, float)) else 0
            if delay > 0:
                print(f"⏳ Aguardando {delay}s para iniciar {bot_func.__name__}...")
                await asyncio.sleep(delay)
            
            # Filtrar argumentos None
            filtered_args = [arg for arg in args[:-1] if arg is not None]
            
            if filtered_args:
                await bot_func(*filtered_args)
            else:
                await bot_func()
        
        # Criar tasks para todos os bots
        tasks = []
        for bot_config in bots:
            bot_func = bot_config[0]
            args = bot_config[1:]
            task = asyncio.create_task(run_bot_with_delay(bot_func, *args))
            tasks.append(task)
        
        print(f"🚀 Iniciando {len(tasks)} bots em paralelo...")
        
        # Executar todos os bots em paralelo
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
    finally:
        print("🧹 Limpando recursos...")
        await connection_manager.cleanup()
        executor.shutdown(wait=True)
        print("✅ Sistema finalizado")

if __name__ == "__main__":
    asyncio.run(main())