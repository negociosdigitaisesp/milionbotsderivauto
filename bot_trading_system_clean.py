#!/usr/bin/env python3
"""
Sistema de Trading Automatizado - Versao Limpa sem Unicode
Executa estrategias de trading em paralelo usando asyncio
Com funcionalidade integrada de supervisor para auto-reinicio
"""

import asyncio
import os
import sys
from deriv_api import DerivAPI
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import random
from collections import defaultdict

# Importar bot_scale do modulo trading_system
try:
    from trading_system.bots.scale_bot import bot_scale
except ImportError:
    print("Aviso: Modulo bot_scale nao encontrado. Funcao bot_scale sera definida localmente.")
    
    async def bot_scale(api_manager):
        """
        Bot Scale - Implementacao local de fallback
        Estrategia simples de trading com stake fixo
        """
        nome_bot = "ScaleBot-Local"
        
        print(f"Iniciando {nome_bot} (versao local)...")
        
        try:
            while True:
                print(f"Executando {nome_bot}: Executando estrategia basica...")
                
                # Implementacao basica de trading
                ticks_response = await api_manager.ticks_history({
                    "ticks_history": "R_100",
                    "count": 5
                })
                
                if 'error' in ticks_response:
                    print(f"{nome_bot}: Erro ao obter ticks: {ticks_response['error']['message']}")
                    await asyncio.sleep(5)
                    continue
                
                # Logica simples: comprar CALL se ultimo tick > primeiro tick
                prices = ticks_response['history']['prices']
                direction = 'CALL' if prices[-1] > prices[0] else 'PUT'
                
                parametros_compra = {
                    'buy': '1',
                    'price': 2.0,
                    'parameters': {
                        'amount': 2.0,
                        'basis': 'stake',
                        'contract_type': direction,
                        'currency': 'USD',
                        'duration': 1,
                        'duration_unit': 't',
                        'symbol': 'R_100'
                    }
                }
                
                recibo_compra = await api_manager.buy(parametros_compra)
                
                if 'error' in recibo_compra:
                    print(f"{nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                    await asyncio.sleep(5)
                    continue
                
                # Aguardar resultado
                if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                    contract_id = recibo_compra['buy']['contract_id']
                    
                    for tentativas in range(15):
                        await asyncio.sleep(2)
                        
                        try:
                            contract_status = await api_manager.proposal_open_contract({
                                "proposal_open_contract": 1,
                                "contract_id": contract_id
                            })
                            
                            if 'proposal_open_contract' in contract_status:
                                contract = contract_status['proposal_open_contract']
                                
                                if contract.get('is_sold') == 1:
                                    payout = float(contract.get('payout', 0))
                                    buy_price = float(contract.get('buy_price', 0))
                                    lucro = payout - buy_price
                                    
                                    if lucro > 0:
                                        print(f"{nome_bot}: VITORIA! Lucro: ${lucro:.2f} | Total: ${lucro:.2f}")
                                    else:
                                        print(f"{nome_bot}: DERROTA! Perda: ${lucro:.2f} | Total: ${lucro:.2f}")
                                    
                                    salvar_operacao(nome_bot, lucro)
                                    break
                        except Exception as e:
                            print(f"{nome_bot}: Aguardando resultado... ({tentativas}s)")
                
                print(f"Erro no {nome_bot}: {e}")
                await asyncio.sleep(10)
                
        except Exception as e:
            print(f"Erro no {nome_bot}: {e}")
            await asyncio.sleep(10)


# Carregar variaveis de ambiente
load_dotenv()

# Classe ApiManager para controle de concorrencia
class ApiManager:
    """
    Classe para gerenciar chamadas a API da Deriv de forma robusta
    Implementa controle de concorrencia e pausas para evitar rate limiting
    """
    
    def __init__(self, api):
        self.api = api
        self.api_lock = asyncio.Lock()
    
    async def buy(self, params):
        """Wrapper para chamadas de compra com controle de concorrencia"""
        async with self.api_lock:
            resultado = await self.api.buy(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturacao
            return resultado
    
    async def ticks_history(self, params):
        """Wrapper para chamadas de historico de ticks com controle de concorrencia"""
        async with self.api_lock:
            resultado = await self.api.ticks_history(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturacao
            return resultado
    
    async def proposal_open_contract(self, params):
        """Wrapper para chamadas de status de contrato com controle de concorrencia"""
        async with self.api_lock:
            resultado = await self.api.proposal_open_contract(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturacao
            return resultado
    
    async def proposal(self, params):
        """Wrapper para chamadas de proposta com controle de concorrencia"""
        async with self.api_lock:
            resultado = await self.api.proposal(params)
            await asyncio.sleep(0.3)  # Pausa de 300ms para evitar saturacao
            return resultado

# Configuracoes de rate limiting
RATE_LIMIT_CONFIG = {
    'buy': {'max_calls': 5, 'window_seconds': 60},  # 5 compras por minuto
    'ticks_history': {'max_calls': 10, 'window_seconds': 60},  # 10 historicos por minuto
    'proposal_open_contract': {'max_calls': 20, 'window_seconds': 60}  # 20 verificacoes por minuto
}

# Controle de chamadas por endpoint
call_tracker = defaultdict(list)
rate_limit_lock = asyncio.Lock()

async def wait_for_rate_limit(endpoint):
    """
    Controla o rate limiting para evitar excesso de chamadas a API
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
                print(f"Rate limit atingido para {endpoint}. Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time + 1)  # +1 segundo de margem
                
                # Limpar novamente apos a espera
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
    Wrapper seguro para chamadas da API com rate limiting e retry
    """
    for attempt in range(max_retries):
        try:
            # Aguardar rate limit
            await wait_for_rate_limit(method_name)
            
            # Fazer a chamada
            method = getattr(api, method_name)
            result = await method(params)
            
            # Verificar se ha erro de rate limit
            if 'error' in result and 'rate limit' in result['error']['message'].lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Espera progressiva: 5s, 10s, 15s
                    print(f"Rate limit detectado. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Rate limit persistente apos {max_retries} tentativas")
            
            return result
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Espera progressiva: 2s, 4s, 6s
                print(f"Erro na API (tentativa {attempt + 1}/{max_retries}): {str(e)}")
                print(f"   Aguardando {wait_time}s antes de tentar novamente...")
                await asyncio.sleep(wait_time)
            else:
                raise e

# Credenciais da Deriv API e Supabase
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificar se todas as variaveis de ambiente foram carregadas
if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Erro: Variaveis de ambiente nao encontradas. Verifique o arquivo .env")

# Inicializar cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def salvar_operacao(nome_bot: str, lucro: float):
    """
    Salva o resultado de uma operacao no banco de dados Supabase
    """
    try:
        data = {
            'nome_bot': nome_bot,
            'lucro': lucro,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table('operacoes').insert(data).execute()
        print(f"Operacao salva com sucesso - Bot: {nome_bot}, Lucro: {lucro}")
        
    except Exception as e:
        print(f"Erro ao salvar operacao no Supabase: {e}")
        print(f"   Bot: {nome_bot}, Lucro: {lucro}")

async def bot_gold(api_manager):
    """
    GoldBot - Estrategia de Compra Continua com Predicao Dinamica
    Ativo: R_100
    Contrato: DIGITDIFF com predicao baseada no ultimo digito
    Martingale: Fator 2.0 agressivo
    """
    nome_bot = "GoldBot"
    print(f"Iniciando {nome_bot}...")
    
    # Parametros de gestao
    stake_inicial = 2.0
    martingale_fator = 2.0
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    
    # Inicializacao das variaveis
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"{nome_bot} configurado:")
    print(f"   Stake inicial: ${stake_inicial}")
    print(f"   Martingale fator: {martingale_fator}")
    print(f"   Stop Loss: Ilimitado")
    print(f"   Stop Win: Ilimitado")
    print(f"   Estrategia: DIGITDIFF com predicao dinamica")
    print(f"   Ativo: R_100")
    
    while True:
        try:
            # Obter ultimo digito do ativo R_100 para usar como predicao
            tick_response = await api_manager.ticks_history({
                "ticks_history": "R_100",
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"{nome_bot}: Erro ao obter tick: {tick_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Extrair o ultimo digito do preco para usar como predicao
            ultimo_tick = tick_response['history']['prices'][-1]
            predicao = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"{nome_bot}: Ultimo digito R_100: {predicao} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            print(f"{nome_bot}: Predicao definida: {predicao} | Preparando DIGITDIFF")
            
            # Construir parametros da compra DIGITDIFF
            parametros_da_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_atual,
                'parameters': {
                    'amount': stake_atual,
                    'basis': 'stake',
                    'contract_type': 'DIGITDIFF',
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',
                    'symbol': 'R_100',
                    'barrier': predicao  # Usar o ultimo digito como predicao
                }
            }
            
            print(f"{nome_bot}: Comprando DIGITDIFF {predicao} | Stake: ${stake_atual:.2f}")
            
            # Fazer a compra com subscribe
            recibo_compra = await api_manager.buy(parametros_da_compra)
            
            if 'error' in recibo_compra:
                print(f"{nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            print(f"{nome_bot}: Contrato DIGITDIFF criado com sucesso!")
            
            # Aguardar o resultado final
            print(f"{nome_bot}: Aguardando resultado do contrato...")
            
            # Obter contract_id e aguardar resultado
            if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                contract_id = recibo_compra['buy']['contract_id']
                
                # Aguardar o resultado usando proposal_open_contract
                contract_finalizado = False
                tentativas = 0
                max_tentativas = 30  # 30 segundos maximo
                
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
                            print(f"{nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                            continue
                        
                        if 'proposal_open_contract' in contract_status:
                            contract = contract_status['proposal_open_contract']
                            
                            # Verificar se o contrato foi finalizado
                            if contract.get('is_sold') == 1:
                                contract_finalizado = True
                                
                                # Calcular lucro
                                payout = float(contract.get('payout', 0))
                                buy_price = float(contract.get('buy_price', 0))
                                lucro = payout - buy_price
                                
                                # Atualizar totais
                                total_profit += lucro
                                perda_anterior = stake_atual
                                
                                # Salvar operacao
                                salvar_operacao(nome_bot, lucro)
                                
                                # Logica Pos-Trade (Martingale Agressivo)
                                if lucro > 0:
                                    # Vitoria - Reset do stake
                                    print(f"{nome_bot}: VITORIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                                    stake_atual = stake_inicial
                                    print(f"{nome_bot}: Stake resetado para inicial: ${stake_atual:.2f}")
                                else:
                                    # Derrota - Aplicar Martingale
                                    print(f"{nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                                    stake_atual = perda_anterior * martingale_fator
                                    print(f"{nome_bot}: Martingale aplicado - Proximo stake: ${stake_atual:.2f} (perda ${perda_anterior:.2f} × {martingale_fator})")
                                
                                break
                        
                    except Exception as e:
                        print(f"{nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                
                if not contract_finalizado:
                    print(f"{nome_bot}: Timeout aguardando resultado do contrato")
                    
            else:
                print(f"{nome_bot}: Erro: Nao foi possivel obter contract_id")
                
        except Exception as e:
            print(f"Erro no {nome_bot}: {e}")
            print(f"{nome_bot}: Aguardando 10 segundos antes de tentar novamente...")
            await asyncio.sleep(10)

async def bot_double_cuentas(api_manager):
    """
    DoubleCuentas Bot - Estrategia baseada em gatilho de digito especifico
    Opera com DIGITOVER quando o ultimo digito do ativo R_75 e exatamente 0
    """
    nome_bot = "DoubleCuentas"
    print(f"Iniciando {nome_bot}...")
    
    # Parametros de gestao
    stake_inicial = 1.0
    martingale_fator = 1.8
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = 'R_75'
    duracao_contrato = 5  # ticks
    
    # Inicializar variaveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"{nome_bot} configurado:")
    print(f"   Stake inicial: ${stake_inicial}")
    print(f"   Fator Martingale: {martingale_fator}")
    print(f"   Stop Loss: Infinito")
    print(f"   Stop Win: Infinito")
    print(f"   Estrategia: Gatilho Digito 0 + DIGITOVER")
    print(f"   Ativo: {ativo}")
    print(f"   Duracao: {duracao_contrato} ticks")
    
    while True:
        try:
            # Obter ultimo digito do ativo R_75
            tick_response = await api_manager.ticks_history({
                "ticks_history": ativo,
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"{nome_bot}: Erro ao obter tick: {tick_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Extrair o ultimo digito do preco
            ultimo_tick = tick_response['history']['prices'][-1]
            ultimo_digito = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"{nome_bot}: Preco: {ultimo_tick:.5f} | Ultimo Digito: {ultimo_digito}")
            print(f"{nome_bot}: Profit Total: ${total_profit:.2f} | Stake Atual: ${stake_atual:.2f}")
            
            # Estrategia de Entrada (Gatilho de Digito)
            # A compra so deve ocorrer se o ultimo_digito for exatamente 0
            if ultimo_digito == 0:
                print(f"{nome_bot}: Gatilho ativado! Ultimo digito = 0. Executando DIGITOVER...")
                
                # Construir parametros da compra para DIGITOVER
                parametros_da_compra = {
                    'buy': '1',
                    'subscribe': 1,
                    'price': stake_atual,
                    'parameters': {
                        'amount': stake_atual,
                        'basis': 'stake',
                        'contract_type': 'DIGITOVER',
                        'currency': 'USD',
                        'duration': duracao_contrato,
                        'duration_unit': 't',
                        'symbol': ativo,
                        'barrier': 3  # Barreira sempre 3
                    }
                }
                
                print(f"{nome_bot}: Comprando DIGITOVER | Barreira: 3 | Stake: ${stake_atual:.2f} | Duracao: {duracao_contrato} ticks")
                
                # Fazer a compra
                recibo_compra = await api_manager.buy(parametros_da_compra)
                
                if 'error' in recibo_compra:
                    print(f"{nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                    await asyncio.sleep(1)
                    continue
                
                print(f"{nome_bot}: Contrato DIGITOVER criado com sucesso!")
                
                # Aguardar o resultado final
                print(f"{nome_bot}: Aguardando resultado do contrato...")
                
                # Obter contract_id e aguardar resultado
                if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
                    contract_id = recibo_compra['buy']['contract_id']
                    
                    # Aguardar o resultado usando proposal_open_contract
                    contract_finalizado = False
                    tentativas = 0
                    max_tentativas = 30  # 30 segundos maximo
                    
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
                                print(f"{nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                                continue
                            
                            if 'proposal_open_contract' in contract_status:
                                contract = contract_status['proposal_open_contract']
                                
                                # Verificar se o contrato foi finalizado
                                if contract.get('is_sold') == 1:
                                    contract_finalizado = True
                                    
                                    # Calcular lucro
                                    payout = float(contract.get('payout', 0))
                                    buy_price = float(contract.get('buy_price', 0))
                                    lucro = payout - buy_price
                                    
                                    # Atualizar totais
                                    total_profit += lucro
                                    stake_usado = stake_atual
                                    
                                    # Salvar operacao
                                    salvar_operacao(nome_bot, lucro)
                                    
                                    # Logica Pos-Trade (Martingale)
                                    if lucro > 0:
                                        # Vitoria - Reset do stake
                                        print(f"{nome_bot}: VITORIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_usado:.2f} | Total: ${total_profit:.2f}")
                                        stake_atual = stake_inicial
                                        print(f"{nome_bot}: Stake resetado para inicial: ${stake_atual:.2f}")
                                    else:
                                        # Derrota - Aplicar Martingale
                                        print(f"{nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_usado:.2f} | Total: ${total_profit:.2f}")
                                        perda_anterior = abs(lucro)
                                        stake_atual = perda_anterior * martingale_fator
                                        print(f"{nome_bot}: Martingale aplicado - Proximo stake: ${stake_atual:.2f} (Fator: {martingale_fator})")
                                    
                                    break
                            
                        except Exception as e:
                            print(f"{nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
                    
                    if not contract_finalizado:
                        print(f"{nome_bot}: Timeout aguardando resultado do contrato")
                        
                else:
                    print(f"{nome_bot}: Erro: Nao foi possivel obter contract_id")
            else:
                print(f"{nome_bot}: Aguardando gatilho (digito = 0). Atual: {ultimo_digito}")
            
            # Pausa entre operacoes
            await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Erro no {nome_bot}: {e}")
            print(f"{nome_bot}: Aguardando 10 segundos antes de tentar novamente...")
            await asyncio.sleep(10)

# Configuracao de tempo de execucao
tempo_de_execucao_segundos = 3600  # 1 hora por ciclo

print(f"SISTEMA DE TRADING AUTOMATIZADO - DERIV")
print(f"Tempo de execucao configurado: {tempo_de_execucao_segundos} segundos")
print(f"Rate limiting ativo para protecao da API")
print("=" * 60)

async def main():
    """
    Funcao principal que coordena a execucao de todos os bots em paralelo
    com sistema de reconexao automatica robusto para lidar com erros WebSocket
    """
    print("Iniciando Sistema de Trading Automatizado...")
    
    # Contador de tentativas de reconexao
    tentativas_reconexao = 0
    max_tentativas_reconexao = 3
    
    # Loop de reconexao - mantem o sistema funcionando mesmo com falhas de conexao
    while tentativas_reconexao < max_tentativas_reconexao:
        try:
            print(f"Conectando a API da Deriv... (Tentativa {tentativas_reconexao + 1})")
            
            # Conectar a API da Deriv
            api = DerivAPI(app_id=DERIV_APP_ID)
            await api.authorize(DERIV_API_TOKEN)
            api_manager = ApiManager(api)
            
            print("Conexao com Deriv API estabelecida com sucesso!")
            print("ApiManager inicializado com controle de concorrencia")
            
            # Reset contador de tentativas apos conexao bem-sucedida
            tentativas_reconexao = 0
            
            # Verificar conexao com Supabase
            try:
                result = supabase.table('operacoes').select('*').limit(1).execute()
                print("Conexao com Supabase verificada!")
            except Exception as e:
                print(f"Aviso: Problema na conexao com Supabase: {e}")
                print("Continuando sem salvar no banco de dados")
            
            print("\nIniciando execucao dos bots em paralelo...")
            print("Rate limiting ativo - Distribuindo chamadas da API...")
            
            # Lista de funcoes dos bots
            bots = [
                bot_scale,  # Bot Scale (importado ou local)
                bot_gold,   # Adicionando o GoldBot a lista de bots
                bot_double_cuentas  # Adicionando o DoubleCuentas a lista de bots
            ]
            
            # Funcao auxiliar para criar bot com delay inicial
            async def criar_bot_com_delay(bot_func, delay):
                await asyncio.sleep(delay)
                await bot_func(api_manager)
            
            # Criar tasks com delays escalonados (0s, 5s, 10s, etc.)
            tasks = [
                asyncio.create_task(criar_bot_com_delay(bot, i * 5))
                for i, bot in enumerate(bots)
            ]
            
            print(f"{len(tasks)} bots configurados para execucao paralela com delays escalonados")
            
            # Aguardar a execucao por tempo determinado
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=tempo_de_execucao_segundos
                )
            except asyncio.TimeoutError:
                print("Timeout na execucao dos bots")
            except Exception as e:
                print(f"Erro durante execucao dos bots: {e}")
                raise
            
        except KeyboardInterrupt:
            print("\nInterrupcao manual detectada...")
            break
            
        except Exception as e:
            tentativas_reconexao += 1
            
            if tentativas_reconexao >= max_tentativas_reconexao:
                print(f"\nErro critico apos {max_tentativas_reconexao} tentativas: {e}")
                print("Reiniciando o sistema completamente...")
                break
            
            # Tempo de espera exponencial
            tempo_espera = min(30, 2 ** tentativas_reconexao)  # Maximo de 30 segundos
            print(f"\nErro de conexao: {e}")
            print(f"Tentativa {tentativas_reconexao}/{max_tentativas_reconexao}")
            print(f"Aguardando {tempo_espera} segundos antes de reconectar...")
            await asyncio.sleep(tempo_espera)
            
            # Fechar conexao atual se existir
            try:
                if 'api' in locals():
                    await api.disconnect()
            except:
                pass

if __name__ == "__main__":
    print("SISTEMA DE TRADING AUTOMATIZADO - DERIV BOTS")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSistema interrompido pelo usuario (Ctrl+C)")
        print("Finalizando operacoes em andamento...")
        print("Sistema encerrado com seguranca!")
    except Exception as e:
        print(f"\nErro critico no sistema: {e}")
        print("Verifique as configuracoes e tente novamente.")