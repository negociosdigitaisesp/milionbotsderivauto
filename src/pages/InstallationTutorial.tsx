import React from 'react';
import { ExternalLink, CheckCircle, AlertCircle, HelpCircle, Download } from 'lucide-react';

const InstallationTutorial = () => {
  return (
    <div className="container max-w-5xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Tutorial de Instalación</h1>
        <p className="text-muted-foreground">Sigue los pasos a continuación para instalar y configurar tu robot de trading con Deriv.</p>
      </div>

      {/* Preparation section */}
      <div className="mb-10 bg-card p-6 rounded-xl border border-border shadow-md">
        <h2 className="text-xl font-bold mb-4">Preparación Inicial</h2>
        <p className="text-muted-foreground mb-6">Antes de comenzar la instalación, asegúrate de tener los siguientes elementos preparados:</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-accent/30 p-4 rounded-lg border border-border flex items-start gap-3">
            <CheckCircle size={20} className="text-green-500 mt-0.5" />
            <div>
              <h3 className="font-medium mb-1">Navegador Actualizado</h3>
              <p className="text-sm text-muted-foreground">Usa Chrome, Firefox o Edge en la versión más reciente para máxima compatibilidad con la plataforma.</p>
            </div>
          </div>
          
          <div className="bg-accent/30 p-4 rounded-lg border border-border flex items-start gap-3">
            <CheckCircle size={20} className="text-green-500 mt-0.5" />
            <div>
              <h3 className="font-medium mb-1">Cuenta en Deriv</h3>
              <p className="text-sm text-muted-foreground">Crea una cuenta con el enlace a continuación <a href="https://track.deriv.be/_XZsgLOqstMrrhBvO3lYd_WNd7ZgqdRLk/1/" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">Deriv</a>, es 100% seguro y con retiros más rápidos.</p>
            </div>
          </div>
          
          <div className="bg-accent/30 p-4 rounded-lg border border-border flex items-start gap-3">
            <CheckCircle size={20} className="text-green-500 mt-0.5" />
            <div>
              <h3 className="font-medium mb-1">Archivo XML del Robot</h3>
              <p className="text-sm text-muted-foreground">Ten el archivo XML del robot descargado y guardado en una carpeta de fácil acceso en tu computadora.</p>
            </div>
          </div>
          
          <div className="bg-accent/30 p-4 rounded-lg border border-border flex items-start gap-3">
            <CheckCircle size={20} className="text-green-500 mt-0.5" />
            <div>
              <h3 className="font-medium mb-1">Conexión Estable</h3>
              <p className="text-sm text-muted-foreground">Asegura una conexión a internet estable para evitar interrupciones durante el proceso de configuración y operación.</p>
            </div>
          </div>
        </div>
        
        <div className="mt-6 bg-warning/10 p-4 rounded-lg border border-warning/30">
          <h3 className="font-medium mb-2 flex items-center gap-2 text-warning">
            <AlertCircle size={18} />
            Nota Importante
          </h3>
          <p className="text-sm">Para operar con bots de trading, es esencial entender los principios básicos del mercado y de la plataforma Deriv. Si eres principiante, recomendamos estudiar el material educativo disponible antes de comenzar.</p>
        </div>
      </div>

      {/* Timeline component */}
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary to-muted-foreground/20 z-0"></div>

        {/* Step 1 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">1</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Accede a la plataforma Deriv</h3>
            <p className="text-muted-foreground mb-4">Para comenzar, accede a la plataforma oficial de Deriv a través del enlace a continuación.</p>
            
            <a 
              href="https://track.deriv.be/_XZsgLOqstMrrhBvO3lYd_WNd7ZgqdRLk/1/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-lg transition-colors inline-block"
            >
              Acceder a la Plataforma Deriv <ExternalLink size={16} />
            </a>
            
            <div className="mt-4 bg-muted p-3 rounded-lg border border-border flex items-start gap-2">
              <HelpCircle size={18} className="text-primary mt-1" />
              <p className="text-sm text-muted-foreground">Este enlace es seguro y te redirigirá al sitio oficial de Deriv.</p>
            </div>
          </div>
        </div>

        {/* Step 2 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">2</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Inicia sesión en tu cuenta</h3>
            <p className="text-muted-foreground mb-4">Ingresa con tus credenciales en la plataforma Deriv (cuenta Demo o Real).</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-accent/30 p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <CheckCircle size={16} className="text-green-500" />
                  Cuenta Demo
                </h4>
                <p className="text-sm text-muted-foreground">Recomendada para principiantes. Practica sin riesgo usando dinero virtual.</p>
              </div>
              <div className="bg-accent/30 p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <AlertCircle size={16} className="text-amber-500" />
                  Cuenta Real
                </h4>
                <p className="text-sm text-muted-foreground">Utiliza solo cuando estés confiado en la estrategia y gestión de riesgo.</p>
              </div>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/login-screen.jpg" 
                alt="Pantalla de inicio de sesión de Deriv" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Pantalla+de+Inicio+Deriv";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 3 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">3</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Importa el robot</h3>
            <p className="text-muted-foreground mb-4">En el menú superior de la plataforma Binary Bot, haz clic en la opción "Importar" (o "Load").</p>
            
            <div className="bg-accent/30 p-4 rounded-lg border border-border mb-4">
              <p className="text-sm"><span className="font-medium">Consejo:</span> Asegúrate de estar en la interfaz de Binary Bot antes de continuar con este paso.</p>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/import-bot.jpg" 
                alt="Importando el robot en la plataforma" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Importar+Robot";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 4 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">4</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Carga el archivo</h3>
            <p className="text-muted-foreground mb-4">Localiza el archivo .xml del robot de tu elección en tu computadora y cárgalo en la plataforma.</p>
            
            <div className="flex items-center gap-2 p-4 bg-muted rounded-lg border border-border mb-4">
              <AlertCircle size={18} className="text-amber-500" />
              <p className="text-sm">Asegúrate de haber descargado el archivo .xml antes de este paso. El archivo debe tener la extensión .xml y ser compatible con Binary Bot.</p>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/load-file.jpg" 
                alt="Cargando archivo XML del robot" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Cargar+Archivo+XML";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 5 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">5</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Verifica la carga</h3>
            <p className="text-muted-foreground mb-4">Confirma que el robot apareció correctamente en el área de trabajo de la plataforma.</p>
            
            <div className="bg-accent/30 p-4 rounded-lg border border-border mb-4">
              <p className="text-sm"><span className="font-medium">Verificación:</span> Debes visualizar los bloques y la lógica del robot en el área de trabajo de Binary Bot.</p>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/verify-loading.jpg" 
                alt="Verificando carga del robot" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Verificar+Carga";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 6 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">6</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Configura los parámetros</h3>
            <p className="text-muted-foreground mb-4">Ajusta las configuraciones del robot según tu estrategia y gestión de riesgo.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-accent/30 p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2">Meta de Ganancia</h4>
                <p className="text-sm text-muted-foreground">Define el valor objetivo de ganancia para finalizar las operaciones automáticamente.</p>
              </div>
              <div className="bg-accent/30 p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2">Límite de Pérdidas</h4>
                <p className="text-sm text-muted-foreground">Configura el valor máximo de pérdidas para proteger tu capital.</p>
              </div>
              <div className="bg-accent/30 p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2">Valor Inicial de la Orden</h4>
                <p className="text-sm text-muted-foreground">Establece el valor inicial para cada operación del robot.</p>
              </div>
              <div className="bg-accent/30 p-4 rounded-lg border border-border">
                <h4 className="font-medium mb-2">Cantidad de Ticks</h4>
                <p className="text-sm text-muted-foreground">Define el número de ticks para cada operación según tu estrategia.</p>
              </div>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/configure-parameters.jpg" 
                alt="Configurando parámetros del robot" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Configurar+Parámetros";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 7 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">7</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Prueba Primero en Cuenta Demo</h3>
            <p className="text-muted-foreground mb-4">Siempre comienza probando el robot en una cuenta demo antes de usar dinero real.</p>
            
            <div className="bg-accent/30 p-4 rounded-lg border border-border mb-4">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <CheckCircle size={16} className="text-green-500" />
                Recomendación Importante
              </h4>
              <p className="text-sm text-muted-foreground">Observa si el bot está presentando una secuencia positiva o negativa. Si el robot está con una secuencia positiva, cambia a la cuenta real. Si está negativa, vuelve en otro horario.</p>
            </div>
            
            <div className="flex items-center gap-2 p-4 bg-muted rounded-lg border border-border mb-4">
              <AlertCircle size={18} className="text-amber-500" />
              <div>
                <p className="text-sm font-medium">Recuerda:</p>
                <p className="text-sm text-muted-foreground">El mercado tiene diferentes momentos de volatilidad durante el día. Algunas horas pueden ser más favorables para el funcionamiento de tu robot.</p>
              </div>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/demo-testing.jpg" 
                alt="Probando el robot en cuenta demo" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Probando+en+Cuenta+Demo";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 8 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">8</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Ejecuta el robot</h3>
            <p className="text-muted-foreground mb-4">Haz clic en el botón "Ejecutar" (o "Run") para iniciar las operaciones automatizadas.</p>
            
            <div className="flex items-center gap-2 p-4 bg-muted rounded-lg border border-border mb-4">
              <AlertCircle size={18} className="text-amber-500" />
              <div>
                <p className="text-sm font-medium">Importante:</p>
                <p className="text-sm text-muted-foreground">Monitorea regularmente el desempeño del robot, incluso en operaciones automatizadas. Está preparado para intervenir si es necesario.</p>
              </div>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/run-bot.jpg" 
                alt="Ejecutando el robot en la plataforma" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Ejecutar+Robot";
                }}
              />
            </div>
          </div>
        </div>

        {/* Step 9 */}
        <div className="relative z-10 mb-10 flex items-start">
          <div className="bg-primary text-primary-foreground flex items-center justify-center w-16 h-16 rounded-xl shadow-lg mr-6">
            <span className="text-2xl font-bold">9</span>
          </div>
          <div className="bg-card shadow-md rounded-xl p-6 flex-1 border border-border">
            <h3 className="text-xl font-bold mb-2">Monitorea los resultados</h3>
            <p className="text-muted-foreground mb-4">Realiza seguimiento al desempeño del robot y haz ajustes cuando sea necesario.</p>
            
            <div className="bg-accent/30 p-4 rounded-lg border border-border mb-4">
              <h4 className="font-medium mb-2">Consejos para monitoreo eficiente:</h4>
              <ul className="text-sm text-muted-foreground space-y-2">
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-green-500 mt-0.5" />
                  <span>Mantén un registro de las operaciones para analizar tendencias y patrones.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-green-500 mt-0.5" />
                  <span>Revisa periódicamente las configuraciones para optimizar el desempeño.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-green-500 mt-0.5" />
                  <span>Mantente atento a cambios en las condiciones del mercado que puedan afectar la estrategia.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-green-500 mt-0.5" />
                  <span>No dudes en pausar el robot si percibes anomalías o resultados inesperados.</span>
                </li>
              </ul>
            </div>
            
            <div className="rounded-lg overflow-hidden border border-border shadow-sm">
              <img 
                src="/images/monitor-results.jpg" 
                alt="Monitoreando resultados del robot" 
                className="w-full h-auto object-cover"
                onError={(e) => {
                  e.currentTarget.src = "https://via.placeholder.com/800x400?text=Monitorear+Resultados";
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Troubleshooting section */}
      <div className="mt-12 bg-card p-6 rounded-xl border border-border shadow-md">
        <h2 className="text-2xl font-bold mb-4">Soluciones a Problemas Comunes</h2>
        <p className="text-muted-foreground mb-6">Si has enfrentado problemas durante la instalación, revisa estas soluciones para los errores más comunes:</p>
        
        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg border border-border">
            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
              <AlertCircle size={18} className="text-amber-500" />
              Error al importar el archivo XML
            </h3>
            <p className="mb-2">Verifica si:</p>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>El archivo XML descargado está completo y no corrupto</li>
              <li>Estás usando la versión más reciente del navegador Chrome o Firefox</li>
              <li>Has descargado completamente el archivo (no solo un enlace al archivo)</li>
              <li>El archivo termina con la extensión .xml</li>
            </ul>
            <p className="mt-3 font-medium">Solución: Intenta descargar el archivo nuevamente y verifica si se abre con un editor de texto.</p>
          </div>

          <div className="p-4 bg-muted rounded-lg border border-border">
            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
              <AlertCircle size={18} className="text-amber-500" />
              Robot no aparece en el área de trabajo tras importación
            </h3>
            <p className="mb-2">Verifica si:</p>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>Estás en la plataforma correcta (Binary Bot o DBot)</li>
              <li>El archivo XML es compatible con la plataforma que estás usando</li>
              <li>Has completado el proceso de importación completo</li>
            </ul>
            <p className="mt-3 font-medium">Solución: Intenta limpiar la caché del navegador, reiniciar la plataforma e importar nuevamente.</p>
          </div>

          <div className="p-4 bg-muted rounded-lg border border-border">
            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
              <AlertCircle size={18} className="text-amber-500" />
              Errores de configuración del robot
            </h3>
            <p className="mb-2">Verifica si:</p>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>Las configuraciones de entrada usan punto (.) y no coma (,) para valores decimales</li>
              <li>Los valores de meta y límite son correctos y están dentro de los límites aceptables</li>
              <li>Has seleccionado el activo correcto para operar (verifica la documentación del robot)</li>
            </ul>
            <p className="mt-3 font-medium">Solución: Revisa la documentación de tu robot específico para las configuraciones recomendadas.</p>
          </div>

          <div className="p-4 bg-muted rounded-lg border border-border">
            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
              <AlertCircle size={18} className="text-amber-500" />
              Robot no inicia después de hacer clic en "Ejecutar"
            </h3>
            <p className="mb-2">Verifica si:</p>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>Has iniciado sesión en la plataforma Deriv</li>
              <li>Tu cuenta tiene saldo suficiente para la operación inicial</li>
              <li>El mercado para el activo seleccionado está abierto</li>
              <li>Has permitido las notificaciones del navegador (muchas veces necesario)</li>
            </ul>
            <p className="mt-3 font-medium">Solución: Verifica en la sección de "Mejores Horarios de los Robots" si el mercado está activo en este momento e intenta nuevamente en los horarios recomendados.</p>
          </div>

          <div className="p-4 bg-muted rounded-lg border border-border">
            <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
              <AlertCircle size={18} className="text-amber-500" />
              Conexión inestable o lenta
            </h3>
            <p className="mb-2">Para un funcionamiento óptimo, verifica si:</p>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>Tu conexión a internet es estable (idealmente con cable, no Wi-Fi)</li>
              <li>No tienes muchas pestañas abiertas consumiendo memoria</li>
              <li>Tu computadora cumple con los requisitos mínimos de procesamiento</li>
            </ul>
            <p className="mt-3 font-medium">Solución: Cierra otros programas pesados, reinicia el navegador e intenta usar una conexión más estable.</p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-primary/10 rounded-lg border border-primary/30">
          <h3 className="font-bold mb-2">¿Aún con problemas?</h3>
          <p>Si ninguna de las soluciones anteriores resuelve tu problema, contacta a nuestro soporte técnico para obtener asistencia personalizada.</p>
        </div>
      </div>

      {/* Support section */}
      <div className="mt-12 bg-card p-6 rounded-xl border border-border shadow-md">
        <h2 className="text-2xl font-bold mb-4">¿Necesitas ayuda adicional?</h2>
        <p className="text-muted-foreground mb-6">Nuestro equipo de soporte está listo para ayudarte con cualquier duda o problema que puedas encontrar durante la instalación o uso del robot.</p>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <a href="#" className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-lg transition-colors inline-flex items-center justify-center gap-2">
            <HelpCircle size={18} />
            Habla con Soporte
          </a>
          <a href="#" className="bg-muted hover:bg-muted/90 text-muted-foreground px-6 py-3 rounded-lg transition-colors inline-flex items-center justify-center gap-2 border border-border">
            <CheckCircle size={18} />
            Revisar FAQ
          </a>
        </div>
      </div>
    </div>
  );
};

export default InstallationTutorial; 