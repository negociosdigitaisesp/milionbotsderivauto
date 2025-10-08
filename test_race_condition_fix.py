#!/usr/bin/env python3
"""
Teste para validar o mecanismo de bloqueio e prevenção de condições de corrida
no bot de trading assíncrono AccumulatorScalpingBot.

Este teste verifica:
1. Inicialização correta da variável is_trading_locked
2. Bloqueio adequado durante operações
3. Liberação correta do bloqueio após conclusão
4. Prevenção de múltiplas operações simultâneas
5. Comportamento correto em cenários de erro
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tunderbotalavanca import AccumulatorScalpingBot

class TestRaceConditionFix(unittest.TestCase):
    """Testes para validar a correção de condições de corrida"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        # Mock da configuração da conta
        self.account_config = {
            'name': 'Test Account',
            'token': 'test_token',
            'app_id': 'test_app_id'
        }
        
        # Criar instância do bot com mocks
        with patch('tunderbotalavanca.DerivWebSocketNativo'), \
             patch('tunderbotalavanca.RobustOrderSystem'), \
             patch('tunderbotalavanca.EnhancedSyncSystem'), \
             patch('tunderbotalavanca.EnhancedTickBuffer'), \
             patch('tunderbotalavanca.WebSocketRecoveryManager'), \
             patch('tunderbotalavanca.ThreadSafeSignalQueue'), \
             patch('tunderbotalavanca.SystemHealthMonitor'):
            
            self.bot = AccumulatorScalpingBot(self.account_config)
    
    def test_initial_lock_state(self):
        """Teste 1: Verificar se is_trading_locked é inicializado como False"""
        print("🧪 Teste 1: Verificando inicialização da variável de bloqueio...")
        
        self.assertFalse(self.bot.is_trading_locked, 
                        "is_trading_locked deve ser inicializado como False")
        print("✅ Variável is_trading_locked inicializada corretamente como False")
    
    @patch('tunderbotalavanca.asyncio.create_task')
    async def test_lock_mechanism_on_trigger(self, mock_create_task):
        """Teste 2: Verificar se o bloqueio é ativado quando um gatilho é disparado"""
        print("\n🧪 Teste 2: Verificando ativação do bloqueio no gatilho...")
        
        # Simular tick que deve disparar compra (dígito seguro + probabilidade alta)
        tick_data = {'quote': 1.23456}  # Último dígito 6 (seguro)
        
        # Mock do random para garantir que should_buy seja True
        with patch('tunderbotalavanca.random.randint', return_value=5):  # 90% chance para 0 perdas
            await self.bot._handle_new_tick(tick_data)
        
        # Verificar se o bloqueio foi ativado
        self.assertTrue(self.bot.is_trading_locked, 
                       "is_trading_locked deve ser True após gatilho de compra")
        
        # Verificar se create_task foi chamado
        mock_create_task.assert_called_once()
        print("✅ Bloqueio ativado corretamente no gatilho de compra")
    
    @patch('tunderbotalavanca.asyncio.create_task')
    async def test_ignore_trigger_when_locked(self, mock_create_task):
        """Teste 3: Verificar se gatilhos são ignorados quando já há operação em andamento"""
        print("\n🧪 Teste 3: Verificando se gatilhos são ignorados quando travado...")
        
        # Simular estado travado
        self.bot.is_trading_locked = True
        
        # Simular tick que deveria disparar compra
        tick_data = {'quote': 1.23456}  # Último dígito 6 (seguro)
        
        # Mock do random para garantir que should_buy seja True
        with patch('tunderbotalavanca.random.randint', return_value=5):
            await self.bot._handle_new_tick(tick_data)
        
        # Verificar se create_task NÃO foi chamado
        mock_create_task.assert_not_called()
        print("✅ Gatilho ignorado corretamente quando bot já está travado")
    
    async def test_lock_release_after_successful_operation(self):
        """Teste 4: Verificar se o bloqueio é liberado após operação bem-sucedida"""
        print("\n🧪 Teste 4: Verificando liberação do bloqueio após operação bem-sucedida...")
        
        # Simular estado travado
        self.bot.is_trading_locked = True
        
        # Mock das funções do ciclo de vida
        self.bot.executar_compra_digitunder = AsyncMock(return_value="contract_123")
        self.bot.monitorar_contrato = AsyncMock(return_value=10.0)  # Lucro
        self.bot.aplicar_gestao_risco = MagicMock()
        
        # Executar ciclo de vida
        await self.bot._execute_trade_lifecycle()
        
        # Verificar se o bloqueio foi liberado
        self.assertFalse(self.bot.is_trading_locked, 
                        "is_trading_locked deve ser False após conclusão da operação")
        print("✅ Bloqueio liberado corretamente após operação bem-sucedida")
    
    async def test_lock_release_after_failed_operation(self):
        """Teste 5: Verificar se o bloqueio é liberado após operação falhada"""
        print("\n🧪 Teste 5: Verificando liberação do bloqueio após operação falhada...")
        
        # Simular estado travado
        self.bot.is_trading_locked = True
        
        # Mock das funções do ciclo de vida (falha na compra)
        self.bot.executar_compra_digitunder = AsyncMock(return_value=None)  # Falha
        
        # Executar ciclo de vida
        await self.bot._execute_trade_lifecycle()
        
        # Verificar se o bloqueio foi liberado
        self.assertFalse(self.bot.is_trading_locked, 
                        "is_trading_locked deve ser False mesmo após falha na operação")
        print("✅ Bloqueio liberado corretamente após operação falhada")
    
    async def test_lock_release_after_exception(self):
        """Teste 6: Verificar se o bloqueio é liberado mesmo quando ocorre exceção"""
        print("\n🧪 Teste 6: Verificando liberação do bloqueio após exceção...")
        
        # Simular estado travado
        self.bot.is_trading_locked = True
        
        # Mock que gera exceção
        self.bot.executar_compra_digitunder = AsyncMock(side_effect=Exception("Erro simulado"))
        
        # Executar ciclo de vida
        await self.bot._execute_trade_lifecycle()
        
        # Verificar se o bloqueio foi liberado
        self.assertFalse(self.bot.is_trading_locked, 
                        "is_trading_locked deve ser False mesmo após exceção")
        print("✅ Bloqueio liberado corretamente após exceção")
    
    @patch('tunderbotalavanca.asyncio.create_task')
    async def test_multiple_simultaneous_triggers(self, mock_create_task):
        """Teste 7: Simular múltiplos gatilhos simultâneos"""
        print("\n🧪 Teste 7: Testando múltiplos gatilhos simultâneos...")
        
        # Simular múltiplos ticks simultâneos que deveriam disparar compra
        tick_data = {'quote': 1.23456}  # Último dígito 6 (seguro)
        
        # Mock do random para garantir que should_buy seja sempre True
        with patch('tunderbotalavanca.random.randint', return_value=5):
            # Simular 5 ticks simultâneos
            tasks = [self.bot._handle_new_tick(tick_data) for _ in range(5)]
            await asyncio.gather(*tasks)
        
        # Verificar se apenas uma operação foi iniciada
        self.assertEqual(mock_create_task.call_count, 1, 
                        "Apenas uma operação deve ser iniciada mesmo com múltiplos gatilhos")
        
        # Verificar se o bot está travado
        self.assertTrue(self.bot.is_trading_locked, 
                       "Bot deve estar travado após primeiro gatilho")
        print("✅ Múltiplos gatilhos simultâneos tratados corretamente")
    
    async def test_safety_filter_with_lock(self):
        """Teste 8: Verificar se filtro de segurança funciona independente do bloqueio"""
        print("\n🧪 Teste 8: Verificando filtro de segurança com bloqueio...")
        
        # Testar com bot desbloqueado
        self.bot.is_trading_locked = False
        
        # Simular tick com dígito perigoso (8)
        tick_data = {'quote': 1.23458}  # Último dígito 8 (perigoso)
        
        with patch('tunderbotalavanca.asyncio.create_task') as mock_create_task:
            await self.bot._handle_new_tick(tick_data)
            
            # Verificar se nenhuma operação foi iniciada
            mock_create_task.assert_not_called()
            
            # Verificar se bot continua desbloqueado
            self.assertFalse(self.bot.is_trading_locked, 
                           "Bot deve continuar desbloqueado após filtro de segurança")
        
        print("✅ Filtro de segurança funciona independente do estado de bloqueio")

