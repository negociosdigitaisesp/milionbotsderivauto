"""
Bot Quantum Fixed Stake - Estratégia com Stake Fixo e Predições Aleatórias
Opera com stake fixo, stop loss/win, predições aleatórias de dígitos e compra contratos DIGITDIFF

Este bot utiliza predições aleatórias para diversificar as operações,
mantendo sempre stake fixo para controle rigoroso de risco.
"""

import asyncio
import random
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

async def bot_quantum_fixed_stake(api) -> None:
    """
    Bot Quantum Fixed Stake - Estratégia com Stake Fixo e Predições Aleatórias
    Opera com stake fixo, stop loss/win, predições aleatórias de dígitos e compra contratos DIGITDIFF
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "Bot_Quantum_Fixed_Stake"
    config = BotSpecificConfig.QUANTUM_CONFIG
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Definir parâmetros fixos
    stake_inicial = config['stake_inicial']
    stake_maximo = config['stake_maximo']
    stop_loss = config['stop_loss']
    stop_win = config['stop_win']
    ativo = config['symbol']
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Stake máximo: ${stake_maximo}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   🎲 Estratégia: Predições aleatórias DIGITDIFF com Martingale")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Gerar predição aleatória (0-9)
            predicao_aleatoria = random.randint(0, 9)
            
            print(f"🎲 {nome_bot}: Predição aleatória: {predicao_aleatoria}")
            print(f"💰 {nome_bot}: Profit: ${total_profit:.2f} | Stake atual: ${stake_atual:.2f}")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Lógica de Compra (sempre DIGITDIFF com predição aleatória)
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type='DIGITDIFF',
                symbol=ativo,
                barrier=predicao_aleatoria
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITDIFF {predicao_aleatoria} | Stake: ${stake_atual:.2f}")
            
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
        
        # Pausa final - aguardar próxima predição
        await asyncio.sleep(1)