#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o controle de concorrência do Telegram
"""

import logging
import threading
import time
from telegram_notifier import TelegramNotifier

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_test.log')
    ]
)

logger = logging.getLogger(__name__)

def enviar_mensaje(id_mensaje):
    """Función para enviar un mensaje de prueba"""
    notifier = TelegramNotifier()
    mensaje = f"Teste de conexão {id_mensaje} - Verificando solução de timeout e concorrência"
    logger.info(f"Iniciando envio de mensaje {id_mensaje}")
    resultado = notifier.enviar_mensaje_sync(mensaje)
    logger.info(f"Resultado del mensaje {id_mensaje}: {resultado}")

def main():
    """Función principal para probar el control de concurrencia"""
    logger.info("Iniciando prueba de concurrencia de Telegram")
    
    # Crear múltiples hilos para enviar mensajes simultáneamente
    threads = []
    for i in range(10):  # Enviar 10 mensajes simultáneos para probar el control de concurrencia
        thread = threading.Thread(target=enviar_mensaje, args=(i,))
        threads.append(thread)
    
    # Iniciar todos los hilos casi simultáneamente
    for thread in threads:
        thread.start()
        time.sleep(0.1)  # Pequeña pausa para simular llegadas casi simultáneas
    
    # Esperar a que todos los hilos terminen
    for thread in threads:
        thread.join()
    
    logger.info("Prueba de concurrencia finalizada")

if __name__ == "__main__":
    main()