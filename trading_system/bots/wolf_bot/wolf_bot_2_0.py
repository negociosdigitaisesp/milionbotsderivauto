"""
Wolf Bot 2.0 - Estratégia Adaptativa com Martingale
Opera com martingale baseado no último dígito do R_100 e no resultado da operação anterior

Este bot adapta sua estratégia baseado no histórico de resultados,
utilizando martingale para gerenciamento de risco.
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

async def wolf_bot_2_0(api) -> None:
    """
    Wolf Bot 2.0 - Estratégia Adaptativa com Martingale
    Opera com martingale baseado no último dígito do R_100 e no resultado da operação anterior
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "Wolf_Bot_2.0"
    config = BotSpecificConfig.WOLF_CONFIG
    
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
    ultima_operacao_ganhou = None  # None, True ou False
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Stake máximo: ${stake_maximo}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   🐺 Estratégia: Adaptativa com Martingale")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último dígito do R_100
            ultimo_tick = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_tick is None:
                await asyncio.sleep(1)
                continue
            
            ultimo_digito = extrair_ultimo_digito(ultimo_tick)
            
            # Lógica adaptativa baseada no último dígito e resultado anterior
            if ultima_operacao_ganhou is None:
                # Primeira operação - usar lógica padrão
                if ultimo_digito in [0, 1, 2, 3, 4]:
                    contract_type = "DIGITOVER"
                    barrier = 5
                    estrategia = "OVER 5 (dígito baixo)"
                else:
                    contract_type = "DIGITUNDER"
                    barrier = 4
                    estrategia = "UNDER 4 (dígito alto)"
            elif ultima_operacao_ganhou:
                # Última operação ganhou - manter estratégia similar
                if ultimo_digito in [0, 1, 2, 3, 4]:
                    contract_type = "DIGITOVER"
                    barrier = 4
                    estrategia = "OVER 4 (mantendo sucesso)"
                else:
                    contract_type = "DIGITUNDER"
                    barrier = 5
                    estrategia = "UNDER 5 (mantendo sucesso)"
            else:
                # Última operação perdeu - inverter estratégia
                if ultimo_digito in [0, 1, 2, 3, 4]:
                    contract_type = "DIGITUNDER"
                    barrier = 6
                    estrategia = "UNDER 6 (invertendo após perda)"
                else:
                    contract_type = "DIGITOVER"
                    barrier = 3
                    estrategia = "OVER 3 (invertendo após perda)"
            
            print(f"🐺 {nome_bot}: Dígito: {ultimo_digito} | Estratégia: {estrategia}")
            print(f"💰 {nome_bot}: Profit: ${total_profit:.2f} | Stake atual: ${stake_atual:.2f}")
            
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
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado com martingale
            if lucro > 0:
                # Vitória
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, True)
                ultima_operacao_ganhou = True
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
            else:
                # Derrota
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, False)
                ultima_operacao_ganhou = False
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
            
        except Exception as e:
            error_msg = f"❌ Erro no {nome_bot}: {e}"
            logger.error(error_msg)
            print(error_msg)
        
        # Pausa final - aguardar próxima análise
        await asyncio.sleep(1)