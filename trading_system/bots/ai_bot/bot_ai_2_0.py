"""
BotAI 2.0 - Original Martingale
Estratégia de compra contínua com martingale simples
Compra DIGITOVER 1 no R_100 continuamente com martingale fator 1

Este bot executa operações contínuas apostando que o último dígito
será maior que 1, aplicando martingale simples após perdas.
"""

import asyncio
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, obter_ultimo_tick, extrair_ultimo_digito,
    log_resultado_operacao, criar_parametros_compra,
    validar_e_ajustar_stake
)
from ...config.settings import BotSpecificConfig
import logging

logger = logging.getLogger(__name__)

async def bot_ai_2_0(api) -> None:
    """
    BotAI 2.0 - Original Martingale
    Estratégia: Compra DIGITOVER 1 continuamente no R_100 com martingale simples
    Com stops infinitos e operação contínua
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "BotAI_2.0_Original_Martingale"
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Parâmetros de Gestão (conforme requisitos)
    stake_inicial = 1.0
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = 'R_100'           # Manter ativo
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   📊 Estratégia: Operação contínua DIGITOVER 1")
    print(f"   🔄 Martingale: Simples (fator 1)")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo (sempre infinitos)
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último tick do ativo para monitoramento
            ultimo_preco = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_preco is None:
                await asyncio.sleep(1)
                continue
                
            ultimo_digito = extrair_ultimo_digito(ultimo_preco)
            
            print(f"🔍 {nome_bot}: Último dígito {ativo}: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Operação Contínua - Sempre comprar DIGITOVER 1 (sem análise de mercado)
            print(f"🎯 {nome_bot}: Executando trade contínuo DIGITOVER 1")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Construir parâmetros da compra (sempre DIGITOVER 1)
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type='DIGITOVER',
                symbol=ativo,
                barrier=1
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITOVER 1 | Stake: ${stake_atual:.2f}")
            
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
            
            # Lógica Pós-Trade com Martingale Simples
            if lucro > 0:
                # Vitória - Reset stake para inicial
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, True)
                stake_atual = stake_inicial
                print(f"✅ {nome_bot}: Vitória! Stake resetado para inicial: ${stake_atual:.2f}")
            else:
                # Derrota - Aplicar martingale simples (fator 1)
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, False)
                perda = abs(lucro)
                stake_atual = perda  # Martingale simples: stake = valor da perda
                print(f"❌ {nome_bot}: Derrota! Próximo stake com martingale simples: ${stake_atual:.2f}")
            
            # Pausa final - operação contínua
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro de conexão no {nome_bot}: {e}. Tentando novamente em 10 segundos...")
            logger.error(f"Erro de conexão no {nome_bot}: {e}")
            await asyncio.sleep(10)