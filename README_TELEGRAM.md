# 📱 Módulo de Notificaciones Telegram

Módulo completo para enviar notificaciones de trading via Telegram cuando se detectan patrones y resultados de operaciones.

## 🚀 Características

- ✅ Notificaciones de patrones detectados
- ✅ Resultados de operaciones en tiempo real
- ✅ Resúmenes de sesiones de trading
- ✅ Alertas de errores del sistema
- ✅ Manejo asíncrono con threading
- ✅ Formato HTML con emojis
- ✅ Manejo robusto de errores

## 📋 Requisitos

```bash
pip install python-telegram-bot==20.7 python-dotenv
```

## ⚙️ Configuración

### 1. Crear Bot de Telegram

1. Habla con [@BotFather](https://t.me/BotFather) en Telegram
2. Usa `/newbot` para crear un nuevo bot
3. Sigue las instrucciones y guarda el **token**

### 2. Obtener Chat ID

**Para chat personal:**
1. Envía un mensaje a tu bot
2. Visita: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
3. Busca `"chat":{"id":XXXXXXX}` en la respuesta
4. Ese número es tu **CHAT_ID**

**Para grupos:**
1. Agrega el bot al grupo
2. Menciona al bot en el grupo
3. Usa el mismo método `getUpdates`
4. Los CHAT_ID de grupos son **negativos**

### 3. Configurar Variables de Entorno

Agrega al archivo `.env`:

```env
# Configuraciones de Telegram
TELEGRAM_BOT_TOKEN="tu_token_del_bot_aqui"
TELEGRAM_CHAT_ID="tu_chat_id_aqui"
```

## 🔧 Uso del Módulo

### Importar el Módulo

```python
from telegram_notifier import (
    inicializar_telegram,
    enviar_alerta_patron,
    enviar_resultado_operacion,
    enviar_resumen_sesion,
    enviar_error_sistema
)
```

### Inicializar

```python
# Inicializar el notificador
if inicializar_telegram():
    print("✅ Telegram listo")
else:
    print("❌ Error en Telegram")
```

### Enviar Alerta de Patrón

```python
strategy_data = {
    'strategy': 'Quantum+',
    'confidence': 85.5,
    'reason': 'Patrón LLLW detectado con alta confianza'
}

enviar_alerta_patron(strategy_data)
```

### Enviar Resultado de Operación

```python
# Parámetros: strategy_name, operacion_num, resultado, total_operaciones
enviar_resultado_operacion("Quantum+", 1, "V", 3)  # WIN
enviar_resultado_operacion("Quantum+", 2, "L", 3)  # LOSS
```

### Enviar Resumen de Sesión

```python
# Parámetros: strategy_name, wins, losses, total, duracion
enviar_resumen_sesion("Quantum+", 2, 1, 3, "15 minutos")
```

### Enviar Error del Sistema

```python
enviar_error_sistema("Conexión perdida con Deriv API", "API")
```

## 🧪 Pruebas

### Probar Conexión

```bash
python telegram_notifier.py
```

### Ejemplos Completos

```bash
# Probar solo conexión
python ejemplo_telegram_usage.py --test

# Ver información sobre CHAT_ID
python ejemplo_telegram_usage.py --info

# Ejecutar ejemplo completo
python ejemplo_telegram_usage.py --full
```

## 📱 Formato de Mensajes

### Patrón Detectado
```
🚨 PATRÓN DETECTADO 🚨

⏰ Hora: 14:30:25
🎯 Estrategia: Quantum+
📊 Confianza: 85.5%
📝 Razón: Patrón LLLW detectado

🤖 ACTIVAR BOT AHORA!

#PatronDetectado #Quantum+
```

### Resultado de Operación
```
✅ RESULTADO OPERACIÓN

⏰ Hora: 14:32:15
🎯 Estrategia: Quantum+
📈 Operación: 1/3
🎲 Resultado: WIN

#Quantum+ #WIN
```

### Resumen de Sesión
```
🎉 RESUMEN DE SESIÓN

⏰ Finalizada: 14:45:30
🎯 Estrategia: Quantum+
⏱️ Duración: 15 minutos

📊 RESULTADOS:
✅ Wins: 2
❌ Losses: 1
📈 Total: 3
🎯 Efectividad: 66.7%

#Quantum+ #ResumenSesion
```

## 🔧 Integración con Radares

### En radar_tunder_new.py

```python
# Al inicio del archivo
from telegram_notifier import inicializar_telegram, enviar_alerta_patron

# En la función main()
inicializar_telegram()

# Cuando se detecta un patrón
if resultado['should_operate']:
    enviar_alerta_patron(resultado)
```

### En radar_scalping_double.py

```python
# Similar integración
from telegram_notifier import (
    inicializar_telegram, 
    enviar_alerta_patron,
    enviar_resultado_operacion
)
```

## 🛠️ Solución de Problemas

### Error: "Chat not found"
- Verifica que el CHAT_ID sea correcto
- Asegúrate de haber enviado al menos un mensaje al bot
- Para grupos, verifica que el bot esté agregado

### Error: "Unauthorized"
- Verifica que el TELEGRAM_BOT_TOKEN sea correcto
- Asegúrate de que el token esté entre comillas en el .env

### Variables no se cargan
- Verifica que el archivo .env esté en el directorio correcto
- Asegúrate de que las variables tengan comillas
- Usa `load_dotenv()` antes de acceder a las variables

## 📊 Logs

El módulo genera logs detallados:

```
[TELEGRAM] Bot inicializado correctamente
[TELEGRAM] Mensaje enviado correctamente
[TELEGRAM] Error de Telegram: Chat not found
```

## 🔒 Seguridad

- ❌ **NUNCA** hagas commit del archivo `.env`
- ✅ Usa `.gitignore` para excluir `.env`
- ✅ Mantén el token del bot seguro
- ✅ Revoca tokens comprometidos en @BotFather

## 📝 Notas

- El módulo usa threading para evitar bloqueos
- Timeout de 10 segundos para operaciones
- Manejo robusto de errores de red
- Formato HTML para mensajes enriquecidos
- Soporte para emojis y hashtags

---

**¡Tu sistema de trading ahora tiene notificaciones en tiempo real! 🚀📱**