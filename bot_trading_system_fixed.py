"""
Sistema de Trading Automatizado - Múltiplos Bots Deriv
Executa estratégias de trading em paralelo usando asyncio
Com funcionalidade integrada de supervisor para auto-reinício
VERSÃO CORRIGIDA COM RATE LIMITING
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

# Importar bot_scale do módulo trading_system
from trading_system.bots.scale_bot import bot_scale

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

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

# SISTEMA DE CONTROLE DE RATE LIMITING
# Configurações de rate limiting
RATE_LIMIT_CONFIG = {
    'buy': {'max_calls': 5, 'window_seconds': 60},  # 5 compras por minuto
    'ticks_history': {'max_calls': 10, 'window_seconds': 60},  # 10 históricos por minuto
    'proposal_open_contract': {'max_calls': 20, 'window_seconds': 60}  # 20 verificações por minuto
}

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
                print(f"Rate limit atingido para {endpoint}. Aguardando {wait_time:.1f}s...")
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
    Wrapper seguro para chamadas da API com rate limiting e retry
    """
    for attempt in range(max_retries):
        try:
            # Aguardar rate limit
            await wait_for_rate_limit(method_name)
            
            # Fazer a chamada
            method = getattr(api, method_name)
            result = await method(params)
            
            # Verificar se há erro de rate limit
            if 'error' in result and 'rate limit' in result['error']['message'].lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Espera progressiva: 5s, 10s, 15s
                    print(f"Rate limit detectado. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Rate limit persistente após {max_retries} tentativas")
            
            return result
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Espera progressiva: 2s, 4s, 6s
                print(f"Erro na API (tentativa {attempt + 1}/{max_retries}): {str(e)}")
                print(f"   Aguardando {wait_time}s antes de tentar novamente...")
                await asyncio.sleep(wait_time)
            else:
                raise e

# 2. CONFIGURAÇÕES E CONEXÃO COM SUPABASE
# Credenciais da Deriv API (carregadas do arquivo .env)
DERIV_APP_ID = os.getenv("DERIV_APP_ID")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")

