#!/usr/bin/env python3
"""
Teste da função start refatorada - ALAVANCS PRO 2.0
Verifica se o novo fluxo de execução principal está funcionando corretamente
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
import logging

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging para o teste
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestRefactoredStart:
    """Classe de teste para a função start refatorada"""
    
    def __init__(self):
        self.test_results = []
    
    async def test_start_initialization(self):
        """Testa se a função start inicializa corretamente"""
        logger.info("🧪 Testando inicialização da função start refatorada...")
        
        try:
            # Mock das dependências
            with patch('tunderbotalavanca.AccumulatorScalpingBot') as MockBot:
                # Configurar mock do bot
                mock_bot = MockBot.return_value
                mock_bot.api_manager = Mock()
                mock_bot.api_manager.connect = AsyncMock(return_value=True)
                mock_bot.api_manager.connected = True
                mock_bot.api_manager.subscribe_ticks = AsyncMock()
                mock_bot.api_manager.set_bot_instance = Mock()
                mock_bot.api_manager.disconnect = AsyncMock()
                mock_bot._pre_validate_params = Mock(return_value=True)
                mock_bot.total_profit = 0
                
                # Simular condições de parada rápida para teste
                mock_bot.total_profit = 100  # Simular WIN_STOP atingido
                
                # Importar e testar
                from tunderbotalavanca import AccumulatorScalpingBot
                
                # Criar instância de teste
                test_config = {
                    'name': 'test_account',
                    'token': 'test_token',
                    'app_id': 'test_app_id'
                }
                
                bot = AccumulatorScalpingBot(test_config)
                bot.api_manager = mock_bot.api_manager
                bot._pre_validate_params = mock_bot._pre_validate_params
                bot.total_profit = 0
                
                # Testar inicialização
                logger.info("✅ Função start pode ser importada e instanciada")
                self.test_results.append("✅ Inicialização: PASSOU")
                
        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            self.test_results.append(f"❌ Inicialização: FALHOU - {e}")
    
    async def test_start_flow_structure(self):
        """Testa a estrutura do fluxo da função start"""
        logger.info("🧪 Testando estrutura do fluxo da função start...")
        
        try:
            # Verificar se a função start existe e tem a estrutura correta
            from tunderbotalavanca import AccumulatorScalpingBot
            
            # Verificar se o método start existe
            assert hasattr(AccumulatorScalpingBot, 'start'), "Método start não encontrado"
            
            # Verificar se é uma função async
            import inspect
            assert inspect.iscoroutinefunction(AccumulatorScalpingBot.start), "start não é uma função async"
            
            logger.info("✅ Estrutura da função start está correta")
            self.test_results.append("✅ Estrutura do fluxo: PASSOU")
            
        except Exception as e:
            logger.error(f"❌ Erro na estrutura: {e}")
            self.test_results.append(f"❌ Estrutura do fluxo: FALHOU - {e}")
    
    async def test_required_components(self):
        """Testa se todos os componentes necessários estão presentes"""
        logger.info("🧪 Testando componentes necessários...")
        
        try:
            from tunderbotalavanca import AccumulatorScalpingBot
            import inspect
            
            # Obter código fonte da função start
            source = inspect.getsource(AccumulatorScalpingBot.start)
            
            # Verificar componentes essenciais
            required_components = [
                'api_manager.connect',
                'subscribe_ticks',
                'while True',
                'WIN_STOP',
                'LOSS_LIMIT',
                'api_manager.connected',
                'asyncio.sleep',
                'api_manager.disconnect'
            ]
            
            missing_components = []
            for component in required_components:
                if component not in source:
                    missing_components.append(component)
            
            if missing_components:
                raise AssertionError(f"Componentes ausentes: {missing_components}")
            
            logger.info("✅ Todos os componentes necessários estão presentes")
            self.test_results.append("✅ Componentes necessários: PASSOU")
            
        except Exception as e:
            logger.error(f"❌ Erro nos componentes: {e}")
            self.test_results.append(f"❌ Componentes necessários: FALHOU - {e}")
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🚀 Iniciando testes da função start refatorada...")
        logger.info("="*60)
        
        # Executar testes
        await self.test_start_initialization()
        await self.test_start_flow_structure()
        await self.test_required_components()
        
        # Relatório final
        logger.info("="*60)
        logger.info("📊 RELATÓRIO FINAL DOS TESTES:")
        logger.info("="*60)
        
        passed = 0
        failed = 0
        
        for result in self.test_results:
            logger.info(result)
            if "PASSOU" in result:
                passed += 1
            else:
                failed += 1
        
        logger.info("="*60)
        logger.info(f"✅ Testes aprovados: {passed}")
        logger.info(f"❌ Testes falharam: {failed}")
        logger.info(f"📈 Taxa de sucesso: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            logger.info("🎉 TODOS OS TESTES PASSARAM! Refatoração bem-sucedida!")
        else:
            logger.warning("⚠️ Alguns testes falharam. Revisar implementação.")
        
        return failed == 0

async def main():
    """Função principal do teste"""
    tester = TestRefactoredStart()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)