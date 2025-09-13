#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar a integração completa do Telegram após as correções
"""

import logging
import sys
import os
import traceback
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
    from radar_tunder_new import (
        inicializar_telegram_bot,
        verificar_status_telegram,
        enviar_mensaje_sistema,
        enviar_alerta_patron,
        enviar_resultado_operacion_seguro
    )
    logger.info("Funções importadas com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar funções: {e}")
    sys.exit(1)

def testar_integracao_telegram_completa():
    """Testa a integração completa do Telegram com todas as funções"""
    print("\n===== TESTE COMPLETO DE INTEGRAÇÃO TELEGRAM =====\n")
    
    # 1. Inicializar Telegram
    print("1. Inicializando Telegram...")
    if not inicializar_telegram_bot():
        print("❌ Falha ao inicializar Telegram - verifique as variáveis de ambiente")
        return False
    
    print("✅ Telegram inicializado com sucesso\n")
    
    # 2. Verificar status
    print("2. Verificando status do Telegram...")
    if not verificar_status_telegram():
        print("❌ Falha na verificação de status do Telegram")
        return False
    
    print("✅ Status do Telegram verificado com sucesso\n")
    
    # 3. Enviar mensagem de sistema
    print("3. Enviando mensagem de sistema...")
    try:
        resultado = enviar_mensaje_sistema("🧪 TESTE: Mensagem de sistema", "INFO")
        if not resultado:
            print("❌ Falha ao enviar mensagem de sistema")
            return False
        print("✅ Mensagem de sistema enviada com sucesso\n")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem de sistema: {e}")
        traceback.print_exc()
        return False
    
    # 4. Enviar alerta de padrão
    print("4. Enviando alerta de padrão...")
    try:
        strategy_data = {
            'strategy': 'WWL_TEST',
            'confidence': 90.0,
            'reason': 'Teste de integração do Telegram'
        }
        resultado = enviar_alerta_patron(strategy_data)
        if not resultado:
            print("❌ Falha ao enviar alerta de padrão")
            return False
        print("✅ Alerta de padrão enviado com sucesso\n")
    except Exception as e:
        print(f"❌ Erro ao enviar alerta de padrão: {e}")
        traceback.print_exc()
        return False
    
    # 5. Enviar resultado de operação
    print("5. Enviando resultado de operação...")
    try:
        resultado = enviar_resultado_operacion_seguro("WIN")
        if not resultado:
            print("❌ Falha ao enviar resultado de operação")
            return False
        print("✅ Resultado de operação enviado com sucesso\n")
    except Exception as e:
        print(f"❌ Erro ao enviar resultado de operação: {e}")
        traceback.print_exc()
        return False
    
    print("\n✅✅✅ TESTE DE INTEGRAÇÃO COMPLETO COM SUCESSO! ✅✅✅\n")
    return True

if __name__ == "__main__":
    print("🧪 Iniciando teste de integração Telegram...")
    
    try:
        resultado = testar_integracao_telegram_completa()
        if resultado:
            print("\n✅ Teste de integração Telegram concluído com sucesso!")
            sys.exit(0)
        else:
            print("\n❌ Teste de integração Telegram falhou!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        traceback.print_exc()
        print(f"\n💥 Erro durante o teste: {e}")
        sys.exit(1)