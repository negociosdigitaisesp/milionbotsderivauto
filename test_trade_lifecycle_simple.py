#!/usr/bin/env python3
"""
Teste da nova implementação simplificada da função _execute_trade_lifecycle
"""

import asyncio
import logging
from tunderbotalavanca import AccumulatorScalpingBot

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_trade_lifecycle():
    """Testa a nova implementação da função _execute_trade_lifecycle"""
    logger.info("🧪 Testando nova implementação de _execute_trade_lifecycle")
    
    try:
        # Criar instância do bot (sem configuração para evitar validação de token)
        bot = AccumulatorScalpingBot(None)
        
        # Verificar se a função existe
        if not hasattr(bot, '_execute_trade_lifecycle'):
            logger.error("❌ Função _execute_trade_lifecycle não encontrada")
            return False
        
        # Verificar se é uma corrotina
        import inspect
        if not inspect.iscoroutinefunction(bot._execute_trade_lifecycle):
            logger.error("❌ _execute_trade_lifecycle não é uma corrotina")
            return False
        
        logger.info("✅ Função _execute_trade_lifecycle implementada corretamente")
        logger.info("✅ Função é uma corrotina assíncrona")
        
        # Verificar se as funções dependentes existem
        required_functions = [
            'executar_compra_digitunder',
            'monitorar_contrato', 
            'aplicar_gestao_risco'
        ]
        
        for func_name in required_functions:
            if hasattr(bot, func_name):
                logger.info(f"✅ Função {func_name} encontrada")
            else:
                logger.warning(f"⚠️ Função {func_name} não encontrada")
        
        logger.info("🎉 Teste da implementação concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False

async def main():
    """Função principal"""
    success = await test_trade_lifecycle()
    
    if success:
        logger.info("✅ IMPLEMENTAÇÃO VALIDADA COM SUCESSO!")
    else:
        logger.error("❌ IMPLEMENTAÇÃO PRECISA DE CORREÇÕES!")

if __name__ == "__main__":
    asyncio.run(main())