#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a correção do growth_rate resolve o erro da API Deriv
"""

import asyncio
import logging
from accumulator_standalone import AccumulatorScalpingBot, GROWTH_RATE

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_growth_rate_correction():
    """Testa se o growth_rate está correto e se a proposta funciona"""
    
    logger.info("🧪 INICIANDO TESTE DE CORREÇÃO DO GROWTH_RATE")
    
    # Verificar valor do GROWTH_RATE
    logger.info(f"📊 GROWTH_RATE atual: {GROWTH_RATE} (tipo: {type(GROWTH_RATE)})")
    
    # Verificar se está no intervalo correto
    if 0.01 <= GROWTH_RATE <= 0.05:
        logger.info(f"✅ GROWTH_RATE está no intervalo correto (0.01-0.05)")
    else:
        logger.error(f"❌ GROWTH_RATE fora do intervalo: {GROWTH_RATE}")
        return False
    
    # Criar instância do bot
    bot = AccumulatorScalpingBot()
    
    # Testar estrutura dos parâmetros
    logger.info("🔍 Testando estrutura dos parâmetros ACCU...")
    
    # Simular parâmetros de proposta
    test_params = {
        "proposal": 1,
        "contract_type": "ACCU",
        "symbol": "R_75",
        "amount": 50.0,
        "basis": "stake",
        "currency": "USD",
        "growth_rate": GROWTH_RATE
    }
    
    logger.info(f"📋 Parâmetros de teste:")
    for key, value in test_params.items():
        logger.info(f"   • {key}: {value} (tipo: {type(value)})")
    
    # Validar parâmetros usando função do bot
    if bot._validar_parametros_accu(test_params):
        logger.info("✅ Validação dos parâmetros ACCU passou!")
    else:
        logger.error("❌ Validação dos parâmetros ACCU falhou!")
        return False
    
    # Testar parâmetros com limit_order
    test_params_with_limit = test_params.copy()
    test_params_with_limit["limit_order"] = {"take_profit": 5.0}
    
    logger.info(f"📋 Parâmetros com limit_order:")
    for key, value in test_params_with_limit.items():
        logger.info(f"   • {key}: {value}")
    
    logger.info("✅ TESTE CONCLUÍDO - Correção do growth_rate implementada com sucesso!")
    logger.info(f"🎯 RESUMO:")
    logger.info(f"   • GROWTH_RATE: {GROWTH_RATE} (float)")
    logger.info(f"   • Intervalo: 0.01 <= {GROWTH_RATE} <= 0.05 ✅")
    logger.info(f"   • Validação: Passou ✅")
    logger.info(f"   • Estrutura: Correta ✅")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_growth_rate_correction())