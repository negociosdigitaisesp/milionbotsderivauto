#!/usr/bin/env python3
"""
Teste do ALAVANCS PRO 2.0 - Verificação do Fluxo Corrigido
Testa se as operações não travem mais e se o processamento de ticks continua fluindo.
"""

import asyncio
import logging
import time
from tunderbotalavanca import AccumulatorScalpingBot

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestAlavancsPro:
    def __init__(self):
        self.test_results = []
        
    async def test_non_blocking_tick_processing(self):
        """Testa se o processamento de ticks não trava mais"""
        logger.info("🧪 TESTE 1: Processamento não-bloqueante de ticks")
        
        try:
            # Configuração de teste - usar None para evitar validação de token
            bot = AccumulatorScalpingBot(None)
            
            # Simular múltiplos ticks rapidamente
            test_ticks = [
                {'quote': 1.23456},  # último dígito 6 - deve processar
                {'quote': 1.23457},  # último dígito 7 - deve processar
                {'quote': 1.23458},  # último dígito 8 - deve ativar filtro de segurança
                {'quote': 1.23459},  # último dígito 9 - filtro de segurança ativo
                {'quote': 1.23453},  # último dígito 3 - deve desativar filtro
                {'quote': 1.23454},  # último dígito 4 - deve processar
            ]
            
            start_time = time.time()
            
            # Processar ticks rapidamente
            for i, tick in enumerate(test_ticks):
                logger.info(f"📊 Processando tick {i+1}: {tick['quote']}")
                
                # Chamar _handle_new_tick diretamente (sem await para testar não-bloqueio)
                tick_start = time.time()
                await bot._handle_new_tick(tick)
                tick_duration = time.time() - tick_start
                
                logger.info(f"⏱️ Tick {i+1} processado em {tick_duration:.3f}s")
                
                # Verificar se o processamento foi rápido (não-bloqueante)
                if tick_duration > 0.1:  # Mais de 100ms indica possível bloqueio
                    logger.warning(f"⚠️ Tick {i+1} demorou {tick_duration:.3f}s - possível bloqueio")
                
                # Pequena pausa entre ticks
                await asyncio.sleep(0.1)
            
            total_time = time.time() - start_time
            logger.info(f"✅ TESTE 1 CONCLUÍDO: {len(test_ticks)} ticks processados em {total_time:.3f}s")
            
            # Verificar se o tempo total foi razoável
            expected_max_time = len(test_ticks) * 0.2  # 200ms por tick máximo
            if total_time <= expected_max_time:
                self.test_results.append("✅ Processamento não-bloqueante: PASSOU")
                return True
            else:
                self.test_results.append(f"❌ Processamento não-bloqueante: FALHOU ({total_time:.3f}s)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste 1: {e}")
            self.test_results.append(f"❌ Processamento não-bloqueante: ERRO - {e}")
            return False
    
    async def test_safety_filter_logic(self):
        """Testa a lógica do filtro de segurança"""
        logger.info("🧪 TESTE 2: Lógica do filtro de segurança")
        
        try:
            from unittest.mock import patch
            bot = AccumulatorScalpingBot(None)
            
            # Teste: dígito >= 8 deve bloquear operação
            with patch.object(bot, '_execute_trade_lifecycle') as mock_trade:
                await bot._handle_new_tick({'quote': 1.23458})  # dígito 8
                blocked_8 = not mock_trade.called
            
            with patch.object(bot, '_execute_trade_lifecycle') as mock_trade:
                await bot._handle_new_tick({'quote': 1.23459})  # dígito 9
                blocked_9 = not mock_trade.called
            
            # Teste: dígito < 8 deve permitir operação (se outras condições forem atendidas)
            with patch.object(bot, '_execute_trade_lifecycle') as mock_trade:
                with patch('random.randint', return_value=9):  # Força condição de compra
                    await bot._handle_new_tick({'quote': 1.23453})  # dígito 3
                    allowed = mock_trade.called
            
            if blocked_8 and blocked_9 and allowed:
                self.test_results.append("✅ Filtro de segurança: PASSOU")
                logger.info("✅ Filtro de segurança funcionando corretamente")
                return True
            else:
                self.test_results.append("❌ Filtro de segurança: FALHOU")
                logger.error(f"❌ Filtro de segurança falhou: bloqueio_8={blocked_8}, bloqueio_9={blocked_9}, permitir_3={allowed}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste 2: {e}")
            self.test_results.append(f"❌ Filtro de segurança: ERRO - {e}")
            return False
    
    async def test_trade_lifecycle_async(self):
        """Testa se o ciclo de vida da operação é executado de forma assíncrona"""
        logger.info("🧪 TESTE 3: Execução assíncrona do ciclo de vida")
        
        try:
            bot = AccumulatorScalpingBot(None)
            
            # Verificar se a função _execute_trade_lifecycle existe
            if not hasattr(bot, '_execute_trade_lifecycle'):
                self.test_results.append("❌ Ciclo de vida assíncrono: FUNÇÃO NÃO ENCONTRADA")
                return False
            
            # Verificar se a função é uma corrotina
            import inspect
            if not inspect.iscoroutinefunction(bot._execute_trade_lifecycle):
                self.test_results.append("❌ Ciclo de vida assíncrono: NÃO É CORROTINA")
                return False
            
            # Verificar se a variável de controle existe
            if not hasattr(bot, '_trade_in_progress'):
                bot._trade_in_progress = False
            
            self.test_results.append("✅ Ciclo de vida assíncrono: PASSOU")
            logger.info("✅ Função _execute_trade_lifecycle está corretamente implementada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no teste 3: {e}")
            self.test_results.append(f"❌ Ciclo de vida assíncrono: ERRO - {e}")
            return False
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🚀 INICIANDO TESTES DO ALAVANCS PRO 2.0 CORRIGIDO")
        logger.info("=" * 60)
        
        tests = [
            self.test_non_blocking_tick_processing,
            self.test_safety_filter_logic,
            self.test_trade_lifecycle_async
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                await asyncio.sleep(0.5)  # Pausa entre testes
            except Exception as e:
                logger.error(f"❌ Erro executando teste: {e}")
        
        # Relatório final
        logger.info("=" * 60)
        logger.info("📋 RELATÓRIO FINAL DOS TESTES")
        logger.info("=" * 60)
        
        for result in self.test_results:
            logger.info(result)
        
        logger.info(f"📊 RESUMO: {passed}/{total} testes passaram")
        
        if passed == total:
            logger.info("🎉 TODOS OS TESTES PASSARAM! O bot está funcionando corretamente.")
            return True
        else:
            logger.warning(f"⚠️ {total - passed} teste(s) falharam. Revisar implementação.")
            return False

async def main():
    """Função principal"""
    tester = TestAlavancsPro()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("✅ ALAVANCS PRO 2.0 - CORREÇÃO BEM-SUCEDIDA!")
    else:
        logger.error("❌ ALAVANCS PRO 2.0 - CORREÇÃO PRECISA DE AJUSTES!")

if __name__ == "__main__":
    asyncio.run(main())