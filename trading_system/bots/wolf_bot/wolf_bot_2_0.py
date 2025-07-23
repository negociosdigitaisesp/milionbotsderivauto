"""
Wolf Bot 2.0 - Estratégia Adaptativa com Martingale
Opera com martingale baseado no último dígito do R_100 e no resultado da operação anterior

Este bot adapta sua estratégia baseado no histórico de resultados,
utilizando martingale para gerenciamento de risco.
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

async def wolf_bot_2_0(api) -> None:
    """
    Wolf Bot 2.0 Original - Estratégia baseada na lógica original do XML
    Opera com martingale adaptativo baseado em condições específicas de dígitos
    
    Args:
        api: Instância da API da Deriv
    """
    # Parâmetros de Gestão (conforme XML original)
    nome_bot = "Wolf_Bot_2.0_Original"
    stake_inicial = 0.6
    martingale_fator = 1.0  # Martingale simples, stake não aumenta
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    ativo = 'R_100'
    
    logger.info(f"🤖 Iniciando {nome_bot}...")
    print(f"🤖 Iniciando {nome_bot}...")
    
    # Variáveis de Estado
    stake_atual = stake_inicial
    total_profit = 0
    ultimo_resultado = "vitoria"  # Inicializar com "vitoria"
    
    print(f"📊 {nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   🔄 Fator Martingale: {martingale_fator} (simples)")
    print(f"   🛑 Stop Loss: Infinito")
    print(f"   🎯 Stop Win: Infinito")
    print(f"   🐺 Estratégia: Lógica Original XML")
    print(f"   🏪 Ativo: {ativo}")
    print(f"   📈 Último resultado inicial: {ultimo_resultado}")
    
    while True:
        try:
            # Verificar Stop Loss/Win no início de cada ciclo (sempre infinito)
            resultado_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            if resultado_stop != 'continue':
                break
            
            # Obter último dígito do R_100
            ultimo_tick = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_tick is None:
                await asyncio.sleep(1)
                continue
            
            ultimo_digito = extrair_ultimo_digito(ultimo_tick)
            
            # Lógica de Entrada (Duas Condições)
            entrada_valida = False
            contract_type = None
            barrier = None
            estrategia = ""
            
            # Condição 1: Se o ultimo_digito for 4
            if ultimo_digito == 4:
                entrada_valida = True
                contract_type = "DIGITUNDER"
                estrategia = "UNDER (dígito 4)"
                
            # Condição 2: Se o ultimo_digito for 6 E se stake_atual > stake_inicial
            elif ultimo_digito == 6 and stake_atual > stake_inicial:
                entrada_valida = True
                contract_type = "DIGITOVER"
                estrategia = "OVER (dígito 6 + stake > inicial)"
            
            # Se não atender às condições, aguardar próximo tick
            if not entrada_valida:
                print(f"🐺 {nome_bot}: Dígito: {ultimo_digito} | Stake: ${stake_atual:.2f} | Aguardando condições...")
                await asyncio.sleep(1)
                continue
            
            # Predição (barrier) adaptativa baseada no último resultado
            if ultimo_resultado == "vitoria":
                barrier = 8
                predicao_info = "Predição 8 (após vitória)"
            else:  # ultimo_resultado == "derrota"
                barrier = 2
                predicao_info = "Predição 2 (após derrota)"
            
            print(f"🐺 {nome_bot}: Dígito: {ultimo_digito} | {estrategia} | {predicao_info}")
            print(f"💰 {nome_bot}: Profit: ${total_profit:.2f} | Stake atual: ${stake_atual:.2f} | Último: {ultimo_resultado}")
            
            # Validar e ajustar stake antes da compra
            stake_atual = validar_e_ajustar_stake(stake_atual, nome_bot)
            
            # Construir parâmetros da compra
            parametros_da_compra = criar_parametros_compra(
                stake=stake_atual,
                contract_type=contract_type,
                symbol=ativo,
                barrier=barrier
            )
            
            print(f"📈 {nome_bot}: Comprando {contract_type} {barrier} | Stake: ${stake_atual:.2f}")
            
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
            
            # Lógica Pós-Trade (Martingale Original)
            stake_anterior = stake_atual
            
            if lucro > 0:
                # Vitória: Resetar stake e definir último resultado
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, True)
                stake_atual = stake_inicial
                ultimo_resultado = "vitoria"
                print(f"✅ {nome_bot}: VITÓRIA! Stake resetado para ${stake_atual:.2f}")
            else:
                # Derrota: Aplicar martingale e definir último resultado
                log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, False)
                stake_atual = stake_anterior * martingale_fator
                ultimo_resultado = "derrota"
                print(f"❌ {nome_bot}: DERROTA! Novo stake: ${stake_atual:.2f} (fator: {martingale_fator})")
            
            # Pausa final - aguardar próxima análise
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro de conexão no {nome_bot}: {e}. Tentando novamente em 10 segundos...")
            logger.error(f"Erro de conexão no {nome_bot}: {e}")
            await asyncio.sleep(10)