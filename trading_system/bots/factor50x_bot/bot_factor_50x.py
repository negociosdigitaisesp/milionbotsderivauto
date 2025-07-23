"""
Bot Factor50X - Conservador
Estratégia com stake fixo para evitar limites de stake
Estratégia: Aguarda dígito 1 no R_100 para comprar DIGITOVER 3

Este bot opera de forma conservadora, aguardando condições específicas
antes de executar operações com stake fixo (sem martingale).
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

async def bot_factor_50x(api) -> None:
    """
    Bot Factor50X - Conservador
    Estratégia: Aguarda dígito 1 no R_100 para comprar DIGITOVER 3
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "Factor50X_Conservador"
    config = BotSpecificConfig.FACTOR50X_CONFIG
    
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
    print(f"   📊 Estratégia: Martingale ativado")
    print(f"   🏪 Mercado: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último tick do ativo
            ultimo_preco = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_preco is None:
                await asyncio.sleep(1)
                continue
                
            ultimo_digito = extrair_ultimo_digito(ultimo_preco)
            
            print(f"🔍 {nome_bot}: Último dígito {ativo}: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Condição de Compra: Se o último dígito for EXATAMENTE 1
            if ultimo_digito == 1:
                print(f"🎯 {nome_bot}: Dígito 1 detectado! Preparando para comprar DIGITOVER 3.")
                
                # Validar e ajustar stake antes da compra
                stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
                
                # Construir parâmetros da compra
                parametros_da_compra = criar_parametros_compra(
                    stake=stake_atual,
                    contract_type='DIGITOVER',
                    symbol=ativo,
                    barrier=3
                )
                
                print(f"📈 {nome_bot}: Comprando DIGITOVER 3 | Stake: ${stake_atual:.2f}")
                
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
                
                # Tratamento do resultado
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