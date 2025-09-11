#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de uso del módulo de notificaciones Telegram
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_notifier import (
    inicializar_telegram,
    enviar_alerta_patron,
    enviar_resultado_operacion,
    enviar_resumen_sesion,
    enviar_error_sistema,
    test_telegram_connection
)

def ejemplo_uso_completo():
    """Ejemplo completo de uso del módulo Telegram"""
    
    print("=== EJEMPLO DE USO DEL MÓDULO TELEGRAM ===")
    
    # 1. Inicializar Telegram
    print("\n1. Inicializando Telegram...")
    if inicializar_telegram():
        print("✅ Telegram inicializado correctamente")
    else:
        print("❌ Error al inicializar Telegram")
        return
    
    # 2. Enviar alerta de patrón detectado
    print("\n2. Enviando alerta de patrón...")
    strategy_data = {
        'strategy': 'Quantum+',
        'confidence': 85.5,
        'reason': 'Patrón LLLW detectado con alta confianza'
    }
    
    if enviar_alerta_patron(strategy_data):
        print("✅ Alerta de patrón enviada")
    else:
        print("❌ Error al enviar alerta de patrón")
    
    # 3. Enviar resultado de operación
    print("\n3. Enviando resultado de operación...")
    if enviar_resultado_operacion("Quantum+", 1, "V", 3):
        print("✅ Resultado de operación enviado")
    else:
        print("❌ Error al enviar resultado")
    
    # 4. Enviar resumen de sesión
    print("\n4. Enviando resumen de sesión...")
    if enviar_resumen_sesion("Quantum+", 2, 1, 3, "15 minutos"):
        print("✅ Resumen de sesión enviado")
    else:
        print("❌ Error al enviar resumen")
    
    # 5. Enviar error del sistema
    print("\n5. Enviando error del sistema...")
    if enviar_error_sistema("Conexión perdida con Deriv API", "API"):
        print("✅ Error del sistema enviado")
    else:
        print("❌ Error al enviar error del sistema")

def obtener_chat_id_info():
    """Información sobre cómo obtener el CHAT_ID correcto"""
    print("""
=== CÓMO OBTENER EL CHAT_ID CORRECTO ===

1. Crear un bot en Telegram:
   - Habla con @BotFather en Telegram
   - Usa /newbot para crear un nuevo bot
   - Guarda el token que te proporciona

2. Obtener tu CHAT_ID:
   - Envía un mensaje a tu bot
   - Visita: https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   - Busca "chat":{"id":XXXXXXX} en la respuesta
   - Ese número es tu CHAT_ID

3. Configurar en .env:
   TELEGRAM_BOT_TOKEN="tu_token_aqui"
   TELEGRAM_CHAT_ID="tu_chat_id_aqui"

4. Para grupos:
   - Agrega el bot al grupo
   - Haz que alguien mencione al bot
   - Usa el mismo método de getUpdates
   - Los CHAT_ID de grupos son negativos
    """)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejemplo de uso del módulo Telegram')
    parser.add_argument('--test', action='store_true', help='Solo probar conexión')
    parser.add_argument('--info', action='store_true', help='Mostrar info sobre CHAT_ID')
    parser.add_argument('--full', action='store_true', help='Ejemplo completo')
    
    args = parser.parse_args()
    
    if args.info:
        obtener_chat_id_info()
    elif args.test:
        print("Probando conexión...")
        test_telegram_connection()
    elif args.full:
        ejemplo_uso_completo()
    else:
        print("Uso: python ejemplo_telegram_usage.py [--test|--info|--full]")
        print("  --test: Probar conexión")
        print("  --info: Mostrar información sobre CHAT_ID")
        print("  --full: Ejecutar ejemplo completo")