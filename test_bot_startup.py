#!/usr/bin/env python3
"""
Script de teste para verificar problemas de inicialização dos bots
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestBot')

async def test_imports():
    """Testa se todas as importações funcionam"""
    try:
        logger.info("🔍 Testando importações...")
        
        # Testar importações básicas
        import websockets
        import json
        from dotenv import load_dotenv
        logger.info("✅ Importações básicas OK")
        
        # Testar importações do projeto
        from error_handler import RobustErrorHandler, with_error_handling, ErrorType, ErrorSeverity
        logger.info("✅ Error handler OK")
        
        # Testar variáveis de ambiente
        load_dotenv()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if supabase_url and supabase_key:
            logger.info("✅ Variáveis de ambiente OK")
        else:
            logger.warning("⚠️ Variáveis de ambiente não encontradas")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro nas importações: {e}")
        logger.error(f"📋 Tipo: {type(e).__name__}")
        return False

async def test_simple_bot():
    """Testa um bot simples"""
    try:
        logger.info("🤖 Testando bot simples...")
        
        class SimpleBotTest:
            def __init__(self):
                self.name = "Test Bot"
                logger.info(f"🚀 {self.name} inicializado")
            
            async def start(self):
                logger.info(f"▶️ {self.name} iniciando...")
                await asyncio.sleep(2)
                logger.info(f"✅ {self.name} rodando")
                
                # Simular trabalho por 10 segundos
                for i in range(10):
                    logger.info(f"📊 {self.name} - Tick {i+1}/10")
                    await asyncio.sleep(1)
                
                logger.info(f"🏁 {self.name} finalizado com sucesso")
        
        bot = SimpleBotTest()
        await bot.start()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no bot simples: {e}")
        logger.error(f"📋 Tipo: {type(e).__name__}")
        return False

async def main():
    """Função principal de teste"""
    try:
        logger.info("🧪 INICIANDO TESTES DE STARTUP")
        logger.info("="*50)
        
        # Teste 1: Importações
        if not await test_imports():
            logger.error("❌ Falha no teste de importações")
            return False
        
        # Teste 2: Bot simples
        if not await test_simple_bot():
            logger.error("❌ Falha no teste de bot simples")
            return False
        
        logger.info("✅ TODOS OS TESTES PASSARAM")
        return True
        
    except KeyboardInterrupt:
        logger.info("🛑 Teste interrompido pelo usuário")
        return True
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO no teste: {e}")
        logger.error(f"📋 Tipo: {type(e).__name__}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            logger.info("🎉 Teste concluído com sucesso")
        else:
            logger.error("💥 Teste falhou")
    except Exception as e:
        logger.error(f"❌ ERRO FATAL: {e}")
        logger.info("🔄 Verificar dependências e configuração")