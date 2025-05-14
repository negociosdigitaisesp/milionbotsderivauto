import React from 'react';
import { Clock, AlertTriangle, CheckCircle, TrendingUp, Sunrise, Sunset, Info, Shield, BarChart2, BookOpen, Award, ThumbsUp, Zap } from 'lucide-react';

const BestHours = () => {
  // Array of market sessions and their characteristics
  const marketSessions = [
    {
      title: "Sesión Asiática",
      hours: "00:00 - 09:00 GMT (21:00 - 06:00 UTC-3)",
      volatility: "Baja a Media",
      characteristics: "Generalmente más predecible, movimientos menos bruscos",
      recommendation: "Bueno para estrategias de tendencia",
      icon: <Sunrise className="h-8 w-8 text-primary" />,
      color: "from-primary/5 to-primary/10",
      borderColor: "border-primary/20",
      textColor: "text-primary"
    },
    {
      title: "Sesión Europea",
      hours: "08:00 - 16:00 GMT (05:00 - 13:00 UTC-3)",
      volatility: "Media a Alta",
      characteristics: "Volumen creciente, mayor volatilidad",
      recommendation: "Ideal para estrategias de reversión y tendencia",
      icon: <Clock className="h-8 w-8 text-primary" />,
      color: "from-primary/5 to-primary/10",
      borderColor: "border-primary/20",
      textColor: "text-primary"
    },
    {
      title: "Sesión Americana",
      hours: "13:00 - 22:00 GMT (10:00 - 19:00 UTC-3)",
      volatility: "Alta",
      characteristics: "Mayor volumen y volatilidad del mercado",
      recommendation: "Bueno para estrategias de breakout y momentum",
      icon: <Sunset className="h-8 w-8 text-primary" />,
      color: "from-primary/5 to-primary/10",
      borderColor: "border-primary/20",
      textColor: "text-primary"
    }
  ];

  // Professional insights data
  const professionalInsights = [
    {
      title: "La consistencia es la clave",
      description: "Mantén tus operaciones consistentes y sigue tu estrategia, independientemente de las fluctuaciones a corto plazo.",
      icon: <Award className="h-6 w-6 text-primary" />
    },
    {
      title: "Gestión de Capital",
      description: "Nunca arriesgues más de lo que puedes perder. La regla del 2% es un buen punto de partida para gestionar riesgos.",
      icon: <Shield className="h-6 w-6 text-primary" />
    },
    {
      title: "Paciencia y Disciplina",
      description: "Las operaciones emocionales generalmente llevan a pérdidas. Mantente fiel a tu estrategia y sé paciente.",
      icon: <ThumbsUp className="h-6 w-6 text-primary" />
    },
    {
      title: "Educación Continua",
      description: "Incluso con robots automatizados, continúa aprendiendo sobre el mercado y actualizando tus estrategias.",
      icon: <BookOpen className="h-6 w-6 text-primary" />
    },
    {
      title: "Análisis de Resultados",
      description: "Mantén registros detallados de las operaciones para identificar patrones de éxito y fracaso.",
      icon: <BarChart2 className="h-6 w-6 text-primary" />
    },
    {
      title: "Adaptabilidad",
      description: "Los mercados cambian constantemente. Prepárate para ajustar parámetros y estrategias cuando sea necesario.",
      icon: <Zap className="h-6 w-6 text-primary" />
    }
  ];

  return (
    <div className="container max-w-6xl mx-auto py-8 px-4 animate-in fade-in duration-500">
      {/* Hero Section - Updated to match Library page gradient */}
      <div className="relative mb-12 overflow-hidden rounded-2xl shadow-xl bg-gradient-to-br from-primary/20 via-primary/10 to-background">
        {/* Decorative elements */}
        <div className="absolute inset-0 w-full h-full overflow-hidden">
          <div className="absolute w-[600px] h-[600px] rounded-full bg-gradient-to-br from-primary/20 to-transparent -top-[350px] -right-[100px] blur-md"></div>
          <div className="absolute w-[500px] h-[500px] rounded-full bg-gradient-to-br from-primary/15 to-transparent top-[50%] -left-[200px] blur-md"></div>
          <div className="absolute top-0 right-0 w-full h-full bg-grid-white/[0.05] [mask-image:linear-gradient(to_bottom,transparent,black)]"></div>
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent"></div>
        </div>
        
        <div className="relative z-10 py-16 px-8">
          <div className="max-w-3xl">
            <div className="inline-block mb-3 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-1.5 border border-primary/20">
              <span className="text-primary font-medium text-sm">Maximiza tu éxito en trading</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-6 text-foreground leading-tight">
              Mejores Horarios <span className="text-primary">para Trading</span>
            </h1>
            <p className="text-xl mb-8 text-muted-foreground leading-relaxed max-w-2xl">
              Comprende cómo los diferentes períodos del día pueden impactar el rendimiento 
              de tus robots de trading y optimiza tus resultados.
            </p>
            
            <div className="bg-card/70 backdrop-blur-sm rounded-lg p-5 border border-border shadow-lg">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 flex-shrink-0 text-yellow-500" />
                <p className="font-medium">Importante: Los mercados sintéticos de Deriv no siguen los mismos patrones que los mercados tradicionales, siendo influenciados por algoritmos pseudoaleatorios.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-8 mb-12">
        {/* Important Note Box */}
        <div className="bg-card rounded-xl p-8 border border-border shadow-lg">
          <div className="flex items-start gap-4 mb-6">
            <div className="bg-primary/10 p-3 rounded-full flex-shrink-0 mt-1">
              <Info className="text-primary" size={28} />
            </div>
            <div>
              <h2 className="text-2xl font-bold mb-3">La Verdad Sobre Horarios y Robots de Trading</h2>
              
              <p className="text-muted-foreground mb-4 leading-relaxed">
                <strong className="text-foreground">No existe un horario "definitivamente mejor" para operar los robots.</strong> El rendimiento de los bots 
                en el mercado de índices sintéticos, como el R_100, no es predecible por horario del día, ya que estos mercados están basados 
                en algoritmos de números pseudoaleatorios que no siguen patrones temporales fijos.
              </p>
              
              <p className="text-muted-foreground leading-relaxed">
                Sin embargo, existen <strong className="text-foreground">factores externos</strong> que pueden influir en tu experiencia de trading, como tu disponibilidad para monitorear las operaciones, 
                niveles de liquidez, e incluso tu estado emocional en diferentes momentos del día.
              </p>
            </div>
          </div>
        </div>

        {/* Best Practices - Improved card design */}
        <div className="mb-10">
          <h2 className="text-2xl font-bold mb-6 border-b pb-2">Prácticas Recomendadas</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-card rounded-xl p-6 shadow-md border border-border hover:shadow-lg transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-primary/10 p-3 rounded-full">
                  <CheckCircle className="text-primary" size={24} />
                </div>
                <h3 className="font-semibold text-lg">Prueba en Cuenta Demo</h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">Siempre comienza probando el bot en la cuenta de demostración para observar si está teniendo una buena asertividad. Si es asertivo, colócalo en la cuenta real. De lo contrario, vuelve en otro horario.</p>
            </div>

            <div className="bg-card rounded-xl p-6 shadow-md border border-border hover:shadow-lg transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-primary/10 p-3 rounded-full">
                  <TrendingUp className="text-primary" size={24} />
                </div>
                <h3 className="font-semibold text-lg">Analiza el Escenario</h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">Observa si el bot está presentando una secuencia positiva o negativa. Si el robot está con una secuencia positiva, cambia a la cuenta real; si está negativa, vuelve en otro horario.</p>
            </div>

            <div className="bg-card rounded-xl p-6 shadow-md border border-border hover:shadow-lg transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-primary/10 p-3 rounded-full">
                  <AlertTriangle className="text-primary" size={24} />
                </div>
                <h3 className="font-semibold text-lg">Gestión de Riesgo</h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">Más importante que el horario es definir límites claros de pérdidas (Stop Loss) y ganancias (Stop Win) antes de iniciar cualquier operación automatizada. Simula tu gestión de riesgos en la cuenta demo antes de iniciar en la real.</p>
            </div>
          </div>
        </div>

        {/* Sessions Information - Updated with consistent site colors */}
        <div className="mb-10">
          <h2 className="text-2xl font-bold mb-6 border-b pb-2">Sesiones de Mercado y Características</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {marketSessions.map((session, index) => (
              <div key={index} className={`bg-gradient-to-r ${session.color} rounded-xl p-6 border ${session.borderColor} shadow-md hover:shadow-lg transition-shadow duration-300`}>
                <div className="flex items-center gap-3 mb-5">
                  {session.icon}
                  <h3 className={`font-semibold text-lg ${session.textColor}`}>{session.title}</h3>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Horario:</span>
                    <span className="font-medium">{session.hours}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Volatilidad:</span>
                    <span className="font-medium">{session.volatility}</span>
                  </div>
                  <div className="border-t border-border pt-4 mt-4">
                    <p className="text-muted-foreground mb-1">Características:</p>
                    <p className="font-medium">{session.characteristics}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Recomendación:</p>
                    <p className="font-medium">{session.recommendation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tips and Insights - Completely redesigned section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6 border-b pb-2">Consejos e Insights Profesionales</h2>
          
          <div className="bg-card rounded-xl border border-border shadow-md p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {professionalInsights.map((insight, index) => (
                <div key={index} className="flex flex-col">
                  <div className="bg-primary/5 p-4 rounded-t-lg flex items-center gap-3 border-t border-l border-r border-primary/20">
                    {insight.icon}
                    <h3 className="font-semibold text-foreground">{insight.title}</h3>
                  </div>
                  <div className="bg-background p-5 rounded-b-lg border border-border shadow-inner">
                    <p className="text-muted-foreground leading-relaxed">{insight.description}</p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-8 bg-primary/5 rounded-lg p-6 border border-primary/20">
              <div className="flex items-start gap-3">
                <div className="bg-primary/10 p-2 rounded-full mt-1">
                  <AlertTriangle className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Recuerda:</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    El éxito en el trading no depende solo de horarios específicos, sino de una combinación de estrategia sólida, 
                    disciplina consistente y gestión de riesgo eficaz. Usa estos consejos como parte de un plan más amplio para alcanzar tus objetivos.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* FAQ Section - Enhanced design */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold mb-6 border-b pb-2">Preguntas Frecuentes</h2>
        
        <div className="bg-card rounded-xl border border-border shadow-md p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-background p-6 rounded-lg border border-border">
              <h3 className="font-semibold text-lg mb-3 text-primary">¿Realmente existe un mejor horario para operar?</h3>
              <p className="text-muted-foreground leading-relaxed">Para índices sintéticos como los disponibles en Deriv, no hay un horario universalmente mejor, ya que están basados en algoritmos pseudoaleatorios. Lo importante es probar y encontrar períodos que funcionen para tu estrategia específica.</p>
            </div>
            
            <div className="bg-background p-6 rounded-lg border border-border">
              <h3 className="font-semibold text-lg mb-3 text-primary">¿Debo dejar mi robot operando durante la madrugada?</h3>
              <p className="text-muted-foreground leading-relaxed">Es recomendable operar en horarios en los que puedas monitorear el rendimiento del robot, especialmente al principio. Las operaciones durante la madrugada sin supervisión pueden resultar en pérdidas inesperadas.</p>
            </div>
            
            <div className="bg-background p-6 rounded-lg border border-border">
              <h3 className="font-semibold text-lg mb-3 text-primary">¿Cómo identificar si un horario está siendo favorable?</h3>
              <p className="text-muted-foreground leading-relaxed">Observa los resultados en cuenta demo por algunas horas. Si el robot presenta una secuencia de 3-5 operaciones positivas consecutivas, puede ser un buen momento para cambiar a la cuenta real, siempre respetando tu gestión de riesgo.</p>
            </div>
            
            <div className="bg-background p-6 rounded-lg border border-border">
              <h3 className="font-semibold text-lg mb-3 text-primary">¿La volatilidad del mercado afecta el rendimiento del robot?</h3>
              <p className="text-muted-foreground leading-relaxed">Sí, cada robot está diseñado para funcionar mejor en determinadas condiciones de mercado. Algunos destacan en mercados más volátiles, mientras que otros rinden mejor en condiciones más estables.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Call to Action - Enhanced with more modern design */}
      <div className="bg-gradient-to-br from-primary via-primary/90 to-primary/80 rounded-2xl shadow-xl overflow-hidden relative">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute h-40 w-40 rounded-full bg-white/20 -top-10 -right-10"></div>
          <div className="absolute h-32 w-32 rounded-full bg-white/20 bottom-0 left-1/4"></div>
          <div className="absolute h-24 w-24 rounded-full bg-white/20 top-1/3 right-1/3"></div>
        </div>
        <div className="relative p-10 text-center">
          <h2 className="text-3xl font-bold mb-4 text-white">¿Listo para Comenzar?</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto text-white/90">Prueba tu robot en la cuenta demo en diferentes horarios y descubre los períodos que funcionan mejor para tu estrategia específica.</p>
          <div className="flex flex-col sm:flex-row gap-5 justify-center">
            <a href="/installation-tutorial" className="bg-white text-primary hover:bg-white/90 px-8 py-4 rounded-lg font-semibold shadow-lg transition-colors inline-flex items-center justify-center gap-2">
              <Clock className="h-5 w-5" />
              Tutorial de Instalación
            </a>
            <a href="/" className="bg-transparent hover:bg-white/10 border-2 border-white px-8 py-4 rounded-lg font-semibold text-white transition-colors inline-flex items-center justify-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Ver Bots Disponibles
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BestHours; 