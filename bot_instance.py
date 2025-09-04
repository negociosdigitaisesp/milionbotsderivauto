#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================
BOT INSTANCE - OPERÁRIO GENÉRICO DA NOVA GERAÇÃO
=====================================================
Este script substitui o accumulator_standalone.py
Implementa a lógica de trading de forma genérica,
buscando parâmetros do banco de dados.

Uso: python bot_instance.py --bot_id <ID>
=====================================================
"""

import os
import sys
import asyncio
import time
import logging
import json
import threading
import websockets
import uuid
import argparse
import signal
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client
from aiohttp import web

# Carregar variáveis de ambiente
load_dotenv('.env.accumulator')

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from robust_order_system import RobustOrderSystem, OperationType
    from enhanced_sync_system import EnhancedSyncSystem
except ImportError:
    # Fallback se os módulos não existirem
    class RobustOrderSystem:
        def __init__(self, api_manager):
            self.api_manager = api_manager
    
    class EnhancedSyncSystem:
        def __init__(self, max_concurrent_operations=2, max_queue_size=3):
            self.operation_semaphore = asyncio.Semaphore(max_concurrent_operations)
            self.signal_queue = asyncio.Queue(maxsize=max_queue_size)
        
        def queue_signal(self, ticks, pattern_detected):
            try:
                signal = type('Signal', (), {'ticks': ticks, 'pattern_detected': pattern_detected})()
                self.signal_queue.put_nowait(signal)
                return True
            except:
                return False
        
        def get_next_signal(self):
            try:
                return self.signal_queue.get_nowait()
            except:
                return None
        
        def can_execute_operation(self):
            return True
        
        def record_operation_success(self):
            pass
        
        def record_operation_failure(self):
            pass

class BotInstance:
    """
    Instância genérica de bot que busca configurações do banco de dados
    """
    
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.bot_config = None
        self.supabase = self._init_supabase()
        
        # Configurar logging específico para este bot
        self.logger = self._setup_logging()
        
        # Variáveis de trading (serão carregadas do banco)
        self.stake = 0.0
        self.initial_stake = 0.0
        self.take_profit_percentual = 0.0
        self.growth_rate = 0.0
        self.max_operations = 10
        self.ativo = 'R_75'
        
        # Carregar configuração do banco
        self._load_bot_configuration()
        
        # Inicializar componentes
        self.api_manager = DerivWebSocketNativo(self.logger)
        self.robust_order_system = RobustOrderSystem(self.api_manager)
        self.sync_system = EnhancedSyncSystem(max_concurrent_operations=2, max_queue_size=3)
        
        # Log de inicialização
        self.logger.info(f"🔧 Componentes inicializados:")
        self.logger.info(f"   • API Manager: {type(self.api_manager).__name__}")
        self.logger.info(f"   • Robust Order System: {type(self.robust_order_system).__name__}")
        self.logger.info(f"   • Sync System: {type(self.sync_system).__name__}")
        
        # WebSocket Lock para resolver concorrência
        self.websocket_lock = asyncio.Lock()
        
        # Estado do bot
        self.running = False
        self.shutdown_requested = False
        self.last_heartbeat = datetime.now()
        self.heartbeat_interval = 60  # segundos
        
        # Log de estado inicial
        self.logger.info(f"🔒 Estado inicial configurado:")
        self.logger.info(f"   • WebSocket Lock: {type(self.websocket_lock).__name__}")
        self.logger.info(f"   • Heartbeat Interval: {self.heartbeat_interval}s")
        
        # Controles de estado
        self.total_profit = 0.0
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        
        # Sistema de ticks
        self.tick_buffer = []
        self.tick_subscription_active = False
        
        # Log de estado final
        self.logger.info(f"📊 Estado final configurado:")
        self.logger.info(f"   • Total Profit: ${self.total_profit}")
        self.logger.info(f"   • Total Operations: {self.total_operations}")
        self.logger.info(f"   • Successful Operations: {self.successful_operations}")
        self.logger.info(f"   • Failed Operations: {self.failed_operations}")
        self.logger.info(f"   • Tick Buffer Size: {len(self.tick_buffer)}")
        
        self.logger.info(f"🤖 Bot Instance inicializado - ID: {bot_id}")
    
    def _init_supabase(self) -> Client:
        """Inicializa conexão com Supabase"""
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_ANON_KEY')
            
            if not url or not key:
                raise ValueError("SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidas")
            
            return create_client(url, key)
            
        except Exception as e:
            print(f"❌ Erro ao conectar com Supabase: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """Configura logging específico para este bot"""
        logger = logging.getLogger(f"bot_instance_{self.bot_id}")
        logger.setLevel(logging.INFO)
        
        # Evitar duplicação de handlers
        if not logger.handlers:
            # Handler para arquivo
            file_handler = logging.FileHandler(f'bot_instance_{self.bot_id}.log', encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Handler para console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formato
            formatter = logging.Formatter(
                f'%(asctime)s - [BOT_{self.bot_id}] - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def _load_bot_configuration(self):
        """Carrega configuração do bot do banco de dados"""
        try:
            response = self.supabase.table('bot_configurations') \
                .select('*') \
                .eq('id', self.bot_id) \
                .single() \
                .execute()
            
            if not response.data:
                raise ValueError(f"Bot ID {self.bot_id} não encontrado")
            
            self.bot_config = response.data
            
            # Carregar parâmetros padrão
            self.bot_name = self.bot_config['bot_name']
            self.stake = float(self.bot_config['param_stake_inicial'])
            self.initial_stake = self.stake
            self.take_profit_percentual = float(self.bot_config['param_take_profit']) / 100.0
            self.growth_rate = float(self.bot_config.get('param_growth_rate', 2.0)) / 100.0
            self.max_operations = int(self.bot_config.get('param_max_operations', 10))
            
            # Configurações adicionais do JSON
            config_json = self.bot_config.get('config_json', {})
            if isinstance(config_json, str):
                config_json = json.loads(config_json)
            
            self.ativo = config_json.get('ativo', 'R_75')
            self.win_stop = config_json.get('win_stop', 1000.0)
            self.loss_limit = config_json.get('loss_limit', 1000.0)
            
            # Aplicar param_overrides se existir
            param_overrides = self.bot_config.get('param_overrides')
            if param_overrides:
                try:
                    if isinstance(param_overrides, str):
                        overrides = json.loads(param_overrides)
                    else:
                        overrides = param_overrides
                    
                    # Sobrescrever parâmetros específicos
                    if 'growth_rate' in overrides:
                        self.growth_rate = float(overrides['growth_rate']) / 100.0
                        self.logger.info(f"🔧 Override aplicado - Growth Rate: {self.growth_rate*100}%")
                    
                    if 'symbol' in overrides:
                        self.ativo = overrides['symbol']
                        self.logger.info(f"🔧 Override aplicado - Symbol: {self.ativo}")
                    
                    if 'stake_inicial' in overrides:
                        self.stake = float(overrides['stake_inicial'])
                        self.initial_stake = self.stake
                        self.logger.info(f"🔧 Override aplicado - Stake: ${self.stake}")
                    
                    if 'take_profit' in overrides:
                        self.take_profit_percentual = float(overrides['take_profit']) / 100.0
                        self.logger.info(f"🔧 Override aplicado - Take Profit: {self.take_profit_percentual*100}%")
                    
                    if 'max_operations' in overrides:
                        self.max_operations = int(overrides['max_operations'])
                        self.logger.info(f"🔧 Override aplicado - Max Operations: {self.max_operations}")
                        
                except Exception as e:
                    self.logger.error(f"⚠️ Erro ao aplicar param_overrides: {e}")
            
            # VALIDAÇÃO CRÍTICA DOS PARÂMETROS
            if self.stake <= 0:
                raise ValueError(f"❌ Stake inválido: ${self.stake}")
            
            if self.ativo not in ['R_10', 'R_25', 'R_50', 'R_75', 'R_100']:
                self.logger.warning(f"⚠️ Ativo não padrão: {self.ativo}")
            
            if self.growth_rate < 0.01 or self.growth_rate > 0.05:
                self.logger.warning(f"⚠️ Growth rate fora do padrão: {self.growth_rate*100}%")
            
            # LOG DETALHADO DA CONFIGURAÇÃO FINAL (CRÍTICO)
            self.logger.info(f"✅ CONFIGURAÇÃO FINAL CARREGADA PARA {self.bot_name}:")
            self.logger.info(f"   • Stake Inicial: ${self.initial_stake}")
            self.logger.info(f"   • Stake Atual: ${self.stake}")
            self.logger.info(f"   • Take Profit: {self.take_profit_percentual*100}%")
            self.logger.info(f"   • Ativo: {self.ativo}")
            self.logger.info(f"   • Growth Rate: {self.growth_rate*100}%")
            self.logger.info(f"   • Max Operations: {self.max_operations}")
            self.logger.info(f"   • Win Stop: ${self.win_stop}")
            self.logger.info(f"   • Loss Limit: ${self.loss_limit}")
            
            # Configuração final consolidada
            self.config = {
                'bot_name': self.bot_name,
                'param_stake_inicial': self.initial_stake,
                'param_stake_atual': self.stake,
                'param_take_profit': self.take_profit_percentual * 100,
                'symbol': self.ativo,
                'growth_rate': self.growth_rate * 100,
                'param_max_operations': self.max_operations,
                'win_stop': self.win_stop,
                'loss_limit': self.loss_limit
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar configuração: {e}")
            sys.exit(1)
    
    async def send_heartbeat(self):
        """Envia sinal de vida para o banco de dados"""
        try:
            # Atualizar status e heartbeat
            update_data = {
                    'last_heartbeat': datetime.now().isoformat(),
                'status': 'running',
                'process_id': os.getpid() if hasattr(os, 'getpid') else None
            }
            
            self.supabase.table('bot_configurations') \
                .update(update_data) \
                .eq('id', self.bot_id) \
                .execute()
            
            self.last_heartbeat = datetime.now()
            self.logger.info(f"💓 Heartbeat enviado - Status: running, PID: {update_data.get('process_id')}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar heartbeat: {e}")
    
    async def log_operation(self, operation_result: str, profit_percentage: float = 0.0, stake_value: float = 0.0):
        """Registra operação na tabela bot_operation_logs"""
        try:
            # Dados para inserção - apenas campos válidos
            log_data = {
                'bot_id': self.bot_id,
                'operation_result': operation_result,
                'profit_percentage': float(profit_percentage),
                'stake_value': float(stake_value),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.debug(f"🔄 Tentando registrar operação no Supabase: {log_data}")
            
            # Inserir no Supabase
            result = self.supabase.table('bot_operation_logs') \
                .insert(log_data) \
                .execute()
            
            self.logger.debug(f"📊 Resposta do Supabase: {result}")
            
            if result.data and len(result.data) > 0:
                self.logger.info(f"✅ Operação registrada no Supabase: {operation_result} - Stake: ${stake_value} - Profit: {profit_percentage}%")
                return True
            else:
                self.logger.error(f"❌ Falha ao registrar no Supabase - Resposta vazia: {result}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ ERRO CRÍTICO ao registrar operação no Supabase: {e}")
            self.logger.error(f"📝 Dados que falharam: bot_id={self.bot_id}, result={operation_result}, profit={profit_percentage}%, stake=${stake_value}")
            
            # Tentar reconectar ao Supabase
            try:
                self.logger.info("🔄 Tentando reconectar ao Supabase...")
                self.supabase = self._init_supabase()
                self.logger.info("✅ Reconexão ao Supabase bem-sucedida")
            except Exception as reconnect_error:
                self.logger.error(f"❌ Falha na reconexão ao Supabase: {reconnect_error}")
            
            return False
    
    async def check_shutdown_signal(self) -> bool:
        """Verifica se deve fazer shutdown graceful"""
        try:
            response = self.supabase.table('bot_configurations') \
                .select('is_active, status') \
                .eq('id', self.bot_id) \
                .single() \
                .execute()
            
            if response.data:
                is_active = response.data.get('is_active', True)
                status = response.data.get('status', 'running')
                
                self.logger.debug(f"🔍 Status check - is_active: {is_active}, status: {status}")
                
                if not is_active or status == 'stopped':
                    self.logger.info(f"🛑 Sinal de shutdown recebido - is_active: {is_active}, status: {status}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao verificar sinal de shutdown: {e}")
            return False
    
    async def _handle_new_tick(self, tick_data):
        """Processa novo tick recebido em tempo real"""
        self.logger.info(f"👁️ TICK RECEBIDO: {tick_data}")
        try:
            tick_value = float(tick_data.get('quote', 0))
            
            if tick_value <= 0:
                self.logger.warning(f"⚠️ Tick inválido recebido: {tick_data}")
                return
            
            # Log do tick recebido
            self.logger.debug(f"📊 Tick recebido: {tick_value:.5f}")
            
            # Adicionar ao buffer
            self.tick_buffer.append(tick_value)
            
            # Manter apenas os últimos 5 ticks
            if len(self.tick_buffer) > 5:
                removed_tick = self.tick_buffer.pop(0)
                self.logger.debug(f"🗑️ Tick removido do buffer: {removed_tick:.5f}")
            
            # Log do buffer atual
            self.logger.debug(f"📋 Buffer atual ({len(self.tick_buffer)} ticks): {[f'{t:.5f}' for t in self.tick_buffer]}")
            
            # Analisar padrão quando tiver 5 ticks
            if len(self.tick_buffer) == 5:
                self.logger.info(f"📊 Buffer completo ({len(self.tick_buffer)} ticks): {[f'{t:.5f}' for t in self.tick_buffer]}")
                
                pattern_detected = self.analisar_padrao_entrada(self.tick_buffer.copy())
                
                if pattern_detected:
                    self.logger.info(f"🎯 PADRÃO DETECTADO! Buffer: {[f'{t:.5f}' for t in self.tick_buffer]}")
                    
                    # Log da operação
                    await self.log_operation(
                        operation_result='SIGNAL_DETECTED',
                        profit_percentage=0.0,
                        stake_value=self.stake
                    )
                else:
                    self.logger.info(f"⏳ Padrão não detectado. Buffer: {[f'{t:.5f}' for t in self.tick_buffer]}")
                
                # Enviar para queue
                success = self.sync_system.queue_signal(self.tick_buffer.copy(), pattern_detected)
                if success:
                    self.logger.info(f"📤 Sinal enviado para queue - Pattern: {pattern_detected}")
                else:
                    self.logger.warning(f"⚠️ Falha ao enviar sinal para queue")
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar tick: {e}")
            self.logger.error(f"📊 Tick data: {tick_data}")
            self.logger.error(f"📋 Buffer atual: {self.tick_buffer}")
    
    def analisar_padrao_entrada(self, ticks: List[float]) -> bool:
        """Analisa padrão de entrada baseado na lógica XML do Accumulator"""
        if len(ticks) < 5:
            self.logger.warning(f"⚠️ Ticks insuficientes para análise: {len(ticks)} < 5")
            return False
        
        try:
            # LÓGICA XML DO ACCUMULATOR STANDALONE
            # Padrão: 4 ticks consecutivos em alta seguidos de 1 em baixa
            # ticks[0] = tick mais antigo, ticks[4] = tick mais recente
            
            # Obter os 5 ticks em ordem cronológica
            tick1 = ticks[0]  # Mais antigo
            tick2 = ticks[1]
            tick3 = ticks[2]
            tick4 = ticks[3]
            tick5 = ticks[4]  # Mais recente
            
            # Verificar se há tendência de alta nos primeiros 4 ticks
            trend_up = (tick2 > tick1 and tick3 > tick2 and tick4 > tick3)
            
            # Verificar se o último tick é uma queda (confirma o padrão)
            last_fall = tick5 < tick4
            
            # Padrão detectado: tendência de alta + queda final
            entrada_xml = trend_up and last_fall
            
            # Log detalhado para debug
            self.logger.info(f"📊 VERIFICAÇÃO DE PADRÃO XML:")
            self.logger.info(f"   • tick1 (antigo): {tick1:.5f}")
            self.logger.info(f"   • tick2: {tick2:.5f} {'↗️' if tick2 > tick1 else '↘️'}")
            self.logger.info(f"   • tick3: {tick3:.5f} {'↗️' if tick3 > tick2 else '↘️'}")
            self.logger.info(f"   • tick4: {tick4:.5f} {'↗️' if tick4 > tick3 else '↘️'}")
            self.logger.info(f"   • tick5 (recente): {tick5:.5f} {'↗️' if tick5 > tick4 else '↘️'}")
            self.logger.info(f"   • Tendência alta: {trend_up}")
            self.logger.info(f"   • Queda final: {last_fall}")
            self.logger.info(f"   • Padrão esperado: 4 ticks ↗️ + 1 tick ↘️")
            self.logger.info(f"   • Entrada detectada: {entrada_xml}")
            
            if entrada_xml:
                self.logger.info("🎯 PADRÃO DE ENTRADA DETECTADO! (XML MATCH)")
                self.logger.info("🚀 EXECUTANDO COMPRA DO CONTRATO ACCUMULATOR...")
            else:
                self.logger.info("⏳ Aguardando padrão correto...")
                
            return entrada_xml
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de padrão: {e}")
            self.logger.error(f"📊 Ticks recebidos: {ticks}")
            return False
    
    async def executar_compra(self) -> Optional[str]:
        """Executa compra baseada nos parâmetros do bot com validação robusta"""
        try:
            # VALIDAÇÃO CRÍTICA DOS PARÂMETROS ANTES DA COMPRA
            # 1. Validar stake mínimo/máximo (conforme Deriv API)
            STAKE_MAXIMO_DERIV = 1000.0
            stake_para_usar = min(self.stake, STAKE_MAXIMO_DERIV)
            
            if stake_para_usar < 0.35:
                self.logger.error(f"❌ Stake muito baixo: ${stake_para_usar} (mínimo: $0.35)")
                return None
                
            if stake_para_usar > STAKE_MAXIMO_DERIV:
                self.logger.error(f"❌ Stake muito alto: ${stake_para_usar} (máximo: ${STAKE_MAXIMO_DERIV})")
                return None
            
            # 2. Validar growth rate (1-5%)
            if self.growth_rate < 0.01 or self.growth_rate > 0.05:
                self.logger.error(f"❌ Growth rate inválido: {self.growth_rate*100}% (deve ser 1-5%)")
                return None
            
            # 3. Validar símbolo
            if not self.ativo or not isinstance(self.ativo, str):
                self.logger.error(f"❌ Símbolo inválido: {self.ativo}")
                return None
            
            # 4. Validar e calcular take profit
            if self.take_profit_percentual <= 0 or self.take_profit_percentual > 1:
                self.logger.error(f"❌ Take profit inválido: {self.take_profit_percentual*100}% (deve ser 0-100%)")
                return None
            
            # CORREÇÃO: Formatar take_profit_amount para exatamente 2 casas decimais
            take_profit_amount = round(self.stake * self.take_profit_percentual, 2)
            
            # LOG DETALHADO DOS PARÂMETROS VALIDADOS
            self.logger.info(f"🔍 PARÂMETROS VALIDADOS PARA COMPRA:")
            self.logger.info(f"   • Stake Original: ${self.stake}")
            self.logger.info(f"   • Stake Limitado: ${stake_para_usar}")
            self.logger.info(f"   • Take Profit: {self.take_profit_percentual*100}% (${take_profit_amount:.2f})")
            self.logger.info(f"   • Ativo: {self.ativo}")
            self.logger.info(f"   • Growth Rate: {self.growth_rate*100}%")
            self.logger.info(f"   • Currency: USD")
            self.logger.info(f"   • Basis: stake")
            
            # ESTRUTURA CORRETA PARA ACCUMULATOR CONFORME DOCUMENTAÇÃO DERIV
            # Primeiro fazer proposal para obter o ID
            proposal_params = {
                "proposal": 1,
                "contract_type": "ACCU",
                "symbol": self.ativo,
                "amount": round(float(stake_para_usar), 2),  # CORREÇÃO: Arredondar para 2 casas decimais
                "basis": "stake",
                "currency": "USD",
                "growth_rate": self.growth_rate,
                "limit_order": {
                    "take_profit": round(float(take_profit_amount), 2)  # CORREÇÃO: Arredondar para 2 casas decimais
                }
            }
            
            self.logger.info(f"🚀 SOLICITANDO PROPOSTA ACCU:")
            self.logger.info(f"   • Parâmetros: {proposal_params}")
            
            # Executar proposta via API com lock
            self.logger.info(f"🔒 Adquirindo lock do WebSocket...")
            async with self.websocket_lock:
                self.logger.info(f"🔒 Lock adquirido, executando proposta...")
                proposal_response = await self.api_manager.proposal(proposal_params)
                self.logger.info(f"🔒 Lock liberado")
            
            if not proposal_response or 'proposal' not in proposal_response:
                self.logger.error(f"❌ Falha na proposta: {proposal_response}")
                await self.log_operation(
                    operation_result='PROPOSAL_FAILED',
                    profit_percentage=0.0,
                    stake_value=stake_para_usar
                )
                return None
            
            proposal = proposal_response['proposal']
            proposal_id = proposal.get('id')
            ask_price = proposal.get('ask_price')
            
            if not proposal_id:
                self.logger.error(f"❌ ID da proposta inválido: {proposal}")
                return None
            
            self.logger.info(f"✅ Proposta obtida - ID: {proposal_id}, Preço: ${ask_price}")
            
            # Agora executar a compra usando o proposal_id
            buy_params = {
                "buy": proposal_id,
                "price": ask_price
            }
            
            self.logger.info(f"💰 EXECUTANDO COMPRA ACCU:")
            self.logger.info(f"   • Proposal ID: {proposal_id}")
            self.logger.info(f"   • Preço: ${ask_price}")
            self.logger.info(f"   • Stake: ${stake_para_usar}")
            self.logger.info(f"   • Ativo: {self.ativo}")
            
            # Log da tentativa
            await self.log_operation(
                operation_result='BUY_PENDING',
                profit_percentage=0.0,
                stake_value=stake_para_usar
            )
            
            # Executar compra via API com lock
            self.logger.info(f"🔒 Adquirindo lock do WebSocket para compra...")
            async with self.websocket_lock:
                self.logger.info(f"🔒 Lock adquirido, executando compra...")
                buy_response = await self.api_manager.buy(buy_params)
                self.logger.info(f"🔒 Lock liberado")
            
            if buy_response and 'buy' in buy_response:
                contract_id = buy_response['buy']['contract_id']
                self.logger.info(f"✅ Compra executada - Contract ID: {contract_id}")
                
                # Atualizar estatísticas
                self.total_operations += 1
                self.logger.info(f"📊 Operação #{self.total_operations} registrada")
                
                # Log de sucesso
                await self.log_operation(
                    operation_result='BUY_SUCCESS',
                    profit_percentage=0.0,
                    stake_value=stake_para_usar
                )
                
                return contract_id
            else:
                self.logger.error(f"❌ Falha na compra: {buy_response}")
                self.failed_operations += 1
                
                await self.log_operation(
                    operation_result='BUY_FAILED',
                    profit_percentage=0.0,
                    stake_value=stake_para_usar
                )
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro na execução da compra: {e}")
            self.failed_operations += 1
            
            await self.log_operation(
                operation_result='BUY_ERROR',
                profit_percentage=0.0,
                stake_value=self.stake
            )
            
            return None
    
    async def monitorar_contrato(self, contract_id: str) -> float:
        """Monitora contrato até finalização"""
        try:
            self.logger.info(f"👁️ Monitorando contrato {contract_id}...")
            
            start_time = time.time()
            check_count = 0
            
            while True:
                check_count += 1
                
                # Verificar status do contrato com lock
                async with self.websocket_lock:
                    self.logger.debug(f"🔍 Verificação {check_count} do contrato {contract_id}")
                    response = await self.api_manager.proposal_open_contract(contract_id)
                    self.logger.debug(f"🔍 Response recebido para contrato {contract_id}")
                
                if response and 'proposal_open_contract' in response:
                    contract = response['proposal_open_contract']
                    
                    # Log do status atual
                    is_sold = contract.get('is_sold', False)
                    current_profit = contract.get('profit', 0)
                    
                    self.logger.debug(f"📊 Status contrato {contract_id}: is_sold={is_sold}, profit=${current_profit}")
                    
                    if is_sold:
                        # Contrato finalizado
                        profit = float(current_profit)
                        
                        self.logger.info(f"🏁 Contrato {contract_id} finalizado - Lucro: ${profit}")
                        
                        # Atualizar estatísticas
                        if profit > 0:
                            self.successful_operations += 1
                            self.logger.info(f"✅ Operação ganha #{self.successful_operations}")
                        else:
                            self.failed_operations += 1
                            self.logger.info(f"❌ Operação perdida #{self.failed_operations}")
                        
                        self.total_profit += profit
                        
                        # Log do resultado
                        profit_percentage = (profit / self.stake) * 100 if self.stake > 0 else 0.0
                        await self.log_operation(
                            operation_result='WON' if profit > 0 else 'LOST',
                            profit_percentage=profit_percentage,
                            stake_value=self.stake
                        )
                        
                        # ATUALIZAR STAKE BASEADO NO GROWTH RATE
                        if profit > 0:
                            # Operação ganha: aumentar stake
                            novo_stake = self.stake * (1 + self.growth_rate)
                            self.logger.info(f"💰 Stake aumentado: ${self.stake:.2f} → ${novo_stake:.2f} (+{self.growth_rate*100}%)")
                            self.stake = novo_stake
                        else:
                            # Operação perdida: manter stake atual
                            self.logger.info(f"📉 Stake mantido após perda: ${self.stake:.2f}")
                        
                        return profit
                else:
                    self.logger.warning(f"⚠️ Resposta inválida do contrato {contract_id}: {response}")
                
                # Aguardar antes da próxima verificação
                await asyncio.sleep(1)
                
                # Timeout de segurança (5 minutos)
                if time.time() - start_time > 300:
                    self.logger.warning(f"⏰ Timeout no monitoramento do contrato {contract_id} após {check_count} verificações")
                    break
            
            self.logger.error(f"❌ Monitoramento do contrato {contract_id} interrompido")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Erro no monitoramento do contrato {contract_id}: {e}")
            return 0.0
    
    async def _process_signals_from_queue(self):
        """Processa sinais da queue"""
        self.logger.info(f"🔄 Processador de sinais iniciado")
        
        while not self.shutdown_requested:
            try:
                signal = self.sync_system.get_next_signal()
                
                if signal and signal.pattern_detected:
                    self.logger.info(f"🎯 SINAL PROCESSADO - Padrão detectado: {[f'{t:.5f}' for t in signal.ticks]}")
                    
                    if self.sync_system.can_execute_operation():
                        self.logger.info(f"✅ Executando operação...")
                        
                        async with self.sync_system.operation_semaphore:
                            self.logger.info(f"🔒 Semáforo adquirido, executando compra...")
                            contract_id = await self.executar_compra()
                            
                            if contract_id:
                                self.logger.info(f"✅ Compra executada, monitorando contrato {contract_id}")
                                lucro = await self.monitorar_contrato(contract_id)
                                self.sync_system.record_operation_success()
                                self.logger.info(f"💰 Operação finalizada - Lucro: ${lucro}")
                            else:
                                self.logger.error(f"❌ Falha na execução da compra")
                                self.sync_system.record_operation_failure()
                    else:
                        self.logger.info(f"⏳ Sistema ocupado, aguardando...")
                elif signal:
                    self.logger.debug(f"📊 Sinal recebido sem padrão: {[f'{t:.5f}' for t in signal.ticks]}")
                else:
                    # Sem sinais na queue
                    pass
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"❌ Erro no processamento de sinais: {e}")
                await asyncio.sleep(1)
        
        self.logger.info(f"🛑 Processador de sinais finalizado")
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat"""
        self.logger.info(f"💓 Loop de heartbeat iniciado - Intervalo: {self.heartbeat_interval}s")
        
        while not self.shutdown_requested:
            try:
                await self.send_heartbeat()
                
                # Verificar sinal de shutdown
                if await self.check_shutdown_signal():
                    self.logger.info(f"🛑 Sinal de shutdown detectado no heartbeat")
                    self.shutdown_requested = True
                    break
                
                # Log de status
                self.logger.debug(f"💓 Heartbeat enviado, aguardando próximo...")
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"❌ Erro no heartbeat: {e}")
                self.logger.info(f"⏳ Aguardando 10s antes do próximo heartbeat...")
                await asyncio.sleep(10)
        
        self.logger.info(f"🛑 Loop de heartbeat finalizado")
    
    async def run(self):
        """Loop principal do bot"""
        try:
            # Log de início
            self.logger.info(f"🚀 Iniciando bot {self.bot_name}...")
            self.logger.info(f"🆔 Bot ID: {self.bot_id}")
            self.logger.info(f"💰 Stake Inicial: ${self.stake}")
            self.logger.info(f"📈 Take Profit: {self.take_profit_percentual*100}%")
            self.logger.info(f"🎯 Ativo: {self.ativo}")
            self.logger.info(f"📊 Growth Rate: {self.growth_rate*100}%")
            
            await self.log_operation(
                operation_result='BOT_START',
                profit_percentage=0.0,
                stake_value=self.stake
            )
            
            # Conectar à API
            self.logger.info(f"🔗 Conectando à API Deriv...")
            await self.api_manager.connect()
            
            # Subscrever ticks
            self.logger.info(f"📡 Subscrevendo ticks do ativo: {self.ativo}")
            await self.api_manager.subscribe_ticks(self.ativo)
            self.api_manager.set_bot_instance(self)
            
            self.logger.info(f"✅ Conexão estabelecida e ticks subscritos")
            
            self.running = True
            
            # Iniciar tasks
            self.logger.info(f"🔄 Iniciando tasks...")
            
            tasks = [
                asyncio.create_task(self._process_signals_from_queue(), name="signal_processor"),
                asyncio.create_task(self._heartbeat_loop(), name="heartbeat")
            ]
            
            self.logger.info(f"✅ {self.bot_name} iniciado com sucesso")
            self.logger.info(f"📋 Tasks ativas: {len(tasks)}")
            
            # Aguardar até shutdown
            self.logger.info(f"⏳ Aguardando tasks...")
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Erro crítico: {e}")
            self.logger.error(f"📋 Stack trace:", exc_info=True)
        finally:
            self.logger.info(f"🛑 Finalizando bot...")
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown graceful"""
        self.logger.info(f"🛑 Finalizando {self.bot_name}...")
        
        self.running = False
        self.shutdown_requested = True
        
        # Log de parada
        self.logger.info(f"📝 Registrando parada do bot...")
        await self.log_operation(
            operation_result='BOT_STOP',
            profit_percentage=0.0,
            stake_value=self.stake
        )
        
        # Atualizar status final
        try:
            self.logger.info(f"📊 Atualizando status final no banco...")
            update_data = {
                    'status': 'stopped',
                'process_id': None,
                'last_heartbeat': datetime.now().isoformat()
            }
            
            self.supabase.table('bot_configurations') \
                .update(update_data) \
                .eq('id', self.bot_id) \
                .execute()
                
            self.logger.info(f"✅ Status final atualizado: stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar status final: {e}")
        
        # Desconectar API
        try:
            self.logger.info(f"🔌 Desconectando da API...")
            await self.api_manager.disconnect()
            self.logger.info(f"✅ API desconectada")
        except Exception as e:
            self.logger.error(f"❌ Erro ao desconectar API: {e}")
        
        # Log final
        self.logger.info(f"📊 Estatísticas finais:")
        self.logger.info(f"   • Total Operations: {self.total_operations}")
        self.logger.info(f"   • Successful: {self.successful_operations}")
        self.logger.info(f"   • Failed: {self.failed_operations}")
        self.logger.info(f"   • Total Profit: ${self.total_profit}")
        self.logger.info(f"   • Stake Final: ${self.stake}")
        
        self.logger.info(f"✅ {self.bot_name} finalizado")

class DerivWebSocketNativo:
    """Gerenciador WebSocket nativo para Deriv API"""
    
    def __init__(self, logger):
        self.logger = logger
        self.ws = None
        self.connected = False
        self.authorized = False
        self.bot_instance = None
        
        # Request management (sistema do accumulator_standalone)
        self.req_id_counter = 0
        self.req_id_lock = threading.Lock()
        self.pending_requests = {}
        self.request_timeout = 15
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        # Configurações
        self.app_id = "85515"
        self.api_token = os.getenv('DERIV_API_TOKEN')
        
        if not self.api_token:
            raise ValueError("DERIV_API_TOKEN deve estar definido")
    
    def _get_next_req_id(self):
        """Gera próximo request ID de forma thread-safe"""
        with self.req_id_lock:
            self.req_id_counter += 1
            req_id = self.req_id_counter
            self.logger.debug(f"🆔 Novo request ID gerado: {req_id}")
            return req_id
    
    def set_bot_instance(self, bot_instance):
        """Define instância do bot para callbacks"""
        self.bot_instance = bot_instance
        self.logger.info(f"🔗 Bot instance definida: {type(bot_instance).__name__}")
        self.logger.info(f"🆔 Bot ID: {getattr(bot_instance, 'bot_id', 'N/A')}")
        self.logger.info(f"📛 Bot Name: {getattr(bot_instance, 'bot_name', 'N/A')}")
    
    async def connect(self):
        """Conecta ao WebSocket"""
        try:
            self.logger.info("🔗 Conectando ao WebSocket...")
            
            url = f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
            self.logger.info(f"🌐 URL: {url}")
            
            self.ws = await websockets.connect(url)
            self.connected = True
            self.logger.info("🔌 WebSocket conectado")
            
            # Iniciar loop de mensagens ANTES da autenticação
            self.logger.info("🔄 Iniciando loop de mensagens...")
            asyncio.create_task(self._handle_messages())
            
            # Autenticar
            self.logger.info("🔐 Autenticando...")
            await self._authenticate()
            
            self.logger.info("✅ WebSocket conectado e autenticado")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na conexão: {e}")
            self.connected = False
            raise
    
    async def _authenticate(self):
        """Autentica com a API"""
        try:
            self.logger.info("🔑 Enviando credenciais...")
            
            auth_message = {
                "authorize": self.api_token
            }
            
            self.logger.debug(f"🔐 Auth message: {auth_message}")
            response = await self._send_request(auth_message)
            
            if 'authorize' in response:
                auth_data = response['authorize']
                self.authorized = True
                self.logger.info("✅ Autenticação bem-sucedida")
                self.logger.info(f"👤 Usuário: {auth_data.get('name', 'N/A')}")
                self.logger.info(f"💰 Saldo: ${auth_data.get('balance', 'N/A')}")
            else:
                error_msg = f"Falha na autenticação: {response}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ Erro na autenticação: {e}")
            self.authorized = False
            raise
    
    async def _handle_messages(self):
        """Processa mensagens recebidas do WebSocket"""
        try:
            self.logger.info("🔄 Loop de mensagens iniciado")
            
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    req_id = data.get('req_id')
                    
                    self.logger.debug(f"📥 Mensagem recebida - req_id: {req_id}")
                    
                    # Processar ticks em tempo real
                    if 'tick' in data and self.bot_instance:
                        self.logger.debug(f"📊 Tick recebido: {data['tick']}")
                        await self.bot_instance._handle_new_tick(data['tick'])
                    
                    # Resolver requests pendentes
                    if req_id and req_id in self.pending_requests:
                        future = self.pending_requests.pop(req_id)
                        if not future.done():
                            future.set_result(data)
                            self.logger.debug(f"✅ Request {req_id} resolvido")
                    
                    # Log de mensagens especiais
                    if 'error' in data:
                        self.logger.warning(f"⚠️ Mensagem de erro: {data['error']}")
                    elif 'msg_type' in data:
                        self.logger.debug(f"📋 Tipo de mensagem: {data['msg_type']}")
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ Erro ao decodificar JSON: {e}")
                    self.logger.error(f"📄 Mensagem raw: {message}")
                except Exception as e:
                    self.logger.error(f"❌ Erro ao processar mensagem: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("⚠️ Conexão WebSocket fechada")
            self.connected = False
        except Exception as e:
            self.logger.error(f"❌ Erro no handler de mensagens: {e}")
            self.connected = False
    
    async def _send_request(self, message):
        """Envia request e aguarda response"""
        req_id = None
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                self.logger.debug(f"⏳ Rate limiting: aguardando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            req_id = message.get('req_id')
            if not req_id:
                req_id = self._get_next_req_id()
                message['req_id'] = req_id
            
            self.logger.debug(f"🆔 Request ID: {req_id}")
            
            # Criar Future para aguardar response
            future = asyncio.Future()
            self.pending_requests[req_id] = future
            
            # Enviar mensagem
            message_str = json.dumps(message)
            self.logger.debug(f"📤 Enviando request {req_id}: {message_str}")
            
            await self.ws.send(message_str)
            self.last_request_time = time.time()
            
            # Aguardar response com timeout
            try:
                self.logger.debug(f"⏳ Aguardando response para request {req_id}...")
                response = await asyncio.wait_for(future, timeout=self.request_timeout)
                self.logger.debug(f"✅ Response recebido para request {req_id}")
                return response
            except asyncio.TimeoutError:
                # Cleanup em caso de timeout
                self.pending_requests.pop(req_id, None)
                timeout_msg = f"Timeout aguardando response para req_id {req_id}"
                self.logger.error(f"⏰ {timeout_msg}")
                raise Exception(timeout_msg)
                
        except Exception as e:
            # Cleanup em caso de erro
            if req_id:
                self.pending_requests.pop(req_id, None)
            self.logger.error(f"❌ Erro no request {req_id}: {e}")
            raise e
    
    async def subscribe_ticks(self, symbol: str):
        """Subscreve ticks de um símbolo"""
        try:
            self.logger.info(f"📡 Subscrevendo ticks do símbolo: {symbol}")
            
            message = {
                "ticks": symbol,
                "subscribe": 1
            }
            
            self.logger.debug(f"📡 Subscribe message: {message}")
            response = await self._send_request(message)
            
            if 'error' in response:
                error_msg = f"Erro na subscrição: {response['error']}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            else:
                self.logger.info(f"✅ Subscrito aos ticks de {symbol}")
                self.logger.debug(f"📡 Response: {response}")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na subscrição de ticks: {e}")
            raise
    
    async def buy(self, params):
        """Executa compra"""
        try:
            self.logger.info(f"💰 Executando compra com parâmetros: {params}")
            
            response = await self._send_request(params)
            
            if 'error' in response:
                error_msg = f"Deriv API Error: {response['error']['message']}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
            self.logger.info(f"✅ Compra executada com sucesso")
            self.logger.debug(f"💰 Response: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Erro na execução da compra: {e}")
            raise
    
    async def proposal_open_contract(self, contract_id: str):
        """Consulta contrato aberto"""
        message = {
            "proposal_open_contract": 1,
            "contract_id": contract_id
        }
        
        response = await self._send_request(message)
        
        if 'error' in response:
            raise Exception(f"Deriv API Error: {response['error']['message']}")
        
        return response
    
    async def proposal(self, params):
        """Solicita proposta para contrato"""
        try:
            self.logger.info(f"📋 Solicitando proposta com parâmetros: {params}")
            
            response = await self._send_request(params)
            
            if 'error' in response:
                error_msg = f"Deriv API Error: {response['error']['message']}"
                self.logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            self.logger.info(f"✅ Proposta solicitada com sucesso")
            self.logger.debug(f"📋 Response: {response}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Erro na solicitação de proposta: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta WebSocket"""
        try:
            self.logger.info("🔌 Desconectando WebSocket...")
            
            self.connected = False
            self.authorized = False
            
            if self.ws:
                await self.ws.close()
                self.ws = None
                self.logger.info("✅ WebSocket desconectado")
            else:
                self.logger.info("ℹ️ WebSocket já estava desconectado")
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao desconectar WebSocket: {e}")
            # Forçar desconexão
            self.connected = False
            self.authorized = False
            self.ws = None

def parse_arguments():
    """Parse argumentos da linha de comando"""
    parser = argparse.ArgumentParser(description='Bot Instance - Operário Genérico')
    parser.add_argument('--bot_id', type=str, required=True, help='ID do bot no banco de dados')
    return parser.parse_args()

async def main():
    """Função principal"""
    args = parse_arguments()
    
    print("")
    print("="*60)
    print("🤖 BOT INSTANCE - OPERÁRIO GENÉRICO")
    print("="*60)
    print(f"🆔 Bot ID: {args.bot_id}")
    print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    print("")
    
    try:
        print(f"🔧 Inicializando BotInstance para ID: {args.bot_id}")
        bot = BotInstance(args.bot_id)
        
        print(f"🚀 Executando bot...")
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n⌨️ Interrupção manual detectada")
        if 'bot' in locals():
            print("🛑 Finalizando bot...")
            await bot.shutdown()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())