# Credenciais do Supabase (carregadas do arquivo .env)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificar se todas as variáveis de ambiente foram carregadas
if not all([DERIV_APP_ID, DERIV_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Erro: Variaveis de ambiente nao encontradas. Verifique o arquivo .env")

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
        print(f"Operacao salva com sucesso - Bot: {nome_bot}, Lucro: {lucro}")
        
    except Exception as e:
        print(f"Erro ao salvar operacao no Supabase: {e}")
        print(f"   Bot: {nome_bot}, Lucro: {lucro}")

# Configuração de tempo de execução
tempo_de_execucao_segundos = 3600  # 1 hora por ciclo

print(f"SISTEMA DE TRADING AUTOMATIZADO - DERIV")
print(f"Tempo de execucao configurado: {tempo_de_execucao_segundos} segundos")
print(f"Rate limiting ativo para protecao da API")
print("=" * 60)


async def bot_gold(api_manager):
    """
    GoldBot - Estratégia de Compra Contínua com Predição Dinâmica
    Ativo: R_100
    Contrato: DIGITDIFF com predição baseada no último dígito
    Martingale: Fator 2.0 agressivo
    """
    nome_bot = "GoldBot"
    print(f"Iniciando {nome_bot}...")
    
    # Parâmetros de gestão
    stake_inicial = 2.0
    martingale_fator = 2.0
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    
    # Inicialização das variáveis
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
            # Obter último dígito do ativo R_100 para usar como predição
            tick_response = await api_manager.ticks_history({
                "ticks_history": "R_100",
                "count": 1,
                "end": "latest"
            })
            
            if 'error' in tick_response:
                print(f"{nome_bot}: Erro ao obter tick: {tick_response['error']['message']}")
                await asyncio.sleep(1)
                continue
            
            # Extrair o último dígito do preço para usar como predição
            ultimo_tick = tick_response['history']['prices'][-1]
            predicao = int(str(ultimo_tick).split('.')[-1][-1])
            
            print(f"{nome_bot}: Ultimo digito R_100: {predicao} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            print(f"{nome_bot}: Predicao definida: {predicao} | Preparando DIGITDIFF")
            
            # Construir parâmetros da compra DIGITDIFF
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
                    'barrier': predicao  # Usar o último dígito como predição
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
            
            # Lógica Pós-Trade (Martingale Agressivo)
            if lucro > 0:
                # Vitória - Reset do stake
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                stake_atual = stake_inicial
                print(f"🔄 {nome_bot}: Stake resetado para inicial: ${stake_atual:.2f}")
            else:
                # Derrota - Martingale agressivo
                perda_anterior = abs(lucro)
                stake_atual = perda_anterior * martingale_fator
                print(f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_atual:.2f} | Total: ${total_profit:.2f}")
                print(f"🔄 {nome_bot}: Martingale aplicado - Próximo stake: ${stake_atual:.2f} (perda ${perda_anterior:.2f} × {martingale_fator})")
            
        except Exception as e:
            print(f"❌ Erro no {nome_bot}: {e}")
            print(f"⏳ {nome_bot}: Aguardando 10 segundos antes de tentar novamente...")
            await asyncio.sleep(10)
        
        # Pausa entre operações para manter ritmo constante
        await asyncio.sleep(1)

# 5. FUNÇÃO PRINCIPAL (ORQUESTRADOR)
async def main():
    """
    Função principal que coordena a execução de todos os bots em paralelo
    com sistema de reconexão automática robusto para lidar com erros WebSocket
    """
    print("🚀 Iniciando Sistema de Trading Automatizado...")
    
    # Contador de tentativas de reconexão
    tentativas_reconexao = 0
    max_tentativas_reconexao = 5
    
    # Loop de reconexão - mantém o sistema funcionando mesmo com falhas de conexão
    while True:
        api = None
        tasks = []
        
        try:
            print(f"📊 Conectando à API da Deriv... (Tentativa {tentativas_reconexao + 1})")
            
            # Conectar à API da Deriv
            api = DerivAPI(app_id=DERIV_APP_ID)
            await api.authorize(DERIV_API_TOKEN)
            print("✅ Conexão com Deriv API estabelecida com sucesso!")
            
            # Criar ApiManager para gerenciar chamadas da API
            api_manager = ApiManager(api)
            print("🔧 ApiManager inicializado com controle de concorrência")
            
            # Reset contador de tentativas após conexão bem-sucedida
            tentativas_reconexao = 0
            
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
                bot_scale,
                bot_gold  # Adicionando o GoldBot à lista de bots
            ]
            
            # Criar tarefas com delays escalonados para distribuir carga da API
            for i, bot_func in enumerate(bot_functions):
                # Função auxiliar para criar bot com delay inicial
                async def delayed_bot(func, delay):
                    await asyncio.sleep(delay)
                    await func(api_manager)
                
                # Adicionar tarefa com delay de 2 segundos entre cada bot
                tasks.append(asyncio.create_task(delayed_bot(bot_func, i * 2)))
            
            print(f"📈 {len(tasks)} bots configurados para execução paralela com delays escalonados")
            
            # Executar todas as tarefas em paralelo com timeout
            try:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=None)
            except asyncio.TimeoutError:
                print("⏰ Timeout na execução dos bots")
            except Exception as e:
                print(f"❌ Erro durante execução dos bots: {e}")
                raise
            
        except KeyboardInterrupt:
            print("\n⏹️  Interrupção manual detectada...")
            break
            
        except Exception as e:
            # Incrementar contador de tentativas
            tentativas_reconexao += 1
            
            # Verificar se atingiu o limite de tentativas
            if tentativas_reconexao > max_tentativas_reconexao:
                print(f"\n❌ Erro crítico após {max_tentativas_reconexao} tentativas: {e}")
                print("🔄 Reiniciando o sistema completamente...")
                break
            
            # Calcular tempo de espera com backoff exponencial
            tempo_espera = min(30, 2 ** tentativas_reconexao)  # Máximo de 30 segundos
            print(f"\n⚠️ Erro de conexão: {e}")
            print(f"🔄 Tentativa {tentativas_reconexao}/{max_tentativas_reconexao}")
            print(f"⏳ Aguardando {tempo_espera} segundos antes de reconectar...")
            
            # Fechar conexão atual se existir
            if api:
                try:
                    await api.clear()
                except:
                    pass
            
            # Aguardar antes de tentar novamente
            await asyncio.sleep(tempo_espera)

# 8. PONTO DE ENTRADA DO SCRIPT
if __name__ == "__main__":
    """
    Ponto de entrada principal do script
    """
    print("🎯 SISTEMA DE TRADING AUTOMATIZADO - DERIV BOTS")
    print("=" * 60)
    
    try:
        # Executar o sistema principal dos bots
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Sistema interrompido pelo usuário (Ctrl+C)")
        print("🔄 Finalizando operações em andamento...")
        print("✅ Sistema encerrado com segurança!")
    except Exception as e:
        print(f"\n❌ Erro crítico no sistema: {e}")
        print("🔧 Verifique as configurações e tente novamente.")