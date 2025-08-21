"""
DoubleCuentas Bot - Estratégia DIGITOVER simples
Opera com DIGITOVER barrier 0 sem gatilho de dígito

Este bot implementa uma estratégia simples de DIGITOVER com barreira 0
e duração de 5 ticks, executando operações continuamente.
"""

import asyncio
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, log_resultado_operacao, 
    criar_parametros_compra, validar_e_ajustar_stake,
    handle_websocket_error, safe_api_call, calcular_martingale
)
import logging

logger = logging.getLogger(__name__)

async def bot_double_cuentas(api) -> None:
    """
    DoubleCuentas Bot - Estratégia DIGITOVER simples
    Opera com DIGITOVER barrier 0 sem gatilho de dígito
    
    Args:
        api: Instância da API da Deriv
    """
    # Parâmetros de Gestão
    nome_bot = "DoubleCuentas"
    stake_inicial = 1.0
    stake_maximo = 15.0  # Limite seguro para evitar erro de stake máximo
    martingale_fator = 1.8
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = 'R_75'
    duracao_contrato = 5  # ticks
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0
    retry_count = 0
    max_retries = 3
    nivel_martingale = 0  # Controle de níveis de martingale
    max_martingale_levels = 5  # Máximo de níveis permitidos
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔒 Stake máximo: ${stake_maximo}")
    print(f"   🔄 Fator Martingale: {martingale_fator}")
    print(f"   📊 Níveis máximos: {max_martingale_levels}")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   📈 Estratégia: DIGITOVER barrier 0")
    print(f"   🏪 Ativo: {ativo}")
    print(f"   ⏱️ Duração: {duracao_contrato} ticks")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            print(f"💰 {nome_bot}: Profit Total: ${total_profit:.2f} | Stake Atual: ${stake_atual:.2f} | Nível MG: {nivel_martingale}")
            
            # Estratégia de Entrada - DIGITOVER simples (sem gatilho)
            print(f"🎯 {nome_bot}: Executando DIGITOVER com barrier 0...")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot, limite_plataforma=20.0)
            
            # Construir parâmetros da compra para DIGITOVER
            # Tipo de contrato: DIGITOVER
            # Predição (barrier): 0
            # Duração: 5 ticks
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type="DIGITOVER",
                symbol=ativo,
                barrier=0,
                duration=duracao_contrato,
                duration_unit="t"
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITOVER | Barreira: 0 | Stake: ${stake_atual:.2f} | Duração: {duracao_contrato} ticks")
            
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
            
            # Salvar operação no Supabase
            salvar_operacao(nome_bot, lucro)
            
            # Lógica Pós-Trade (Martingale Corrigida)
            # Usar a função calcular_martingale para evitar stakes excessivos
            stake_atual, nivel_martingale = calcular_martingale(
                lucro=lucro,
                stake_atual=stake_atual,
                stake_inicial=stake_inicial,
                stake_maximo=stake_maximo,
                nome_bot=nome_bot,
                nivel_martingale=nivel_martingale,
                max_martingale_levels=max_martingale_levels
            )
            
            # Log do resultado
            if lucro > 0:
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
            else:
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
            
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