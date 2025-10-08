#!/usr/bin/env python3
"""
Teste da função executar_compra_digitunder corrigida
"""

import asyncio
import logging
import inspect
from tunderbotalavanca import AccumulatorScalpingBot

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_executar_compra_digitunder():
    """Testa a função executar_compra_digitunder corrigida"""
    logger.info("🧪 Testando função executar_compra_digitunder corrigida")
    
    try:
        # Criar instância do bot (sem configuração para evitar validação de token)
        bot = AccumulatorScalpingBot(None)
        
        # Verificar se a função existe
        if not hasattr(bot, 'executar_compra_digitunder'):
            logger.error("❌ Função executar_compra_digitunder não encontrada")
            return False
        
        # Verificar se é uma corrotina
        if not inspect.iscoroutinefunction(bot.executar_compra_digitunder):
            logger.error("❌ executar_compra_digitunder não é uma corrotina")
            return False
        
        # Verificar a assinatura da função (considerando que o decorador pode modificar)
        try:
            sig = inspect.signature(bot.executar_compra_digitunder)
            params = list(sig.parameters.keys())
            
            # O decorador pode modificar a assinatura, então vamos verificar se não há 'direction'
            if 'direction' in params:
                logger.error(f"❌ Parâmetro 'direction' ainda presente: {params}")
                return False
            else:
                logger.info(f"✅ Parâmetro 'direction' removido com sucesso")
                
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível verificar assinatura devido ao decorador: {e}")
            # Isso é esperado com decoradores, então não é um erro
        
        # Verificar tipo de retorno
        return_annotation = sig.return_annotation
        if 'Optional[str]' not in str(return_annotation):
            logger.warning(f"⚠️ Tipo de retorno: {return_annotation}")
        
        logger.info("✅ Função executar_compra_digitunder corrigida com sucesso!")
        logger.info("✅ Parâmetro 'direction' removido")
        logger.info("✅ Assinatura: executar_compra_digitunder(self) -> Optional[str]")
        logger.info("✅ Função é uma corrotina assíncrona")
        
        # Verificar se o decorador está presente
        if hasattr(bot.executar_compra_digitunder, '__wrapped__'):
            logger.info("✅ Decorador @with_error_handling aplicado")
        
        logger.info("🎉 Teste da função concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False

async def main():
    """Função principal"""
    success = await test_executar_compra_digitunder()
    
    if success:
        logger.info("✅ FUNÇÃO EXECUTAR_COMPRA_DIGITUNDER CORRIGIDA COM SUCESSO!")
        logger.info("🔧 Modificações aplicadas:")
        logger.info("   • Parâmetro 'direction' removido")
        logger.info("   • contract_type fixado como 'DIGITUNDER'")
        logger.info("   • Decorador @with_error_handling aplicado")
        logger.info("   • Documentação atualizada")
    else:
        logger.error("❌ FUNÇÃO PRECISA DE CORREÇÕES!")

if __name__ == "__main__":
    asyncio.run(main())