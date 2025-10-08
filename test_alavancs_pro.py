#!/usr/bin/env python3
"""
TESTE E VALIDAÇÃO - ESTRATÉGIA ALAVANCS PRO 2.0
===============================================

Script de teste para validar todas as funcionalidades da estratégia ALAVANCS PRO 2.0
"""

import asyncio
import logging
import sys
import time
from unittest.mock import Mock, AsyncMock
from tunderbotalavanca import AccumulatorScalpingBot

# Configuração de logging para testes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class TestAlavancsProStrategy:
    """Classe de teste para a estratégia ALAVANCS PRO 2.0"""
    
    def __init__(self):
        self.test_results = []
        self.account_config = {
            'name': 'TEST_ALAVANCS_PRO',
            'token': 'TEST_TOKEN',
            'app_id': 1089,
            'server': 'frontend.derivws.com'
        }
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Registra resultado de um teste"""
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        logger.info(f"{status} - {test_name}: {details}")
    
    def test_initialization(self):
        """Teste 1: Verificar inicialização correta do bot"""
        try:
            bot = AccumulatorScalpingBot(self.account_config)
            
            # Verificar se as novas variáveis de estado foram inicializadas
            has_consecutive_losses = hasattr(bot, 'consecutive_losses')
            has_tick_buffer = hasattr(bot, 'tick_buffer_alavancs')
            
            # Verificar valores iniciais
            correct_initial_values = (
                bot.consecutive_losses == 0 and
                len(bot.tick_buffer_alavancs) == 0
            )
            
            passed = has_consecutive_losses and has_tick_buffer and correct_initial_values
            details = f"Variáveis de estado: {has_consecutive_losses}, {has_tick_buffer}"
            
            self.log_test_result("Inicialização do Bot", passed, details)
            return bot
            
        except Exception as e:
            self.log_test_result("Inicialização do Bot", False, f"Erro: {e}")
            return None
    
    def test_tick_buffer_functionality(self, bot):
        """Teste 2: Verificar funcionalidade do buffer de ticks"""
        try:
            # Simular adição de ticks
            test_ticks = [1.234, 1.235, 1.236, 1.237, 1.238]
            
            for tick in test_ticks:
                bot._add_tick_to_buffer(tick)
            
            # Verificar se o buffer mantém o número correto de ticks
            buffer_size_correct = len(bot.tick_buffer_alavancs) == len(test_ticks)
            
            # Verificar se os ticks têm a estrutura correta
            structure_correct = all(
                'value' in tick_data and 'timestamp' in tick_data and 'last_digit' in tick_data
                for tick_data in bot.tick_buffer_alavancs
            )
            
            # Verificar se os valores estão corretos
            values_correct = [tick_data['value'] for tick_data in bot.tick_buffer_alavancs] == test_ticks
            
            passed = buffer_size_correct and structure_correct and values_correct
            details = f"Buffer size: {len(bot.tick_buffer_alavancs)}, Structure: {structure_correct}, Values: {values_correct}"
            
            self.log_test_result("Funcionalidade do Buffer de Ticks", passed, details)
            
        except Exception as e:
            self.log_test_result("Funcionalidade do Buffer de Ticks", False, f"Erro: {e}")
    
    def test_pattern_analysis(self, bot):
        """Teste 3: Verificar análise de padrões"""
        try:
            # Simular buffer com dados de tick no formato correto
            bot.tick_buffer_alavancs = [
                {'value': 1.200, 'last_digit': 0, 'timestamp': time.time()},
                {'value': 1.201, 'last_digit': 1, 'timestamp': time.time()},
                {'value': 1.202, 'last_digit': 2, 'timestamp': time.time()},
                {'value': 1.203, 'last_digit': 3, 'timestamp': time.time()},
                {'value': 1.204, 'last_digit': 4, 'timestamp': time.time()}
            ]
            
            analysis = bot._analyze_tick_pattern()
            
            # Verificar se a análise retorna dados válidos
            has_signal = 'signal' in analysis
            has_confidence = 'confidence' in analysis
            valid_signal = analysis.get('signal') in ['BUY', 'SELL', 'WAIT', 'OVER', 'UNDER', 'STRONG_BUY', 'STRONG_SELL']
            
            passed = has_signal and has_confidence and valid_signal
            details = f"Sinal: {analysis.get('signal')}, Confiança: {analysis.get('confidence', 0):.2f}"
            
            self.log_test_result("Análise de Padrões", passed, details)
            
        except Exception as e:
            self.log_test_result("Análise de Padrões", False, f"Erro: {e}")
    
    def test_consecutive_patterns(self, bot):
        """Teste 4: Verificar detecção de padrões consecutivos"""
        try:
            # Simular dígitos para análise
            test_digits = [2, 4, 6, 8]  # Padrão par
            
            consecutive = bot._detect_consecutive_patterns(test_digits)
            
            # Verificar se detectou padrões consecutivos
            has_pattern = 'pattern' in consecutive
            has_strength = 'strength' in consecutive
            has_prediction = 'prediction' in consecutive
            
            passed = has_pattern and has_strength and has_prediction
            details = f"Padrão: {consecutive.get('pattern')}, Força: {consecutive.get('strength')}"
            
            self.log_test_result("Detecção de Padrões Consecutivos", passed, details)
            
        except Exception as e:
            self.log_test_result("Detecção de Padrões Consecutivos", False, f"Erro: {e}")
    
    def test_probability_filters(self, bot):
        """Teste 5: Verificar filtros probabilísticos"""
        try:
            # Simular dígitos para filtros probabilísticos
            test_digits = [7, 8, 9, 6]  # Dígitos altos
            
            filtered = bot._apply_probability_filters(test_digits)
            
            # Verificar se o filtro funciona corretamente
            has_filter = 'filter' in filtered
            has_score = 'score' in filtered
            has_prediction = 'prediction' in filtered
            
            passed = has_filter and has_score and has_prediction
            details = f"Filtro: {filtered.get('filter')}, Score: {filtered.get('score', 0):.2f}"
            
            self.log_test_result("Filtros Probabilísticos", passed, details)
            
        except Exception as e:
            self.log_test_result("Filtros Probabilísticos", False, f"Erro: {e}")
    
    def test_risk_management(self, bot):
        """Teste 6: Verificar gestão de risco sem pausa de segurança (fiel ao XML)"""
        try:
            # Simular perdas consecutivas
            initial_losses = bot.consecutive_losses
            
            # Simular 3 perdas consecutivas
            for i in range(3):
                bot.aplicar_gestao_risco_alavancs_pro(-2.0)  # Perda de $2
            
            # Verificar se as perdas foram contadas corretamente
            losses_counted = bot.consecutive_losses == 3
            
            # Simular uma vitória para resetar
            bot.aplicar_gestao_risco_alavancs_pro(4.0)  # Ganho de $4
            
            # Verificar se resetou corretamente
            losses_reset = bot.consecutive_losses == 0
            
            passed = losses_counted and losses_reset
            details = f"Perdas contadas: {losses_counted}, Reset após WIN: {losses_reset}"
            
            self.log_test_result("Gestão de Risco sem Pausa", passed, details)
            
        except Exception as e:
            self.log_test_result("Gestão de Risco sem Pausa", False, f"Erro: {e}")
    
    def test_trade_entry_logic(self, bot):
        """Teste 7: Verificar lógica de entrada em trades"""
        try:
            # Simular buffer com dados favoráveis para entrada
            bot.tick_buffer_alavancs = [
                {'value': 1.200, 'last_digit': 2, 'timestamp': time.time()},
                {'value': 1.201, 'last_digit': 4, 'timestamp': time.time()},
                {'value': 1.202, 'last_digit': 6, 'timestamp': time.time()},
                {'value': 1.203, 'last_digit': 8, 'timestamp': time.time()}
            ]
            
            should_enter, signal, analysis = bot._should_enter_trade()
            
            # Verificar se a decisão é lógica
            is_boolean = isinstance(should_enter, bool)
            valid_signal = signal in ['OVER', 'UNDER', 'WAIT', 'SAFETY_PAUSE', 'INSUFFICIENT_TICKS', 'NO_SIGNAL']
            has_analysis = isinstance(analysis, dict)
            
            passed = is_boolean and valid_signal and has_analysis
            details = f"Decisão: {should_enter}, Sinal: {signal}"
            
            self.log_test_result("Lógica de Entrada em Trades", passed, details)
            
        except Exception as e:
            self.log_test_result("Lógica de Entrada em Trades", False, f"Erro: {e}")
    

    
    def test_method_availability(self, bot):
        """Teste 9: Verificar disponibilidade dos novos métodos"""
        try:
            methods_to_check = [
                'executar_compra_alavancs_pro',
                'executar_compra_digitunder',
                '_handle_new_tick',
                '_collect_ticks_for_analysis',
                '_process_tick_message',
                '_add_tick_to_buffer',
                '_analyze_tick_pattern',
                '_detect_consecutive_patterns',
                '_apply_probability_filters',
                '_combine_analysis_results',
                '_should_enter_trade',
                'aplicar_gestao_risco_alavancs_pro'
            ]
            
            missing_methods = []
            for method_name in methods_to_check:
                if not hasattr(bot, method_name):
                    missing_methods.append(method_name)
            
            passed = len(missing_methods) == 0
            details = f"Métodos faltando: {missing_methods}" if missing_methods else "Todos os métodos disponíveis"
            
            self.log_test_result("Disponibilidade de Métodos", passed, details)
            
        except Exception as e:
            self.log_test_result("Disponibilidade de Métodos", False, f"Erro: {e}")
    
    async def run_all_tests(self):
        """Executa todos os testes"""
        logger.info("🧪 INICIANDO TESTES DA ESTRATÉGIA ALAVANCS PRO 2.0")
        logger.info("="*60)
        
        # Teste 1: Inicialização
        bot = self.test_initialization()
        if not bot:
            logger.error("❌ Falha na inicialização - interrompendo testes")
            return
        
        # Teste 2: Buffer de ticks
        self.test_tick_buffer_functionality(bot)
        
        # Teste 3: Análise de padrões
        self.test_pattern_analysis(bot)
        
        # Teste 4: Padrões consecutivos
        self.test_consecutive_patterns(bot)
        
        # Teste 5: Filtros probabilísticos
        self.test_probability_filters(bot)
        
        # Teste 6: Gestão de risco
        self.test_risk_management(bot)
        
        # Teste 7: Lógica de entrada
        self.test_trade_entry_logic(bot)
        
        # Teste 8: Disponibilidade de métodos
        self.test_method_availability(bot)
        
        # Relatório final
        self.generate_test_report()
    
    def generate_test_report(self):
        """Gera relatório final dos testes"""
        logger.info("\n" + "="*60)
        logger.info("📊 RELATÓRIO FINAL DOS TESTES")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        logger.info(f"📈 Total de testes: {total_tests}")
        logger.info(f"✅ Testes aprovados: {passed_tests}")
        logger.info(f"❌ Testes falharam: {failed_tests}")
        logger.info(f"📊 Taxa de sucesso: {success_rate:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ TESTES QUE FALHARAM:")
            for result in self.test_results:
                if not result['passed']:
                    logger.info(f"   • {result['test']}: {result['details']}")
        
        logger.info("\n" + "="*60)
        
        if success_rate >= 90:
            logger.info("🎉 ESTRATÉGIA ALAVANCS PRO 2.0 VALIDADA COM SUCESSO!")
        elif success_rate >= 70:
            logger.info("⚠️ ESTRATÉGIA PARCIALMENTE VALIDADA - REVISAR FALHAS")
        else:
            logger.info("❌ ESTRATÉGIA REQUER CORREÇÕES ANTES DO USO")
        
        logger.info("="*60)

async def main():
    """Função principal para executar os testes"""
    tester = TestAlavancsProStrategy()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 TESTE ALAVANCS PRO 2.0                       ║
    ║            Validação da Estratégia Implementada             ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())