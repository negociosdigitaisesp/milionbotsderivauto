"""
Funções auxiliares e helpers para o sistema de trading automatizado
Contém funções comuns utilizadas por todos os bots
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from trading_system.config.settings import get_supabase_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system/logs/bot_logs.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def is_websocket_error(error):
    """
    Verifica se o erro é relacionado a problemas de conexão WebSocket
    
    Args:
        error: Exception ou string do erro
    
    Returns:
        bool: True se for erro de WebSocket, False caso contrário
    """
    error_str = str(error).lower()
    websocket_keywords = [
        'no close frame received',
        'no close frame sent',
        'connection closed',
        'websocket',
        'connection lost',
        'connection reset',
        'connection aborted',
        'network is unreachable',
        'connection timed out',
        'connection refused',
        'connection error',
        'socket error',
        'timeout',
        'disconnected'
    ]
    
    return any(keyword in error_str for keyword in websocket_keywords)

async def handle_websocket_error(bot_name, error, api=None, retry_count=0, max_retries=3):
    """
    Trata erros de WebSocket de forma robusta com reconexão automática
    
    Args:
        bot_name (str): Nome do bot para logging
        error: Exceção capturada
        api: Instância da API Deriv (opcional)
        retry_count (int): Número atual de tentativas
        max_retries (int): Máximo de tentativas antes de desistir
    
    Returns:
        bool: True se deve continuar tentando, False se deve parar
    """
    if is_websocket_error(error):
        print(f"🔌 {bot_name}: Erro de conexão WebSocket detectado: {error}")
        
        # Tentar fechar conexão existente se houver
        if api:
            try:
                await api.disconnect()
                print(f"🔌 {bot_name}: Conexão anterior fechada")
            except Exception:
                pass  # Ignorar erros ao fechar
        
        # Verificar se deve continuar tentando
        if retry_count >= max_retries:
            print(f"❌ {bot_name}: Máximo de tentativas de reconexão atingido ({max_retries})")
            print(f"⏳ {bot_name}: Aguardando 60 segundos antes de resetar contador...")
            await asyncio.sleep(60)
            return True  # Resetar contador e continuar
        
        # Tempo de espera progressivo
        wait_time = min(10 + (retry_count * 5), 30)  # 10s, 15s, 20s, 25s, 30s
        print(f"🔄 {bot_name}: Tentativa {retry_count + 1}/{max_retries} - Aguardando {wait_time}s...")
        await asyncio.sleep(wait_time)
        return True
    
    else:
        # Erro não relacionado a WebSocket
        print(f"❌ {bot_name}: Erro não relacionado à conexão: {error}")
        await asyncio.sleep(5)  # Pausa menor para outros tipos de erro
        return True

async def safe_api_call(api_func, bot_name, operation_name, *args, **kwargs):
    """
    Executa uma chamada à API de forma segura com tratamento de erros WebSocket
    
    Args:
        api_func: Função da API a ser chamada
        bot_name (str): Nome do bot para logging
        operation_name (str): Nome da operação para logging
        *args, **kwargs: Argumentos para a função da API
    
    Returns:
        tuple: (success: bool, result: any)
    """
    try:
        result = await api_func(*args, **kwargs)
        return True, result
    except Exception as e:
        if is_websocket_error(e):
            print(f"🔌 {bot_name}: Erro WebSocket em {operation_name}: {e}")
        else:
            print(f"❌ {bot_name}: Erro em {operation_name}: {e}")
        return False, None

def salvar_operacao(nome_bot: str, lucro: float) -> bool:
    """
    Salva o resultado de uma operação no banco de dados Supabase
    
    Args:
        nome_bot (str): Nome identificador do bot
        lucro (float): Valor do lucro/prejuízo da operação
        
    Returns:
        bool: True se a operação foi salva com sucesso, False caso contrário
    """
    try:
        supabase = get_supabase_client()
        
        # Preparar dados para inserção
        data = {
            'nome_bot': nome_bot,
            'lucro': lucro,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Inserir dados na tabela 'operacoes'
        result = supabase.table('operacoes').insert(data).execute()
        
        logger.info(f"✅ Operação salva com sucesso - Bot: {nome_bot}, Lucro: {lucro}")
        print(f"✅ Operação salva com sucesso - Bot: {nome_bot}, Lucro: {lucro}")
        
        return True
        
    except Exception as e:
        error_msg = f"❌ Erro ao salvar operação no Supabase: {e}"
        logger.error(f"{error_msg} - Bot: {nome_bot}, Lucro: {lucro}")
        print(f"{error_msg}\n   Bot: {nome_bot}, Lucro: {lucro}")
        return False

async def aguardar_resultado_contrato(api_manager, contract_id: str, nome_bot: str, max_tentativas: int = 30) -> Optional[float]:
    """
    Aguarda o resultado de um contrato usando proposal_open_contract
    
    Args:
        api: Instância da API da Deriv
        contract_id (str): ID do contrato
        nome_bot (str): Nome do bot para logging
        max_tentativas (int): Número máximo de tentativas (segundos)
        
    Returns:
        Optional[float]: Lucro do contrato ou None se timeout/erro
    """
    contract_finalizado = False
    tentativas = 0
    
    logger.info(f"⏳ {nome_bot}: Aguardando resultado do contrato {contract_id}...")
    print(f"⏳ {nome_bot}: Aguardando resultado do contrato...")
    
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
                logger.warning(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                print(f"⚠️ {nome_bot}: Erro ao verificar status: {contract_status['error']['message']}")
                continue
            
            contract_info = contract_status['proposal_open_contract']
            
            if contract_info.get('is_sold', False):
                contract_finalizado = True
                lucro = float(contract_info.get('profit', 0))
                logger.info(f"✅ {nome_bot}: Contrato finalizado com lucro: {lucro}")
                return lucro
                
        except Exception as e:
            logger.debug(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s) - {str(e)}")
            print(f"⏳ {nome_bot}: Aguardando resultado... ({tentativas}s)")
    
    if not contract_finalizado:
        logger.warning(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
        print(f"⚠️ {nome_bot}: Timeout aguardando resultado do contrato")
        return None
    
    return None

async def executar_compra(api_manager, parametros_da_compra: Dict[str, Any], nome_bot: str) -> Optional[str]:
    """
    Executa uma compra na API da Deriv e retorna o contract_id
    
    Args:
        api: Instância da API da Deriv
        parametros_da_compra (Dict): Parâmetros da compra
        nome_bot (str): Nome do bot para logging
        
    Returns:
        Optional[str]: Contract ID ou None se erro
    """
    try:
        # Validar e ajustar stake antes da compra
        stake_original = parametros_da_compra.get('price', 0)
        stake_validado = validar_e_ajustar_stake(stake_original, nome_bot)
        
        # Atualizar parâmetros com stake validado
        if stake_validado != stake_original:
            parametros_da_compra['price'] = stake_validado
            parametros_da_compra['parameters']['amount'] = stake_validado
            logger.info(f"🔧 {nome_bot}: Stake ajustado para compra: ${stake_validado:.2f}")
            print(f"🔧 {nome_bot}: Stake ajustado para compra: ${stake_validado:.2f}")
        
        logger.info(f"🛒 {nome_bot}: Executando compra com stake ${stake_validado:.2f}...")
        print(f"🛒 {nome_bot}: Executando compra com stake ${stake_validado:.2f}...")
        
        # Fazer a compra
        recibo_compra = await api_manager.buy(parametros_da_compra)
        
        if 'error' in recibo_compra:
            error_msg = f"❌ {nome_bot}: Erro na compra: {recibo_compra['error']['message']}"
            logger.error(error_msg)
            print(error_msg)
            
            # Se ainda houver erro de stake, tentar com valor ainda menor
            if "stake amount is more than" in recibo_compra['error']['message'].lower():
                stake_emergencia = min(stake_validado * 0.3, 5.0)  # 30% do stake ou 5 USD
                logger.warning(f"🚨 {nome_bot}: Tentando compra de emergência com stake ${stake_emergencia:.2f}")
                print(f"🚨 {nome_bot}: Tentando compra de emergência com stake ${stake_emergencia:.2f}")
                
                parametros_da_compra['price'] = stake_emergencia
                parametros_da_compra['parameters']['amount'] = stake_emergencia
                
                # Tentar novamente com stake de emergência
                recibo_compra = await api_manager.buy(parametros_da_compra)
                
                if 'error' in recibo_compra:
                    error_msg = f"❌ {nome_bot}: Erro na compra de emergência: {recibo_compra['error']['message']}"
                    logger.error(error_msg)
                    print(error_msg)
                    return None
            else:
                return None
        
        if 'buy' in recibo_compra and 'contract_id' in recibo_compra['buy']:
            contract_id = recibo_compra['buy']['contract_id']
            logger.info(f"📋 {nome_bot}: Contrato criado com sucesso! ID: {contract_id}")
            print(f"📋 {nome_bot}: Contrato criado com sucesso!")
            return contract_id
        else:
            logger.error(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
            print(f"❌ {nome_bot}: Erro: Não foi possível obter contract_id")
            return None
            
    except Exception as e:
        error_msg = f"❌ {nome_bot}: Erro ao executar compra: {e}"
        logger.error(error_msg)
        print(error_msg)
        return None

def verificar_stops(total_profit: float, stop_loss: float, stop_win: float, nome_bot: str) -> str:
    """
    Verifica se os stops de loss ou win foram atingidos
    CONFIGURAÇÃO VPS: Stops infinitos para operação contínua
    
    Args:
        total_profit (float): Lucro total atual
        stop_loss (float): Valor do stop loss (ignorado se infinito)
        stop_win (float): Valor do stop win (ignorado se infinito)
        nome_bot (str): Nome do bot para logging
        
    Returns:
        str: Sempre 'continue' para operação infinita em VPS
    """
    # Verificar se os stops estão configurados como infinitos
    if stop_loss == float('inf') and stop_win == float('inf'):
        # Stops infinitos - apenas log do status atual
        if total_profit > 0:
            logger.info(f"📈 {nome_bot}: Profit atual: ${total_profit:.2f} (Stops infinitos - Operação contínua)")
        elif total_profit < 0:
            logger.info(f"📉 {nome_bot}: Loss atual: ${total_profit:.2f} (Stops infinitos - Operação contínua)")
        else:
            logger.info(f"⚖️ {nome_bot}: Break-even: ${total_profit:.2f} (Stops infinitos - Operação contínua)")
        
        return 'continue'
    
    # Manter lógica original para compatibilidade (caso stops não sejam infinitos)
    if stop_win != float('inf') and total_profit >= stop_win:
        msg = f"🎯 {nome_bot}: STOP WIN ATINGIDO! Profit: ${total_profit:.2f} >= ${stop_win}"
        logger.info(msg)
        print(msg)
        salvar_operacao(nome_bot, 0)  # Registro final
        return 'stop_win'
    elif stop_loss != float('inf') and total_profit <= -stop_loss:
        msg = f"🛑 {nome_bot}: STOP LOSS ATINGIDO! Profit: ${total_profit:.2f} <= ${-stop_loss}"
        logger.info(msg)
        print(msg)
        salvar_operacao(nome_bot, 0)  # Registro final
        return 'stop_loss'
    
    return 'continue'

async def obter_ultimo_tick(api_manager, symbol: str, nome_bot: str) -> Optional[float]:
    """
    Obtém o último tick de um símbolo
    
    Args:
        api: Instância da API da Deriv
        symbol (str): Símbolo do ativo
        nome_bot (str): Nome do bot para logging
        
    Returns:
        Optional[float]: Último preço ou None se erro
    """
    try:
        tick_response = await api_manager.ticks_history({
            "ticks_history": symbol,
            "count": 1,
            "end": "latest"
        })
        
        if 'error' in tick_response:
            logger.error(f"❌ {nome_bot}: Erro ao obter tick: {tick_response['error']['message']}")
            print(f"❌ {nome_bot}: Erro ao obter tick: {tick_response['error']['message']}")
            return None
        
        ultimo_tick = tick_response['history']['prices'][-1]
        return float(ultimo_tick)
        
    except Exception as e:
        logger.error(f"❌ {nome_bot}: Erro ao obter último tick: {e}")
        print(f"❌ {nome_bot}: Erro ao obter último tick: {e}")
        return None

def extrair_ultimo_digito(preco: float) -> int:
    """
    Extrai o último dígito de um preço
    
    Args:
        preco (float): Preço do ativo
        
    Returns:
        int: Último dígito do preço
    """
    return int(str(preco).replace('.', '')[-1])

def log_resultado_operacao(nome_bot: str, lucro: float, total_profit: float, stake_usado: float, vitoria: bool):
    """
    Registra o resultado de uma operação nos logs
    
    Args:
        nome_bot (str): Nome do bot
        lucro (float): Lucro/prejuízo da operação
        total_profit (float): Lucro total acumulado
        stake_usado (float): Valor apostado
        vitoria (bool): Se foi vitória ou derrota
    """
    if vitoria:
        msg = f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f} | Stake usado: ${stake_usado:.2f} | Total: ${total_profit:.2f}"
    else:
        msg = f"❌ {nome_bot}: DERROTA! Perda: ${lucro:.2f} | Stake usado: ${stake_usado:.2f} | Total: ${total_profit:.2f}"
    
    logger.info(msg)
    print(msg)

def criar_parametros_compra(stake: float, contract_type: str, symbol: str, barrier: int, 
                          currency: str = "USD", duration: int = 1, duration_unit: str = "t") -> Dict[str, Any]:
    """
    Cria os parâmetros padrão para uma compra
    
    Args:
        stake (float): Valor da aposta
        contract_type (str): Tipo do contrato
        symbol (str): Símbolo do ativo
        barrier (int): Barreira/predição
        currency (str): Moeda (padrão: USD)
        duration (int): Duração (padrão: 1)
        duration_unit (str): Unidade de duração (padrão: t)
        
    Returns:
        Dict[str, Any]: Parâmetros formatados para a API
    """
    # CORREÇÃO: Formatar stake para exatamente 2 casas decimais
    stake_formatado = formatar_valor_monetario(stake)
    
    return {
        'buy': '1',
        'subscribe': 1,
        'price': stake_formatado,
        'parameters': {
            'amount': stake_formatado,
            'basis': 'stake',
            'contract_type': contract_type,
            'currency': currency,
            'duration': duration,
            'duration_unit': duration_unit,
            'symbol': symbol,
            'barrier': barrier
        }
    }

def calcular_martingale(lucro: float, stake_atual: float, stake_inicial: float, stake_maximo: float, nome_bot: str, nivel_martingale: int = 0, max_martingale_levels: int = 5) -> tuple[float, int]:
    """
    Calcula o próximo stake baseado na estratégia de martingale com limite de níveis
    
    Args:
        lucro (float): Lucro/prejuízo da operação anterior
        stake_atual (float): Stake atual
        stake_inicial (float): Stake inicial (1.0)
        stake_maximo (float): Stake máximo permitido
        nome_bot (str): Nome do bot para logging
        nivel_martingale (int): Nível atual do martingale (0 = stake inicial)
        max_martingale_levels (int): Máximo de níveis de martingale permitidos (padrão: 5)
        
    Returns:
        tuple[float, int]: (Próximo valor do stake, Novo nível do martingale)
    """
    if lucro > 0:
        # Vitória - Reset para stake inicial
        novo_stake = formatar_valor_monetario(stake_inicial)
        novo_nivel = 0
        logger.info(f"✅ {nome_bot}: Vitória! Reset stake para ${novo_stake:.2f} (Nível 0)")
        print(f"✅ {nome_bot}: Vitória! Reset stake para ${novo_stake:.2f} (Nível 0)")
    else:
        # Derrota - Verificar se pode aplicar martingale
        if nivel_martingale >= max_martingale_levels:
            # Atingiu o limite máximo de martingales - Reset para stake inicial
            novo_stake = formatar_valor_monetario(stake_inicial)
            novo_nivel = 0
            logger.warning(f"🔄 {nome_bot}: Limite de {max_martingale_levels} martingales atingido! Reset para ${novo_stake:.2f}")
            print(f"🔄 {nome_bot}: Limite de {max_martingale_levels} martingales atingido! Reset para ${novo_stake:.2f}")
        else:
            # Aplicar martingale - Dobrar o stake
            novo_stake = formatar_valor_monetario(stake_atual * 2)
            novo_nivel = nivel_martingale + 1
            
            # Verificar se não excede o limite máximo
            if novo_stake > stake_maximo:
                novo_stake = formatar_valor_monetario(stake_maximo)
                logger.warning(f"⚠️ {nome_bot}: Stake limitado ao máximo de ${stake_maximo:.2f} (Nível {novo_nivel})")
                print(f"⚠️ {nome_bot}: Stake limitado ao máximo de ${stake_maximo:.2f} (Nível {novo_nivel})")
            else:
                logger.info(f"🔄 {nome_bot}: Derrota! Martingale Nível {novo_nivel} - Novo stake: ${novo_stake:.2f}")
                print(f"🔄 {nome_bot}: Derrota! Martingale Nível {novo_nivel} - Novo stake: ${novo_stake:.2f}")
    
    return novo_stake, novo_nivel

def validar_e_ajustar_stake(stake: float, nome_bot: str, limite_plataforma: float = 20.0) -> float:
    """
    Valida e ajusta o stake para garantir que não exceda os limites da plataforma
    
    Args:
        stake (float): Valor do stake a ser validado
        nome_bot (str): Nome do bot para logging
        limite_plataforma (float): Limite máximo da plataforma (padrão: 20.0 USD)
        
    Returns:
        float: Stake ajustado dentro dos limites seguros
    """
    # CORREÇÃO: Arredondar para 2 casas decimais primeiro
    stake = round(stake, 2)
    
    # Definir limite seguro (muito conservador)
    limite_seguro = min(limite_plataforma * 0.8, 15.0)  # 80% do limite ou 15 USD
    
    if stake > limite_seguro:
        stake_ajustado = round(limite_seguro, 2)
        logger.warning(f"⚠️ {nome_bot}: Stake ajustado de ${stake:.2f} para ${stake_ajustado:.2f} (limite seguro)")
        print(f"⚠️ {nome_bot}: Stake ajustado de ${stake:.2f} para ${stake_ajustado:.2f} (limite seguro)")
        return stake_ajustado
    
    # Verificar stake mínimo
    stake_minimo = 1.0
    if stake < stake_minimo:
        stake_ajustado = round(stake_minimo, 2)
        logger.warning(f"⚠️ {nome_bot}: Stake ajustado de ${stake:.2f} para ${stake_ajustado:.2f} (mínimo)")
        print(f"⚠️ {nome_bot}: Stake ajustado de ${stake:.2f} para ${stake_ajustado:.2f} (mínimo)")
        return stake_ajustado
    
    return round(stake, 2)

def formatar_valor_monetario(valor: float) -> float:
    """
    Formata valor monetário para exatamente 2 casas decimais
    
    Args:
        valor (float): Valor a ser formatado
        
    Returns:
        float: Valor arredondado para 2 casas decimais
    """
    return round(float(valor), 2)