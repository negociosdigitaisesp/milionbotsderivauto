"""
Sistema de Trading Automatizado - Múltiplos Bots Deriv
Executa estratégias de trading em paralelo usando asyncio
Com funcionalidade integrada de supervisor para auto-reinício
"""

# 1. IMPORTAÇÕES
import asyncio
import os
import sys
import subprocess
import time
from deriv_api import DerivAPI
from supabase import create_client, Client
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import random
from collections import defaultdict
import threading
from typing import List, Optional

# Importar bot_scale do módulo trading_system
try:
    from trading_system.bots.scale_bot import bot_scale
except ImportError:
    print("Aviso: Modulo bot_scale nao encontrado. Funcao bot_scale sera definida localmente.")
    
# Importar bot_gold do arquivo bot_trading_system_fixed
from bot_trading_system_fixed import bot_gold

# Importar bot doublecuentas
try:
    from trading_system.bots.double_cuentas_bot.bot_double_cuentas import bot_double_cuentas
except ImportError:
    print("Aviso: Modulo bot_double_cuentas nao encontrado. Sera definido localmente.")

# Importar bot aura_under8
try:
    from trading_system.bots.aura_bot.bot_aura_under8 import bot_aura_under8
except ImportError:
    print("Aviso: Modulo bot_aura_under8 nao encontrado. Sera definido localmente.")

# Importar bot accumulator_scalping
try:
    from trading_system.bots.accumulator_bot.bot_accumulator_scalping import bot_accumulator_scalping
except ImportError:
    print("Aviso: Modulo bot_accumulator_scalping nao encontrado. Sera definido localmente.")

