#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Notificaciones Telegram para Radar Analisis Bot
Envía alertas cuando se detectan patrones de trading
"""

import os
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import threading
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Clase para enviar notificaciones via Telegram"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = None
        
        if not self.token or not self.chat_id:
            logger.error("[TELEGRAM] Token o Chat ID no encontrados en .env")
            raise ValueError("Configuración de Telegram incompleta")
        
        try:
            self.bot = Bot(token=self.token)
            logger.info("[TELEGRAM] Bot inicializado correctamente")
        except Exception as e:
            logger.error(f"[TELEGRAM] Error al inicializar bot: {e}")
            raise
    
    def enviar_mensaje_sync(self, mensaje: str) -> bool:
        """Envía mensaje de forma síncrona usando threading"""
        try:
            def ejecutar_envio():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._enviar_mensaje_async(mensaje))
                finally:
                    loop.close()
            
            # Ejecutar en un hilo separado para evitar bloqueos
            thread = threading.Thread(target=ejecutar_envio)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10)  # Timeout de 10 segundos
            
            logger.info(f"[TELEGRAM] Mensaje enviado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"[TELEGRAM] Error al enviar mensaje: {e}")
            return False
    
    async def _enviar_mensaje_async(self, mensaje: str) -> bool:
        """Envía mensaje de forma asíncrona"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=mensaje,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            return True
        except TelegramError as e:
            logger.error(f"[TELEGRAM] Error de Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"[TELEGRAM] Error general: {e}")
            return False
    
    def verificar_conexion(self) -> bool:
        """Verifica si el bot puede conectarse a Telegram"""
        try:
            def verificar():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._verificar_conexion_async())
                finally:
                    loop.close()
            
            thread = threading.Thread(target=verificar)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10)
            
            return True
        except Exception as e:
            logger.error(f"[TELEGRAM] Error en verificación: {e}")
            return False
    
    async def _verificar_conexion_async(self) -> bool:
        """Verifica conexión de forma asíncrona"""
        try:
            await self.bot.get_me()
            return True
        except Exception as e:
            logger.error(f"[TELEGRAM] Error en verificación async: {e}")
            return False

# Instancia global del notificador
telegram_notifier = None

def inicializar_telegram():
    """Inicializa el notificador de Telegram"""
    global telegram_notifier
    try:
        telegram_notifier = TelegramNotifier()
        logger.info("[TELEGRAM] Notificador inicializado")
        return True
    except Exception as e:
        logger.error(f"[TELEGRAM] Fallo al inicializar: {e}")
        telegram_notifier = None
        return False

def enviar_alerta_patron(strategy_data: Dict) -> bool:
    """Envía alerta cuando se detecta un patrón"""
    global telegram_notifier
    
    if not telegram_notifier:
        logger.warning("[TELEGRAM] Notificador no inicializado")
        return False
    
    try:
        # Formatear mensaje para patrón detectado
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        mensaje = f"""
🚨 <b>PATRÓN DETECTADO</b> 🚨

⏰ <b>Hora:</b> {timestamp}
🎯 <b>Estrategia:</b> {strategy_data['strategy']}
📊 <b>Confianza:</b> {strategy_data['confidence']:.1f}%
📝 <b>Razón:</b> {strategy_data['reason']}

🤖 <b>ACTIVAR BOT AHORA!</b>

Atencion - Ingresar solo en la primera operacion
        """.strip()
        
        return telegram_notifier.enviar_mensaje_sync(mensaje)
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al formatear mensaje de patrón: {e}")
        return False

def enviar_resultado_operacion(strategy_name: str, operacion_num: int, resultado: str, total_operaciones: int) -> bool:
    """Envía resultado de una operación"""
    global telegram_notifier
    
    if not telegram_notifier:
        logger.warning("[TELEGRAM] Notificador no inicializado")
        return False
    
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Emoji según resultado
        emoji_resultado = "✅" if resultado == "V" else "❌"
        texto_resultado = "WIN" if resultado == "V" else "LOSS"
        
        mensaje = f"""
{emoji_resultado} <b>RESULTADO OPERACIÓN</b>

⏰ <b>Hora:</b> {timestamp}
🎯 <b>Estrategia:</b> {strategy_name}
📈 <b>Operación:</b> {operacion_num}/{total_operaciones}
🎲 <b>Resultado:</b> {texto_resultado}

#{strategy_name} #{texto_resultado}
        """.strip()
        
        return telegram_notifier.enviar_mensaje_sync(mensaje)
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al formatear mensaje de resultado: {e}")
        return False

