"""
Bot BK_1.0 Premium: Estratégia baseada em análise de dígitos com sistema de pausa por risco
e martingale simples

Este bot opera no ativo 1HZ10V com contratos DIGITUNDER, pausando quando detecta
dígitos de risco (8 ou 9) e aplicando martingale simples após perdas.
"""

import asyncio
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, obter_ultimo_tick, extrair_ultimo_digito,
    log_resultado_operacao, criar_parametros_compra,
    validar_e_ajustar_stake, handle_websocket_error, safe_api_call, is_websocket_error
)
from ...config.settings import BotSpecificConfig
import logging

logger = logging.getLogger(__name__)

async def bot_bk_1_0(api) -> None:
    """
    Bot BK_1.0 Premium: Estratégia baseada em análise de dígitos com sistema de pausa por risco
    e martingale simples com stops ilimitados
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "BK_BOT_1.0_PREMIUM"
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Parâmetros de Gestão (conforme requisitos)
    stake_inicial = 1.0
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = '1HZ10V'          # Conforme especificado
    
    # Inicialização das variáveis
    stake_atual = stake_inicial
    total_profit = 0
    loss_seguidas = 0
    pausado_por_risco = False
    retry_count = 0
    max_retries = 5
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   🏪 Ativo: {ativo}")
    print(f"   🔄 Martingale: Simples (fator 1)")
    print(f"   ⚠️ Sistema de pausa por risco: Ativo (dígitos 8 e 9)")
    
    while True:
        try:
            # Verificar Stop Loss/Win (sempre infinitos)
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último tick do ativo usando safe_api_call
            ultimo_preco = await safe_api_call(obter_ultimo_tick, api, ativo, nome_bot)
            if ultimo_preco is None:
                await asyncio.sleep(2)
                continue
                
            ultimo_digito = extrair_ultimo_digito(ultimo_preco)
            
            print(f"🔍 {nome_bot}: Último dígito: {ultimo_digito} | Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f} | Perdas: {loss_seguidas}")
            
            # Verificar dígito de risco (8 ou 9) - Lógica mantida
            if ultimo_digito in [8, 9]:
                if not pausado_por_risco:
                    pausado_por_risco = True
                    logger.warning(f"⚠️ {nome_bot}: Dígito de Risco Detectado ({ultimo_digito}). Pausando...")
                    print(f"⚠️ {nome_bot}: Dígito de Risco Detectado ({ultimo_digito}). Pausando...")
                await asyncio.sleep(2)
                continue
            
            # Verificar se deve reativar o bot - Lógica mantida
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
            # Definir a predição baseada nas perdas seguidas - Lógica mantida
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
            
            # Executar compra usando safe_api_call
            contract_id = await safe_api_call(executar_compra, api, parametros_da_compra, nome_bot)
            if contract_id is None:
                await asyncio.sleep(2)
                continue
            
            # Aguardar resultado usando safe_api_call
            lucro = await safe_api_call(aguardar_resultado_contrato, api, contract_id, nome_bot)
            if lucro is None:
                await asyncio.sleep(2)
                continue
            
            # Atualizar lucro total
            total_profit += lucro
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Lógica Pós-Trade com Martingale Simples
            if lucro > 0:
                # Vitória - Reset stake para inicial
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, True)
                stake_atual = stake_inicial
                loss_seguidas = 0
                print(f"✅ {nome_bot}: Vitória! Stake resetado para inicial: ${stake_atual:.2f}")
            else:
                # Derrota - Aplicar martingale simples (fator 1)
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, False)
                loss_seguidas += 1
                perda = abs(lucro)
                stake_atual = perda  # Martingale simples: stake = valor da perda
                print(f"❌ {nome_bot}: Derrota! Perdas seguidas: {loss_seguidas} | Próximo stake com martingale simples: ${stake_atual:.2f}")
            
            # Reset contador de tentativas após operação bem-sucedida
            retry_count = 0
            
            # Pausa entre operações
            await asyncio.sleep(2)
            
        except Exception as e:
            if is_websocket_error(e):
                retry_count = await handle_websocket_error(e, nome_bot, retry_count, max_retries)
                if retry_count >= max_retries:
                    logger.error(f"❌ {nome_bot}: Máximo de tentativas de reconexão atingido. Encerrando...")
                    break
            else:
                print(f"❌ Erro no {nome_bot}: {e}. Tentando novamente em 10 segundos...")
                logger.error(f"Erro no {nome_bot}: {e}")
                await asyncio.sleep(10)