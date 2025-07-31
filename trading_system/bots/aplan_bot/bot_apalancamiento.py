"""
Bot del Apalancamiento Original - Estratégia com Alternância, Martingale Agressivo e Controle de Risco
Alterna entre DIGITUNDER e DIGITOVER a cada 100 trades com martingale fator 2.1

Este bot alterna estratégias baseado no número de trades executados,
aplicando martingale agressivo com controle de perdas seguidas e predição adaptativa.
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

async def bot_apalancamiento(api) -> None:
    """
    Bot del Apalancamiento Original - Estratégia com Alternância, Martingale Agressivo e Controle de Risco
    Alterna entre DIGITUNDER e DIGITOVER a cada 100 trades com martingale fator 2.1
    
    Args:
        api: Instância da API da Deriv
    """
    nome_bot = "Bot_Apalancamiento"
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Parâmetros de Gestão (conforme requisitos)
    stake_inicial = 1.0
    martingale_fator = 2.1
    max_loss_seguidas = 6
    limite_trades_para_troca = 100
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = '1HZ75V'          # Conforme especificado
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    trades_counter = 0
    loss_seguidas = 0
    retry_count = 0
    max_retries = 3
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Martingale fator: {martingale_fator}")
    print(f"   ⚠️ Máx. perdas seguidas: {max_loss_seguidas}")
    print(f"   🔀 Troca estratégia a cada: {limite_trades_para_troca} trades")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   📊 Estratégia: Alternância com Martingale Agressivo")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo (sempre infinitos)
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Lógica de Controle de Risco (Antes da Compra)
            if loss_seguidas >= max_loss_seguidas:
                logger.warning(f"⚠️ {nome_bot}: Máximo de perdas seguidas atingido ({loss_seguidas}). Resetando...")
                print(f"⚠️ {nome_bot}: Máximo de perdas seguidas atingido ({loss_seguidas}). Resetando...")
                loss_seguidas = 0
                stake_atual = stake_inicial
                print(f"🔄 {nome_bot}: Reset completo - Stake: ${stake_atual:.2f} | Perdas: {loss_seguidas}")
            
            # Definir a Estratégia (Alternância a cada 100 trades)
            estrategia_atual = (trades_counter // limite_trades_para_troca) % 2
            if estrategia_atual == 0:
                contract_type = "DIGITUNDER"
                estrategia_nome = "UNDER"
                # Lógica de Predição Adaptativa para DIGITUNDER
                if loss_seguidas == 0:
                    prediction = 9
                else:
                    prediction = 5
            else:
                contract_type = "DIGITOVER"
                estrategia_nome = "OVER"
                # Lógica de Predição Adaptativa para DIGITOVER
                if loss_seguidas == 0:
                    prediction = 0
                else:
                    prediction = 5
            
            print(f"🔍 {nome_bot}: Trade #{trades_counter + 1} | Estratégia: {estrategia_nome} | Predição: {prediction}")
            print(f"📊 {nome_bot}: Profit: ${total_profit:.2f} | Stake: ${stake_atual:.2f} | Perdas seguidas: {loss_seguidas}")
            
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
            
            # Executar compra com tratamento robusto de erro
            success, contract_id = await safe_api_call(
                executar_compra, nome_bot, "executar compra", api, parametros_da_compra, nome_bot
            )
            
            if not success or contract_id is None:
                print(f"❌ {nome_bot}: Erro ao executar compra. Tentando novamente...")
                retry_count += 1
                should_continue = await handle_websocket_error(
                    nome_bot, "Falha ao executar compra", api, retry_count, max_retries
                )
                if should_continue:
                    if retry_count > max_retries:
                        retry_count = 0  # Reset contador
                    continue
                else:
                    break
            
            # Reset contador de retry após sucesso
            retry_count = 0
            
            # Aguardar resultado com tratamento robusto de erro
            success, lucro = await safe_api_call(
                aguardar_resultado_contrato, nome_bot, "aguardar resultado", api, contract_id, nome_bot
            )
            
            if not success or lucro is None:
                print(f"❌ {nome_bot}: Erro ao aguardar resultado. Continuando...")
                continue
            
            # Após a Compra - Incrementar contador
            trades_counter += 1
            
            # Atualizar total_profit
            total_profit += lucro
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Lógica Pós-Trade (Implementar Martingale Agressivo)
            if lucro > 0:
                # Vitória - Reset completo
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, True)
                stake_atual = stake_inicial
                loss_seguidas = 0
                print(f"✅ {nome_bot}: Vitória! Reset completo - Stake: ${stake_atual:.2f} | Perdas: {loss_seguidas}")
            else:
                # Derrota - Aplicar martingale agressivo
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, False)
                loss_seguidas += 1
                perda = abs(lucro)
                stake_atual = perda * martingale_fator  # Martingale agressivo fator 2.1
                print(f"❌ {nome_bot}: Derrota! Perdas seguidas: {loss_seguidas} | Próximo stake com martingale {martingale_fator}x: ${stake_atual:.2f}")
            
            # Pausa final - checar mercado a cada segundo
            await asyncio.sleep(1)
            
        except Exception as e:
            # Usar o novo sistema de tratamento de erros
            retry_count += 1
            should_continue = await handle_websocket_error(
                nome_bot, e, api, retry_count, max_retries
            )
            
            if should_continue:
                if retry_count > max_retries:
                    retry_count = 0  # Reset contador após máximo de tentativas
                continue
            else:
                print(f"❌ {nome_bot}: Parando execução devido a erros persistentes")
                break