async def run_all_tests():
    """Executa todos os testes de forma assíncrona"""
    print("🚀 Iniciando testes do mecanismo de bloqueio para prevenção de condições de corrida...\n")
    
    test_instance = TestRaceConditionFix()
    test_instance.setUp()
    
    try:
        # Executar testes síncronos
        test_instance.test_initial_lock_state()
        
        # Executar testes assíncronos
        await test_instance.test_lock_mechanism_on_trigger()
        await test_instance.test_ignore_trigger_when_locked()
        await test_instance.test_lock_release_after_successful_operation()
        await test_instance.test_lock_release_after_failed_operation()
        await test_instance.test_lock_release_after_exception()
        await test_instance.test_multiple_simultaneous_triggers()
        await test_instance.test_safety_filter_with_lock()
        
        print("\n" + "="*80)
        print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("✅ Mecanismo de bloqueio implementado corretamente")
        print("✅ Condições de corrida prevenidas efetivamente")
        print("✅ Bot agora processa operações de forma sequencial e segura")
        print("✅ API protegida contra sobrecarga")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        return False

if __name__ == "__main__":
    # Executar os testes
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🔒 CORREÇÃO DE CONDIÇÃO DE CORRIDA VALIDADA COM SUCESSO!")
        print("O bot agora está protegido contra operações simultâneas.")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM - REVISAR IMPLEMENTAÇÃO")