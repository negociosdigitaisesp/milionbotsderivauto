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
    validar_e_ajustar_stake, handle_websocket_error, safe_api_call, is_websocket_error
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
    nome_bot = "BotAI_2.0"
    
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
    retry_count = 0
    max_retries = 3
    
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
            
            # Obter último tick do ativo para monitoramento com tratamento robusto de erro
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
                
            ultimo_digito = extrair_ultimo_digito(ultimo_preco)
            
            print(f"🔄 {nome_bot}: Iniciando nova compra contínua | Profit: ${total_profit:.2f}")
            print(f"🔍 {nome_bot}: Último dígito {ativo}: {ultimo_digito} | Stake: ${stake_atual:.2f}")
            
            # Operação Contínua - Sempre comprar DIGITOVER 0 (sem análise de mercado)
            print(f"🎯 {nome_bot}: Executando trade contínuo DIGITOVER 0")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Construir parâmetros da compra (sempre DIGITOVER 0)
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type='DIGITOVER',
                symbol=ativo,
                barrier=0
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITOVER 0 | Stake: ${stake_atual:.2f}")
            
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