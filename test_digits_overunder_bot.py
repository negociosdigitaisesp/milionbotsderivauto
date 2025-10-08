#!/usr/bin/env python3
"""
Script de teste para validar o bot refatorado com estratégia Digits Over/Under
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging para teste
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_digits_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar o bot refatorado
try:
    from tunderbotalavanca import AccumulatorScalpingBot, ACCOUNTS, ACTIVE_ACCOUNTS
    from tunderbotalavanca import NOME_BOT, STAKE_INICIAL, ATIVO, WIN_STOP, LOSS_LIMIT, PREDICTION
    logger.info("✅ Importação do bot bem-sucedida")
except ImportError as e:
    logger.error(f"❌ Erro na importação: {e}")
    sys.exit(1)

async def test_bot_initialization():
    """Testa a inicialização do bot"""
    logger.info("\n" + "="*50)
    logger.info("🧪 TESTE 1: Inicialização do Bot")
    logger.info("="*50)
    
    try:
        # Usar a primeira conta ativa
        account_config = ACTIVE_ACCOUNTS[0]
        bot = AccumulatorScalpingBot(account_config)
        
        # Verificar se os parâmetros foram configurados corretamente
        assert bot.nome_bot == NOME_BOT, f"Nome do bot incorreto: {bot.nome_bot}"
        assert bot.stake == STAKE_INICIAL, f"Stake inicial incorreto: {bot.stake}"
        assert bot.ativo == ATIVO, f"Ativo incorreto: {bot.ativo}"
        
        logger.info(f"✅ Bot inicializado com sucesso:")
        logger.info(f"   - Nome: {bot.nome_bot}")
        logger.info(f"   - Stake: ${bot.stake}")
        logger.info(f"   - Ativo: {bot.ativo}")
        logger.info(f"   - Predição: {PREDICTION}")
        logger.info(f"   - Win Stop: ${WIN_STOP}")
        logger.info(f"   - Loss Limit: ${LOSS_LIMIT}")
        
        return bot
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        return None

async def test_parameter_validation(bot):
    """Testa a validação de parâmetros"""
    logger.info("\n" + "="*50)
    logger.info("🧪 TESTE 2: Validação de Parâmetros")
    logger.info("="*50)
    
    try:
        # Testar pré-validação
        validation_result = bot._pre_validate_params()
        
        if validation_result:
            logger.info("✅ Pré-validação de parâmetros bem-sucedida")
            return True
        else:
            logger.error("❌ Falha na pré-validação de parâmetros")
            logger.error(f"   Resultado da validação: {validation_result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False

async def test_risk_management(bot):
    """Testa o sistema de gestão de risco"""
    logger.info("\n" + "="*50)
    logger.info("🧪 TESTE 3: Gestão de Risco")
    logger.info("="*50)
    
    try:
        # Simular lucro
        initial_stake = bot.stake
        initial_profit = bot.total_profit
        
        logger.info(f"Estado inicial - Stake: ${initial_stake}, Profit: ${initial_profit}")
        
        # Simular vitória
        bot.aplicar_gestao_risco(2.0)  # Lucro de $2
        logger.info(f"Após vitória - Stake: ${bot.stake}, Profit: ${bot.total_profit}")
        
        # Verificar se o stake permanece fixo
        assert bot.stake == STAKE_INICIAL, f"Stake deveria permanecer fixo em ${STAKE_INICIAL}, mas está ${bot.stake}"
        
        # Simular derrota
        bot.aplicar_gestao_risco(-1.0)  # Perda de $1
        logger.info(f"Após derrota - Stake: ${bot.stake}, Profit: ${bot.total_profit}")
        
        # Verificar se o stake ainda permanece fixo
        assert bot.stake == STAKE_INICIAL, f"Stake deveria permanecer fixo em ${STAKE_INICIAL}, mas está ${bot.stake}"
        
        logger.info("✅ Sistema de gestão de risco funcionando corretamente (stake fixo)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na gestão de risco: {e}")
        return False

async def test_connection_setup(bot):
    """Testa a configuração de conexão (sem conectar de fato)"""
    logger.info("\n" + "="*50)
    logger.info("🧪 TESTE 4: Configuração de Conexão")
    logger.info("="*50)
    
    try:
        # Verificar se o API manager foi inicializado
        assert bot.api_manager is not None, "API Manager não foi inicializado"
        
        # Verificar configuração da conta
        assert bot.account_name is not None, "Nome da conta não foi configurado"
        assert bot.token is not None, "Token não foi configurado"
        assert bot.app_id is not None, "App ID não foi configurado"
        
        logger.info(f"✅ Configuração de conexão válida:")
        logger.info(f"   - Conta: {bot.account_name}")
        logger.info(f"   - App ID: {bot.app_id}")
        logger.info(f"   - Token: {'*' * (len(bot.token) - 4) + bot.token[-4:] if len(bot.token) > 4 else '****'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na configuração de conexão: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        logger.error(f"   Atributos do bot: {[attr for attr in dir(bot) if not attr.startswith('_')]}")
        return False

async def test_contract_parameters():
    """Testa os parâmetros do contrato DIGITOVER"""
    logger.info("\n" + "="*50)
    logger.info("🧪 TESTE 5: Parâmetros do Contrato DIGITOVER")
    logger.info("="*50)
    
    try:
        # Verificar parâmetros globais
        assert ATIVO == 'R_100', f"Ativo deveria ser 'R_100', mas é '{ATIVO}'"
        assert STAKE_INICIAL == 1.0, f"Stake inicial deveria ser 1.0, mas é {STAKE_INICIAL}"
        assert PREDICTION == 1, f"Predição deveria ser 1, mas é {PREDICTION}"
        assert WIN_STOP == 50.0, f"Win Stop deveria ser 50.0, mas é {WIN_STOP}"
        assert LOSS_LIMIT == 100.0, f"Loss Limit deveria ser 100.0, mas é {LOSS_LIMIT}"
        
        logger.info("✅ Parâmetros do contrato DIGITOVER configurados corretamente:")
        logger.info(f"   - Ativo: {ATIVO}")
        logger.info(f"   - Stake: ${STAKE_INICIAL}")
        logger.info(f"   - Predição: {PREDICTION}")
        logger.info(f"   - Win Stop: ${WIN_STOP}")
        logger.info(f"   - Loss Limit: ${LOSS_LIMIT}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro nos parâmetros do contrato: {e}")
        return False

async def run_all_tests():
    """Executa todos os testes"""
    logger.info("\n" + "🚀" + "="*60 + "🚀")
    logger.info("🧪 INICIANDO TESTES DO BOT DIGITS OVER/UNDER REFATORADO")
    logger.info("🚀" + "="*60 + "🚀")
    logger.info(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    test_results = []
    
    # Teste 1: Inicialização
    bot = await test_bot_initialization()
    test_results.append(("Inicialização", bot is not None))
    
    if bot:
        # Teste 2: Validação de parâmetros
        param_test = await test_parameter_validation(bot)
        test_results.append(("Validação de Parâmetros", param_test))
        
        # Teste 3: Gestão de risco
        risk_test = await test_risk_management(bot)
        test_results.append(("Gestão de Risco", risk_test))
        
        # Teste 4: Configuração de conexão
        conn_test = await test_connection_setup(bot)
        test_results.append(("Configuração de Conexão", conn_test))
    
    # Teste 5: Parâmetros do contrato
    contract_test = await test_contract_parameters()
    test_results.append(("Parâmetros do Contrato", contract_test))
    
    # Resumo dos resultados
    logger.info("\n" + "📊" + "="*60 + "📊")
    logger.info("📊 RESUMO DOS TESTES")
    logger.info("📊" + "="*60 + "📊")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        logger.info("🎉 TODOS OS TESTES PASSARAM! Bot está pronto para uso.")
        return True
    else:
        logger.error(f"⚠️ {total - passed} teste(s) falharam. Revisar antes de usar o bot.")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(run_all_tests())
        if result:
            logger.info("\n✅ Validação concluída com sucesso!")
            sys.exit(0)
        else:
            logger.error("\n❌ Validação falhou!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Erro durante os testes: {e}")
        sys.exit(1)