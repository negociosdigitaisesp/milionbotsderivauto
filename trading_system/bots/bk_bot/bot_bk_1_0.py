"""
Bot BK_1.0: Estratégia baseada em análise de dígitos com sistema de pausa por risco
e martingale adaptativo

Este bot opera no ativo 1HZ10V com contratos DIGITUNDER, pausando quando detecta
dígitos de risco (8 ou 9) e aplicando martingale após perdas.
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

async def bot_bk_1_0(api) -> None:
    """
    Bot BK_1.0: Estratégia baseada em análise de dígitos com sistema de pausa por risco
    e martingale adaptativo
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "BK_BOT_1.0"
    config = BotSpecificConfig.BK_BOT_CONFIG
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Variáveis de estado do bot
    stake_inicial = config['stake_inicial']
    stake_maximo = config['stake_maximo']
    stop_loss = config['stop_loss']
    stop_win = config['stop_win']
    ativo = config['symbol']
    
    # Inicialização das variáveis
    stake_atual = stake_inicial
    total_profit = 0
    loss_seguidas = 0
    pausado_por_risco = False
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🛑 Stop Loss: ${stop_loss}")
    print(f"   🎯 Stop Win: ${stop_win}")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último tick do ativo
            ultimo_preco = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_preco is None:
                await asyncio.sleep(2)
                continue
                
            ultimo_digito = extrair_ultimo_digito(ultimo_preco)
            
            print(f"🔍 {nome_bot}: Último dígito: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f}")
            
            # Verificar dígito de risco (8 ou 9)
            if ultimo_digito in [8, 9]:
                if not pausado_por_risco:
                    pausado_por_risco = True
                    logger.warning(f"⚠️ {nome_bot}: Dígito de Risco Detectado ({ultimo_digito}). Pausando...")
                    print(f"⚠️ {nome_bot}: Dígito de Risco Detectado ({ultimo_digito}). Pausando...")
                await asyncio.sleep(2)
                continue
            
            # Verificar se deve reativar o bot
            if pausado_por_risco and ultimo_digito < 8:
                pausado_por_risco = False
                logger.info(f"✅ {nome_bot}: Reativando bot... (dígito: {ultimo_digito})")
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
            
            # Validar stake antes da compra
            stake_validado = validar_e_ajustar_stake(stake_atual, nome_bot)
            if stake_validado != stake_atual:
                logger.info(f"🔧 {nome_bot}: Stake ajustado de ${stake_atual:.2f} para ${stake_validado:.2f}")
                print(f"🔧 {nome_bot}: Stake ajustado de ${stake_atual:.2f} para ${stake_validado:.2f}")
                stake_atual = stake_validado
            
            # Construir parâmetros da compra
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type='DIGITUNDER',
                symbol=ativo,
                barrier=prediction
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITUNDER {prediction} | Stake: ${stake_atual:.2f}")
            
            # Executar compra
            contract_id = await executar_compra(api, parametros_da_compra, nome_bot)
            if contract_id is None:
                await asyncio.sleep(2)
                continue
            
            # Aguardar resultado
            lucro = await aguardar_resultado_contrato(api, contract_id, nome_bot)
            if lucro is None:
                await asyncio.sleep(2)
                continue
            
            # Atualizar lucro total
            total_profit += lucro
            stake_usado = stake_atual
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Tratamento do resultado
            if lucro > 0:
                # Vitória
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
                # Reset do stake e perdas seguidas usando martingale
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
                loss_seguidas = 0
            else:
                # Derrota
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
                # Aumentar contador de perdas
                loss_seguidas += 1
                # Aplicar martingale
                stake_atual = calcular_martingale(lucro, stake_atual, stake_inicial, stake_maximo, nome_bot)
                print(f"🔄 {nome_bot}: Perdas seguidas: {loss_seguidas} | Próximo stake: ${stake_atual:.2f}")
            
        except Exception as e:
            error_msg = f"❌ Erro no {nome_bot}: {e}"
            logger.error(error_msg)
            print(error_msg)
        
        # Pausa entre operações
        await asyncio.sleep(2)