#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accumulator Scalping Bot - Estratégia Accumulator para Deriv
Opera no ativo Volatility 75 Index (R_75) com análise de padrão de ticks
Implementa gestão de risco dinâmica conforme especificação XML

Este bot replica fielmente a lógica do arquivo XML 'Scalping Bot.xml':
- Análise de 5 ticks: Red, Red, Red, Blue (condição de entrada)
- Contratos Accumulator com Growth Rate 2%
- Take Profit inicial 10% do stake
- Gestão de risco com recuperação agressiva
- Operação contínua 24/7
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import time
from ...utils.helpers import (
    handle_websocket_error, safe_api_call, is_websocket_error
)
from ...config.settings import get_supabase_client

logger = logging.getLogger(__name__)


class AccumulatorScalpingBot:
    """
    Bot de trading com estratégia Accumulator Scalping
    Implementa a lógica exata do XML fornecido
    """
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.nome_bot = "Accumulator_Scalping_Bot"
        
        # Parâmetros conforme XML
        self.stake_inicial = 50.0  # Valor inicial definido no XML
        self.khizzbot = 50.0  # Fator multiplicador do XML
        self.growth_rate = 0.02  # 2% Growth Rate
        self.take_profit_inicial = 0.10  # 10% do stake inicial
        self.ativo = 'R_75'  # Volatility 75 Index
        
        # Variáveis de controle de estado
        self.stake_atual = self.stake_inicial
        self.total_lost = 0.0  # Total perdido acumulado
        self.take_profit_atual = self.stake_inicial * self.take_profit_inicial
        self.ticks_history = []  # Histórico dos últimos 5 ticks
        
        # Cache de ticks para evitar rate limiting
        self.ticks_cache = []
        self.ultimo_update_ticks = 0
        self.cache_duration = 5  # Cache válido por 5 segundos
        self.min_interval_ticks = 3  # Mínimo 3 segundos entre requisições
        
        # Configuração do Supabase
        self.supabase = get_supabase_client()
        
        logger.info(f"🤖 {self.nome_bot} inicializado")
        
    async def obter_ticks_com_cache(self) -> Optional[List[float]]:
        """
        Obtém ticks com sistema de cache para evitar rate limiting
        
        Returns:
            List[float]: Lista de preços dos ticks ou None se erro
        """
        try:
            tempo_atual = time.time()
            
            # Verificar se o cache ainda é válido
            if (self.ticks_cache and 
                tempo_atual - self.ultimo_update_ticks < self.cache_duration):
                logger.debug(f"{self.nome_bot}: Usando ticks do cache")
                return self.ticks_cache
            
            # Verificar rate limiting
            if tempo_atual - self.ultimo_update_ticks < self.min_interval_ticks:
                tempo_espera = self.min_interval_ticks - (tempo_atual - self.ultimo_update_ticks)
                logger.info(f"{self.nome_bot}: Rate limiting - aguardando {tempo_espera:.1f}s")
                await asyncio.sleep(tempo_espera)
            
            # Obter novos ticks da API
            try:
                ticks_response = await self.api_manager.ticks_history({
                    "ticks_history": self.ativo,
                    "count": 5,
                    "end": "latest"
                })
                success = True
            except Exception as e:
                logger.error(f"{self.nome_bot}: Erro ao obter ticks: {e}")
                success = False
                ticks_response = None
            
            if not success or not ticks_response or 'error' in ticks_response:
                logger.warning(f"{self.nome_bot}: Erro ao obter ticks da API")
                # Retornar cache antigo se disponível
                if self.ticks_cache:
                    logger.info(f"{self.nome_bot}: Usando cache antigo devido ao erro")
                    return self.ticks_cache
                return None
            
            # Extrair e validar ticks
            ticks = ticks_response.get('history', {}).get('prices', [])
            
            if len(ticks) < 5:
                logger.warning(f"{self.nome_bot}: Ticks insuficientes ({len(ticks)}/5)")
                return None
            
            # Converter para float e atualizar cache
            ticks_float = [float(tick) for tick in ticks]
            self.ticks_cache = ticks_float
            self.ultimo_update_ticks = tempo_atual
            
            logger.debug(f"{self.nome_bot}: Cache de ticks atualizado")
            return ticks_float
            
        except Exception as e:
            logger.error(f"{self.nome_bot}: Erro ao obter ticks: {e}")
            # Retornar cache antigo se disponível
            if self.ticks_cache:
                logger.info(f"{self.nome_bot}: Usando cache antigo devido ao erro")
                return self.ticks_cache
            return None
    
    async def analisar_ticks(self) -> bool:
        """
        Analisa os últimos 5 ticks para determinar condição de entrada
        Condição: Red, Red, Red, Blue (do mais antigo para o mais recente)
        
        Returns:
            bool: True se condição de entrada for atendida
        """
        try:
            # Obter ticks com cache
            ticks = await self.obter_ticks_com_cache()
            
            if not ticks or len(ticks) < 5:
                print(f"🔍 {self.nome_bot}: Ticks insuficientes ({len(ticks) if ticks else 0}/5)")
                return False
            
            # Analisar direção dos últimos 5 ticks
            direcoes = []
            for i in range(1, len(ticks)):
                if ticks[i] > ticks[i-1]:
                    direcoes.append('Blue')  # Alta
                else:
                    direcoes.append('Red')   # Baixa
            
            # Verificar padrão: Red, Red, Red, Blue
            # (do 4º mais antigo para o mais recente)
            padrao_esperado = ['Red', 'Red', 'Red', 'Blue']
            
            if len(direcoes) >= 4:
                padrao_atual = direcoes[-4:]  # Últimos 4 movimentos
                
                print(f"🔍 {self.nome_bot}: Ticks: {[f'{t:.5f}' for t in ticks[-5:]]}")
                print(f"🔍 {self.nome_bot}: Padrão atual: {padrao_atual} | Esperado: {padrao_esperado}")
                
                if padrao_atual == padrao_esperado:
                    print(f"✅ {self.nome_bot}: Condição de entrada atendida!")
                    logger.info(f"{self.nome_bot}: ✅ Condição de entrada atendida!")
                    return True
                else:
                    print(f"⏳ {self.nome_bot}: Aguardando padrão correto...")
            
            return False
            
        except Exception as e:
            print(f"❌ {self.nome_bot}: Erro na análise de ticks: {e}")
            logger.error(f"{self.nome_bot}: Erro na análise de ticks: {e}")
            return False
    
    async def executar_compra_accumulator(self) -> Optional[str]:
        """
        Executa compra de contrato Accumulator
        
        Returns:
            str: ID do contrato se bem-sucedido, None caso contrário
        """
        try:
            # Calcular take profit baseado no stake atual
            take_profit_value = self.take_profit_atual
            
            # Parâmetros do contrato Accumulator
            parametros_compra = {
                "buy": {
                    "contract_type": "ACCU",
                    "symbol": self.ativo,
                    "amount": self.stake_atual,
                    "currency": "USD",
                    "growth_rate": self.growth_rate,
                    "take_profit": take_profit_value
                }
            }
            
            logger.info(f"{self.nome_bot}: Executando compra ACCU")
            logger.info(f"   💰 Stake: ${self.stake_atual:.2f}")
            logger.info(f"   📈 Growth Rate: {self.growth_rate*100}%")
            logger.info(f"   🎯 Take Profit: ${take_profit_value:.2f}")
            
            # Executar compra
            try:
                resultado = await self.api_manager.buy(parametros_compra)
                success = True
            except Exception as e:
                logger.error(f"{self.nome_bot}: Erro na compra: {e}")
                success = False
                resultado = None
            
            if success and resultado and 'error' not in resultado:
                contract_id = resultado.get('buy', {}).get('contract_id')
                if contract_id:
                    logger.info(f"{self.nome_bot}: ✅ Compra executada - ID: {contract_id}")
                    return str(contract_id)
            
            logger.error(f"{self.nome_bot}: ❌ Erro na compra: {resultado}")
            return None
            
        except Exception as e:
            logger.error(f"{self.nome_bot}: Erro ao executar compra: {e}")
            return None
    
    async def aguardar_resultado_contrato(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Aguarda o resultado do contrato Accumulator
        
        Args:
            contract_id: ID do contrato
            
        Returns:
            dict: Resultado do contrato com informações de lucro/prejuízo
        """
        try:
            max_tentativas = 300  # 5 minutos máximo
            tentativa = 0
            
            while tentativa < max_tentativas:
                # Verificar status do contrato
                try:
                    status_response = await self.api_manager.proposal_open_contract(
                        {"proposal_open_contract": 1, "contract_id": contract_id}
                    )
                    success = True
                except Exception as e:
                    logger.error(f"{self.nome_bot}: Erro ao verificar contrato: {e}")
                    success = False
                    status_response = None
                
                if success and status_response and 'error' not in status_response:
                    contract_info = status_response.get('proposal_open_contract', {})
                    
                    # Verificar se contrato foi finalizado
                    if contract_info.get('is_sold') or contract_info.get('is_expired'):
                        profit = float(contract_info.get('profit', 0))
                        buy_price = float(contract_info.get('buy_price', 0))
                        
                        resultado = {
                            'profit': profit,
                            'buy_price': buy_price,
                            'profit_percentage': (profit / buy_price * 100) if buy_price > 0 else 0,
                            'is_win': profit > 0,
                            'contract_info': contract_info
                        }
                        
                        logger.info(f"{self.nome_bot}: Contrato finalizado")
                        logger.info(f"   💰 Lucro: ${profit:.2f}")
                        logger.info(f"   📊 Percentual: {resultado['profit_percentage']:.2f}%")
                        
                        return resultado
                
                await asyncio.sleep(1)
                tentativa += 1
            
            logger.warning(f"{self.nome_bot}: Timeout aguardando resultado do contrato")
            return None
            
        except Exception as e:
            logger.error(f"{self.nome_bot}: Erro ao aguardar resultado: {e}")
            return None
    
    def processar_resultado(self, resultado: Dict[str, Any]):
        """
        Processa resultado da operação e ajusta parâmetros para próxima
        Implementa lógica exata do XML
        
        Args:
            resultado: Dicionário com informações do resultado
        """
        is_win = resultado['is_win']
        profit = resultado['profit']
        
        if is_win:
            # VITÓRIA: Resetar tudo para valores iniciais
            logger.info(f"{self.nome_bot}: 🎉 VITÓRIA! Resetando parâmetros")
            self.stake_atual = self.stake_inicial
            self.total_lost = 0.0
            self.take_profit_atual = self.stake_inicial * self.take_profit_inicial
            
        else:
            # DERROTA: Implementar lógica de recuperação
            perda = abs(profit)  # Valor perdido (positivo)
            self.total_lost += perda
            
            logger.info(f"{self.nome_bot}: ❌ DERROTA! Perda: ${perda:.2f}")
            logger.info(f"   📊 Total perdido acumulado: ${self.total_lost:.2f}")
            
            # Novo take profit = total lost (para recuperar tudo)
            self.take_profit_atual = self.total_lost
            
            # Novo stake = total lost * khizzbot (conforme XML)
            self.stake_atual = self.total_lost * self.khizzbot
            
            logger.info(f"   🎯 Novo Take Profit: ${self.take_profit_atual:.2f}")
            logger.info(f"   💰 Novo Stake: ${self.stake_atual:.2f}")
    
    async def salvar_resultado_supabase(self, resultado: Dict[str, Any]):
        """
        Salva apenas operações finalizadas (WIN/LOSS) na tabela bot_operation_logs
        
        Args:
            resultado: Dicionário com informações do resultado
        """
        try:
            # Apenas registrar operações finalizadas com resultado claro
            operation_result = 'WIN' if resultado['is_win'] else 'LOSS'
            profit_percentage = resultado['profit_percentage']
            stake_value = self.stake_atual
            
            dados = {
                'bot_name': self.nome_bot,
                'operation_result': operation_result,
                'profit_percentage': float(profit_percentage),
                'stake_value': float(stake_value)
            }
            
            # Inserir na tabela padrão bot_operation_logs
            response = self.supabase.table('bot_operation_logs').insert(dados).execute()
            
            if response.data:
                logger.info(f"{self.nome_bot}: ✅ Resultado finalizado salvo no Supabase: {operation_result}")
            else:
                logger.warning(f"{self.nome_bot}: ⚠️ Falha ao salvar no Supabase")
                
        except Exception as e:
            logger.error(f"{self.nome_bot}: Erro ao salvar no Supabase: {e}")
            # Log local como fallback
            logger.error(f"{self.nome_bot}: FALLBACK - Operação: {operation_result} - Stake: ${stake_value} - Profit: {profit_percentage}%")
    
    async def executar_ciclo_trading(self):
        """
        Executa um ciclo completo de trading
        """
        try:
            # 1. Analisar condição de entrada
            if not await self.analisar_ticks():
                return False  # Condição não atendida
            
            # 2. Executar compra
            contract_id = await self.executar_compra_accumulator()
            if not contract_id:
                return False
            
            # 3. Aguardar resultado
            resultado = await self.aguardar_resultado_contrato(contract_id)
            if not resultado:
                return False
            
            # 4. Processar resultado e ajustar parâmetros
            self.processar_resultado(resultado)
            
            # 5. Salvar no Supabase
            await self.salvar_resultado_supabase(resultado)
            
            return True
            
        except Exception as e:
            logger.error(f"{self.nome_bot}: Erro no ciclo de trading: {e}")
            return False


async def bot_accumulator_scalping(api_manager) -> None:
    """
    Função principal do Accumulator Scalping Bot
    Implementa operação contínua 24/7 conforme especificação
    
    Args:
        api_manager: Instância do ApiManager para controle de rate limiting
    """
    bot = AccumulatorScalpingBot(api_manager)
    
    logger.info(f"🚀 Iniciando {bot.nome_bot}...")
    print(f"🚀 Iniciando {bot.nome_bot}...")
    
    print(f"📊 {bot.nome_bot} configurado:")
    print(f"   💰 Stake inicial: ${bot.stake_inicial}")
    print(f"   🔢 Fator khizzbot: {bot.khizzbot}")
    print(f"   📈 Growth Rate: {bot.growth_rate*100}%")
    print(f"   🎯 Take Profit inicial: {bot.take_profit_inicial*100}%")
    print(f"   🏪 Ativo: {bot.ativo}")
    print(f"   🔄 Operação: Contínua 24/7")
    print(f"   📋 Condição: Red, Red, Red, Blue (últimos 4 ticks)")
    
    retry_count = 0
    max_retries = 3
    
    # Loop principal - operação contínua
    while True:
        try:
            # Executar ciclo de trading
            sucesso = await bot.executar_ciclo_trading()
            
            if sucesso:
                retry_count = 0  # Reset contador em caso de sucesso
            
            # Pausa entre análises (evitar rate limiting)
            await asyncio.sleep(30)  # Aumentado para 30 segundos
            
        except Exception as e:
            if is_websocket_error(e):
                # Tratar erros de WebSocket
                should_continue = await handle_websocket_error(
                    bot.nome_bot, e, api, retry_count, max_retries
                )
                
                if should_continue:
                    retry_count += 1
                    continue
                else:
                    break
            else:
                # Outros erros
                logger.error(f"{bot.nome_bot}: Erro não relacionado à conexão: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    logger.error(f"{bot.nome_bot}: Máximo de tentativas atingido")
                    await asyncio.sleep(60)  # Pausa longa antes de resetar
                    retry_count = 0
                
                await asyncio.sleep(5)

    logger.info(f"{bot.nome_bot}: Bot finalizado")