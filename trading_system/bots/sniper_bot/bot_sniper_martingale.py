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
    criar_parametros_compra, validar_e_ajustar_stake,
    handle_websocket_error, safe_api_call, is_websocket_error
)
import logging

logger = logging.getLogger(__name__)

async def calcular_sma_3_periodos(api, symbol: str, nome_bot: str) -> Optional[float]:
    """
    Calcula a Média Móvel Simples (SMA) de 3 períodos com tratamento robusto de erro
    
    Args:
        api: Instância da API da Deriv
        symbol: Símbolo do ativo
        nome_bot: Nome do bot para logging
        
    Returns:
        float: Valor da SMA de 3 períodos ou None se erro
    """
    try:
        ticks = []
        for i in range(3):
            success, tick = await safe_api_call(
                obter_ultimo_tick, nome_bot, f"obter tick {i+1}/3 para SMA", api, symbol, nome_bot
            )
            if success and tick is not None:
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
    nome_bot = "Sniper_Bot_Martingale"
    stake_inicial = 0.35
    stake_maximo = 15.0  # Limite máximo para evitar erro
    martingale_fator = 1.05
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = '1HZ100V'
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    nivel_martingale = 0  # Controle do nível de martingale
    total_profit = 0
    retry_count = 0
    max_retries = 3
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   💎 Stake máximo: ${stake_maximo}")
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
            
            # Obter último preço de tick com tratamento robusto de erro
            success, ultimo_preco = await safe_api_call(
                obter_ultimo_tick, nome_bot, "obter último tick", api, ativo, nome_bot
            )
            
            if not success or ultimo_preco is None:
                print(f"❌ {nome_bot}: Erro ao obter último tick. Tentando novamente...")
                retry_count += 1
                should_continue = await handle_websocket_error(
                    nome_bot, "Falha ao obter tick", api, retry_count, max_retries
                )
                if should_continue:
                    if retry_count > max_retries:
                        retry_count = 0  # Reset contador
                    continue
                else:
                    break
            
            # Reset contador de retry após sucesso
            retry_count = 0
            
            # Calcular SMA de 3 períodos
            sma = await calcular_sma_3_periodos(api, ativo, nome_bot)
            if sma is None:
                print(f"❌ {nome_bot}: Erro ao calcular SMA. Tentando novamente...")
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
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot, limite_plataforma=20.0)
            
            # Construir parâmetros da compra
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type=contract_type,
                symbol=ativo
            )
            
            print(f"📈 {nome_bot}: Comprando {contract_type} | Stake: ${stake_atual:.2f}")
            
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
            
            # Atualizar total_profit
            total_profit += lucro
            stake_usado = stake_atual
            
            # Salvar operação
            salvar_operacao(nome_bot, lucro)
            
            # Lógica Pós-Trade (Martingale Controlado)
            if lucro > 0:
                # Vitória: Reset para stake inicial
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
                stake_atual = stake_inicial
                nivel_martingale = 0
                print(f"✅ {nome_bot}: VITÓRIA! Stake resetado para inicial: ${stake_atual:.2f} (Nível 0)")
            else:
                # Derrota: Usar função calcular_martingale com controle
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
                
                # Calcular próximo stake com controle de limite
                if nivel_martingale >= 5:
                    # Limite de 5 martingales atingido - Reset
                    stake_atual = stake_inicial
                    nivel_martingale = 0
                    print(f"🔄 {nome_bot}: Limite de 5 martingales atingido! Reset para ${stake_atual:.2f}")
                else:
                    # Aplicar martingale controlado
                    novo_stake = stake_atual * martingale_fator
                    nivel_martingale += 1
                    
                    # Verificar limite máximo
                    if novo_stake > stake_maximo:
                        stake_atual = stake_maximo
                        print(f"⚠️ {nome_bot}: Stake limitado ao máximo de ${stake_maximo:.2f} (Nível {nivel_martingale})")
                    else:
                        stake_atual = novo_stake
                        print(f"🔄 {nome_bot}: Martingale Nível {nivel_martingale} - Novo stake: ${stake_atual:.2f}")
            
            # Pausa entre operações
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