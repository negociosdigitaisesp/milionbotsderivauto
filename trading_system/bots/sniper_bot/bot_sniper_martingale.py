"""
Sniper Bot Original Martingale - Estratégia baseada em SMA com Martingale Original
Opera com base na Média Móvel Simples (SMA) de 3 períodos e aplica martingale original

Este bot analisa a tendência usando SMA de 3 períodos e executa operações CALL/PUT
com sistema de martingale original para recuperação de perdas.
"""

import asyncio
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, obter_ultimo_tick, log_resultado_operacao, 
    criar_parametros_compra, validar_e_ajustar_stake
)
import logging

logger = logging.getLogger(__name__)

async def calcular_sma_3_periodos(api, symbol: str) -> Optional[float]:
    """
    Calcula a Média Móvel Simples (SMA) de 3 períodos
    
    Args:
        api: Instância da API da Deriv
        symbol: Símbolo do ativo
        
    Returns:
        float: Valor da SMA de 3 períodos ou None se erro
    """
    try:
        ticks = []
        for _ in range(3):
            tick = await obter_ultimo_tick(api, symbol)
            if tick is not None:
                ticks.append(tick)
            await asyncio.sleep(0.3)  # Aguardar entre ticks
        
        if len(ticks) == 3:
            sma = sum(ticks) / 3
            return sma
        return None
    except Exception as e:
        logger.error(f"Erro ao calcular SMA de 3 períodos: {e}")
        return None

async def bot_sniper_martingale(api) -> None:
    """
    Sniper Bot Original Martingale - Estratégia baseada em SMA com Martingale Original
    Opera com base na Média Móvel Simples (SMA) de 3 períodos
    
    Args:
        api: Instância da API da Deriv
    """
    # Parâmetros de Gestão (Lógica Original)
    nome_bot = "Sniper_Bot_Original_Martingale"
    stake_inicial = 0.35
    martingale_fator = 1.05
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = '1HZ100V'
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Fator Martingale: {martingale_fator}")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   📈 Estratégia: SMA 3 períodos + Martingale Original")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último preço de tick
            ultimo_preco = await obter_ultimo_tick(api, ativo)
            if ultimo_preco is None:
                await asyncio.sleep(1)
                continue
            
            # Calcular SMA de 3 períodos
            sma = await calcular_sma_3_periodos(api, ativo)
            if sma is None:
                await asyncio.sleep(1)
                continue
            
            # Lógica de Entrada baseada em SMA
            if ultimo_preco > sma:
                # Condição de Compra CALL: último preço MAIOR que SMA
                contract_type = "CALL"
                direcao = "CALL"
            else:
                # Condição de Compra PUT: último preço MENOR que SMA
                contract_type = "PUT"
                direcao = "PUT"
            
            print(f"📊 {nome_bot}: Último Preço: {ultimo_preco:.5f} | SMA(3): {sma:.5f} | Sinal: {direcao}")
            print(f"💰 {nome_bot}: Profit Total: ${total_profit:.2f} | Stake Atual: ${stake_atual:.2f}")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Construir parâmetros da compra
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type=contract_type,
                symbol=ativo
            )
            
            print(f"📈 {nome_bot}: Comprando {contract_type} | Stake: ${stake_atual:.2f}")
            
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
            
            # Lógica Pós-Trade (Implementar Martingale Original)
            if lucro > 0:
                # Vitória: Redefina stake_atual para o stake_inicial
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
                stake_atual = stake_inicial
                print(f"✅ {nome_bot}: VITÓRIA! Stake resetado para inicial: ${stake_atual:.2f}")
            else:
                # Derrota: Calcule o novo stake multiplicando pelo martingale_fator
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
                stake_atual = stake_atual * martingale_fator
                print(f"❌ {nome_bot}: DERROTA! Martingale aplicado - Novo stake: ${stake_atual:.2f} (Fator: {martingale_fator})")
            
            # Pausa entre operações
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro de conexão no {nome_bot}: {e}. Tentando novamente em 10 segundos...")
            logger.error(f"❌ Erro de conexão no {nome_bot}: {e}. Tentando novamente em 10 segundos...")
            await asyncio.sleep(10)