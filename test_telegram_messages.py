#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar o envio de mensagens Telegram
"""

import logging
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Importar funções do bot principal
try:
    from radar_analisis_scalping_bot import (
        inicializar_telegram_seguro,
        enviar_alerta_padrao_SEGURO,
        enviar_resultado_seguro,
        enviar_finalizacao_segura
    )
    logger.info("Funções importadas com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar funções: {e}")
    sys.exit(1)

def test_telegram_messages():
    """Testa o envio de mensagens para o Telegram"""
    
    # Inicializar Telegram
    logger.info("Inicializando Telegram...")
    telegram_ativo = inicializar_telegram_seguro()
    
    if not telegram_ativo:
        logger.error("❌ Falha ao inicializar Telegram")
        return False
    
    logger.info("✅ Telegram inicializado com sucesso")
    
    # 1. Testar envio de alerta de padrão encontrado
    logger.info("\n1. Testando envio de alerta de padrão encontrado...")
    strategy_data = {
        'strategy': 'PRECISION_SURGE',
        'confidence': 85.5,
        'reason': 'Padrão de alta confiança detectado',
        'wins_consecutivos': 4,
        'losses_ultimas_15': 2
    }
    
    alerta_enviado = enviar_alerta_padrao_SEGURO(strategy_data)
    logger.info(f"Resultado do envio de alerta: {'✅ Sucesso' if alerta_enviado else '❌ Falha'}")
    
    # 2. Testar envio de resultado de operação
    logger.info("\n2. Testando envio de resultado de operação...")
    resultado_enviado = enviar_resultado_seguro(
        operacion_num=1,
        resultado="V",  # V para vitória
        total_operaciones=2
    )
    logger.info(f"Resultado do envio de resultado (WIN): {'✅ Sucesso' if resultado_enviado else '❌ Falha'}")
    
    # Testar resultado de perda também
    resultado_enviado = enviar_resultado_seguro(
        operacion_num=2,
        resultado="L",  # L para loss
        total_operaciones=2
    )
    logger.info(f"Resultado do envio de resultado (LOSS): {'✅ Sucesso' if resultado_enviado else '❌ Falha'}")
    
    # 3. Testar envio de finalização
    logger.info("\n3. Testando envio de finalização...")
    resultados = ['V', 'L']  # Uma vitória e uma derrota
    exito = False  # Não foi um sucesso completo
    
    finalizacao_enviada = enviar_finalizacao_segura(resultados, exito)
    logger.info(f"Resultado do envio de finalização: {'✅ Sucesso' if finalizacao_enviada else '❌ Falha'}")
    
    return True

if __name__ == "__main__":
    print("🧪 Iniciando teste de mensagens Telegram...")
    
    try:
        resultado = test_telegram_messages()
        if resultado:
            print("\n✅ Teste de mensagens Telegram concluído com sucesso!")
        else:
            print("\n❌ Teste de mensagens Telegram falhou!")
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        print(f"\n💥 Erro durante o teste: {e}")