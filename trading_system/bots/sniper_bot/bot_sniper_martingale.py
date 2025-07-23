"""
Bot Sniper Martingale - Estratégia baseada em SMA com Martingale
Opera com base na Média Móvel Simples (SMA) e aplica martingale após perdas

Este bot analisa a tendência usando SMA e executa operações com
sistema de martingale para recuperação de perdas.
"""

import asyncio
from typing import Optional, List
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, obter_ultimo_tick, extrair_ultimo_digito,
    log_resultado_operacao, criar_parametros_compra, calcular_martingale,
    validar_e_ajustar_stake
)
from ...config.settings import BotSpecificConfig
import logging

logger = logging.getLogger(__name__)

async def calcular_sma(api, symbol: str, periodo: int = 10) -> Optional[float]:
    """
    Calcula a Média Móvel Simples (SMA) dos últimos ticks
    
    Args:
        api: Instância da API da Deriv
        symbol: Símbolo do ativo
        periodo: Número de períodos para calcular a SMA
        
    Returns:
        float: Valor da SMA ou None se erro
    """
    try:
        ticks = []
        for _ in range(periodo):
            tick = await obter_ultimo_tick(api, symbol)
            if tick is not None:
                ticks.append(tick)
            await asyncio.sleep(0.5)  # Aguardar entre ticks
        
        if len(ticks) >= periodo:
            sma = sum(ticks) / len(ticks)
            return sma
        return None
    except Exception as e:
        logger.error(f"Erro ao calcular SMA: {e}")
        return None

async def bot_sniper_martingale(api) -> None:
    """
    Bot Sniper Martingale - Estratégia baseada em SMA com Martingale
    Opera com base na Média Móvel Simples (SMA) e aplica martingale após perdas
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "Bot_Sniper_Martingale"
    config = BotSpecificConfig.SNIPER_CONFIG
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Definir parâmetros fixos
    stake_inicial = config['stake_inicial']
    stake_maximo = config['stake_maximo']
    stop_loss = config['stop_loss']
    stop_win = config['stop_win']
    ativo = config['symbol']
    periodo_sma = config.get('periodo_sma', 10)
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Stake máximo: ${stake_maximo}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   📈 Estratégia: SMA + Martingale")
    print(f"   📊 Período SMA: {periodo_sma}")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter tick atual e calcular SMA
            tick_atual = await obter_ultimo_tick(api, ativo)
            if tick_atual is None:
                await asyncio.sleep(1)
                continue
            
            sma_atual = await calcular_sma(api, ativo, periodo_sma)
            if sma_atual is None:
                await asyncio.sleep(1)
                continue
            
            # Lógica de decisão baseada na SMA
            if tick_atual > sma_atual:
                # Preço acima da SMA - tendência de alta
                contract_type = "DIGITOVER"
                barrier = 5
                direcao = "ALTA"
            else:
                # Preço abaixo da SMA - tendência de baixa
                contract_type = "DIGITUNDER"
                barrier = 4
                direcao = "BAIXA"
            
            print(f"📊 {nome_bot}: Tick: {tick_atual:.5f} | SMA: {sma_atual:.5f} | Tendência: {direcao}")
            print(f"💰 {nome_bot}: Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Construir parâmetros da compra
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type=contract_type,
                symbol=ativo,
                barrier=barrier
            )
            
            print(f"📈 {nome_bot}: Comprando {contract_type} {barrier} | Stake: ${stake_atual:.2f}")
            
            # Executar compra
            contract_id = await executar_compra(api, parametros_da_compra, nome_bot)
            if contract_id is None:
                await asyncio.sleep(1)
                continue
            
            # Aguardar resultado
            lucro = await aguardar_resultado_contrato(api, contract_id, nome_bot)
            if lucro is None:
                await asyncio.sleep(1)
                continue
            
            # Atualizar total_profit
            total_profit += lucro
            stake_usado = stake_atual
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado
            if lucro > 0:
                # Vitória - Reset stake usando martingale
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
            else:
                # Derrota - Aplicar martingale
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
                print(f"🔄 {nome_bot}: Martingale aplicado - Novo stake: ${stake_atual:.2f}")
            
        except Exception as e:
            error_msg = f"❌ Erro no {nome_bot}: {e}"
            logger.error(error_msg)
            print(error_msg)
        
        # Pausa final - aguardar próxima análise
        await asyncio.sleep(2)