def enviar_resumen_sesion(strategy_name: str, wins: int, losses: int, total: int, duracion: str) -> bool:
    """Envía resumen de la sesión de trading"""
    global telegram_notifier
    
    if not telegram_notifier:
        logger.warning("[TELEGRAM] Notificador no inicializado")
        return False
    
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        porcentaje_wins = (wins / total * 100) if total > 0 else 0
        
        # Emoji según performance
        emoji_performance = "🎉" if porcentaje_wins >= 70 else "📊" if porcentaje_wins >= 50 else "⚠️"
        
        mensaje = f"""
{emoji_performance} <b>RESUMEN DE SESIÓN</b>

⏰ <b>Finalizada:</b> {timestamp}
🎯 <b>Estrategia:</b> {strategy_name}
⏱️ <b>Duración:</b> {duracion}

📊 <b>RESULTADOS:</b>
✅ Wins: {wins}
❌ Losses: {losses}
📈 Total: {total}
🎯 Efectividad: {porcentaje_wins:.1f}%

#{strategy_name} #ResumenSesion
        """.strip()
        
        return telegram_notifier.enviar_mensaje_sync(mensaje)
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al formatear resumen de sesión: {e}")
        return False

def enviar_error_sistema(error_msg: str, componente: str = "Sistema") -> bool:
    """Envía alerta de error del sistema"""
    global telegram_notifier
    
    if not telegram_notifier:
        logger.warning("[TELEGRAM] Notificador no inicializado")
        return False
    
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        mensaje = f"""
🚨 <b>ERROR DEL SISTEMA</b> 🚨

⏰ <b>Hora:</b> {timestamp}
🔧 <b>Componente:</b> {componente}
❌ <b>Error:</b> {error_msg}

🔍 <b>REVISAR INMEDIATAMENTE</b>

#ErrorSistema #{componente}
        """.strip()
        
        return telegram_notifier.enviar_mensaje_sync(mensaje)
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al formatear mensaje de error: {e}")
        return False

def test_telegram_connection() -> bool:
    """Función de prueba para verificar la conexión"""
    try:
        if inicializar_telegram():
            mensaje_test = """
🧪 <b>TEST DE CONEXIÓN</b>

✅ Bot de Telegram funcionando correctamente
⏰ Hora: {}

#TestConexion
            """.format(datetime.now().strftime("%H:%M:%S")).strip()
            
            return telegram_notifier.enviar_mensaje_sync(mensaje_test)
        return False
    except Exception as e:
        logger.error(f"[TELEGRAM] Error en test de conexión: {e}")
        return False

def enviar_finalizacion_estrategia(strategy_name: str, resultados: list, exito: bool) -> bool:
    """Envía mensaje de finalización de estrategia
    
    Args:
        strategy_name: Nombre de la estrategia
        resultados: Lista de resultados (V/L)
        exito: Si la estrategia fue exitosa
    """
    global telegram_notifier
    
    if not telegram_notifier:
        logger.warning("[TELEGRAM] Notificador no inicializado")
        return False
    
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        wins = resultados.count('V')
        losses = resultados.count('L')
        total = len(resultados)
        porcentaje = (wins / total * 100) if total > 0 else 0
        
        # Emoji según resultado
        emoji = "🎉" if exito else "😔"
        estado = "EXITOSA" if exito else "FALLIDA"
        
        mensaje = f"""
{emoji} <b>ESTRATEGIA {estado}</b>

⏰ <b>Finalizada:</b> {timestamp}
🎯 <b>Estrategia:</b> {strategy_name}

📊 <b>RESULTADOS:</b>
✅ Wins: {wins}
❌ Losses: {losses}
📈 Total: {total}
🎯 Efectividad: {porcentaje:.1f}%

📋 <b>Secuencia:</b> {' '.join(resultados)}

#{strategy_name} #Finalizacion
        """.strip()
        
        return telegram_notifier.enviar_mensaje_sync(mensaje)
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al enviar finalización de estrategia: {e}")
        return False

def enviar_mensaje_sistema(mensaje: str, tipo: str = "INFO") -> bool:
    """Envía mensaje del sistema
    
    Args:
        mensaje: Mensaje a enviar
        tipo: Tipo de mensaje (INFO, WARNING, ERROR)
    """
    global telegram_notifier
    
    if not telegram_notifier:
        logger.warning("[TELEGRAM] Notificador no inicializado")
        return False
    
    try:
        # Iconos según el tipo
        iconos = {
            "INFO": "ℹ️",
            "WARNING": "⚠️", 
            "ERROR": "❌"
        }
        
        icono = iconos.get(tipo.upper(), "ℹ️")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        mensaje_formateado = f"""
{icono} <b>SISTEMA</b>

⏰ <b>Hora:</b> {timestamp}
📝 <b>Mensaje:</b> {mensaje}

#Sistema #{tipo.upper()}
        """.strip()
        
        return telegram_notifier.enviar_mensaje_sync(mensaje_formateado)
        
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al enviar mensaje del sistema: {e}")
        return False

if __name__ == "__main__":
    # Test del módulo
    print("Probando conexión de Telegram...")
    if test_telegram_connection():
        print("✅ Telegram funcionando correctamente")
    else:
        print("❌ Error en la conexión de Telegram")