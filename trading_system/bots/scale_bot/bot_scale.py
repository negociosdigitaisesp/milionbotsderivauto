"""
ScaleBot - Estratégia de Trading com Predição Adaptativa
Bot que implementa uma estratégia baseada na comparação de dígitos para decidir entre DIGITEVEN e DIGITODD
"""

import asyncio
import logging
from typing import Optional
from trading_system.utils.helpers import (
    salvar_operacao, 
    aguardar_resultado_contrato, 
    executar_compra, 
    obter_ultimo_tick, 
    extrair_ultimo_digito, 
    log_resultado_operacao, 
    criar_parametros_compra, 
    verificar_stops
)

# Configurar logging
logger = logging.getLogger(__name__)

async def bot_scale(api) -> None:
    """
    ScaleBot: Estratégia baseada em predição adaptativa com martingale agressivo
    
    Estratégia:
    - Obtém um dígito de predição
    - Espera 0.75 segundos
    - Obtém o dígito atual
    - Compra DIGITEVEN se forem iguais, DIGITODD se diferentes
    - Aplica martingale agressivo (fator 2.0) em caso de derrota
    
    Args:
        api: Instância da API da Deriv
    """
    # Definir parâmetros fixos
    nome_bot = "ScaleBot"
    ativo = "1HZ100V"
    stake_inicial = 1.0
    martingale_fator = 2.0
    stop_loss = float('inf')  # Ilimitado
    stop_win = float('inf')   # Ilimitado
    
    # Inicializar variáveis de estado
    stake_atual = stake_inicial
    total_profit = 0.0
    
    print(f"🤖 Iniciando {nome_bot}...")
    print(f"📊 {nome_bot} configurado:")
    print(f"   🎯 Ativo: {ativo}")
    print(f"   💰 Stake inicial: ${stake_inicial}")
    print(f"   📈 Fator martingale: {martingale_fator}x")
    print(f"   🛑 Stop Loss: Ilimitado")
    print(f"   🎯 Stop Win: Ilimitado")
    print(f"   ⚡ Duração: 1 tick")
    print("🚀 Iniciando operações...\n")
    
    while True:
        try:
            # 1. Obter dígito de predição
            print(f"🔍 {nome_bot}: Obtendo dígito de predição...")
            ultimo_tick_predicao = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_tick_predicao is None:
                print(f"❌ {nome_bot}: Erro ao obter tick de predição. Tentando novamente...")
                await asyncio.sleep(5)
                continue
            
            predicao = extrair_ultimo_digito(ultimo_tick_predicao)
            print(f"🎯 {nome_bot}: Dígito de predição: {predicao}")
            
            # 2. Esperar 0.75 segundos
            print(f"⏳ {nome_bot}: Aguardando 0.75 segundos...")
            await asyncio.sleep(0.75)
            
            # 3. Obter dígito atual
            print(f"🔍 {nome_bot}: Obtendo dígito atual...")
            ultimo_tick_atual = await obter_ultimo_tick(api, ativo, nome_bot)
            if ultimo_tick_atual is None:
                print(f"❌ {nome_bot}: Erro ao obter tick atual. Tentando novamente...")
                await asyncio.sleep(5)
                continue
            
            ultimo_digito_atual = extrair_ultimo_digito(ultimo_tick_atual)
            print(f"🎯 {nome_bot}: Dígito atual: {ultimo_digito_atual}")
            
            # 4. Determinar condição de compra
            # Estratégia: Se dígitos forem iguais -> apostar em PAR (DIGITEVEN)
            #            Se dígitos forem diferentes -> apostar em ÍMPAR (DIGITODD)
            if ultimo_digito_atual == predicao:
                contract_type = "DIGITEVEN"
                condicao = "IGUAIS"
                estrategia_info = "Apostando em dígito PAR"
            else:
                contract_type = "DIGITODD"
                condicao = "DIFERENTES"
                estrategia_info = "Apostando em dígito ÍMPAR"
            
            print(f"📊 {nome_bot}: Dígitos {condicao} ({predicao} vs {ultimo_digito_atual}) -> {estrategia_info}")
            print(f"💰 {nome_bot}: Stake atual: ${stake_atual:.2f}")
            
            # 5. Criar parâmetros da compra
            # DIGITEVEN/DIGITODD não usam barrier - apenas verificam se o dígito é par ou ímpar
            parametros_compra = {
                'buy': '1',
                'subscribe': 1,
                'price': stake_atual,
                'parameters': {
                    'amount': stake_atual,
                    'basis': 'stake',
                    'contract_type': contract_type,
                    'currency': 'USD',
                    'duration': 1,
                    'duration_unit': 't',  # 1 tick
                    'symbol': ativo
                    # Nota: DIGITEVEN/DIGITODD não precisam de barrier
                }
            }
            
            # 6. Executar compra
            print(f"🚀 {nome_bot}: Executando {contract_type} (1 tick) | Stake: ${stake_atual:.2f}")
            contract_id = await executar_compra(api, parametros_compra, nome_bot)
            
            if contract_id is None:
                print(f"❌ {nome_bot}: Falha na execução da compra. Tentando novamente...")
                await asyncio.sleep(5)
                continue
            
            print(f"✅ {nome_bot}: Compra executada! Contract ID: {contract_id}")
            
            # 7. Aguardar resultado
            lucro = await aguardar_resultado_contrato(api, contract_id, nome_bot)
            
            if lucro is None:
                print(f"❌ {nome_bot}: Timeout ao aguardar resultado. Continuando...")
                await asyncio.sleep(5)
                continue
            
            # 8. Processar resultado
            total_profit += lucro
            vitoria = lucro > 0
            
            # Log do resultado
            log_resultado_operacao(nome_bot, lucro, total_profit, stake_atual, vitoria)
            
            # Salvar operação no Supabase
            salvar_operacao(nome_bot, lucro)
            
            # 9. Aplicar lógica pós-trade (Martingale Agressivo)
            stake_anterior = stake_atual
            
            if vitoria:
                # Vitória: Reset para stake inicial
                stake_atual = stake_inicial
                print(f"✅ {nome_bot}: Vitória! Reset stake para ${stake_atual:.2f}")
            else:
                # Derrota: Aplicar martingale agressivo
                stake_atual = stake_anterior * martingale_fator
                print(f"🔄 {nome_bot}: Derrota! Martingale: ${stake_anterior:.2f} -> ${stake_atual:.2f}")
            
            # 10. Verificar stops (sempre retorna 'continue' pois são infinitos)
            status_stop = verificar_stops(total_profit, stop_loss, stop_win, nome_bot)
            
            if status_stop != 'continue':
                print(f"🛑 {nome_bot}: Stop atingido. Encerrando...")
                break
            
            # Pausa antes da próxima operação
            print(f"⏳ {nome_bot}: Aguardando próximo ciclo...\n")
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ {nome_bot}: Erro no loop principal: {e}")
            print(f"❌ {nome_bot}: Erro no loop principal: {e}")
            print(f"⏳ {nome_bot}: Aguardando 10 segundos antes de tentar novamente...")
            await asyncio.sleep(10)