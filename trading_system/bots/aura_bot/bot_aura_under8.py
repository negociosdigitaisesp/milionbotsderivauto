"""
AuraBot_Under8 - Estratégia de compra contínua com Martingale Dividido
Opera com DIGITUNDER barrier 8 continuamente

Este bot implementa uma estratégia de compra contínua sem análise de mercado,
executando operações DIGITUNDER com gestão de risco baseada em Martingale Dividido.
"""

import asyncio
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, log_resultado_operacao, 
    criar_parametros_compra, validar_e_ajustar_stake,
    handle_websocket_error, safe_api_call
)
import logging

logger = logging.getLogger(__name__)

async def bot_aura_under8(api) -> None:
    """
    AuraBot_Under8 - Estratégia de compra contínua com Martingale Dividido
    Opera com DIGITUNDER barrier 8 sem análise de mercado
    
    Args:
        api: Instância da API da Deriv
    """
    # Parâmetros de Gestão
    nome_bot = "AuraBot_Under8"
    stake_inicial = 1.0
    divisor_martingale = 2
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = 'R_100'
    duracao_contrato = 1  # tick
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Variáveis de Estado
    stake_atual = stake_inicial
    total_perdido = 0.0
    contador_divisao_mg = 0
    total_profit = 0.0
    retry_count = 0
    max_retries = 3
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Divisor Martingale: {divisor_martingale}")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   📈 Estratégia: Compra contínua DIGITUNDER barrier 8")
    print(f"   🏪 Ativo: {ativo}")
    print(f"   ⏱️ Duração: {duracao_contrato} tick")
    print(f"   🎲 Gestão: Martingale Dividido")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            print(f"💰 {nome_bot}: Profit Total: ${total_profit:.2f} | Stake Atual: ${stake_atual:.2f}")
            print(f"📉 {nome_bot}: Total Perdido: ${total_perdido:.2f} | Contador MG: {contador_divisao_mg}")
            
            # Estratégia de Entrada - Compra Contínua (sem análise)
            print(f"🎯 {nome_bot}: Executando compra contínua DIGITUNDER barrier 8...")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot, limite_plataforma=20.0)
            
            # Construir parâmetros da compra para DIGITUNDER
            # Tipo de contrato: DIGITUNDER
            # Predição (barrier): 8
            # Duração: 1 tick
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type="DIGITUNDER",
                symbol=ativo,
                barrier=8,
                duration=duracao_contrato,
                duration_unit="t"
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITUNDER | Barreira: 8 | Stake: ${stake_atual:.2f} | Duração: {duracao_contrato} tick")
            
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
            
            # Lógica Pós-Trade (Martingale Dividido)
            if lucro > 0:
                # Vitória
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
                print(f"✅ {nome_bot}: VITÓRIA! Lucro: ${lucro:.2f}")
                
                # Se total_perdido > 0, abater o lucro do total_perdido
                if total_perdido > 0:
                    total_perdido -= abs(lucro)
                    print(f"💰 {nome_bot}: Abatendo lucro do total perdido: ${total_perdido:.2f}")
                    
                    # Se total_perdido <= 0, resetar variáveis
                    if total_perdido <= 0:
                        total_perdido = 0.0
                        contador_divisao_mg = 0
                        print(f"🔄 {nome_bot}: Total perdido zerado! Reset completo.")
                
                # Resetar stake_atual para o stake_inicial
                stake_atual = stake_inicial
                print(f"✅ {nome_bot}: Stake resetado para inicial: ${stake_atual:.2f}")
                
            else:
                # Derrota
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
                perda_atual = abs(lucro)
                print(f"❌ {nome_bot}: DERROTA! Perda: ${perda_atual:.2f}")
                
                # Adicionar a perda ao total_perdido
                total_perdido += perda_atual
                print(f"📉 {nome_bot}: Total perdido atualizado: ${total_perdido:.2f}")
                
                # Definir contador_divisao_mg como divisor_martingale
                contador_divisao_mg = divisor_martingale
                
                # Calcular novo stake: total_perdido / contador_divisao_mg
                # Garantindo que seja no mínimo stake_inicial
                novo_stake = total_perdido / contador_divisao_mg
                stake_atual = max(novo_stake, stake_inicial)
                
                print(f"🔄 {nome_bot}: Martingale Dividido - Novo stake: ${stake_atual:.2f}")
                print(f"📊 {nome_bot}: Cálculo: ${total_perdido:.2f} ÷ {contador_divisao_mg} = ${novo_stake:.2f} (mín: ${stake_inicial})")
            
            # Log do estado atual
            print(f"📊 {nome_bot}: Estado - Profit: ${total_profit:.2f} | Perdido: ${total_perdido:.2f} | Próximo Stake: ${stake_atual:.2f}")
            
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