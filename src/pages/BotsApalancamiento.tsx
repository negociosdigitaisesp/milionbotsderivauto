import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bot, ChartLine, Clock, TrendingUp, BarChart3, AlertTriangle, Zap, Target, Shield, Award, Star, ArrowRight, Info, DollarSign, Activity, Gauge } from 'lucide-react';
import { cn } from '../lib/utils';
import { bots } from '../lib/mockData';

// Función para obtener los bots de apalancamiento desde la biblioteca
const getLeverageBots = () => {
  // IDs de los bots de apalancamiento específicos
  const leverageBotIds = ['factor50x', '15', '14', 'apalancamiento-100x']; // Factor50X, Sniper Bot, NexusBot, Apalancamiento 100X
  
  // Filtrar y mapear los bots desde la biblioteca
  const leverageBots = leverageBotIds.map(id => {
    const bot = bots.find(b => b.id === id);
    if (!bot) return null;
    
    // Mapear los datos del bot a la estructura esperada
    return {
      id: bot.id,
      name: bot.name,
      description: bot.description,
      accuracy: bot.accuracy,
      operations: bot.operations,
      profit: `+${Math.round(bot.profitFactor * 100)}%`,
      risk: bot.riskLevel <= 3 ? 'Bajo' : bot.riskLevel <= 6 ? 'Medio' : bot.riskLevel <= 8 ? 'Alto' : 'Extremo',
      leverage: bot.id === 'factor50x' ? '50x' : bot.id === 'apalancamiento-100x' ? '100x' : bot.id === '15' ? '20x - 50x' : '10x - 75x',
      strategy: bot.strategy,
      timeframe: bot.id === 'factor50x' ? '5 ticks' : bot.id === '15' ? '5m - 15m' : bot.id === '14' ? '1m - 30m' : '1m - 5m',
      features: bot.id === 'factor50x' ? [
        'Análisis de momentum avanzado',
        'Gestión inteligente de riesgo',
        'Indicadores técnicos sofisticados',
        'Protección contra drawdown'
      ] : bot.id === '15' ? [
        'Análisis de patrones avanzado',
        'Señales de alta precisión',
        'Gestión conservadora de riesgo',
        'Backtesting continuo'
      ] : bot.id === '14' ? [
        'Inteligencia artificial avanzada',
        'Múltiples estrategias simultáneas',
        'Adaptación automática al mercado',
        'Optimización continua'
      ] : [
        'Stop-loss automático',
        'Take-profit dinámico',
        'Gestión de riesgo avanzada',
        'Análisis técnico en tiempo real'
      ],
      pros: bot.id === 'factor50x' ? [
        'Máxima precisión (87.2%)',
        'Equilibrio riesgo-rentabilidad',
        'Sistema anti-drawdown'
      ] : bot.id === '15' ? [
        'Alta tasa de acierto',
        'Riesgo controlado',
        'Operaciones selectivas'
      ] : bot.id === '14' ? [
        'Versatilidad en mercados',
        'Adaptación automática',
        'Balance riesgo-rentabilidad'
      ] : [
        'Alta rentabilidad potencial',
        'Ejecución ultra-rápida',
        'Gestión automática de posiciones'
      ],
      cons: bot.id === 'factor50x' ? [
        'Requiere experiencia avanzada',
        'Apalancamiento alto (50x)',
        'Necesita monitoreo constante'
      ] : bot.id === '15' ? [
        'Menor frecuencia de operaciones',
        'Rentabilidad moderada',
        'Requiere paciencia'
      ] : bot.id === '14' ? [
        'Complejidad técnica',
        'Curva de aprendizaje',
        'Requiere monitoreo'
      ] : [
        'Riesgo elevado de pérdidas',
        'Requiere capital considerable',
        'Volatilidad extrema'
      ]
    };
  }).filter(Boolean);
  
  // Ordenar por assertividade (accuracy) de mayor a menor
  return leverageBots.sort((a, b) => b.accuracy - a.accuracy);
};

const leverageBots = getLeverageBots();

