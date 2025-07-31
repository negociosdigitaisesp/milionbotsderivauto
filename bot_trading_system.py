"""
Sistema de Trading Automatizado - Múltiplos Bots Deriv
Executa estratégias de trading em paralelo usando asyncio
"""

# 1. IMPORTAÇÕES
import asyncio
import os
from deriv_api import DerivAPI
from supabase import create_client, Client
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import random

# Importar bot_scale do módulo trading_system
from trading_system.bots.scale_bot import bot_scale

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# 2. CONFIGURAÇÕES E CONEXÃO COM SUPABASE
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

async def bot_bk_1_0(api):
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
            ticks_history = await api.ticks_history({
                "ticks_history": "1HZ10V",
                "count": 1,
                "end": "latest"
            })
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
            recibo_compra = await api.buy(parametros_da_compra)
            
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
                        contract_status = await api.proposal_open_contract({
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

async def bot_2_digito_par(api):
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

async def bot_factor_50x(api):
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
            tick_response = await api.ticks_history({
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
                recibo_compra = await api.buy(parametros_da_compra)
                
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
                            contract_status = await api.proposal_open_contract({
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

async def bot_ai_2_0(api):
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
            recibo_compra = await api.buy(parametros_da_compra)
            
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
                        contract_status = await api.proposal_open_contract({
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

async def bot_apalancamiento(api):
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
            recibo_compra = await api.buy(parametros_da_compra)
            
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
                        contract_status = await api.proposal_open_contract({
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

async def wolf_bot_2_0(api):
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
            ticks_response = await api.ticks_history({
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
                recibo_compra = await api.buy(parametros_da_compra)
                
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
                            contract_status = await api.proposal_open_contract({
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

async def bot_sniper_martingale(api):
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
            ticks_response = await api.ticks_history({
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
            try:
                recibo_compra = await api.buy(parametros_da_compra)
                
                if 'error' in recibo_compra:
                    print(f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}")
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                # Verificar se o erro é relacionado ao limite de stake
                if 'more than the maximum purchase price' in str(e):
                    print(f"⚠️  {nome_bot}: Stake de ${stake_atual:.2f} excedeu o limite da corretora. Resetando para o valor inicial.")
                    stake_atual = stake_inicial
                    continue
                else:
                    print(f"❌ {nome_bot}: Erro na compra: {e}")
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
                        contract_status = await api.proposal_open_contract({
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

async def bot_quantum_fixed_stake(api):
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
            recibo_compra = await api.buy(parametros_da_compra)
            
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
                        contract_status = await api.proposal_open_contract({
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
            
            # Reset contador de tentativas após conexão bem-sucedida
            tentativas_reconexao = 0
            
            # Verificar conexão com Supabase
            try:
                supabase.table('operacoes').select("*").limit(1).execute()
                print("✅ Conexão com Supabase verificada!")
            except Exception as e:
                print(f"⚠️  Aviso: Problema na conexão com Supabase: {e}")
            
            print("\n🤖 Iniciando execução dos bots em paralelo...")
            
            # Criar lista de tarefas para executar os bots em paralelo
            tasks = [
                asyncio.create_task(bot_bk_1_0(api)),
                asyncio.create_task(bot_factor_50x(api)),
                asyncio.create_task(bot_ai_2_0(api)),
                asyncio.create_task(bot_apalancamiento(api)),
                asyncio.create_task(wolf_bot_2_0(api)),
                asyncio.create_task(bot_sniper_martingale(api)),
                asyncio.create_task(bot_quantum_fixed_stake(api)),
                asyncio.create_task(bot_scale(api)),
                # TODO: Adicionar os outros 3 bots aqui quando forem criados
                # asyncio.create_task(bot_8_macd_divergence(api)),
                # asyncio.create_task(bot_9_support_resistance(api)),
                # asyncio.create_task(bot_10_volume_analysis(api)),
            ]
            
            print(f"📈 {len(tasks)} bots configurados para execução paralela")
            
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
            
            # Verificar se é erro de WebSocket
            error_str = str(e).lower()
            is_websocket_error = any(keyword in error_str for keyword in [
                'no close frame received',
                'connection closed',
                'websocket',
                'connection lost',
                'connection reset',
                'connection aborted',
                'network is unreachable',
                'connection timed out'
            ])
            
            if is_websocket_error:
                print(f"🔌 Erro de conexão WebSocket detectado: {e}")
                print(f"🔄 Tentativa de reconexão {tentativas_reconexao}/{max_tentativas_reconexao}")
            else:
                print(f"❌ Erro não relacionado à conexão: {e}")
            
            # Cancelar todas as tarefas pendentes
            if tasks:
                print("🛑 Cancelando tarefas pendentes...")
                for task in tasks:
                    if not task.done():
                        task.cancel()
                
                # Aguardar cancelamento das tarefas
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception:
                    pass  # Ignorar erros de cancelamento
            
            # Fechar conexão API se existir
            if api:
                try:
                    await api.disconnect()
                    print("🔌 Conexão API fechada")
                except Exception:
                    pass  # Ignorar erros ao fechar conexão
            
            # Verificar se deve continuar tentando reconectar
            if tentativas_reconexao >= max_tentativas_reconexao:
                print(f"❌ Máximo de tentativas de reconexão atingido ({max_tentativas_reconexao})")
                print("🔄 Resetando contador e tentando novamente...")
                tentativas_reconexao = 0
                tempo_espera = 60  # Esperar 1 minuto antes de resetar
            else:
                # Tempo de espera progressivo: 15s, 30s, 45s, 60s, 75s
                tempo_espera = min(15 * tentativas_reconexao, 75)
            
            print(f"⏳ Aguardando {tempo_espera} segundos antes de tentar reconectar...")
            await asyncio.sleep(tempo_espera)
            
            # O loop while True fará com que o sistema tente reconectar automaticamente
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
            
            print("🔚 Encerrando conexões...")

# 6. PONTO DE ENTRADA DO SCRIPT
if __name__ == "__main__":
    """
    Ponto de entrada principal do script
    Executa o sistema com tratamento de interrupção por teclado
    """
    print("=" * 60)
    print("🎯 SISTEMA DE TRADING AUTOMATIZADO - DERIV BOTS")
    print("=" * 60)
    
    try:
        # Executar o sistema principal
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Sistema interrompido pelo usuário (Ctrl+C)")
        print("🔄 Finalizando operações em andamento...")
        print("✅ Sistema encerrado com segurança!")
    except Exception as e:
        print(f"\n❌ Erro crítico no sistema: {e}")
        print("🔧 Verifique as configurações e tente novamente.")