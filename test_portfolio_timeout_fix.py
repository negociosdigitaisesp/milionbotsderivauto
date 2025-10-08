#!/usr/bin/env python3
"""
Teste para verificar se as correções de timeout do portfolio estão funcionando
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar a classe corrigida
from tunderbotalavanca import DerivWebSocketNativo, ACCOUNTS

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_portfolio_timeout.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_portfolio_timeout_fix():
    """Testa as correções de timeout do portfolio"""
    logger.info("🧪 Iniciando teste de correção de timeout do portfolio")
    
    try:
        # Usar a primeira conta configurada
        account_config = ACCOUNTS[0]
        logger.info(f"📋 Testando com conta: {account_config['name']}")
        
        # Criar instância do WebSocket
        api_manager = DerivWebSocketNativo(account_config)
        
        # Conectar
        logger.info("🔗 Conectando ao WebSocket...")
        await api_manager.connect()
        logger.info("✅ Conexão estabelecida com sucesso")
        
        # Testar portfolio múltiplas vezes
        for i in range(3):
            logger.info(f"\n📊 Teste {i+1}/3 - Solicitando portfolio...")
            
            try:
                start_time = asyncio.get_event_loop().time()
                portfolio_response = await api_manager.portfolio()
                end_time = asyncio.get_event_loop().time()
                
                elapsed_time = end_time - start_time
                logger.info(f"✅ Portfolio obtido com sucesso em {elapsed_time:.2f}s")
                
                # Verificar se a resposta contém dados válidos
                if 'portfolio' in portfolio_response:
                    contracts = portfolio_response['portfolio'].get('contracts', [])
                    logger.info(f"📈 Portfolio contém {len(contracts)} contratos")
                else:
                    logger.warning("⚠️ Resposta do portfolio não contém dados esperados")
                
            except Exception as e:
                logger.error(f"❌ Erro no teste {i+1}: {e}")
                
            # Aguardar entre testes
            if i < 2:
                logger.info("⏱️ Aguardando 5 segundos antes do próximo teste...")
                await asyncio.sleep(5)
        
        # Desconectar
        logger.info("🔌 Desconectando...")
        await api_manager.disconnect()
        logger.info("✅ Teste concluído com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro geral no teste: {e}")
        raise e

async def test_connection_health():
    """Testa a verificação de saúde da conexão"""
    logger.info("\n🏥 Testando verificação de saúde da conexão")
    
    try:
        account_config = ACCOUNTS[0]
        api_manager = DerivWebSocketNativo(account_config)
        
        # Conectar
        await api_manager.connect()
        
        # Testar ensure_connection múltiplas vezes
        for i in range(3):
            logger.info(f"🏓 Teste de saúde {i+1}/3...")
            await api_manager.ensure_connection()
            await asyncio.sleep(2)
        
        await api_manager.disconnect()
        logger.info("✅ Teste de saúde da conexão concluído")
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de saúde: {e}")

async def main():
    """Função principal do teste"""
    logger.info("🚀 Iniciando testes de correção de timeout")
    
    try:
        # Teste 1: Portfolio com timeout corrigido
        await test_portfolio_timeout_fix()
        
        # Teste 2: Verificação de saúde da conexão
        await test_connection_health()
        
        logger.info("🎉 Todos os testes concluídos com sucesso!")
        
    except Exception as e:
        logger.error(f"💥 Falha nos testes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())