# CLASSE APIMANAGER - GERENCIAMENTO ROBUSTO DE API
class ApiManager:
    """
    Classe para gerenciar chamadas à API da Deriv de forma robusta
    Implementa controle de concorrência e pausas para evitar rate limiting
    """
    
    def __init__(self, api):
        self.api = api
        self.api_lock = asyncio.Lock()
    
    async def buy(self, params):
        """Wrapper para chamadas de compra com controle de concorrência"""
        async with self.api_lock:
            resultado = await self.api.buy(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturação
            return resultado
    
    async def ticks_history(self, params):
        """Wrapper para chamadas de histórico de ticks com controle de concorrência"""
        async with self.api_lock:
            resultado = await self.api.ticks_history(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturação
            return resultado
    
    async def proposal_open_contract(self, params):
        """Wrapper para chamadas de status de contrato com controle de concorrência"""
        async with self.api_lock:
            resultado = await self.api.proposal_open_contract(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturação
            return resultado
    
    async def proposal(self, params):
        """Wrapper para chamadas de proposta com controle de concorrência"""
        async with self.api_lock:
            resultado = await self.api.proposal(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturação
            return resultado

async def bot_scale(api_manager):
        """
        Bot Scale - Implementação local de fallback
        Estratégia simples de trading com stake fixo
        """
        nome_bot = "Scale_Bot_Local"
        stake_fixo = 1.0
        total_profit = 0
        
        print(f"Iniciando {nome_bot} (versao local)...")
        
        while True:
            try:
                # Implementação básica de trading
                print(f"🔄 {nome_bot}: Executando estratégia básica...")
                
                # Obter último tick
                ticks_response = await api_manager.ticks_history({
                    'ticks_history': 'R_100',
                    'count': 1,
                    'end': 'latest'
                })
                
                if 'error' in ticks_response:
                    print(f"❌ {nome_bot}: Erro ao obter ticks: {ticks_response['error']['message']}")
                    await asyncio.sleep(1)
                    continue
                
                # Estratégia simples: DIGITOVER 0
                parametros_da_compra = {
                    'buy': '1',
                    'subscribe': 1,
                    'price': stake_fixo,
                    'parameters': {
                        'amount': stake_fixo,
                        'basis': 'stake',
                        'contract_type': 'DIGITOVER',
                        'currency': 'USD',
                        'duration': 1,
                        'duration_unit': 't',
                        'symbol': 'R_100',
                        'barrier': 0
                    }
                }
                
                recibo_compra = await api_manager.buy(parametros_da_compra)
                
                if 'error' in recibo_compra:
                    print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                    await asyncio.sleep(1)
                    continue
                
                # Aguardar resultado
                if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                    contract_id = recibo_compra['buy']['contract_id']
                    
                    contract_finalizado = False
                    tentativas = 0
                    max_tentativas = 30
                    
                    while not contract_finalizado and tentativas < max_tentativas:
                        await asyncio.sleep(1)
                        tentativas += 1
                        
                        try:
                            contract_status = await api_manager.proposal_open_contract({
                                "proposal_open_contract": 1,
                                "contract_id": contract_id
                            })
                            
                            if 'error' in contract_status:
                                continue
                            
                            contract_info = contract_status['proposal_open_contract']
                            
                            if contract_info.get('is_sold', False):
                                contract_finalizado = True
                                lucro = float(contract_info.get('profit', 0))
                                total_profit += lucro
                                salvar_operacao(nome_bot, lucro)
                                
                                if lucro > 0:
                                    print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Total: ${total_profit:.2f}")
                                else:
                                    print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Total: ${total_profit:.2f}")
                                break
                                
                        except Exception as e:
                            print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s)")
                
            except Exception as e:
                print(f"❌ Erro no {nome_bot}: {e}")
            
            await asyncio.sleep(2)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# CLASSES PARA CORREÇÃO DE WEBSOCKET E SUPERVISÃO INTEGRADA
class AdvancedRateLimiter:
    """Rate limiter avançado com jitter e distribuição inteligente"""
    def __init__(self):
        self.call_tracker = defaultdict(list)
        self.rate_limit_lock = asyncio.Lock()
        
    async def wait_for_rate_limit(self, method_name: str):
        """Aguarda respeitando o rate limit com jitter"""
        async with self.rate_limit_lock:
            config = RATE_LIMIT_CONFIG.get(method_name, {'max_calls': 5, 'window_seconds': 60})
            now = time.time()
            
            # Limpar chamadas antigas
            self.call_tracker[method_name] = [
                call_time for call_time in self.call_tracker[method_name]
                if now - call_time < config['window_seconds']
            ]
            
            # Verificar se precisa aguardar
            if len(self.call_tracker[method_name]) >= config['max_calls']:
                oldest_call = min(self.call_tracker[method_name])
                wait_time = config['window_seconds'] - (now - oldest_call)
                
                if wait_time > 0:
                    # Adicionar jitter para distribuir chamadas
                    jitter = random.uniform(0.1, 0.5)
                    total_wait = wait_time + jitter
                    print(f"⏳ Rate limit atingido para {method_name}. Aguardando {total_wait:.1f}s...")
                    await asyncio.sleep(total_wait)
            
            # Registrar a chamada
            self.call_tracker[method_name].append(time.time())

class ConnectionPool:
    """Pool de conexões WebSocket com failover e reconexão automática"""
    def __init__(self, app_id: str, token: str, pool_size: int = 2):
        self.app_id = app_id
        self.token = token
        self.pool_size = pool_size
        self.connections: List[Optional[DerivAPI]] = []
        self.current_index = 0
        self.connection_lock = asyncio.Lock()
        
    async def initialize(self):
        """Inicializa o pool de conexões"""
        print(f"🔌 Inicializando pool de {self.pool_size} conexões...")
        
        for i in range(self.pool_size):
            try:
                api = DerivAPI(app_id=self.app_id)
                await api.authorize(self.token)
                self.connections.append(api)
                print(f"✅ Conexão {i+1}/{self.pool_size} estabelecida")
            except Exception as e:
                print(f"❌ Falha na conexão {i+1}: {e}")
                self.connections.append(None)
        
        active_connections = sum(1 for conn in self.connections if conn is not None)
        print(f"🎯 Pool inicializado com {active_connections} conexões")
        
        if active_connections == 0:
            raise Exception("Nenhuma conexão WebSocket pôde ser estabelecida")
    
    async def get_connection(self) -> DerivAPI:
        """Obtém uma conexão ativa do pool com failover"""
        async with self.connection_lock:
            attempts = 0
            max_attempts = self.pool_size * 2
            
            while attempts < max_attempts:
                conn = self.connections[self.current_index]
                
                if conn is not None:
                    try:
                        # Testar se a conexão está ativa
                        await conn.ping()
                        return conn
                    except Exception:
                        print(f"🔌 Conexão {self.current_index} inativa, tentando reconectar...")
                        await self._reconnect(self.current_index)
                
                # Próxima conexão
                self.current_index = (self.current_index + 1) % self.pool_size
                attempts += 1
            
            raise Exception("Todas as conexões do pool falharam")
    
    async def _reconnect(self, index: int):
        """Reconecta uma conexão específica"""
        try:
            if self.connections[index]:
                await self.connections[index].disconnect()
        except:
            pass
        
        try:
            api = DerivAPI(app_id=self.app_id)
            await api.authorize(self.token)
            self.connections[index] = api
            print(f"✅ Conexão {index} reconectada")
        except Exception as e:
            print(f"❌ Falha na reconexão {index}: {e}")
            self.connections[index] = None
    
    async def close_all(self):
        """Fecha todas as conexões do pool"""
        for i, conn in enumerate(self.connections):
            if conn:
                try:
                    await conn.disconnect()
                    print(f"🔌 Conexão {i} fechada")
                except:
                    pass
        self.connections.clear()

class SupervisorStats:
    """Classe para monitorar estatísticas do supervisor integrado"""
    def __init__(self):
        self.inicio_sistema = time.time()
        self.ciclos_executados = 0
        self.reinicios_programados = 0
        self.reinicios_por_falha = 0
        self.ultimo_reinicio = None
        
    def registrar_ciclo(self):
        self.ciclos_executados += 1
        
    def registrar_reinicio_programado(self):
        self.reinicios_programados += 1
        self.ultimo_reinicio = time.time()
        
    def registrar_reinicio_falha(self):
        self.reinicios_por_falha += 1
        self.ultimo_reinicio = time.time()
        
    def get_tempo_ativo(self):
        return time.time() - self.inicio_sistema
        
    def exibir_estatisticas(self):
        tempo_ativo = self.get_tempo_ativo()
        horas = int(tempo_ativo // 3600)
        minutos = int((tempo_ativo % 3600) // 60)
        
        print("\n📊 ESTATÍSTICAS DO SUPERVISOR INTEGRADO")
        print("=" * 50)
        print(f"⏰ Tempo ativo: {horas}h {minutos}m")
        print(f"🔄 Ciclos executados: {self.ciclos_executados}")
        print(f"⏰ Reinícios programados: {self.reinicios_programados}")
        print(f"❌ Reinícios por falha: {self.reinicios_por_falha}")
        if self.ultimo_reinicio:
            ultimo = datetime.fromtimestamp(self.ultimo_reinicio).strftime("%H:%M:%S")
            print(f"🕐 Último reinício: {ultimo}")
        print("=" * 50)

# Instâncias globais
rate_limiter = AdvancedRateLimiter()
connection_pool = None
supervisor_stats = SupervisorStats()

# SISTEMA DE CONTROLE DE RATE LIMITING

# Controle de chamadas por endpoint
call_tracker = defaultdict(list)
rate_limit_lock = asyncio.Lock()

async def wait_for_rate_limit(endpoint):
    """
    Controla o rate limiting para evitar excesso de chamadas à API
    """
    async with rate_limit_lock:
        now = datetime.now()
        config = RATE_LIMIT_CONFIG.get(endpoint, {'max_calls': 5, 'window_seconds': 60})
        
        # Limpar chamadas antigas
        cutoff_time = now - timedelta(seconds=config['window_seconds'])
        call_tracker[endpoint] = [
            call_time for call_time in call_tracker[endpoint] 
            if call_time > cutoff_time
        ]
        
        # Verificar se excedeu o limite
        if len(call_tracker[endpoint]) >= config['max_calls']:
            # Calcular tempo de espera
            oldest_call = min(call_tracker[endpoint])
            wait_time = config['window_seconds'] - (now - oldest_call).total_seconds()
            
            if wait_time > 0:
                print(f"⏳ Rate limit atingido para {endpoint}. Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time + 1)  # +1 segundo de margem
                
                # Limpar novamente após a espera
                now = datetime.now()
                cutoff_time = now - timedelta(seconds=config['window_seconds'])
                call_tracker[endpoint] = [
                    call_time for call_time in call_tracker[endpoint] 
                    if call_time > cutoff_time
                ]
        
        # Registrar a nova chamada
        call_tracker[endpoint].append(now)

async def safe_api_call(api, method_name, params, max_retries=3):
    """
    Wrapper seguro para chamadas da API com rate limiting avançado e retry
    """
    global connection_pool
    
    for attempt in range(max_retries):
        try:
            # Usar rate limiter avançado
            await rate_limiter.wait_for_rate_limit(method_name)
            
            # Obter conexão do pool se disponível, senão usar a API passada
            if connection_pool:
                try:
                    api_conn = await connection_pool.get_connection()
                except Exception:
                    api_conn = api  # Fallback para API original
            else:
                api_conn = api
            
            # Fazer a chamada
            method = getattr(api_conn, method_name)
            result = await method(params)
            
            # Verificar se há erro de rate limit
            if 'error' in result and 'rate limit' in result['error']['message'].lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Espera progressiva: 5s, 10s, 15s
                    print(f"⚠️ Rate limit detectado. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Rate limit persistente após {max_retries} tentativas")
            
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            is_no_close_frame_error = 'no close frame received' in error_str or 'no close frame sent' in error_str
            is_websocket_error = any(keyword in error_str for keyword in [
                'no close frame received',
                'connection closed',
                'websocket',
                'connection lost',
                'connection reset',
                'connection aborted'
            ])
            
            # Tratamento específico para erro "no close frame received or sent"
            if is_no_close_frame_error:
                print(f"🔌 Erro 'no close frame received or sent' detectado: {e}")
                if attempt == 0:  # Primeira tentativa - tentar reconectar uma vez
                    print("🔄 Tentando reconectar uma vez...")
                    if connection_pool:
                        try:
                            await connection_pool.close_all()
                            await connection_pool.initialize()
                            print("✅ Reconexão realizada com sucesso")
                        except Exception as pool_error:
                            print(f"❌ Falha na reconexão: {pool_error}")
                    
                    # Tentar novamente após reconexão
                    await asyncio.sleep(2)
                    continue
                else:  # Segunda tentativa falhou - reiniciar bots
                    print("❌ Reconexão falhou. Reiniciando bots...")
                    # Sinalizar para reiniciar todo o sistema
                    raise Exception("RESTART_BOTS_REQUIRED")
            
            elif is_websocket_error and connection_pool:
                print(f"🔌 Erro WebSocket detectado: {e}")
                # Tentar reconectar todas as conexões do pool
                try:
                    await connection_pool.initialize()
                except Exception as pool_error:
                    print(f"❌ Falha na reinicialização do pool: {pool_error}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Espera progressiva: 2s, 4s, 6s
                print(f"⚠️ Erro na API (tentativa {attempt + 1}/{max_retries}): {str(e)}")
                print(f"   Aguardando {wait_time}s antes de tentar novamente...")
                await asyncio.sleep(wait_time)
            else:
                raise e

# 2. CONFIGURAÇÕES DE RATE LIMITING
# Configuração para controle de taxa de chamadas à API
RATE_LIMIT_CONFIG = {
    'buy': {'max_calls': 5, 'window_seconds': 60},  # 5 compras por minuto
    'ticks_history': {'max_calls': 10, 'window_seconds': 60},  # 10 históricos por minuto
    'proposal_open_contract': {'max_calls': 20, 'window_seconds': 60}  # 20 verificações por minuto
}

# 3. CONFIGURAÇÕES E CONEXÃO COM SUPABASE
# Credenciais da Deriv API (carregadas do arquivo .env)
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")

# Credenciais do Supabase (carregadas do arquivo .env)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificar se todas as variáveis de ambiente foram carregadas
if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("❌ Erro: Variáveis de ambiente não encontradas. Verifique o arquivo .env")

# Inicializar cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. FUNÇÃO GENÉRICA PARA SALVAR DADOS
def salvar_operacao(nome_bot: str, lucro: float):
    """
    Salva o resultado de uma operação no banco de dados Supabase
    
    Args:
        nome_bot (str): Nome identificador do bot
        lucro (float): Valor do lucro/prejuízo da operação
    """
    try:
        # Inserir dados na tabela 'operacoes' do Supabase
        data = {
            'nome_bot': nome_bot,
            'lucro': lucro,
            # Usa datetime.now(timezone.utc) para criar um timestamp com fuso horário UTC
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table('operacoes').insert(data).execute()
        print(f"✅ Operação salva com sucesso - Bot: {nome_bot}, Lucro: {lucro}")
        
    except Exception as e:
        print(f"❌ Erro ao salvar operação no Supabase: {e}")
        print(f"   Bot: {nome_bot}, Lucro: {lucro}")

# 4. ESTRUTURA DAS FUNÇÕES DOS BOTS

async def bot_bk_1_0(api_manager):
    """
    Bot BK_1.0: Estratégia baseada em análise de dígitos com sistema de pausa por risco
    e martingale adaptativo
    """
    nome_bot = "BK_BOT_1.0"
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Variáveis de estado do bot
    stake_inicial = 1.0
    stop_loss = 50.0
    stop_win = 20.0
    
    # Inicialização das variáveis
    stake_atual = stake_inicial
    total_profit = 0
    loss_seguidas = 0
    pausado_por_risco = False
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    
    while True:
        try:
            # Verificar Stop Loss/Win
            if total_profit >= stop_win:
                print(f"🎉 {nome_bot}: Meta de lucro atingida! Total: ${total_profit:.2f}")
                break
            elif total_profit <= -stop_loss:
                print(f"🛑 {nome_bot}: Stop Loss ativado! Total: ${total_profit:.2f}")
                break
            
            # Obter último tick do ativo '1HZ10V' usando histórico
            ticks_history = await api_manager.ticks_history({
                "ticks_history": "1HZ10V",
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in ticks_history:
                print(f"❌ {nome_bot}: Erro ao obter ticks: {ticks_history['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            ultimo_preco = ticks_history['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_preco).replace('.', '')[-1])
            
            print(f"🔍 {nome_bot}: Último dígito: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Verificar dígito de risco (8 ou 9)
            if ultimo_digito in [8, 9]:
                if not pausado_por_risco:
                    pausado_por_risco = True
                    print(f"⚠️ {nome_bot}: Dígito de Risco Detectado ({ultimo_digito}). Pausando...")
                await asyncio.sleep(2)
                continue
            
            # Verificar se deve reativar o bot
            if pausado_por_risco and ultimo_digito < 8:
                pausado_por_risco = False
                print(f"✅ {nome_bot}: Reativando bot... (dígito: {ultimo_digito})")
                await asyncio.sleep(2)
                continue
            
            # Se ainda pausado, pular lógica de compra
            if pausado_por_risco:
                await asyncio.sleep(2)
                continue
            
            # Lógica de Compra (se não estiver pausado)
            # Definir a predição baseada nas perdas seguidas
            if loss_seguidas == 0:
                prediction = 8
            else:
                prediction = 5
            
            # Construir parâmetros da compra corretamente
            parametros_da_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_atual,
                'parameters': {
                    'amount': stake_atual,
                    'basis': 'stake',
                    'contract_type': 'DIGITUNDER',
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',
                    'symbol': '1HZ10V',
                    'barrier': prediction  # A predição aqui é chamada de 'barrier'
                }
            }
            
            print(f"📈 {nome_bot}: Comprando DIGITUNDER {prediction} | Stake: ${stake_atual:.2f}")
            
            # Fazer a compra com subscribe
            recibo_compra = await api_manager.buy(parametros_da_compra)
            
            if 'error' in recibo_compra:
                print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            
            # Aguardar o resultado final (o subscribe: 1 cuidará de enviar o resultado)
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # O recibo_compra já contém as informações do contrato
            # Extrair lucro do resultado final
            if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                contract_id = recibo_compra['buy']['contract_id']
                
                # Aguardar o resultado usando proposal_open_contract
                contract_finalizado = False
                tentativas = 0
                max_tentativas = 30  # 30 segundos máximo
                
                while not contract_finalizado and tentativas < max_tentativas:
                    await asyncio.sleep(1)
                    tentativas += 1
                    
                    try:
                        # Verificar status atual do contrato
                        contract_status = await api_manager.proposal_open_contract({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        })
                        
                        if 'error' in contract_status:
                            print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                            continue
                        
                        contract_info = contract_status['proposal_open_contract']
                        
                        if contract_info.get('is_sold', False):
                            contract_finalizado = True
                            # Extrair lucro do resultado final
                            lucro = float(contract_info.get('profit', 0))
                            stake_usado = stake_atual
                            break
                            
                    except Exception as e:
                        print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                
                if not contract_finalizado:
                    print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                    await asyncio.sleep(2)
                    continue
            else:
                print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                await asyncio.sleep(2)
                continue
            
            # Atualizar lucro total
            total_profit += lucro
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado
            if lucro > 0:
                # Vitória
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_usado:.2f} | Total: ${total_profit:.2f}")
                # Reset do stake e perdas seguidas
                stake_atual = stake_inicial
                loss_seguidas = 0
            else:
                # Derrota
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_usado:.2f} | Total: ${total_profit:.2f}")
                # Aumentar contador de perdas
                loss_seguidas += 1
                # Calcular novo stake (martingale)
                stake_atual = abs(lucro) if abs(lucro) > 0 else stake_inicial * 2
                print(f"🔄 {nome_bot}: Perdas seguidas: {loss_seguidas} | Próximo stake: ${stake_atual:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa entre operações
        await asyncio.sleep(2)

async def bot_2_digito_par(api_manager):
    """
    Bot 2: Estratégia baseada em dígitos pares
    Traduzido da lógica do arquivo .xml correspondente
    """
    nome_bot = "Digito_Par_Bot"
    print(f"🤖 Iniciando {nome_bot}...")
    
    while True:
        try:
            # TODO: Traduzir a lógica do arquivo .xml aqui
            # Ex: obter último tick, verificar se último dígito é par,
            # definir parâmetros do contrato para apostar em dígito par
            
            # Exemplo de como seria a implementação:
            # 1. Obter último tick
            # tick = await api.tick({"ticks": "R_100"})
            # ultimo_digito = int(str(tick['tick']['quote']).split('.')[-1][-1])
            # 
            # 2. Analisar padrão dos últimos dígitos
            # historico_digitos = obter_historico_digitos()
            # 
            # 3. Verificar condição de entrada
            # if deve_apostar_par(historico_digitos):
            #     contract_params = {
            #         "buy": 1,
            #         "price": 5,  # Valor da aposta
            #         "parameters": {
            #             "contract_type": "DIGITEVEN",
            #             "symbol": "R_100",
            #             "duration": 1,
            #             "duration_unit": "t"
            #         }
            #     }
            
            # Exemplo de como a compra e o registro seriam feitos:
            # contrato = await api.buy(contract_params)
            # resultado = await contrato.result
            # lucro_real = resultado['profit']
            # print(f"Bot '{nome_bot}': Resultado = {lucro_real}")
            # salvar_operacao(nome_bot, lucro_real)
            
            # Simulação para teste (remover quando implementar a lógica real)
            print(f"🔄 {nome_bot}: Analisando padrão de dígitos...")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Aguardar 5 segundos antes da próxima análise
        await asyncio.sleep(5)

async def bot_factor_50x(api_manager):
    """
    Bot Factor50X - Conservador
    # Estratégia com stake fixo para evitar limites de stake
    Estratégia: Aguarda dígito 1 no R_100 para comprar DIGITOVER 3
    """
    # Definir parâmetros fixos
    nome_bot = "Factor50X_Conservador"
    stake_inicial = 1.0
    stop_loss = 8.5
    stop_win = 4.0
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"🤖 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake fixo: ${stake_inicial}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   📊 Estratégia: Stake fixo (sem martingale)")
    print(f"   🏪 Mercado: R_100")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            if total_profit >= stop_win:
                print(f"🎯 {nome_bot}: META ATINGIDA! Profit: ${total_profit:.2f} >= ${stop_win}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            elif total_profit <= -stop_loss:
                print(f"🛑 {nome_bot}: STOP LOSS ATINGIDO! Profit: ${total_profit:.2f} <= ${-stop_loss}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            
            # Análise do Último Dígito
            # Obter último tick do ativo R_100
            tick_response = await api_manager.ticks_history({
                "ticks_history": "R_100",
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"❌ {nome_bot}: Erro ao obter tick: {tick_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Extrair o último dígito do preço
            ultimo_tick = tick_response['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"🔍 {nome_bot}: Último dígito R_100: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Condição de Compra: Se o último dígito for EXATAMENTE 1
            if ultimo_digito == 1:
                print(f"🎯 {nome_bot}: Dígito 1 detectado! Preparando para comprar DIGITOVER 3.")
                
                # Construir parâmetros da compra
                parametros_da_compra = {
                    'buy': '1',
                    'subscribe': 1,
                    'price': stake_atual,
                    'parameters': {
                        'amount': stake_atual,
                        'basis': 'stake',
                        'contract_type': 'DIGITOVER',
                        'currency': 'USD',
                        'duration': 1,
                        'duration_unit': 't',
                        'symbol': 'R_100',
                        'barrier': 3
                    }
                }
                
                print(f"📈 {nome_bot}: Comprando DIGITOVER 3 | Stake: ${stake_atual:.2f}")
                
                # Fazer a compra com subscribe
                recibo_compra = await api_manager.buy(parametros_da_compra)
                
                if 'error' in recibo_compra:
                    print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                    await asyncio.sleep(1)
                    continue
                
                print(f"📋 {nome_bot}: Contrato criado com sucesso!")
                
                # Aguardar o resultado final
                print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
                
                # Obter contract_id e aguardar resultado
                if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                    contract_id = recibo_compra['buy']['contract_id']
                    
                    # Aguardar o resultado usando proposal_open_contract
                    contract_finalizado = False
                    tentativas = 0
                    max_tentativas = 30  # 30 segundos máximo
                    
                    while not contract_finalizado and tentativas < max_tentativas:
                        await asyncio.sleep(1)
                        tentativas += 1
                        
                        try:
                            # Verificar status atual do contrato
                            contract_status = await api_manager.proposal_open_contract({
                                "proposal_open_contract": 1,
                                "contract_id": contract_id
                            })
                            
                            if 'error' in contract_status:
                                print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                                continue
                            
                            contract_info = contract_status['proposal_open_contract']
                            
                            if contract_info.get('is_sold', False):
                                contract_finalizado = True
                                # Extrair lucro do resultado final
                                lucro = float(contract_info.get('profit', 0))
                                break
                                
                        except Exception as e:
                            print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                    
                    if not contract_finalizado:
                        print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                        await asyncio.sleep(1)
                        continue
                else:
                    print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                    await asyncio.sleep(1)
                    continue
                
                # Atualizar total_profit
                total_profit += lucro
                
                # Salvar operação
                salvar_operacao(nome_bot, lucro)
                
                # Tratamento do resultado
                if lucro > 0:
                    # Vitória - Stake continua fixo
                    print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake fixo: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                    stake_atual = stake_inicial  # Mantém stake fixo
                else:
                    # Derrota - Stake continua fixo (sem martingale)
                    print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake fixo: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                    stake_atual = stake_inicial  # Mantém stake fixo
                    print(f"📊 {nome_bot}: Próxima aposta mantém stake fixo: ${stake_atual:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final - checar mercado a cada segundo
        await asyncio.sleep(1)

async def bot_ai_2_0(api_manager):
    """
    BotAI 2.0 - Estratégia de Compra Contínua com Martingale
    Compra DIGITOVER 0 no R_100 continuamente (alta probabilidade)
    """
    # Definir parâmetros fixos
    nome_bot = "BotAI_2.0"
    stake_inicial = 1.0
    stop_loss = 100.0
    stop_win = 50.0
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"🤖 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   🔄 Estratégia: Compra contínua DIGITOVER 0")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            if total_profit >= stop_win:
                print(f"🎯 {nome_bot}: META ATINGIDA! Profit: ${total_profit:.2f} >= ${stop_win}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            elif total_profit <= -stop_loss:
                print(f"🛑 {nome_bot}: STOP LOSS ATINGIDO! Profit: ${total_profit:.2f} <= ${-stop_loss}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            
            # Lógica de Compra (Compra Contínua)
            print(f"🔄 {nome_bot}: Iniciando nova compra contínua | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Construir parâmetros da compra
            parametros_da_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_atual,
                'parameters': {
                    'amount': stake_atual,
                    'basis': 'stake',
                    'contract_type': 'DIGITOVER',
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',
                    'symbol': 'R_100',
                    'barrier': 0
                }
            }
            
            print(f"📈 {nome_bot}: Comprando DIGITOVER 0 | Stake: ${stake_atual:.2f}")
            
            # Fazer a compra com subscribe
            recibo_compra = await api_manager.buy(parametros_da_compra)
            
            if 'error' in recibo_compra:
                print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            
            # Aguardar o resultado final
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Obter contract_id e aguardar resultado
            if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                contract_id = recibo_compra['buy']['contract_id']
                
                # Aguardar o resultado usando proposal_open_contract
                contract_finalizado = False
                tentativas = 0
                max_tentativas = 30  # 30 segundos máximo
                
                while not contract_finalizado and tentativas < max_tentativas:
                    await asyncio.sleep(1)
                    tentativas += 1
                    
                    try:
                        # Verificar status atual do contrato
                        contract_status = await api_manager.proposal_open_contract({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        })
                        
                        if 'error' in contract_status:
                            print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                            continue
                        
                        contract_info = contract_status['proposal_open_contract']
                        
                        if contract_info.get('is_sold', False):
                            contract_finalizado = True
                            # Extrair lucro do resultado final
                            lucro = float(contract_info.get('profit', 0))
                            break
                            
                    except Exception as e:
                        print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                
                if not contract_finalizado:
                    print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                    await asyncio.sleep(1)
                    continue
            else:
                print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                await asyncio.sleep(1)
                continue
            
            # Atualizar total_profit
            total_profit += lucro
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado
            if lucro > 0:
                # Vitória - Reset stake
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                stake_atual = stake_inicial
            else:
                # Derrota - Calcular novo stake com Martingale simples
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                stake_atual = abs(lucro)
                print(f"🔄 {nome_bot}: Novo stake: ${stake_atual:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final - ritmo rápido entre operações
        await asyncio.sleep(1)

async def bot_apalancamiento(api_manager):
    """
    Bot del Apalancamiento - Estratégia com Alternância e Stake Fixo
    Alterna entre DIGITUNDER e DIGITOVER a cada 100 trades (sem martingale)
    """
    # Definir parâmetros fixos
    nome_bot = "Bot_Apalancamiento"
    stake_inicial = 1.0
    stop_loss = 10.0
    stop_win = 10.0
    limite_trades_para_troca = 100
    
    # Inicializar variáveis de estado
    total_profit = 0
    trades_counter = 0
    
    print(f"🤖 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake fixo: ${stake_inicial}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   📊 Estratégia: Stake fixo (sem martingale)")
    print(f"   🔀 Troca estratégia a cada: {limite_trades_para_troca} trades")
    print(f"   🏪 Mercado: 1HZ75V")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            if total_profit >= stop_win:
                print(f"🎯 {nome_bot}: META ATINGIDA! Profit: ${total_profit:.2f} >= ${stop_win}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            elif total_profit <= -stop_loss:
                print(f"🛑 {nome_bot}: STOP LOSS ATINGIDO! Profit: ${total_profit:.2f} <= ${-stop_loss}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            
            # Definir a Estratégia (Alternância)
            estrategia_atual = (trades_counter // limite_trades_para_troca) % 2
            if estrategia_atual == 0:
                contract_type = "DIGITUNDER"
                estrategia_nome = "UNDER"
                prediction = 9  # Sempre 9 para DIGITUNDER
            else:
                contract_type = "DIGITOVER"
                estrategia_nome = "OVER"
                prediction = 0  # Sempre 0 para DIGITOVER
            
            print(f"🔍 {nome_bot}: Trade #{trades_counter + 1} | Estratégia: {estrategia_nome} | Predição: {prediction}")
            print(f"📊 {nome_bot}: Profit: ${total_profit:.2f} | Stake fixo: ${stake_inicial:.2f}")
            
            # Lógica de Compra
            parametros_da_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_inicial,
                'parameters': {
                    'amount': stake_inicial,
                    'basis': 'stake',
                    'contract_type': contract_type,
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',
                    'symbol': '1HZ75V',
                    'barrier': prediction
                }
            }
            
            print(f"📈 {nome_bot}: Comprando {contract_type} {prediction} | Stake fixo: ${stake_inicial:.2f}")
            
            # Fazer a compra com subscribe
            recibo_compra = await api_manager.buy(parametros_da_compra)
            
            if 'error' in recibo_compra:
                print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            
            # Aguardar o resultado final
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Obter contract_id e aguardar resultado
            if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                contract_id = recibo_compra['buy']['contract_id']
                
                # Aguardar o resultado usando proposal_open_contract
                contract_finalizado = False
                tentativas = 0
                max_tentativas = 30  # 30 segundos máximo
                
                while not contract_finalizado and tentativas < max_tentativas:
                    await asyncio.sleep(1)
                    tentativas += 1
                    
                    try:
                        # Verificar status atual do contrato
                        contract_status = await api_manager.proposal_open_contract({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        })
                        
                        if 'error' in contract_status:
                            print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                            continue
                        
                        contract_info = contract_status['proposal_open_contract']
                        
                        if contract_info.get('is_sold', False):
                            contract_finalizado = True
                            # Extrair lucro do resultado final
                            lucro = float(contract_info.get('profit', 0))
                            break
                            
                    except Exception as e:
                        print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                
                if not contract_finalizado:
                    print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                    await asyncio.sleep(1)
                    continue
            else:
                print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                await asyncio.sleep(1)
                continue
            
            # Após a Compra - Incrementar contador
            trades_counter += 1
            
            # Atualizar total_profit
            total_profit += lucro
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado (stake sempre fixo)
            if lucro > 0:
                # Vitória - Stake continua fixo
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake fixo: ${stake_inicial:.2f} | Total: ${total_profit:.2f}")
            else:
                # Derrota - Stake continua fixo (sem martingale)
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake fixo: ${stake_inicial:.2f} | Total: ${total_profit:.2f}")
                print(f"📊 {nome_bot}: Próxima aposta mantém stake fixo: ${stake_inicial:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final - checar mercado a cada segundo
        await asyncio.sleep(1)

async def wolf_bot_2_0(api_manager):
    """
    Wolf Bot 2.0 - Estratégia de Mão Fixa sem Limites de Stop
    Baseado no último dígito do R_100 e resultado da operação anterior
    """
    # Definir parâmetros fixos
    nome_bot = "Wolf_Bot_2.0"
    stake_fixo = 1.0  # Corrigido para valor mínimo válido
    
    # Inicializar variável de estado
    ultimo_resultado = "vitoria"  # Primeira operação será conservadora
    
    print(f"🐺 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake fixo: ${stake_fixo}")
    print(f"   🏪 Mercado: R_100")
    print(f"   ⏱️ Duração: 1 tick")
    print(f"   🎯 Estratégia: Mão fixa baseada em último dígito")
    print(f"   🚫 Sem limites de stop")
    print(f"   🔄 Estado inicial: {ultimo_resultado}")
    print(f"   📈 Predições ajustadas para compatibilidade com Deriv")
    
    while True:
        try:
            # Análise do Último Dígito do R_100
            print(f"🔍 {nome_bot}: Obtendo último dígito do R_100...")
            
            # Obter ticks do R_100
            ticks_response = await api_manager.ticks_history({
                'ticks_history': 'R_100',
                'adjust_start_time': 1,
                'count': 1,
                'end': 'latest',
                'start': 1,
                'style': 'ticks'
            })
            
            if 'error' in ticks_response:
                print(f"❌ {nome_bot}: Erro ao obter ticks: {ticks_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Extrair último dígito
            ultimo_tick = ticks_response['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_tick).replace('.', '')[-1])
            
            print(f"📊 {nome_bot}: Último dígito: {ultimo_digito} | Último resultado: {ultimo_resultado}")
            
            # Definir Parâmetros da Compra
            contract_type = None
            prediction = None
            
            # Lógica de entrada baseada no último dígito
            if ultimo_digito == 4:
                contract_type = 'DIGITUNDER'
                if ultimo_resultado == "vitoria":
                    prediction = 7  # Ajustado de 8 para 7 (conservadora compatível)
                    estrategia_tipo = "conservadora"
                else:  # ultimo_resultado == "derrota"
                    prediction = 2  # Mantido (agressiva)
                    estrategia_tipo = "agressiva"
                print(f"🎯 {nome_bot}: Dígito 4 detectado! UNDER {prediction} ({estrategia_tipo} - resultado anterior: {ultimo_resultado})")
                
            elif ultimo_digito == 6 and ultimo_resultado == "derrota":
                contract_type = 'DIGITOVER'
                prediction = 3  # Ajustado de 2 para 3 (conservadora compatível)
                estrategia_tipo = "conservadora após derrota"
                print(f"🎯 {nome_bot}: Dígito 6 + derrota anterior! OVER {prediction} ({estrategia_tipo})")
            
            # Lógica de Compra
            if contract_type is not None:
                print(f"📈 {nome_bot}: Condição de entrada atingida!")
                
                # Construir dicionário de compra
                parametros_da_compra = {
                    'buy': '1',
                    'subscribe': 1,
                    'price': stake_fixo,
                    'parameters': {
                        'amount': stake_fixo,
                        'basis': 'stake',
                        'contract_type': contract_type,
                        'currency': 'USD',
                        'duration': 1,
                        'duration_unit': 't',
                        'symbol': 'R_100',
                        'barrier': prediction
                    }
                }
                
                print(f"🛒 {nome_bot}: Comprando {contract_type} {prediction} | Stake: ${stake_fixo} | Tipo: {estrategia_tipo}")
                
                # Executar a compra
                recibo_compra = await api_manager.buy(parametros_da_compra)
                
                if 'error' in recibo_compra:
                    print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                    await asyncio.sleep(1)
                    continue
                
                print(f"📋 {nome_bot}: Contrato criado com sucesso!")
                
                # Aguardar o resultado final
                print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
                
                # Obter contract_id e aguardar resultado
                if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                    contract_id = recibo_compra['buy']['contract_id']
                    
                    # Aguardar o resultado usando proposal_open_contract
                    contract_finalizado = False
                    tentativas = 0
                    max_tentativas = 30  # 30 segundos máximo
                    
                    while not contract_finalizado and tentativas < max_tentativas:
                        await asyncio.sleep(1)
                        tentativas += 1
                        
                        try:
                            # Verificar status atual do contrato
                            contract_status = await api_manager.proposal_open_contract({
                                "proposal_open_contract": 1,
                                "contract_id": contract_id
                            })
                            
                            if 'error' in contract_status:
                                print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                                continue
                            
                            contract_info = contract_status['proposal_open_contract']
                            
                            if contract_info.get('is_sold', False):
                                contract_finalizado = True
                                # Extrair lucro do resultado final
                                lucro = float(contract_info.get('profit', 0))
                                break
                                
                        except Exception as e:
                            print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                    
                    if not contract_finalizado:
                        print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                        await asyncio.sleep(1)
                        continue
                else:
                    print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                    await asyncio.sleep(1)
                    continue
                
                # Após a Compra - Salvar operação
                salvar_operacao(nome_bot, lucro)
                
                # Atualizar estado baseado no resultado
                if lucro > 0:
                    # Vitória
                    ultimo_resultado = "vitoria"
                    print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Próxima estratégia: conservadora (UNDER 7 / OVER 3)")
                else:
                    # Derrota
                    ultimo_resultado = "derrota"
                    print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Próxima estratégia: agressiva (UNDER 2)")
                
                print(f"🔄 {nome_bot}: Estado atualizado para: {ultimo_resultado}")
                
            else:
                # Nenhuma condição de entrada atingida
                print(f"⏸️ {nome_bot}: Aguardando condições de entrada...")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final
        await asyncio.sleep(1)

# 4.10. TIP BOT - ESTRATÉGIA DE COMPRA CONTÍNUA
async def bot_tip(api_manager):
    """
    Tip_Bot - Estratégia de compra contínua no ativo R_75
    com Martingale agressivo (fator 2.0) e sem análise de mercado
    """
    nome_bot = "Tip_Bot"
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Parâmetros de gestão
    stake_inicial = 1.0
    martingale_fator = 2.0
    stop_loss = float('inf')  # ilimitado
    stop_win = float('inf')   # ilimitado
    
    # Variáveis de estado do bot
    stake_atual = stake_inicial
    total_profit = 0.0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   📈 Fator martingale: {martingale_fator}")
    print(f"   🏪 Ativo: R_75")
    print(f"   ⏱️ Duração: 1 tick")
    print(f"   🎯 Estratégia: Compra contínua DIGITOVER 0")
    
    while True:
        try:
            # Execução do Trade (Compra Contínua)
            print(f"🛒 {nome_bot}: Comprando DIGITOVER 0 | Stake: ${stake_atual:.2f}")
            print(f"💰 {nome_bot}: Total profit atual: ${total_profit:.2f}")
            
            # Criar proposta
            proposta = {
                "proposal": 1,
                "amount": stake_atual,
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "symbol": "R_75",
                "duration": 1,
                "duration_unit": "t",
                "barrier": "0"
            }
            
            response = await api_manager.proposal(proposta)
            
            if 'error' in response:
                print(f"❌ {nome_bot}: Erro na proposta: {response['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            # Comprar o contrato
            buy_response = await api_manager.buy({"buy": response['proposal']['id'], "price": stake_atual})
            
            if 'error' in buy_response:
                print(f"❌ {nome_bot}: Erro na compra: {buy_response['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Aguardar o resultado usando proposal_open_contract
            contract_finalizado = False
            tentativas = 0
            max_tentativas = 30  # 30 segundos máximo
            
            while not contract_finalizado and tentativas < max_tentativas:
                await asyncio.sleep(1)
                tentativas += 1
                
                try:
                    # Verificar status atual do contrato
                    contract_status = await api_manager.proposal_open_contract({
                        "proposal_open_contract": 1,
                        "contract_id": contract_id
                    })
                    
                    if 'error' in contract_status:
                        print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                        continue
                    
                    contract_info = contract_status['proposal_open_contract']
                    
                    if contract_info.get('is_sold', False):
                        contract_finalizado = True
                        # Extrair lucro do resultado final
                        lucro = float(contract_info.get('profit', 0))
                        break
                        
                except Exception as e:
                    print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
            
            if not contract_finalizado:
                print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                await asyncio.sleep(2)
                continue
            
            # Lógica Pós-Trade (Martingale Agressivo)
            total_profit += lucro
            salvar_operacao(nome_bot, lucro)
            
            if lucro > 0:
                # Vitória
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                # Resetar para stake inicial
                stake_atual = stake_inicial
                print(f"🔄 {nome_bot}: Resetando stake para ${stake_inicial:.2f}")
            else:
                # Derrota
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                # Martingale agressivo: multiplicar por 2.0
                stake_atual = stake_atual * martingale_fator
                print(f"📈 {nome_bot}: Novo stake (Martingale x{martingale_fator}): ${stake_atual:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
            print(f"⏸️ {nome_bot}: Aguardando 10 segundos antes de tentar novamente...")
            await asyncio.sleep(10)
        
        # Pausa entre operações contínuas
        await asyncio.sleep(2)

async def bot_sniper_martingale(api_manager):
    """
    Sniper Bot (Martingale) - Estratégia com Indicadores SMA e Sistema Martingale
    Opera com base na Média Móvel Simples e aplica martingale após perdas
    """
    # Definir parâmetros iniciais
    nome_bot = "Sniper_Bot_Martingale"
    stake_inicial = 1.0
    stake_atual = stake_inicial
    martingale_fator = 1.05
    stop_loss = 100000000.0  # Stop muito alto para operação contínua
    stop_win = 100000000.0   # Stop muito alto para operação contínua
    ativo = '1HZ100V'
    periodo_sma = 3
    duracao_contrato = 1
    
    # Inicializar variáveis de controle
    total_profit = 0
    
    print(f"🎯 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Fator martingale: {martingale_fator}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   🏪 Ativo: {ativo}")
    print(f"   📈 Período SMA: {periodo_sma}")
    print(f"   ⏱️ Duração: {duracao_contrato} tick")
    print(f"   🎲 Estratégia: SMA com Martingale")
    
    while True:
        try:
            # Verificar Stops no início do loop
            if total_profit >= stop_win:
                print(f"🎯 {nome_bot}: STOP WIN ATINGIDO! Profit: ${total_profit:.2f} >= ${stop_win}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            elif total_profit <= -stop_loss:
                print(f"🛑 {nome_bot}: STOP LOSS ATINGIDO! Profit: ${total_profit:.2f} <= ${-stop_loss}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            
            # Obter Dados e Calcular Indicador SMA
            print(f"🔍 {nome_bot}: Obtendo dados para cálculo da SMA...")
            
            # Obter histórico de ticks
            ticks_response = await api_manager.ticks_history({
                'ticks_history': ativo,
                'adjust_start_time': 1,
                'count': periodo_sma,
                'end': 'latest',
                'start': 1,
                'style': 'ticks'
            })
            
            if 'error' in ticks_response:
                print(f"❌ {nome_bot}: Erro ao obter ticks: {ticks_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Extrair preços dos ticks
            precos = ticks_response['history']['prices']
            
            if len(precos) < periodo_sma:
                print(f"⚠️ {nome_bot}: Dados insuficientes para SMA. Aguardando...")
                await asyncio.sleep(1)
                continue
            
            # Calcular Média Móvel Simples (SMA)
            sma = sum(precos) / len(precos)
            ultimo_preco = precos[-1]
            
            print(f"📊 {nome_bot}: Último preço: {ultimo_preco:.5f} | SMA({periodo_sma}): {sma:.5f}")
            print(f"💰 {nome_bot}: Stake atual: ${stake_atual:.2f} | Total profit: ${total_profit:.2f}")
            
            # Determinar Ação (Condição de Entrada)
            contract_type = None
            
            if ultimo_preco > sma:
                contract_type = 'CALL'
                direcao = "ALTA"
                print(f"📈 {nome_bot}: Preço ACIMA da SMA → Sinal de CALL")
            elif ultimo_preco < sma:
                contract_type = 'PUT'
                direcao = "BAIXA"
                print(f"📉 {nome_bot}: Preço ABAIXO da SMA → Sinal de PUT")
            
            # Se nenhuma condição atingida, aguardar
            if contract_type is None:
                print(f"⏸️ {nome_bot}: Aguardando condição de entrada...")
                await asyncio.sleep(1)
                continue
            
            # Executar Compra
            print(f"🎯 {nome_bot}: Condição de entrada atingida! Executando {contract_type}")
            
            # Arredondar o valor do stake para duas casas decimais
            stake_atual = round(stake_atual, 2)
            
            # Construir parâmetros da compra
            parametros_da_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_atual,
                'parameters': {
                    'amount': stake_atual,
                    'basis': 'stake',
                    'contract_type': contract_type,
                    'currency': 'USD',
                    'duration': duracao_contrato,
                    'duration_unit': 't',
                    'symbol': ativo
                }
            }
            
            print(f"🛒 {nome_bot}: Comprando {contract_type} | Stake: ${stake_atual:.2f} | Direção: {direcao}")
            
            # Executar a compra com tratamento de erro
            recibo_compra = await api_manager.buy(parametros_da_compra)
            
            if 'error' in recibo_compra:
                error_msg = recibo_compra['error']['message']
                # Verificar se o erro é relacionado ao limite de stake
                if 'more than the maximum purchase price' in error_msg:
                    print(f"⚠️  {nome_bot}: Stake de ${stake_atual:.2f} excedeu o limite da corretora. Resetando para o valor inicial.")
                    stake_atual = stake_inicial
                    continue
                else:
                    print(f"❌ {nome_bot}: Erro na compra: {error_msg}")
                    await asyncio.sleep(1)
                    continue
            
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            
            # Aguardar o resultado final
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Obter contract_id e aguardar resultado
            if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                contract_id = recibo_compra['buy']['contract_id']
                
                # Aguardar o resultado usando proposal_open_contract
                contract_finalizado = False
                tentativas = 0
                max_tentativas = 30  # 30 segundos máximo
                
                while not contract_finalizado and tentativas < max_tentativas:
                    await asyncio.sleep(1)
                    tentativas += 1
                    
                    try:
                        # Verificar status atual do contrato
                        contract_status = await api_manager.proposal_open_contract({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        })
                        
                        if 'error' in contract_status:
                            print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                            continue
                        
                        contract_info = contract_status['proposal_open_contract']
                        
                        if contract_info.get('is_sold', False):
                            contract_finalizado = True
                            # Extrair lucro do resultado final
                            lucro = float(contract_info.get('profit', 0))
                            break
                            
                    except Exception as e:
                        print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                
                if not contract_finalizado:
                    print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                    await asyncio.sleep(1)
                    continue
            else:
                print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                await asyncio.sleep(1)
                continue
            
            # Tratamento do Resultado (com Martingale)
            total_profit += lucro
            salvar_operacao(nome_bot, lucro)
            
            if lucro > 0:
                # Vitória - Reset stake
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Total: ${total_profit:.2f}")
                print(f"🔄 {nome_bot}: Resetando stake para inicial: ${stake_inicial:.2f}")
                stake_atual = stake_inicial
            else:
                # Derrota - Aplicar Martingale
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Total: ${total_profit:.2f}")
                novo_stake = abs(lucro) * martingale_fator
                print(f"🔄 {nome_bot}: Aplicando martingale: ${stake_atual:.2f} → ${novo_stake:.2f}")
                stake_atual = novo_stake
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final
        await asyncio.sleep(1)

async def bot_quantum_fixed_stake(api_manager):
    """
    QuantumBot_FixedStake - Bot de dígitos com stake fixo
    Opera com contratos DIGITDIFF no ativo R_100 com predições aleatórias
    """
    # Definir parâmetros iniciais
    nome_bot = "QuantumBot_FixedStake"
    stake_fixo = 1.0
    stop_loss = 50.0
    stop_win = 25.0
    
    # Inicializar variáveis de controle
    total_profit = 0
    
    print(f"🎯 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake fixo: ${stake_fixo}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   🏪 Ativo: R_100")
    print(f"   🎲 Estratégia: DIGITDIFF com predições aleatórias")
    print(f"   ⏱️ Duração: 1 tick")
    
    while True:
        try:
            # Verificar Stops no início do loop
            if total_profit >= stop_win:
                print(f"🎯 {nome_bot}: STOP WIN ATINGIDO! Profit: ${total_profit:.2f} >= ${stop_win}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            elif total_profit <= -stop_loss:
                print(f"🛑 {nome_bot}: STOP LOSS ATINGIDO! Profit: ${total_profit:.2f} <= ${-stop_loss}")
                salvar_operacao(nome_bot, 0)  # Registro final
                break
            
            # Gerar predição aleatória (dígito entre 0 e 9)
            predicao_aleatoria = random.randint(0, 9)
            
            print(f"🎲 {nome_bot}: Predição aleatória: {predicao_aleatoria} | Total profit: ${total_profit:.2f}")
            print(f"🎯 {nome_bot}: Apostando que o último dígito será DIFERENTE de {predicao_aleatoria}")
            
            # Construir parâmetros da compra
            parametros_da_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_fixo,
                'parameters': {
                    'amount': stake_fixo,
                    'basis': 'stake',
                    'contract_type': 'DIGITDIFF',
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',
                    'symbol': 'R_100',
                    'barrier': predicao_aleatoria
                }
            }
            
            print(f"🛒 {nome_bot}: Comprando DIGITDIFF (diferente de {predicao_aleatoria}) | Stake: ${stake_fixo:.2f}")
            
            # Executar a compra
            recibo_compra = await api_manager.buy(parametros_da_compra)
            
            if 'error' in recibo_compra:
                print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            
            # Aguardar o resultado final
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Obter contract_id e aguardar resultado
            if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                contract_id = recibo_compra['buy']['contract_id']
                
                # Aguardar o resultado usando proposal_open_contract
                contract_finalizado = False
                tentativas = 0
                max_tentativas = 30  # 30 segundos máximo
                
                while not contract_finalizado and tentativas < max_tentativas:
                    await asyncio.sleep(1)
                    tentativas += 1
                    
                    try:
                        # Verificar status atual do contrato
                        contract_status = await api_manager.proposal_open_contract({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        })
                        
                        if 'error' in contract_status:
                            print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                            continue
                        
                        contract_info = contract_status['proposal_open_contract']
                        
                        if contract_info.get('is_sold', False):
                            contract_finalizado = True
                            # Extrair lucro do resultado final
                            lucro = float(contract_info.get('profit', 0))
                            break
                            
                    except Exception as e:
                        print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                
                if not contract_finalizado:
                    print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                    await asyncio.sleep(1)
                    continue
            else:
                print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
                await asyncio.sleep(1)
                continue
            
            # Tratamento do Resultado (sem Martingale - stake sempre fixo)
            total_profit += lucro
            salvar_operacao(nome_bot, lucro)
            
            if lucro > 0:
                # Vitória
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Total: ${total_profit:.2f}")
                print(f"🔄 {nome_bot}: Mantendo stake fixo: ${stake_fixo:.2f}")
            else:
                # Derrota
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Total: ${total_profit:.2f}")
                print(f"🔄 {nome_bot}: Mantendo stake fixo: ${stake_fixo:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final
        await asyncio.sleep(1)

# 4.9. BOT ALFA - ESTRATÉGIA ADAPTATIVA COM PAUSA POR RISCO
async def bot_alfa(api_manager):
    """
    Alfa_Bot - Estratégia baseada no ativo 1HZ10V com pausa por risco
    e predição adaptativa baseada no número de perdas seguidas
    """
    nome_bot = "Alfa_Bot"
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Parâmetros de gestão
    stake_inicial = 1.0
    martingale_fator = 1.05
    stop_loss = float('inf')  # ilimitado
    stop_win = float('inf')   # ilimitado
    
    # Variáveis de estado do bot
    stake_atual = stake_inicial
    total_profit = 0.0
    loss_seguidas = 0
    pausado = False
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   📈 Fator martingale: {martingale_fator}")
    print(f"   🏪 Ativo: 1HZ10V")
    print(f"   ⏱️ Duração: 1 tick")
    print(f"   🎯 Estratégia: Predição adaptativa com pausa por risco")
    
    while True:
        try:
            # Obter último dígito do ativo 1HZ10V usando histórico
            ticks_history = await api_manager.ticks_history({
                "ticks_history": "1HZ10V",
                "count": 1,
                "end": "latest"
            })
            
            # Verificar se há erro na resposta
            if not ticks_history or 'error' in ticks_history:
                error_msg = ticks_history.get('error', {}).get('message', 'Erro desconhecido') if ticks_history else 'Resposta vazia'
                print(f"❌ {nome_bot}: Erro ao obter histórico: {error_msg}")
                await asyncio.sleep(1)
                continue
            
            # Verificar se a resposta contém dados válidos
            if 'history' not in ticks_history or 'prices' not in ticks_history['history'] or not ticks_history['history']['prices']:
                print(f"⚠️ {nome_bot}: Dados de histórico não disponíveis, aguardando...")
                await asyncio.sleep(1)
                continue
            
            # Extrair último dígito de forma segura
            ultimo_preco = ticks_history['history']['prices'][-1]
            if ultimo_preco is None:
                print(f"⚠️ {nome_bot}: Preço não disponível, aguardando...")
                await asyncio.sleep(1)
                continue
                
            ultimo_digito = int(str(ultimo_preco).replace('.', '')[-1])
            print(f"🔍 {nome_bot}: Último dígito 1HZ10V: {ultimo_digito}")
            
            # Estratégia de Entrada (com Pausa por Risco)
            if ultimo_digito in [8, 9]:
                if not pausado:
                    print(f"⏸️ {nome_bot}: Dígito {ultimo_digito} detectado! Entrando em modo PAUSA por risco")
                    pausado = True
                else:
                    print(f"⏸️ {nome_bot}: Ainda em pausa (dígito {ultimo_digito})")
                await asyncio.sleep(1)
                continue
            else:
                if pausado:
                    print(f"▶️ {nome_bot}: Dígito {ultimo_digito} < 8 detectado! Saindo do modo pausa")
                    pausado = False
            
            # Lógica da Predição (Barrier) - Adaptativa por Nível de Perda
            if loss_seguidas == 0:
                prediction = 8
            elif loss_seguidas < 3:  # 1 ou 2 perdas
                prediction = 5
            else:  # 3 ou mais perdas
                prediction = 7
            
            print(f"🎯 {nome_bot}: Perdas seguidas: {loss_seguidas} → Predição: DIGITUNDER {prediction}")
            print(f"💰 {nome_bot}: Stake atual: ${stake_atual:.2f} | Total profit: ${total_profit:.2f}")
            
            # Execução do Trade
            print(f"🛒 {nome_bot}: Comprando DIGITUNDER {prediction} | Stake: ${stake_atual:.2f}")
            
            # Criar proposta
            proposta = {
                "proposal": 1,
                "amount": stake_atual,
                "basis": "stake",
                "contract_type": "DIGITUNDER",
                "currency": "USD",
                "symbol": "1HZ10V",
                "duration": 1,
                "duration_unit": "t",
                "barrier": str(prediction)
            }
            
            response = await api_manager.proposal(proposta)
            
            if 'error' in response:
                print(f"❌ {nome_bot}: Erro na proposta: {response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Comprar o contrato
            buy_response = await api_manager.buy({"buy": response['proposal']['id'], "price": stake_atual})
            
            if 'error' in buy_response:
                print(f"❌ {nome_bot}: Erro na compra: {buy_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Aguardar o resultado usando proposal_open_contract
            contract_finalizado = False
            tentativas = 0
            max_tentativas = 30  # 30 segundos máximo
            
            while not contract_finalizado and tentativas < max_tentativas:
                await asyncio.sleep(1)
                tentativas += 1
                
                try:
                    # Verificar status atual do contrato
                    contract_status = await api_manager.proposal_open_contract({
                        "proposal_open_contract": 1,
                        "contract_id": contract_id
                    })
                    
                    if 'error' in contract_status:
                        print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                        continue
                    
                    contract_info = contract_status['proposal_open_contract']
                    
                    if contract_info.get('is_sold', False):
                        contract_finalizado = True
                        # Extrair lucro do resultado final
                        lucro = float(contract_info.get('profit', 0))
                        break
                        
                except Exception as e:
                    print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
            
            if not contract_finalizado:
                print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                await asyncio.sleep(1)
                continue
            
            # Lógica Pós-Trade (Martingale)
            total_profit += lucro
            salvar_operacao(nome_bot, lucro)
            
            if lucro > 0:
                # Vitória
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                # Resetar para valores iniciais
                stake_atual = stake_inicial
                loss_seguidas = 0
                print(f"🔄 {nome_bot}: Resetando stake para ${stake_inicial:.2f} e perdas seguidas para 0")
            else:
                # Derrota
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                # Incrementar perdas seguidas e calcular novo stake
                loss_seguidas += 1
                stake_atual = abs(lucro) * martingale_fator
                print(f"📈 {nome_bot}: Perdas seguidas: {loss_seguidas} | Novo stake: ${stake_atual:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
        
        # Pausa final
        await asyncio.sleep(2)

# 4.11. BOT XTREME - ESTRATÉGIA ULTRA AGRESSIVA COM MARTINGALE X10
async def bot_xtreme(api_manager):
    """
    XtremeBot - Bot ultra agressivo com Martingale x10
    Opera apenas quando último dígito do R_100 for exatamente 5
    Contrato DIGITDIFF com predição fixa 3
    """
    nome_bot = "XtremeBot"
    print(f"🔥 Iniciando {nome_bot}...")
    
    # Parâmetros de gestão
    stake_inicial = 1.0
    martingale_fator = 10.0  # Martingale ultra agressivo x10
    stop_loss = float('inf')  # ilimitado
    stop_win = float('inf')   # ilimitado
    
    # Variáveis de estado do bot
    stake_atual = stake_inicial
    total_profit = 0.0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🚀 Fator martingale: {martingale_fator}x (ULTRA AGRESSIVO)")
    print(f"   🏪 Ativo: R_100")
    print(f"   🎯 Condição de entrada: Último dígito = 5")
    print(f"   📋 Contrato: DIGITDIFF")
    print(f"   🎲 Predição fixa: 3")
    print(f"   ⏱️ Duração: 1 tick")
    
    while True:
        try:
            # Obter último dígito do ativo R_100 usando histórico
            ticks_history = await api_manager.ticks_history({
                "ticks_history": "R_100",
                "count": 1,
                "end": "latest"
            })
            
            # Verificar se há erro na resposta
            if not ticks_history or 'error' in ticks_history:
                error_msg = ticks_history.get('error', {}).get('message', 'Erro desconhecido') if ticks_history else 'Resposta vazia'
                print(f"❌ {nome_bot}: Erro ao obter histórico: {error_msg}")
                await asyncio.sleep(1)
                continue
            
            # Verificar se a resposta contém dados válidos
            if 'history' not in ticks_history or 'prices' not in ticks_history['history'] or not ticks_history['history']['prices']:
                print(f"⚠️ {nome_bot}: Dados de histórico não disponíveis, aguardando...")
                await asyncio.sleep(1)
                continue
            
            # Extrair último dígito de forma segura
            ultimo_preco = ticks_history['history']['prices'][-1]
            if ultimo_preco is None:
                print(f"⚠️ {nome_bot}: Preço não disponível, aguardando...")
                await asyncio.sleep(1)
                continue
            
            # Calcular último dígito
            ultimo_digito = int(str(ultimo_preco).replace('.', '')[-1])
            
            print(f"🔍 {nome_bot}: Último dígito R_100: {ultimo_digito}")
            
            # Condição de Entrada: Só operar se último dígito for exatamente 5
            if ultimo_digito != 5:
                print(f"⏸️ {nome_bot}: Dígito {ultimo_digito} ≠ 5. Aguardando próximo ciclo...")
                await asyncio.sleep(1)
                continue
            
            print(f"🎯 {nome_bot}: CONDIÇÃO ATENDIDA! Dígito = 5. Preparando para operar...")
            print(f"💰 {nome_bot}: Stake atual: ${stake_atual:.2f} | Total profit: ${total_profit:.2f}")
            
            # Executar compra DIGITDIFF com predição fixa 3
            predicao_fixa = 3
            print(f"🛒 {nome_bot}: Comprando DIGITDIFF (diferente de {predicao_fixa}) | Stake: ${stake_atual:.2f}")
            
            # Construir parâmetros da proposta
            proposta = {
                "proposal": 1,
                "amount": stake_atual,
                "basis": "stake",
                "contract_type": "DIGITDIFF",
                "currency": "USD",
                "symbol": "R_100",
                "duration": 1,
                "duration_unit": "t",
                "barrier": str(predicao_fixa)
            }
            
            response = await api_manager.proposal(proposta)
            
            if 'error' in response:
                print(f"❌ {nome_bot}: Erro na proposta: {response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Comprar o contrato
            buy_response = await api_manager.buy({"buy": response['proposal']['id'], "price": stake_atual})
            
            if 'error' in buy_response:
                print(f"❌ {nome_bot}: Erro na compra: {buy_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # Aguardar o resultado usando proposal_open_contract
            contract_finalizado = False
            tentativas = 0
            max_tentativas = 30  # 30 segundos máximo
            
            while not contract_finalizado and tentativas < max_tentativas:
                await asyncio.sleep(1)
                tentativas += 1
                
                try:
                    # Verificar status atual do contrato
                    contract_status = await api_manager.proposal_open_contract({
                        "proposal_open_contract": 1,
                        "contract_id": contract_id
                    })
                    
                    if 'error' in contract_status:
                        print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                        continue
                    
                    contract_info = contract_status['proposal_open_contract']
                    
                    if contract_info.get('is_sold', False):
                        contract_finalizado = True
                        # Extrair lucro do resultado final
                        lucro = float(contract_info.get('profit', 0))
                        break
                        
                except Exception as e:
                    print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
            
            if not contract_finalizado:
                print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                await asyncio.sleep(1)
                continue
            
            # Lógica Pós-Trade (Martingale Ultra Agressivo x10)
            total_profit += lucro
            salvar_operacao(nome_bot, lucro)
            
            if lucro > 0:
                # Vitória
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                # Resetar para valores iniciais
                stake_atual = stake_inicial
                print(f"🔄 {nome_bot}: Resetando stake para ${stake_inicial:.2f}")
            else:
                # Derrota - Martingale Ultra Agressivo x10
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                # Calcular novo stake: perda * fator 10
                novo_stake = abs(lucro) * martingale_fator
                stake_atual = novo_stake
                print(f"🚀 {nome_bot}: MARTINGALE x10! Novo stake: ${stake_atual:.2f}")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
            await asyncio.sleep(10)  # Pausa de 10 segundos em caso de erro
        
        # Pausa final
        await asyncio.sleep(1)

# 5. BOT TURBO GANÂNCIA (ANÁLISE ESTATÍSTICA PAR/ÍMPAR)
async def bot_turbo_ganancia(api_manager):
    """
    Bot TurboGanancia - Estratégia de análise estatística par/ímpar nos últimos 5 ticks
    Ativo: R_75
    Martingale: Fator 2.1 após primeira derrota
    """
    nome_bot = "TurboGanancia"
    ativo = "R_75"
    stake_inicial = 1.0
    martingale_fator = 2.1
    martingale_inicio_apos_derrotas = 1
    stop_loss = float('inf')
    stop_win = float('inf')
    
    # Variáveis de controle
    stake_atual = stake_inicial
    total_profit = 0.0
    loss_seguidas = 0
    
    print(f"🚀 {nome_bot}: Iniciando bot com análise estatística par/ímpar")
    print(f"💰 {nome_bot}: Stake inicial: ${stake_inicial}")
    print(f"📈 {nome_bot}: Martingale fator: {martingale_fator}x após {martingale_inicio_apos_derrotas} derrota(s)")
    print(f"🎯 {nome_bot}: Ativo: {ativo}")
    
    while True:
        try:
            # 1. Obter histórico dos últimos 5 ticks
            ticks_response = await api_manager.ticks_history({
                "ticks_history": ativo,
                "adjust_start_time": 1,
                "count": 5,
                "end": "latest",
                "start": 1,
                "style": "ticks"
            })
            
            if 'error' in ticks_response:
                print(f"❌ {nome_bot}: Erro ao obter ticks: {ticks_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            if 'history' not in ticks_response or 'prices' not in ticks_response['history']:
                print(f"⚠️ {nome_bot}: Dados de histórico inválidos")
                await asyncio.sleep(1)
                continue
            
            prices = ticks_response['history']['prices']
            if len(prices) < 5:
                print(f"⚠️ {nome_bot}: Histórico insuficiente ({len(prices)} ticks)")
                await asyncio.sleep(1)
                continue
            
            # 2. Extrair últimos dígitos dos 5 ticks
            ultimos_digitos = []
            for price in prices[-5:]:
                ultimo_digito = int(str(price).replace('.', '')[-1])
                ultimos_digitos.append(ultimo_digito)
            
            # 3. Análise estatística: contar pares e ímpares
            pares = sum(1 for digito in ultimos_digitos if digito % 2 == 0)
            impares = sum(1 for digito in ultimos_digitos if digito % 2 == 1)
            
            print(f"📊 {nome_bot}: Últimos 5 dígitos: {ultimos_digitos}")
            print(f"📊 {nome_bot}: Pares: {pares} | Ímpares: {impares}")
            
            # 4. Determinar condição de entrada
            contract_type = None
            if pares > impares:
                contract_type = "DIGITEVEN"
                print(f"🎯 {nome_bot}: Condição DIGITEVEN detectada (Pares > Ímpares)")
            elif impares > pares:
                contract_type = "DIGITODD"
                print(f"🎯 {nome_bot}: Condição DIGITODD detectada (Ímpares > Pares)")
            else:
                print(f"⚖️ {nome_bot}: Empate entre pares e ímpares - aguardando próximo ciclo")
                await asyncio.sleep(1)
                continue
            
            # 5. Executar proposta
            proposal_params = {
                "proposal": 1,
                "amount": stake_atual,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": ativo
            }
            
            response = await api_manager.proposal(proposal_params)
            
            if 'error' in response:
                print(f"❌ {nome_bot}: Erro na proposta: {response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            print(f"💵 {nome_bot}: Proposta aceita - Stake: ${stake_atual}")
            
            # 6. Comprar o contrato
            buy_response = await api_manager.buy({"buy": response['proposal']['id'], "price": stake_atual})
            
            if 'error' in buy_response:
                print(f"❌ {nome_bot}: Erro na compra: {buy_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            contract_id = buy_response['buy']['contract_id']
            print(f"📋 {nome_bot}: Contrato {contract_type} criado com sucesso!")
            print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
            
            # 7. Aguardar o resultado usando proposal_open_contract
            contract_finalizado = False
            tentativas = 0
            max_tentativas = 30  # 30 segundos máximo
            
            while not contract_finalizado and tentativas < max_tentativas:
                await asyncio.sleep(1)
                tentativas += 1
                
                try:
                    # Verificar status atual do contrato
                    contract_status = await api_manager.proposal_open_contract({
                        "proposal_open_contract": 1,
                        "contract_id": contract_id
                    })
                    
                    if 'error' in contract_status:
                        print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                        continue
                    
                    contract_info = contract_status['proposal_open_contract']
                    
                    if contract_info.get('is_sold', False):
                        contract_finalizado = True
                        # Extrair lucro do resultado final
                        lucro = float(contract_info.get('profit', 0))
                        break
                        
                except Exception as e:
                    print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
            
            if not contract_finalizado:
                print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
                await asyncio.sleep(1)
                continue
            
            # 8. Lógica Pós-Trade (Martingale com Atraso)
            total_profit += lucro
            
            # Salvar operação no Supabase
            try:
                salvar_operacao(nome_bot, lucro)
            except Exception as e:
                print(f"⚠️ {nome_bot}: Erro ao salvar no Supabase: {e}")
            
            if lucro > 0:
                # Vitória
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Total: ${total_profit:.2f}")
                stake_atual = stake_inicial
                loss_seguidas = 0
                print(f"🔄 {nome_bot}: Stake resetado para ${stake_inicial}")
            else:
                # Derrota
                loss_seguidas += 1
                print(f"❌ {nome_bot}: DERROTA! Prejuízo: ${lucro:.2f} | Total: ${total_profit:.2f}")
                print(f"📉 {nome_bot}: Derrotas seguidas: {loss_seguidas}")
                
                # Aplicar Martingale após primeira derrota
                if loss_seguidas > martingale_inicio_apos_derrotas:
                    stake_atual = round(stake_atual * martingale_fator, 2)
                    print(f"🚀 {nome_bot}: Martingale ativado! Novo stake: ${stake_atual}")
                else:
                    print(f"⏸️ {nome_bot}: Aguardando mais {martingale_inicio_apos_derrotas - loss_seguidas + 1} derrota(s) para ativar Martingale")
            
        except Exception as e:
            print(f"❌ {nome_bot}: Erro de conexão: {e}")
            await asyncio.sleep(10)
        
        # Pausa final
        await asyncio.sleep(1)

# 6. FUNÇÃO "CÃO DE GUARDA" (CONNECTION WATCHDOG)
async def bot_vip_boster(api_manager):
    """
    Bot VipBoster - Estratégia de alternância OVER/UNDER com gatilhos de dígitos específicos
    
    Ativo: R_100
    Estratégia: Alternância entre DIGITOVER e DIGITUNDER baseada em gatilhos específicos
    - OVER quando último dígito = 7 (barrier 2)
    - UNDER quando último dígito = 2 (barrier 8)
    Martingale: Sistema dividido para recuperação gradual
    """
    # Parâmetros de gestão
    nome_bot = "VipBoster"
    ativo = "R_100"
    stake_inicial = 1.0
    divisor_martingale = 2
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    
    # Variáveis de estado
    proxima_operacao = 'OVER'  # Inicializada como OVER
    valor_recuperacao_mg = 0   # Valor para recuperação no Martingale
    contador_divisao_mg = 0    # Contador para divisão do Martingale
    stake_atual = stake_inicial
    total_profit = 0
    operacao_count = 0
    
    print(f"🚀 Iniciando {nome_bot} - Estratégia de Alternância com Gatilhos")
    print(f"💰 Stake inicial: ${stake_inicial}")
    print(f"🎯 Ativo: {ativo}")
    print(f"🔄 Divisor Martingale: {divisor_martingale}")
    print(f"📊 Stop Loss: Ilimitado | Stop Win: Ilimitado")
    print(f"🎲 Próxima operação: {proxima_operacao}")
    
    while True:
        try:
            # Verificar condições de parada
            if total_profit <= -stop_loss or total_profit >= stop_win:
                print(f"🛑 {nome_bot} - Condição de parada atingida. Lucro total: ${total_profit:.2f}")
                break
            
            # Obter último dígito do ativo
            print(f"\n📊 {nome_bot} - Obtendo último dígito do ativo {ativo}...")
            ticks_response = await api_manager.ticks_history({
                'ticks_history': ativo,
                'adjust_start_time': 1,
                'count': 1,
                'end': 'latest',
                'start': 1,
                'style': 'ticks'
            })
            
            if 'error' in ticks_response:
                print(f"❌ {nome_bot} - Erro ao obter ticks: {ticks_response['error']['message']}")
                await asyncio.sleep(2)
                continue
            
            # Extrair último dígito
            ultimo_tick = ticks_response['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_tick).split('.')[-1][-1])
            print(f"🎯 {nome_bot} - Último dígito: {ultimo_digito} | Próxima operação: {proxima_operacao}")
            
            # Verificar condições de entrada
            deve_operar = False
            contract_type = None
            barrier = None
            
            if proxima_operacao == 'OVER' and ultimo_digito == 7:
                deve_operar = True
                contract_type = 'DIGITOVER'
                barrier = '2'
                print(f"✅ {nome_bot} - Gatilho OVER ativado! Dígito {ultimo_digito} = 7")
            elif proxima_operacao == 'UNDER' and ultimo_digito == 2:
                deve_operar = True
                contract_type = 'DIGITUNDER'
                barrier = '8'
                print(f"✅ {nome_bot} - Gatilho UNDER ativado! Dígito {ultimo_digito} = 2")
            else:
                print(f"⏳ {nome_bot} - Aguardando gatilho. Dígito: {ultimo_digito}, Esperando: {proxima_operacao}")
                await asyncio.sleep(1)
                continue
            
            if deve_operar:
                operacao_count += 1
                print(f"\n🎯 {nome_bot} - OPERAÇÃO #{operacao_count}")
                print(f"📊 Tipo: {contract_type} | Barrier: {barrier} | Stake: ${stake_atual:.2f}")
                
                # Criar proposta
                proposal_data = {
                    'proposal': 1,
                    'amount': stake_atual,
                    'basis': 'stake',
                    'contract_type': contract_type,
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',
                    'symbol': ativo,
                    'barrier': barrier
                }
                
                try:
                    # Enviar proposta
                    proposal_response = await api_manager.proposal(proposal_data)
                    
                    if 'error' in proposal_response:
                        print(f"❌ {nome_bot} - Erro na proposta: {proposal_response['error']['message']}")
                        await asyncio.sleep(2)
                        continue
                    
                    proposal_id = proposal_response['proposal']['id']
                    print(f"📋 {nome_bot} - Proposta criada: {proposal_id}")
                    
                    # Comprar contrato
                    buy_response = await api_manager.buy({'buy': proposal_id, 'price': stake_atual})
                    
                    if 'error' in buy_response:
                        print(f"❌ {nome_bot} - Erro na compra: {buy_response['error']['message']}")
                        await asyncio.sleep(2)
                        continue
                    
                    contract_id = buy_response['buy']['contract_id']
                    print(f"✅ {nome_bot} - Contrato comprado: {contract_id}")
                    
                    # Aguardar resultado
                    print(f"⏳ {nome_bot} - Aguardando resultado do contrato...")
                    
                    while True:
                        contract_status = await api_manager.proposal_open_contract({'proposal_open_contract': 1, 'contract_id': contract_id})
                        
                        if 'error' in contract_status:
                            print(f"❌ {nome_bot} - Erro ao verificar status: {contract_status['error']['message']}")
                            break
                        
                        contract_info = contract_status['proposal_open_contract']
                        
                        if contract_info['is_sold']:
                            lucro = float(contract_info['profit'])
                            print(f"🏁 {nome_bot} - Resultado: ${lucro:.2f}")
                            break
                        
                        await asyncio.sleep(0.5)
                    
                    # Lógica pós-trade
                    total_profit += lucro
                    print(f"💰 {nome_bot} - Lucro da operação: ${lucro:.2f} | Total: ${total_profit:.2f}")
                    
                    # Inverter próxima operação
                    if proxima_operacao == 'OVER':
                        proxima_operacao = 'UNDER'
                    else:
                        proxima_operacao = 'OVER'
                    print(f"🔄 {nome_bot} - Próxima operação invertida para: {proxima_operacao}")
                    
                    # Sistema de Martingale Dividido
                    if lucro > 0:
                        # Vitória - Reset completo
                        print(f"🎉 {nome_bot} - VITÓRIA! Resetando sistema Martingale")
                        stake_atual = stake_inicial
                        valor_recuperacao_mg = 0
                        contador_divisao_mg = 0
                    else:
                        # Derrota - Aplicar Martingale Dividido
                        print(f"💔 {nome_bot} - DERROTA! Aplicando Martingale Dividido")
                        valor_recuperacao_mg += abs(lucro)
                        contador_divisao_mg = divisor_martingale
                        stake_atual = valor_recuperacao_mg / contador_divisao_mg
                        print(f"📊 {nome_bot} - Valor recuperação: ${valor_recuperacao_mg:.2f}")
                        print(f"🔢 {nome_bot} - Novo stake: ${stake_atual:.2f} (${valor_recuperacao_mg:.2f} ÷ {contador_divisao_mg})")
                    
                    # Salvar operação no Supabase
                    try:
                        salvar_operacao(nome_bot, lucro)
                        print(f"💾 {nome_bot} - Operação salva no Supabase")
                    except Exception as e:
                        print(f"⚠️ {nome_bot} - Erro ao salvar no Supabase: {e}")
                    
                except Exception as e:
                    print(f"❌ {nome_bot} - Erro durante operação: {e}")
                    await asyncio.sleep(2)
                    continue
            
            # Pausa antes da próxima verificação
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"💥 {nome_bot} - Erro de conexão: {e}")
            print(f"🔄 {nome_bot} - Reconectando em 5 segundos...")
            await asyncio.sleep(5)


async def connection_watchdog(api_manager, main_task):
    """
    Função watchdog que monitora a saúde da conexão com a Deriv API.
    Verifica a conexão a cada 20 segundos e força o reinício se detectar falhas.
    """
    while True:
        # Pausa de 20 segundos entre verificações
        await asyncio.sleep(20)
        
        try:
            # Teste leve da conexão com ping
            await api_manager.api.ping()
            print("🟢 WATCHDOG: Conexão com Deriv OK")
        except Exception as e:
            # Conexão perdida - forçar reinício do sistema
            print("🚨 WATCHDOG: Conexão com a Deriv perdida! Forçando o reinício de todo o sistema...")
            print(f"🔍 Erro detectado: {e}")
            
            # Cancelar a tarefa principal que roda o gather dos bots
            main_task.cancel()
            
            # Sair da função watchdog
            return

# 6. FUNÇÃO PRINCIPAL (ORQUESTRADOR AUTORREPARÁVEL)
async def main():
    """
    Função principal autorreparável que coordena a execução de todos os bots em paralelo.
    Implementa um loop infinito com reinício automático em caso de falhas.
    """
    global connection_pool, supervisor_stats
    
    print("🚀 Iniciando Sistema de Trading Automatizado v3.0 (Autorreparável)...")
    
    # Loop infinito para auto-reparação
    while True:
        api = None
        tasks = []
        connection_pool = None
        
        try:
            print("\n" + "="*60)
            print("🔄 INICIANDO NOVO CICLO DO SISTEMA AUTORREPARÁVEL")
            print("="*60)
            
            # Inicializar pool de conexões
            try:
                print("🔌 Inicializando pool de conexões...")
                connection_pool = ConnectionPool(DERIV_APP_ID, DERIV_API_TOKEN, pool_size=3)
                await connection_pool.initialize()
                print("✅ Pool de conexões inicializado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao inicializar pool de conexões: {e}")
                print("⚠️  Continuando com conexão única...")
                connection_pool = None
            
            print("📊 Conectando à API da Deriv...")
            
            # Conectar à API da Deriv
            api = DerivAPI(app_id=DERIV_APP_ID)
            await api.authorize(DERIV_API_TOKEN)
            print("✅ Conexão com Deriv API estabelecida com sucesso!")
            
            # Criar instância única do ApiManager
            api_manager = ApiManager(api)
            print("🛡️ ApiManager inicializado com controle de concorrência")
            
            # Verificar conexão com Supabase
            try:
                supabase.table('operacoes').select("*").limit(1).execute()
                print("✅ Conexão com Supabase verificada!")
            except Exception as e:
                print(f"⚠️  Aviso: Problema na conexão com Supabase: {e}")
            
            print("\n🤖 Iniciando execução dos bots em paralelo...")
            print("🔄 Rate limiting ativo - Distribuindo chamadas da API...")
            
            # Lista de funções dos bots
            bot_functions = [
                bot_bk_1_0,
                bot_factor_50x,
                bot_accumulator_scalping,  # Movido para posição 3 para inicialização mais rápida
                bot_ai_2_0,
                bot_apalancamiento,
                wolf_bot_2_0,
                bot_sniper_martingale,
                bot_quantum_fixed_stake,
                bot_scale,
                bot_alfa,
                bot_tip,
                bot_xtreme,
                bot_gold,  # Adicionando o GoldBot à lista
                bot_double_cuentas,  # Adicionando o DoubleCuentas à lista
                bot_turbo_ganancia,  # Adicionando o TurboGanancia à lista
                bot_vip_boster,  # Adicionando o VipBoster à lista
                bot_aura_under8  # Adicionando o AuraBot_Under8 à lista
            ]
            
            # Função auxiliar para criar bot com delay inicial (fora do loop para evitar closure)
            async def delayed_bot(func, delay, manager, bot_name):
                print(f"⏰ Bot {bot_name} aguardando {delay}s para iniciar...")
                await asyncio.sleep(delay)
                print(f"🚀 Iniciando {bot_name}...")
                try:
                    await func(manager)
                except Exception as e:
                    print(f"❌ Erro no {bot_name}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Criar tarefas passando api_manager para cada bot
            for i, bot_func in enumerate(bot_functions):
                # Obter nome do bot
                bot_name = bot_func.__name__
                
                # Adicionar tarefa com delay de 2 segundos entre cada bot
                tasks.append(asyncio.create_task(delayed_bot(bot_func, i * 2, api_manager, bot_name)))
            
            # Obter a tarefa atual que está rodando o gather
            main_task = asyncio.current_task()
            
            # Adicionar a tarefa do watchdog à lista
            tasks.append(asyncio.create_task(connection_watchdog(api_manager, main_task)))
            
            print(f"📈 {len(tasks)-1} bots configurados para execução paralela com ApiManager")
            print("🛡️ Watchdog de conexão ativado - monitoramento a cada 20 segundos")
            print("🎯 Sistema em execução - aguardando falhas para auto-reparação...")
            
            # PONTO CRÍTICO: Esta linha só termina se um bot falhar catastroficamente ou watchdog detectar falha
            await asyncio.gather(*tasks)
            
            # Se chegou aqui, significa que gather() terminou (provavelmente por falha)
            print("⚠️ Um ou mais bots pararam. Reiniciando todas as tarefas em 15 segundos...")
            await asyncio.sleep(15)
            
        except KeyboardInterrupt:
            print("\n⏹️  Interrupção manual detectada...")
            break
            
        except asyncio.CancelledError:
            # Cancelamento iniciado pelo watchdog devido à perda de conexão
            print("🔄 WATCHDOG: Reinício forçado devido à perda de conexão detectada")
            print("⚠️ Reiniciando todo o sistema em 15 segundos...")
            
        except Exception as e:
            # Este bloco captura qualquer erro fatal não tratado
            print(f"❌ Erro fatal no sistema de bots: {e}. Reiniciando todo o sistema em 15 segundos...")
            
            # Cancelar todas as tarefas pendentes
            if tasks:
                print("🛑 Cancelando tarefas pendentes...")
                for task in tasks:
                    if not task.done():
                        task.cancel()
                
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception:
                    pass  # Ignorar erros de cancelamento
            
            # Fechar conexões
            if connection_pool:
                try:
                    await connection_pool.close_all()
                    print("🔌 Pool de conexões fechado")
                except Exception:
                    pass
            
            if api:
                try:
                    await api.disconnect()
                    print("🔌 Conexão API fechada")
                except Exception:
                    pass
            
            # Aguardar antes de reiniciar
            await asyncio.sleep(15)
            
            # O loop while True fará com que o sistema reinicie automaticamente
            continue
        
        finally:
            # Limpeza final
            if tasks:
                for task in tasks:
                    if not task.done():
                        task.cancel()
            
            if api:
                try:
                    await api.disconnect()
                except Exception:
                    pass
            
            # Fechar pool de conexões se existir
            if connection_pool:
                try:
                    await connection_pool.close_all()
                    print("🔌 Pool de conexões fechado")
                except Exception:
                    pass
            
            print("🔚 Encerrando conexões...")

# 7. FUNÇÃO SUPERVISOR INTEGRADA
def supervisor():
    """
    Função supervisor que gerencia o auto-reinício dos bots
    Reinicia o sistema a cada intervalo definido para manter estabilidade
    """
    print("🔧 MODO SUPERVISOR ATIVADO")
    print("=" * 60)
    
    # Configurações do supervisor
    tempo_de_execucao_segundos = 3600  # 1 hora (3600 segundos)
    pausa_entre_reinicios_segundos = 15
    ciclo = 1
    
    print(f"🎯 SISTEMA DE TRADING AUTOMATIZADO - DERIV")
    print(f"⏰ Tempo de execução configurado: {tempo_de_execucao_segundos} segundos")
    print(f"🔄 Rate limiting ativo para proteção da API")
    print(f"📊 Configurações de rate limiting:")
    print(f"   • Compras: {RATE_LIMIT_CONFIG['buy']['max_calls']} por {RATE_LIMIT_CONFIG['buy']['window_seconds']}s")
    print(f"   • Históricos: {RATE_LIMIT_CONFIG['ticks_history']['max_calls']} por {RATE_LIMIT_CONFIG['ticks_history']['window_seconds']}s")
    print(f"   • Verificações: {RATE_LIMIT_CONFIG['proposal_open_contract']['max_calls']} por {RATE_LIMIT_CONFIG['proposal_open_contract']['window_seconds']}s")
    print("=" * 60)
    print(f"⚙️  Configurações do Supervisor:")
    print(f"   ⏱️  Tempo de execução: {tempo_de_execucao_segundos} segundos")
    print(f"   ⏸️  Pausa entre reinícios: {pausa_entre_reinicios_segundos} segundos")
    print("=" * 60)
    
    while True:
        try:
            print(f"\n🔄 CICLO {ciclo} - Iniciando modo worker dos bots...")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Iniciando execução")
            
            # Executar o próprio script em modo worker
            comando = [sys.executable, __file__, "--worker"]
            processo = subprocess.Popen(
                comando,
                # Remover stdout=subprocess.PIPE para mostrar saída dos bots
                # stdout=subprocess.PIPE,
                # stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            try:
                # Aguardar o processo por tempo_de_execucao_segundos
                processo.wait(timeout=tempo_de_execucao_segundos)
                print(f"✅ Processo worker finalizado naturalmente")
                
            except subprocess.TimeoutExpired:
                print(f"⏰ Tempo limite atingido ({tempo_de_execucao_segundos}s)")
                print("🔄 Encerrando processo worker educadamente...")
                
                # Tentar encerrar educadamente
                processo.terminate()
                
                try:
                    # Aguardar 10 segundos para encerramento educado
                    processo.wait(timeout=10)
                    print("✅ Processo worker encerrado educadamente")
                except subprocess.TimeoutExpired:
                    print("⚠️  Forçando encerramento do processo worker...")
                    processo.kill()
                    processo.wait()
                    print("🛑 Processo worker encerrado forçadamente")
            
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Ciclo {ciclo} finalizado")
            
            # Incrementar contador de ciclos
            ciclo += 1
            
            # Pausa entre reinícios
            if pausa_entre_reinicios_segundos > 0:
                print(f"⏸️  Aguardando {pausa_entre_reinicios_segundos} segundos antes do próximo ciclo...")
                time.sleep(pausa_entre_reinicios_segundos)
            
        except KeyboardInterrupt:
            print("\n⏹️  Interrupção manual detectada no supervisor...")
            
            # Encerrar processo worker se estiver rodando
            try:
                if 'processo' in locals() and processo.poll() is None:
                    print("🛑 Encerrando processo worker...")
                    processo.terminate()
                    processo.wait(timeout=5)
            except:
                pass
            
            print("✅ Supervisor encerrado pelo usuário")
            break
            
        except Exception as e:
            print(f"❌ Erro no supervisor: {e}")
            
            # Tentar encerrar processo worker se existir
            try:
                if 'processo' in locals() and processo.poll() is None:
                    processo.terminate()
                    processo.wait(timeout=5)
            except:
                pass
            
            print(f"⏸️  Aguardando {pausa_entre_reinicios_segundos} segundos antes de tentar novamente...")
            time.sleep(pausa_entre_reinicios_segundos)

# 8. PONTO DE ENTRADA DO SCRIPT
if __name__ == "__main__":
    """
    Ponto de entrada principal do script
    Decide entre executar como supervisor ou como worker baseado nos argumentos
    """
    
    # Verificar se foi chamado em modo worker
    if "--worker" in sys.argv:
        # MODO WORKER: Executar os bots
        print("🤖 MODO WORKER ATIVADO")
        print("=" * 60)
        print("🎯 SISTEMA DE TRADING AUTOMATIZADO - DERIV BOTS")
        print("=" * 60)
        
        try:
            # Executar o sistema principal dos bots
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n⏹️  Sistema worker interrompido pelo usuário (Ctrl+C)")
            print("🔄 Finalizando operações em andamento...")
            print("✅ Sistema worker encerrado com segurança!")
        except Exception as e:
            print(f"\n❌ Erro crítico no sistema worker: {e}")
            print("🔧 Verifique as configurações e tente novamente.")
    
    else:
        # MODO SUPERVISOR: Gerenciar auto-reinício
        print("SISTEMA DE TRADING AUTOMATIZADO - DERIV BOTS")
        print("MODO SUPERVISOR COM AUTO-REINICIO")
        print("=" * 60)
        
        try:
            # Executar o supervisor
            supervisor()
        except KeyboardInterrupt:
            print("\n\n⏹️  Supervisor interrompido pelo usuário (Ctrl+C)")
            print("✅ Supervisor encerrado com segurança!")
        except Exception as e:
            print(f"\n❌ Erro crítico no supervisor: {e}")
            print("🔧 Verifique as configurações e tente novamente.")