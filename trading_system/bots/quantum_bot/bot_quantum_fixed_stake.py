"""
QuantumBot Original - Estratégia Complexa com Sorosgale e Martingale Dividido
Opera com lógica avançada combinando Soros e Martingale dividido para recuperação otimizada

Este bot implementa uma estratégia complexa que combina:
- Sorosgale: Acumula lucros até atingir níveis máximos
- Martingale Dividido: Divide a recuperação em partes menores
- Predições aleatórias com contratos DIGITDIFF
"""

import asyncio
import random
from typing import Optional
from ...utils.helpers import (
    salvar_operacao, aguardar_resultado_contrato, executar_compra,
    verificar_stops, log_resultado_operacao, criar_parametros_compra,
    validar_e_ajustar_stake, handle_websocket_error, safe_api_call, is_websocket_error
)
import logging

logger = logging.getLogger(__name__)

async def bot_quantum_fixed_stake(api) -> None:
    """
    QuantumBot Original - Estratégia Complexa com Sorosgale e Martingale Dividido
    Implementa lógica avançada combinando Soros e Martingale dividido
    
    Args:
        api: Instância da API da Deriv
    """
    # Parâmetros de Gestão (Lógica Original Complexa)
    nome_bot = "QuantumBot_FixedStake"
    stake_inicial = 0.35
    niveis_soros = 12
    divisor_martingale = 5  # Quantas partes dividir o martingale
    multiplicador_martingale = 12.0  # Fator para calcular a recuperação
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = 'R_100'
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Variáveis de Estado
    stake_atual = stake_inicial
    total_profit = 0
    nivel_soros_atual = 0
    valor_recuperacao_mg = 0.0  # Para o martingale dividido
    contador_divisao_mg = 0
    retry_count = 0
    max_retries = 3
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🎯 Níveis Soros: {niveis_soros}")
    print(f"   🔄 Divisor Martingale: {divisor_martingale}")
    print(f"   📈 Multiplicador Martingale: {multiplicador_martingale}")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   🎲 Estratégia: Sorosgale + Martingale Dividido + DIGITDIFF")
    print(f"   🏪 Ativo: {ativo}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Gerar predição (barrier) aleatória de 0 a 9
            barrier_aleatorio = random.randint(0, 9)
            
            print(f"🎲 {nome_bot}: Predição aleatória: {barrier_aleatorio}")
            print(f"💰 {nome_bot}: Profit Total: ${total_profit:.2f} | Stake Atual: ${stake_atual:.2f}")
            print(f"🎯 {nome_bot}: Nível Soros: {nivel_soros_atual}/{niveis_soros} | Recuperação MG: ${valor_recuperacao_mg:.2f}")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Lógica de Compra (sempre DIGITDIFF com predição aleatória)
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type='DIGITDIFF',
                symbol=ativo,
                barrier=barrier_aleatorio
            )
            
            print(f"📈 {nome_bot}: Comprando DIGITDIFF {barrier_aleatorio} | Stake: ${stake_atual:.2f}")
            
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
            
            # Lógica Pós-Trade (Sorosgale e Martingale Dividido)
            if lucro > 0:
                # VITÓRIA - Lógica complexa de Sorosgale e recuperação
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, True)
                
                if valor_recuperacao_mg > 0:
                    # Está em modo de recuperação do martingale
                    valor_recuperacao_mg -= abs(lucro)
                    print(f"✅ {nome_bot}: VITÓRIA! Abatendo ${abs(lucro):.2f} da recuperação MG")
                    
                    if valor_recuperacao_mg <= 0:
                        # Recuperação completa - voltar ao stake inicial
                        valor_recuperacao_mg = 0.0
                        contador_divisao_mg = 0
                        stake_atual = stake_inicial
                        print(f"🎉 {nome_bot}: RECUPERAÇÃO COMPLETA! Voltando ao stake inicial: ${stake_atual:.2f}")
                    else:
                        # Continuar com stake de recuperação
                        stake_atual = valor_recuperacao_mg / divisor_martingale
                        print(f"🔄 {nome_bot}: Continuando recuperação - Novo stake: ${stake_atual:.2f} | Restante: ${valor_recuperacao_mg:.2f}")
                
                elif nivel_soros_atual < niveis_soros:
                    # Aplicar Sorosgale - acumular lucros
                    stake_atual += lucro
                    nivel_soros_atual += 1
                    print(f"🚀 {nome_bot}: SOROS APLICADO! Novo stake: ${stake_atual:.2f} | Nível: {nivel_soros_atual}/{niveis_soros}")
                
                else:
                    # Ciclo de Soros completado - resetar
                    stake_atual = stake_inicial
                    nivel_soros_atual = 0
                    print(f"🏆 {nome_bot}: CICLO SOROS COMPLETO! Resetando - Stake: ${stake_atual:.2f} | Nível: {nivel_soros_atual}")
            
            else:
                # DERROTA - Aplicar Martingale Dividido
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_usado, False)
                
                # Resetar nível de Soros
                nivel_soros_atual = 0
                
                # Calcular valor a ser recuperado
                valor_a_recuperar = abs(lucro) * multiplicador_martingale
                valor_recuperacao_mg += valor_a_recuperar
                
                # Resetar contador de divisão
                contador_divisao_mg = divisor_martingale
                
                # Calcular novo stake dividido
                stake_atual = valor_recuperacao_mg / contador_divisao_mg
                
                print(f"❌ {nome_bot}: DERROTA! Perda: ${abs(lucro):.2f}")
                print(f"🔄 {nome_bot}: Valor a recuperar: ${valor_a_recuperar:.2f} | Total recuperação: ${valor_recuperacao_mg:.2f}")
                print(f"📊 {nome_bot}: Martingale Dividido - Novo stake: ${stake_atual:.2f} (Divisor: {divisor_martingale})")
                print(f"🎯 {nome_bot}: Soros resetado para nível 0")
            
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