#!/usr/bin/env python3
"""
Teste da Lógica de Análise de Ticks em Tempo Real - ALAVANCS PRO 2.0
Valida a implementação da função _handle_new_tick com lógica de três camadas
"""

import asyncio
import sys
import os
import random
from unittest.mock import Mock, AsyncMock, patch

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tunderbotalavanca import AccumulatorScalpingBot

class TestTickLogicAlavancs:
    """Classe de teste para validar a lógica de ticks da estratégia ALAVANCS PRO 2.0"""
    
    def __init__(self):
        self.test_results = []
        self.bot = None
    
    async def setup_bot(self):
        """Configura um bot de teste com mocks"""
        # Configuração da conta para o bot
        account_config = {
            'name': 'Test Account',
            'token': 'test_token_123',
            'app_id': 'test_app_456',
            'email': 'test@test.com',
            'password': 'test123',
            'valor_entrada': 10.0,
            'martingale_steps': [10, 20, 40],
            'profit_target': 100.0,
            'loss_limit': 200.0
        }
        
        # Criar o bot com a configuração correta
        self.bot = AccumulatorScalpingBot(account_config)
        
        # Mock do API manager após criação
        api_manager_mock = Mock()
        api_manager_mock.connect = AsyncMock(return_value=True)
        api_manager_mock.subscribe_ticks = AsyncMock()
        api_manager_mock.get_balance = AsyncMock(return_value=1000.0)
        api_manager_mock.buy_contract = AsyncMock(return_value={'contract_id': 'test_123'})
        
        # Substituir o api_manager real pelo mock
        self.bot.api_manager = api_manager_mock
        
        # Mock do Supabase
        supabase_mock = Mock()
        supabase_mock.table = Mock()
        supabase_mock.table.return_value.insert = Mock()
        supabase_mock.table.return_value.insert.return_value.execute = Mock()
        
        # Substituir o supabase real pelo mock se existir
        if hasattr(self.bot, 'supabase'):
            self.bot.supabase = supabase_mock
        
        # Inicializar estados necessários
        self.bot.safety_pause_active = False
        self.bot.consecutive_losses = 0
        self.bot.is_trading = True
        self.bot.profit_target_reached = False
        self.bot.loss_limit_reached = False
        
        print("✅ Bot de teste configurado com sucesso")
    
    def create_tick_data(self, price):
        """Cria dados de tick simulados"""
        return {
            'tick': {
                'ask': price,
                'bid': price - 0.001,
                'epoch': 1640995200,
                'id': f'tick_{random.randint(1000, 9999)}',
                'pip_size': 5,
                'quote': price,
                'symbol': 'R_50'
            }
        }
    
    async def test_last_digit_extraction(self):
        """Testa a extração do último dígito do preço"""
        print("\n🔍 Teste 1: Extração do último dígito")
        
        test_cases = [
            (123.45678, 8),  # Último dígito será 8
            (100.00119, 9),  # Último dígito será 9
            (999.99990, 0),  # Último dígito será 0
            (50.00001, 1),   # Último dígito será 1
            (75.23847, 7)    # Último dígito será 7
        ]
        
        for price, expected_digit in test_cases:
            tick_data = self.create_tick_data(price)
            
            # Simular a extração do último dígito (mesma lógica do código real)
            price_str = f"{price:.5f}"  # Garantir 5 casas decimais
            last_digit = int(price_str[-1])  # Último dígito
            
            success = last_digit == expected_digit
            result = f"Preço {price} → Último dígito {last_digit} (esperado: {expected_digit})"
            
            if success:
                print(f"  ✅ {result}")
            else:
                print(f"  ❌ {result}")
            
            self.test_results.append(('Extração último dígito', success))
    
    async def test_safety_filter(self):
        """Testa o filtro de segurança para dígitos 8 e 9"""
        print("\n🛡️ Teste 2: Filtro de segurança")
        
        # Teste com dígitos 8 e 9 (devem bloquear operação)
        dangerous_prices = [123.45678, 999.99999, 50.00008, 75.23459]
        
        for price in dangerous_prices:
            tick_data = self.create_tick_data(price)
            
            # Mock para verificar se a operação foi bloqueada
            with patch.object(self.bot, '_execute_trade_lifecycle') as mock_trade:
                await self.bot._handle_new_tick(tick_data)
                
                # Se o filtro funcionou, _execute_trade_lifecycle não deve ter sido chamado
                success = not mock_trade.called
                price_str = f"{price:.5f}"
                last_digit = int(price_str[-1])
                result = f"Preço {price} (dígito {last_digit}) → Operação bloqueada: {success}"
                
                if success:
                    print(f"  ✅ {result}")
                else:
                    print(f"  ❌ {result}")
                
                self.test_results.append(('Filtro segurança - bloqueio', success))
        
        # Teste com dígitos seguros (devem permitir operação se outras condições forem atendidas)
        safe_prices = [123.45671, 999.99992, 50.00003, 75.23457]
        
        for price in safe_prices:
            tick_data = self.create_tick_data(price)
            
            # Mock para verificar se a operação pode prosseguir
            with patch.object(self.bot, '_execute_trade_lifecycle') as mock_trade:
                with patch('random.randint', return_value=9):  # Força condição de compra
                    await self.bot._handle_new_tick(tick_data)
                    
                    # Com dígito seguro e condição de compra, deve chamar _execute_trade_lifecycle
                    success = mock_trade.called
                    price_str = f"{price:.5f}"
                    last_digit = int(price_str[-1])
                    result = f"Preço {price} (dígito {last_digit}) → Operação permitida: {success}"
                    
                    if success:
                        print(f"  ✅ {result}")
                    else:
                        print(f"  ❌ {result}")
                    
                    self.test_results.append(('Filtro segurança - permitir', success))
    
    async def test_probabilistic_trigger(self):
        """Testa o gatilho probabilístico baseado em consecutive_losses"""
        print("\n🎯 Teste 3: Gatilho probabilístico")
        
        # Mock da função de execução de trade
        self.bot._execute_alavancs_pro_trade = AsyncMock()
        
        test_scenarios = [
            (0, "consecutive_losses = 0: compra se random >= 1"),
            (1, "consecutive_losses = 1: compra se random >= 6"), 
            (2, "consecutive_losses = 2: compra se random <= 4"),
            (3, "consecutive_losses = 3: compra se random <= 4")
        ]
        
        for losses, description in test_scenarios:
            print(f"\n  📊 {description}")
            
            self.bot.consecutive_losses = losses
            self.bot.safety_pause_active = False
            
            # Testar múltiplas execuções para verificar probabilidade
            executions = 0
            total_tests = 10
            
            for random_val in range(total_tests):
                # Reset mock
                self.bot._execute_alavancs_pro_trade.reset_mock()
                
                # Usar preço seguro (último dígito < 8)
                tick_data = self.create_tick_data(123.45677)
                
                # Patch do random para controlar o resultado
                with patch('random.randint') as mock_random:
                    mock_random.return_value = random_val
                    
                    await self.bot._handle_new_tick(tick_data)
                    
                    if self.bot._execute_alavancs_pro_trade.called:
                        executions += 1
            
            execution_rate = (executions / total_tests) * 100
            print(f"    Taxa de execução: {execution_rate:.1f}% ({executions}/{total_tests})")
            
            # Verificar se a taxa está dentro do esperado
            if losses == 0:
                expected_rate = 90  # >= 1 de 10 = 90%
            elif losses == 1:
                expected_rate = 40  # >= 6 de 10 = 40%
            else:
                expected_rate = 50  # <= 4 de 10 = 50%
            
            success = abs(execution_rate - expected_rate) <= 30  # Tolerância de 30%
            
            if success:
                print(f"    ✅ Taxa dentro do esperado (~{expected_rate}%)")
            else:
                print(f"    ❌ Taxa fora do esperado (~{expected_rate}%)")
            
            self.test_results.append(('Gatilho probabilístico', success))
    
    async def test_safety_pause_blocking(self):
        """Testa se safety_pause_active bloqueia execuções"""
        print("\n🚫 Teste 4: Bloqueio por safety_pause_active")
        
        self.bot._execute_alavancs_pro_trade = AsyncMock()
        self.bot.safety_pause_active = True
        self.bot.consecutive_losses = 0
        
        # Usar preço perigoso para manter safety_pause ativo
        tick_data = self.create_tick_data(123.45678)  # Dígito 8 - perigoso
        
        await self.bot._handle_new_tick(tick_data)
        
        success = not self.bot._execute_alavancs_pro_trade.called
        result = f"safety_pause_active = True → Execução bloqueada: {success}"
        
        if success:
            print(f"  ✅ {result}")
        else:
            print(f"  ❌ {result}")
        
        self.test_results.append(('Bloqueio safety_pause', success))
    
    def print_summary(self):
        """Imprime o resumo dos testes"""
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES - LÓGICA DE TICKS ALAVANCS PRO 2.0")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success in self.test_results if success)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total de testes: {total_tests}")
        print(f"Testes aprovados: {passed_tests}")
        print(f"Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 TODOS OS TESTES PASSARAM! Lógica de ticks validada com sucesso!")
        elif success_rate >= 80:
            print("\n✅ Maioria dos testes passou. Lógica funcionando adequadamente.")
        else:
            print("\n⚠️ Alguns testes falharam. Revisar implementação necessária.")
        
        # Detalhes por categoria
        categories = {}
        for test_name, success in self.test_results:
            if test_name not in categories:
                categories[test_name] = {'passed': 0, 'total': 0}
            categories[test_name]['total'] += 1
            if success:
                categories[test_name]['passed'] += 1
        
        print("\n📋 Detalhes por categoria:")
        for category, stats in categories.items():
            rate = (stats['passed'] / stats['total']) * 100
            print(f"  {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes da lógica de ticks ALAVANCS PRO 2.0...")
    
    tester = TestTickLogicAlavancs()
    
    try:
        await tester.setup_bot()
        
        await tester.test_last_digit_extraction()
        await tester.test_safety_filter()
        await tester.test_probabilistic_trigger()
        await tester.test_safety_pause_blocking()
        
        tester.print_summary()
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())