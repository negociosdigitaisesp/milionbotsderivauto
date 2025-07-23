"""
Bot del Apalancamiento - Estratégia com Alternância e Stake Fixo
Alterna entre DIGITUNDER e DIGITOVER a cada 100 trades (sem martingale)

Este bot alterna estratégias baseado no número de trades executados,
mantendo sempre stake fixo para controle de risco.
"""

import asyncio
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, obter_ultimo_tick, extrair_ultimo_digito,
    log_resultado_operacao, criar_parametros_compra, calcular_martingale,
    validar_e_ajustar_stake
)
from ...config.settings import BotSpecificConfig
import logging

logger = logging.getLogger(__name__)

async def bot_apalancamiento(api) -> None:
    """
    Bot del Apalancamiento - Estratégia com Alternância e Stake Fixo
    Alterna entre DIGITUNDER e DIGITOVER a cada 100 trades (sem martingale)
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "Bot_Apalancamiento"
    config = BotSpecificConfig.APALANCAMIENTO_CONFIG
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Definir parâmetros fixos
    stake_inicial = config['stake_inicial']
    stake_maximo = config['stake_maximo']
    stop_loss = config['stop_loss']
    stop_win = config['stop_win']
    ativo = config['symbol']
    limite_trades_para_troca = config.get('limite_trades_para_troca', 100)
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    trades_counter = 0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Stake máximo: ${stake_maximo}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   📊 Estratégia: Alternância com Martingale")
    print(f"   🔀 Troca estratégia a cada: {limite_trades_para_troca} trades")
    print(f"   🏪 Mercado: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
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
            print(f"📊 {nome_bot}: Profit: ${total_profit:.2f} | Stake atual: ${stake_atual:.2f}")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Lógica de Compra
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type=contract_type,
                symbol=ativo,
                barrier=prediction
            )
            
            print(f"📈 {nome_bot}: Comprando {contract_type} {prediction} | Stake: ${stake_atual:.2f}")
            
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
            
            # Após a Compra - Incrementar contador
            trades_counter += 1
            
            # Atualizar total_profit
            total_profit += lucro
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado com martingale
            if lucro > 0:
                # Vitória - Reset stake usando martingale
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, True)
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
            else:
                # Derrota - Aplicar martingale
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, False)
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
                print(f"📊 {nome_bot}: Próxima aposta com martingale: ${stake_atual:.2f}")
            
        except Exception as e:
            error_msg = f"❌ Erro no {nome_bot}: {e}"
            logger.error(error_msg)
            print(error_msg)
        
        # Pausa final - checar mercado a cada segundo
        await asyncio.sleep(1)