const BotsApalancamiento = () => {
  const [selectedBot, setSelectedBot] = useState<string | null>(null);
  const navigate = useNavigate();

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Alto': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'Medio-Alto': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
      case 'Medio': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      default: return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    }
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-emerald-500';
    if (accuracy >= 70) return 'text-blue-500';
    return 'text-orange-500';
  };

  return (
    <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
      {/* Hero Section */}
      <section className="mb-12">
        <div className="relative overflow-hidden rounded-2xl shadow-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/25 via-primary/15 to-background"></div>
          
          {/* Decorative elements */}
          <div className="absolute inset-0 w-full h-full overflow-hidden opacity-70">
            <div className="absolute w-[600px] h-[600px] rounded-full bg-gradient-to-br from-primary/20 to-transparent -top-[350px] -right-[100px] blur-md"></div>
            <div className="absolute w-[500px] h-[500px] rounded-full bg-gradient-to-br from-primary/15 to-transparent top-[50%] -left-[200px] blur-md"></div>
            <div className="absolute top-0 right-0 w-full h-full bg-grid-white/[0.05] [mask-image:linear-gradient(to_bottom,transparent,black)]"></div>
            <svg className="absolute right-0 bottom-0 text-primary/10 w-64 h-64" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M47.1,-57.8C58.6,-47.6,63.6,-30.8,66.8,-13.5C70,3.8,71.5,21.6,64.6,35.5C57.6,49.4,42.2,59.5,25.7,65.1C9.1,70.7,-8.5,72,-23.9,66.3C-39.3,60.7,-52.5,48.1,-63.1,32.5C-73.7,16.9,-81.7,-1.7,-77.9,-17.7C-74.1,-33.7,-58.5,-47.1,-42.2,-56.5C-25.9,-65.9,-8.9,-71.4,6.8,-79.5C22.6,-87.6,39.4,-98.5,47.1,-57.8Z" transform="translate(120 130)" />
            </svg>
          </div>
          
          <div className="relative z-10 py-12 px-8 flex flex-col md:flex-row items-start gap-10">
            <div className="flex-1 max-w-3xl">
              <div className="inline-block mb-3 bg-primary/10 backdrop-blur-sm rounded-full px-4 py-1.5 border border-primary/20">
                <span className="text-primary font-medium text-sm flex items-center gap-2">
                  <Zap size={14} className="text-primary" />
                  Bots de Alta Apalancagem
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-4 text-foreground leading-tight">
                Bots de <span className="text-primary relative z-10">Apalancamiento
                  <svg className="absolute -bottom-2 -z-10 left-0 w-full opacity-20" viewBox="0 0 200 20" xmlns="http://www.w3.org/2000/svg">
                    <path fill="currentColor" d="M0,0 Q50,40 100,0 Q150,40 200,0 Z" />
                  </svg>
                </span>
              </h1>
              <p className="text-xl mb-6 text-muted-foreground leading-relaxed max-w-2xl">
                Descubre nuestros bots especializados en trading con apalancamiento para la plataforma Deriv. 
                Diseñados por traders expertos para maximizar oportunidades en mercados volátiles.
              </p>
              <div className="flex flex-wrap gap-4 mt-8">
                <div className="flex items-center gap-2 bg-card/80 backdrop-blur-sm rounded-lg px-4 py-2 border border-border/50">
                  <Target className="text-primary" size={16} />
                  <span className="text-sm font-medium">Precisión Avanzada</span>
                </div>
                <div className="flex items-center gap-2 bg-card/80 backdrop-blur-sm rounded-lg px-4 py-2 border border-border/50">
                  <Shield className="text-emerald-500" size={16} />
                  <span className="text-sm font-medium">Gestión de Riesgo</span>
                </div>
                <div className="flex items-center gap-2 bg-card/80 backdrop-blur-sm rounded-lg px-4 py-2 border border-border/50">
                  <Activity className="text-blue-500" size={16} />
                  <span className="text-sm font-medium">Trading Automatizado</span>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 gap-4 bg-card/80 backdrop-blur-sm rounded-lg p-6 border border-border/50 shadow-sm min-w-[300px]">
              <div className="text-center">
                <span className="text-xs text-muted-foreground">Bots Disponibles</span>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-3xl font-bold">{leverageBots.length}</span>
                  <Bot size={16} className="text-primary" />
                </div>
              </div>
              
              <div className="text-center">
                <span className="text-xs text-muted-foreground">Asertividad Promedio</span>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-3xl font-bold">
                    {Math.round(leverageBots.reduce((sum, bot) => sum + bot.accuracy, 0) / leverageBots.length)}%
                  </span>
                  <ChartLine size={16} className="text-primary" />
                </div>
              </div>
              
              <div className="text-center">
                <span className="text-xs text-muted-foreground">Total Operaciones</span>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-3xl font-bold">
                    {leverageBots.reduce((sum, bot) => sum + bot.operations, 0).toLocaleString()}
                  </span>
                  <Clock size={16} className="text-primary" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Risk Warning Section */}
      <section className="mb-12">
        <div className="bg-gradient-to-r from-red-500/10 via-orange-500/10 to-red-500/10 border border-red-500/30 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <AlertTriangle className="text-red-500 flex-shrink-0 mt-1" size={24} />
            <div>
              <h3 className="text-lg font-bold text-red-700 dark:text-red-400 mb-3">
                ⚠️ ADVERTENCIA IMPORTANTE SOBRE APALANCAMIENTO
              </h3>
              <div className="space-y-3 text-sm text-red-600 dark:text-red-300">
                <p className="font-medium">
                  El trading con apalancamiento amplifica tanto las ganancias como las pérdidas potenciales.
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Puede perder más dinero del que invirtió inicialmente</li>
                  <li>Los mercados pueden moverse en su contra rápidamente</li>
                  <li>El apalancamiento alto requiere gestión estricta de riesgo</li>
                  <li>Solo opere con dinero que pueda permitirse perder</li>
                  <li>Considere usar stop-loss y take-profit siempre</li>
                </ul>
                <p className="font-medium bg-red-500/20 p-3 rounded-lg border border-red-500/30">
                  📊 <strong>Recomendación:</strong> Comience con apalancamiento bajo y aumente gradualmente según su experiencia y tolerancia al riesgo.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Minimum Account Recommendation Section */}
      <section className="mb-12">
        <div className="bg-gradient-to-r from-emerald-500/10 via-blue-500/10 to-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <DollarSign className="text-emerald-500 flex-shrink-0 mt-1" size={24} />
            <div>
              <h3 className="text-lg font-bold text-emerald-700 dark:text-emerald-400 mb-3">
                💰 RECOMENDACIÓN DE CUENTA MÍNIMA
              </h3>
              <div className="space-y-3 text-sm text-emerald-600 dark:text-emerald-300">
                <p className="font-medium text-base">
                  Para obtener los mejores resultados con nuestros bots de apalancamiento, recomendamos una cuenta mínima de <span className="font-bold text-emerald-700 dark:text-emerald-300">$50 USD</span>.
                </p>
                <div className="bg-emerald-500/20 p-4 rounded-lg border border-emerald-500/30">
                  <h4 className="font-semibold mb-2 text-emerald-800 dark:text-emerald-200">¿Por qué $50 USD?</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>Permite diversificar operaciones y reducir riesgo</li>
                    <li>Proporciona margen suficiente para gestión de posiciones</li>
                    <li>Optimiza el rendimiento de las estrategias de apalancamiento</li>
                    <li>Facilita la implementación de stop-loss y take-profit efectivos</li>
                  </ul>
                </div>
                <p className="text-xs text-emerald-600 dark:text-emerald-400 italic">
                  * Esta recomendación se basa en análisis de rendimiento histórico y mejores prácticas de trading con apalancamiento en la región de América Latina.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Leverage Education Section */}
      <section className="mb-12">
        <div className="bg-card/50 rounded-xl border border-border shadow-sm p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Info className="text-primary" size={24} />
            ¿Qué es el Apalancamiento?
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-3 text-primary">Concepto Básico</h3>
              <p className="text-muted-foreground mb-4">
                El apalancamiento permite controlar una posición más grande con una cantidad menor de capital. 
                Por ejemplo, con apalancamiento 100:1, puede controlar $10,000 con solo $100.
              </p>
              <div className="bg-primary/5 p-4 rounded-lg border border-primary/20">
                <h4 className="font-medium mb-2">Ejemplo Práctico:</h4>
                <p className="text-sm text-muted-foreground">
                  Con $100 y apalancamiento 50x, puede abrir una posición de $5,000. 
                  Si el mercado sube 2%, gana $100 (100% de retorno). 
                  Si baja 2%, pierde $100 (100% de pérdida).
                </p>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-3 text-emerald-500">Gestión de Riesgo</h3>
              <ul className="space-y-2 text-muted-foreground">
                <li className="flex items-center gap-2">
                  <Shield size={16} className="text-emerald-500" />
                  Use stop-loss en todas las operaciones
                </li>
                <li className="flex items-center gap-2">
                  <Target size={16} className="text-blue-500" />
                  Defina objetivos de ganancia claros
                </li>
                <li className="flex items-center gap-2">
                  <DollarSign size={16} className="text-orange-500" />
                  No arriesgue más del 2-5% por operación
                </li>
                <li className="flex items-center gap-2">
                  <Activity size={16} className="text-purple-500" />
                  Diversifique sus estrategias
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Bots Grid */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="text-primary" size={24} />
            Nuestros Bots de Apalancamiento
          </h2>
          <div className="text-sm text-muted-foreground">
            Desarrollados por traders expertos en Deriv
          </div>
        </div>
        
        <div className="grid lg:grid-cols-3 gap-8">
          {leverageBots.map((bot) => (
            <div key={bot.id} className="group relative">
              <div className="bg-card rounded-xl border border-border shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden">
                {/* Header */}
                <div className="relative p-6 border-b border-border bg-gradient-to-br from-card via-card to-card/50">
                  <div className="absolute top-4 right-4">
                    <div className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-semibold border shadow-sm backdrop-blur-sm",
                      getRiskColor(bot.risk)
                    )}>
                      {bot.risk}
                    </div>
                  </div>
                  
                  <div className="pr-20">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        bot.accuracy >= 80 ? "bg-emerald-500" : bot.accuracy >= 70 ? "bg-blue-500" : "bg-orange-500"
                      )}></div>
                      <h3 className="text-xl font-bold">{bot.name}</h3>
                    </div>

                  </div>
                  
                  {/* Enhanced Stats */}
                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="text-center bg-background/50 rounded-lg p-3 border border-border/50">
                      <div className={cn("text-2xl font-bold mb-1", getAccuracyColor(bot.accuracy))}>
                        {bot.accuracy}%
                      </div>
                      <div className="text-xs text-muted-foreground font-medium">Asertividad</div>
                    </div>
                    <div className="text-center bg-background/50 rounded-lg p-3 border border-border/50">
                      <div className="text-2xl font-bold text-emerald-500 mb-1">
                        {bot.profit}
                      </div>
                      <div className="text-xs text-muted-foreground font-medium">Ganancia</div>
                    </div>
                    <div className="text-center bg-background/50 rounded-lg p-3 border border-border/50">
                      <div className="text-2xl font-bold text-blue-500 mb-1">
                        {bot.operations.toLocaleString()}
                      </div>
                      <div className="text-xs text-muted-foreground font-medium">Operaciones</div>
                    </div>
                  </div>
                </div>
                
                {/* Enhanced Details */}
                <div className="p-6">
                  <div className="space-y-6">
                    {/* Technical Specs */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-muted/30 rounded-lg p-3 border border-border/50">
                        <div className="text-xs text-muted-foreground mb-1">Apalancamiento</div>
                        <div className="font-bold text-primary">{bot.leverage}</div>
                      </div>
                      <div className="bg-muted/30 rounded-lg p-3 border border-border/50">
                        <div className="text-xs text-muted-foreground mb-1">Timeframe</div>
                        <div className="font-bold">{bot.timeframe}</div>
                      </div>
                    </div>
                    
                    {/* Strategy Badge */}
                    <div className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-lg p-4 border border-primary/20">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity size={16} className="text-primary" />
                        <span className="text-sm font-medium text-primary">Estrategia Principal</span>
                      </div>
                      <div className="font-bold text-lg">{bot.strategy}</div>
                    </div>
                    
                    {/* Features */}
                    <div>
                      <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Shield size={14} className="text-emerald-500" />
                        Características Principales
                      </h4>
                      <div className="grid grid-cols-1 gap-2">
                        {bot.features.map((feature, index) => (
                          <div key={index} className="flex items-center gap-3 p-2 bg-muted/20 rounded-md border border-border/30">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full flex-shrink-0"></div>
                            <span className="text-sm">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Footer */}
                <div className="p-6 pt-0">
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setSelectedBot(selectedBot === bot.id ? null : bot.id)}
                      className="flex-1 px-4 py-2 bg-muted hover:bg-muted/80 text-foreground rounded-md text-sm font-medium transition-colors"
                    >
                      {selectedBot === bot.id ? 'Ocultar Detalles' : 'Ver Detalles'}
                    </button>
                    <button 
                      onClick={() => navigate(bot.id === 'factor50x' ? '/factor50x' : `/bot/${bot.id}`)}
                      className="flex-1 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-md text-sm font-medium transition-colors text-center flex items-center justify-center gap-1"
                    >
                      {bot.id === 'factor50x' ? 'Ver Configurações' : 'Usar Bot'}
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
                
                {/* Expanded Details */}
                {selectedBot === bot.id && (
                  <div className="border-t border-border p-6 bg-muted/20 animate-in fade-in slide-in-from-top-4 duration-300">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium mb-3 text-emerald-500 flex items-center gap-1">
                          <Award size={14} />
                          Ventajas
                        </h4>
                        <ul className="text-xs space-y-1">
                          {bot.pros.map((pro, index) => (
                            <li key={index} className="flex items-center gap-2 text-emerald-600">
                              <div className="w-1 h-1 bg-emerald-500 rounded-full"></div>
                              {pro}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium mb-3 text-orange-500 flex items-center gap-1">
                          <AlertTriangle size={14} />
                          Consideraciones
                        </h4>
                        <ul className="text-xs space-y-1">
                          {bot.cons.map((con, index) => (
                            <li key={index} className="flex items-center gap-2 text-orange-600">
                              <div className="w-1 h-1 bg-orange-500 rounded-full"></div>
                              {con}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Expert Insights Section */}
      <section className="mb-12">
        <div className="bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 rounded-xl border border-primary/20 p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold mb-4 flex items-center justify-center gap-2">
              <Star className="text-primary" size={24} />
              Consejos de Traders Expertos
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Recomendaciones de profesionales con años de experiencia en trading con apalancamiento en Deriv
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-card/50 rounded-lg p-6 border border-border">
              <div className="text-primary mb-3">
                <Gauge size={24} />
              </div>
              <h3 className="font-semibold mb-2">Gestión de Capital</h3>
              <p className="text-sm text-muted-foreground">
                "Nunca arriesgues más del 2% de tu capital en una sola operación. 
                La consistencia es más importante que las ganancias grandes."
              </p>
              <div className="text-xs text-primary mt-2 font-medium">- Carlos Mendoza, Trader Senior</div>
            </div>
            
            <div className="bg-card/50 rounded-lg p-6 border border-border">
              <div className="text-emerald-500 mb-3">
                <Target size={24} />
              </div>
              <h3 className="font-semibold mb-2">Análisis Técnico</h3>
              <p className="text-sm text-muted-foreground">
                "Combina múltiples indicadores y siempre confirma las señales. 
                Los bots son herramientas, pero el análisis humano sigue siendo clave."
              </p>
              <div className="text-xs text-emerald-500 mt-2 font-medium">- Ana Rodriguez, Analista Técnica</div>
            </div>
            
            <div className="bg-card/50 rounded-lg p-6 border border-border">
              <div className="text-blue-500 mb-3">
                <Activity size={24} />
              </div>
              <h3 className="font-semibold mb-2">Psicología del Trading</h3>
              <p className="text-sm text-muted-foreground">
                "Mantén la disciplina emocional. Los bots te ayudan a eliminar 
                las decisiones impulsivas, pero debes seguir el plan establecido."
              </p>
              <div className="text-xs text-blue-500 mt-2 font-medium">- Miguel Santos, Trader Profesional</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section>
        <div className="bg-gradient-to-r from-primary to-primary/80 rounded-xl p-8 text-center text-primary-foreground">
          <h2 className="text-2xl font-bold mb-4">¿Listo para Comenzar?</h2>
          <p className="mb-6 opacity-90 max-w-2xl mx-auto">
            Únete a miles de traders que ya están utilizando nuestros bots de apalancamiento 
            para maximizar sus oportunidades en los mercados financieros.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/library" 
              className="px-6 py-3 bg-white text-primary rounded-lg font-medium hover:bg-gray-100 transition-colors"
            >
              Ver Todos los Bots
            </Link>
            <Link 
              to="/installation-tutorial" 
              className="px-6 py-3 bg-primary-foreground/20 text-white rounded-lg font-medium hover:bg-primary-foreground/30 transition-colors border border-primary-foreground/30"
            >
              Tutorial de Instalación
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default BotsApalancamiento;