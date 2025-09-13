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
import time

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

# Semáforo global para controlar conexiones concurrentes
MAX_CONCURRENT_CONNECTIONS = 3  # Limitar a 3 conexiones simultáneas
connection_semaphore = threading.Semaphore(MAX_CONCURRENT_CONNECTIONS)

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
        """Envía mensaje de forma síncrona usando threading con control de concurrencia"""
        # Intentos máximos y tiempo de espera inicial
        max_intentos = 3
        tiempo_espera_base = 1  # segundos
        
        for intento in range(1, max_intentos + 1):
            # Intentar adquirir el semáforo con timeout
            semaforo_adquirido = False
            try:
                # Intentar adquirir el semáforo con un timeout
                semaforo_adquirido = connection_semaphore.acquire(timeout=2)
                if not semaforo_adquirido:
                    logger.warning(f"[TELEGRAM] Intento {intento}/{max_intentos}: No se pudo adquirir el semáforo, todas las conexiones ocupadas")
                    # Backoff exponencial entre intentos
                    tiempo_espera = tiempo_espera_base * (2 ** (intento - 1))
                    time.sleep(tiempo_espera)
                    continue
                
                # Ejecutar el envío en un hilo separado
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
                thread.join(timeout=5)  # Reducir timeout para liberar conexiones más rápido
                
                logger.info(f"[TELEGRAM] Mensaje enviado correctamente (intento {intento}/{max_intentos})")
                return True
                
            except Exception as e:
                logger.error(f"[TELEGRAM] Error al enviar mensaje (intento {intento}/{max_intentos}): {e}")
                # Si no es el último intento, esperar y reintentar
                if intento < max_intentos:
                    tiempo_espera = tiempo_espera_base * (2 ** (intento - 1))
                    logger.info(f"[TELEGRAM] Reintentando en {tiempo_espera} segundos...")
                    time.sleep(tiempo_espera)
            finally:
                # Liberar el semáforo si fue adquirido
                if semaforo_adquirido:
                    connection_semaphore.release()
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error(f"[TELEGRAM] Todos los intentos de envío fallaron")
        return False
    
    async def _enviar_mensaje_async(self, mensaje: str) -> bool:
        """Envía mensaje de forma asíncrona con manejo específico de errores"""
        try:
            # Intentar enviar el mensaje con un timeout específico
            await asyncio.wait_for(
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=mensaje,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                ),
                timeout=4.0  # Timeout más estricto para la operación
            )
            return True
        except asyncio.TimeoutError:
            logger.error(f"[TELEGRAM] Timeout al enviar mensaje")
            return False
        except TelegramError as e:
            # Manejar específicamente el error de pool timeout
            if "Pool timeout" in str(e):
                logger.error(f"[TELEGRAM] Error de pool de conexiones: {e}")
                # Este error ya está siendo manejado por el sistema de reintentos
            else:
                logger.error(f"[TELEGRAM] Error de Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"[TELEGRAM] Error general: {e}")
            return False
    
    def verificar_conexion(self) -> bool:
        """Verifica si el bot puede conectarse a Telegram con control de concurrencia"""
        # Intentos máximos y tiempo de espera inicial
        max_intentos = 2
        tiempo_espera_base = 1  # segundos
        
        for intento in range(1, max_intentos + 1):
            # Intentar adquirir el semáforo con timeout
            semaforo_adquirido = False
            try:
                # Intentar adquirir el semáforo con un timeout
                semaforo_adquirido = connection_semaphore.acquire(timeout=2)
                if not semaforo_adquirido:
                    logger.warning(f"[TELEGRAM] Verificación {intento}/{max_intentos}: No se pudo adquirir el semáforo, todas las conexiones ocupadas")
                    # Backoff exponencial entre intentos
                    tiempo_espera = tiempo_espera_base * (2 ** (intento - 1))
                    time.sleep(tiempo_espera)
                    continue
                
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
                thread.join(timeout=5)  # Reducir timeout para liberar conexiones más rápido
                
                logger.info(f"[TELEGRAM] Verificación de conexión exitosa (intento {intento}/{max_intentos})")
                return True
                
            except Exception as e:
                logger.error(f"[TELEGRAM] Error al verificar conexión (intento {intento}/{max_intentos}): {e}")
                # Si no es el último intento, esperar y reintentar
                if intento < max_intentos:
                    tiempo_espera = tiempo_espera_base * (2 ** (intento - 1))
                    logger.info(f"[TELEGRAM] Reintentando verificación en {tiempo_espera} segundos...")
                    time.sleep(tiempo_espera)
            finally:
                # Liberar el semáforo si fue adquirido
                if semaforo_adquirido:
                    connection_semaphore.release()
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error(f"[TELEGRAM] Todos los intentos de verificación fallaron")
        return False
    
    async def _verificar_conexion_async(self) -> bool:
        """Verifica conexión de forma asíncrona con timeout"""
        try:
            # Intentar obtener información del bot con timeout
            await asyncio.wait_for(
                self.bot.get_me(),
                timeout=4.0  # Timeout estricto para la operación
            )
            return True
        except asyncio.TimeoutError:
            logger.error(f"[TELEGRAM] Timeout al verificar conexión")
            return False
        except TelegramError as e:
            # Manejar específicamente el error de pool timeout
            if "Pool timeout" in str(e):
                logger.error(f"[TELEGRAM] Error de pool de conexiones en verificación: {e}")
            else:
                logger.error(f"[TELEGRAM] Error de Telegram en verificación: {e}")
            return False
        except Exception as e:
            logger.error(f"[TELEGRAM] Error general en verificación asíncrona: {e}")
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
🚨 <b>ACTIVAR SCALPING BOT AHORA</b> 🚨

🤖 <b>Bot:</b> Scalping Bot I.A
📊 <b>Confianza:</b> {strategy_data['confidence']:.1f}%
📝 <b>Razón:</b> {strategy_data['reason']}

⚠️ <b>ACTIVAR BOT AHORA!</b>

Atencion - Ingresar solo en la primera 2 operaciones
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

🤖 <b>Bot:</b> Scalping Bot I.A
🎯 <b>Resultado:</b> {texto_resultado}

#ScalpingBotIA #{texto_resultado}
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

🤖 <b>Bot:</b> Scalping Bot I.A

📊 <b>RESULTADOS:</b>
✅ Wins: {wins}
❌ Losses: {losses}
📈 Total: {total}
🎯 Efectividad: {porcentaje:.1f}%

📋 <b>Secuencia:</b> {' '.join(resultados)}

#ScalpingBotIA #Finalizacion
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