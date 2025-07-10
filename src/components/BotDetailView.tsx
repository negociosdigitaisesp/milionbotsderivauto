import React, { useState } from 'react';
import { ArrowRight, Download, ShieldCheck, ChartLine, Info, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import CodeViewer from './CodeViewer';
import { Bot } from '../lib/mockData';
import PerformanceChart from './PerformanceChart';
interface BotDetailViewProps {
  bot: Bot;
}
const BotDetailView = ({
  bot
}: BotDetailViewProps) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'riskManagement' | 'instructions'>('overview');

  // Risk color based on risk level
  const getRiskColor = (level: number) => {
    if (level <= 3) return 'text-success bg-success/10';
    if (level <= 5) return 'text-warning bg-warning/10';
    return 'text-danger bg-danger/10';
  };
  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 60) return 'text-success';
    if (accuracy >= 45) return 'text-warning';
    return 'text-danger';
  };

  // Generate sample performance data for the chart
  const generatePerformanceData = (baseAccuracy: number) => {
    const data = [];
    // 12 months of data
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    let currentValue = baseAccuracy;
    for (let i = 0; i < 12; i++) {
      // Add some slight variation to accuracy (-3 to +3)
      const variation = Math.floor(Math.random() * 7) - 3;
      currentValue = Math.max(30, Math.min(95, baseAccuracy + variation));
      data.push({
        date: months[i],
        value: currentValue
      });
    }
    return data;
  };

  // Sample daily performance data for detailed chart
  const generateDailyPerformanceData = (baseAccuracy: number) => {
    const data = [];
    let currentValue = baseAccuracy;
    for (let i = 1; i <= 30; i++) {
      // Add more variation for daily data (-5 to +5)
      const variation = Math.floor(Math.random() * 11) - 5;
      currentValue = Math.max(30, Math.min(95, baseAccuracy + variation));
      data.push({
        date: `Día ${i}`,
        value: currentValue
      });
    }
    return data;
  };

  // Investment Risk Warning Banner Component
  const InvestmentWarningBanner = () => (
    <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <AlertTriangle className="text-red-500 flex-shrink-0" size={20} />
        <div className="text-sm">
          <p className="font-medium text-red-700 dark:text-red-400 mb-1">
             AVISO SOBRE RIESGOS DE INVERSIÓN
           </p>
           <p className="text-red-600 dark:text-red-300">
              Los retornos pasados no garantizan retornos futuros. La negociación de productos financieros complejos, como opciones y derivados, implica un elevado nivel de riesgo y puede resultar en la pérdida de todo el capital invertido. Asegúrese de comprender plenamente los riesgos antes de invertir y nunca arriesgue más dinero del que pueda permitirse perder.
            </p>
        </div>
      </div>
    </div>
  );

  // Special content for bots
  const renderBotSpecificOverview = () => {
    if (bot.id === "8") {
      // Optin Trade
      return <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info size={18} /> Estrategia Explicada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                El robot <strong>Optin Trade</strong> está diseñado para el mercado de Índices Sintéticos (R_100) 
                en Deriv. Identifica tendencias de muy corto plazo usando el cruce de 
                Medias Móviles Simples (SMA) y opera con contratos tipo "Run" (Run High / Run Low).
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Análisis de Tendencia (SMA)</h4>
                  <p className="text-sm text-muted-foreground">
                    El robot utiliza dos SMAs: una <strong>Rápida</strong> (período 1) y una 
                    <strong> Lenta</strong> (período 20). Cuando la SMA Rápida cruza por encima de la SMA Lenta, 
                    compra un contrato <strong>RUNHIGH</strong>. Cuando cruza por debajo, 
                    compra un contrato <strong>RUNLOW</strong>.
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Sistema de Martingale Especializado</h4>
                  <p className="text-sm text-muted-foreground">
                    Después de una pérdida, el robot utiliza una lógica de recuperación especial:
                    si la pérdida total es pequeña, usa stake fijo de <strong>0.35</strong>; 
                    si es significativa, calcula el siguiente stake como <strong>pérdida total × -0.45</strong>.
                  </p>
                </div>
              </div>
              

            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ChartLine size={18} /> Rendimiento Esperado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-8">
                <h4 className="font-medium mb-4">Precisión por Operación</h4>
                <div className="grid grid-cols-1 gap-8">
                  <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Asertividad Diaria" yAxisLabel="Precisión %" />
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  La asertividad individual es de <strong>40-55%</strong>, dependiendo de las condiciones del mercado.
                  El objetivo del Martingale NO es aumentar la tasa de acierto individual, sino aumentar 
                  la probabilidad de cerrar una sesión con ganancias.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>;
    }
    
    if (bot.id === "14") {
      // NexusBot
      return (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info size={18} /> Estrategia Explicada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                El <strong>NexusBot</strong> opera en el Índice Sintético <strong>RDBEAR</strong> (Random Daily Bear Market Index) 
                de Deriv. Su estrategia se basa en el análisis secuencial de múltiples ticks anteriores para identificar 
                un patrón de subida o bajada, realizando operaciones "Rise/Fall" (Sube/Baja) con duración de 5 minutos.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Análisis de Tendencia (Secuencia de Ticks)</h4>
                  <p className="text-sm text-muted-foreground">
                    El robot recopila los últimos 9 ticks y analiza patrones específicos:
                    <ul className="list-disc list-inside mt-2">
                      <li><strong>Señal de Compra "PUT" (Baja):</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Si el Tick 5 {'>'} Tick 4, Y</li>
                          <li>Si el Tick 4 {'>'} Tick 3, Y</li>
                          <li>Si el Tick 3 {'>'} Tick 2, Y</li>
                          <li>Si el Tick 1 {'<'} Tick 2 (indicando una posible reversión después de una secuencia de subida)</li>
                        </ul>
                      </li>
                      <li className="mt-2"><strong>Señal de Compra "CALL" (Sube):</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Si el Tick 5 {'<'} Tick 4, Y</li>
                          <li>Si el Tick 4 {'<'} Tick 3, Y</li>
                          <li>Si el Tick 3 {'<'} Tick 2, Y</li>
                          <li>Si el Tick 1 {'>'} Tick 2 (indicando una posible reversión después de una secuencia de bajada)</li>
                        </ul>
                      </li>
                    </ul>
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Gestión Durante la Operación</h4>
                  <p className="text-sm text-muted-foreground">
                    <strong>Venta Anticipada:</strong> Después de la compra, si el contrato está disponible para venta:
                    <ul className="list-disc list-inside mt-2">
                      <li>Si la ganancia actual de la venta es mayor que <strong>(Valor de la Compra / 100) * 5</strong> (es decir, 5% del valor de la apuesta), el robot vende el contrato en el mercado.</li>
                    </ul>
                  </p>
                  <div className="mt-3">
                    <h5 className="font-medium text-sm">Tipo de Operación:</h5>
                    <p className="text-sm text-muted-foreground">
                      <ul className="list-disc list-inside mt-1">
                        <li>Contratos "Rise/Fall" (Sube/Baja)</li>
                        <li>Duración: Fijo en <strong>5 minutos</strong></li>
                      </ul>
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-secondary/50 p-4 rounded-lg mt-4">
                <h4 className="font-medium mb-2">Gestión de Apuesta (Martingale Específico)</h4>
                <p className="text-sm text-muted-foreground">
                  <ul className="list-disc list-inside">
                    <li><strong>Después de una Ganancia:</strong> La siguiente apuesta vuelve al "Valor Inicial de la Orden" definido por el usuario.</li>
                    <li><strong>Después de una Pérdida:</strong>
                      <ul className="list-disc list-inside ml-4 mt-1">
                        <li><strong>Pequeñas Pérdidas</strong> (Pérdida Total ≥ -1.4 USD): La siguiente apuesta se fija en <strong>0.35 USD</strong>.</li>
                        <li><strong>Grandes Pérdidas</strong> (Pérdida Total {'<'} -1.4 USD): La siguiente apuesta se calcula como <strong>(Pérdida Total Acumulada * -0.35)</strong>.</li>
                      </ul>
                    </li>
                  </ul>
                </p>
              </div>
              

            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ChartLine size={18} /> Proyecciones de Ganancias y Riesgos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-8">
                <h4 className="font-medium mb-4">Precisión por Operación</h4>
                <div className="grid grid-cols-1 gap-8">
                  <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Asertividad Diaria" yAxisLabel="Precisión %" />
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  La asertividad individual es de <strong>45-50%</strong>, dependiendo de las condiciones del mercado.
                  Operaciones de 5 minutos pueden tener payouts interesantes si la tendencia se confirma.
                  La venta anticipada (si es rentable) puede garantizar pequeñas ganancias antes del vencimiento del contrato.
                </p>
              </div>
              
              <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-4">
                <h4 className="font-medium mb-2 text-primary">Ejemplo de Riesgo con Martingale</h4>
                <p className="text-sm">
                  El Martingale con factor <strong>-0.35</strong> sobre la pérdida total es inusual. Ejemplo:
                  <ul className="list-disc list-inside mt-2">
                    <li>Pérdida 1 (Stake $0.35): $0.35 (Total Perdido: $0.35) → Siguiente Apuesta: $0.35</li>
                    <li>Pérdida 2 (Stake $0.35): $0.35 (Total Perdido: $0.70) → Siguiente Apuesta: $0.35</li>
                    <li>Pérdida 3 (Stake $0.35): $0.35 (Total Perdido: $1.05) → Siguiente Apuesta: $0.35</li>
                    <li>Pérdida 4 (Stake $0.35): $0.35 (Total Perdido: $1.40) → Siguiente Apuesta: $1.40 * 0.35 = ~$0.49</li>
                    <li>Pérdida 5 (Stake $0.49): $0.49 (Total Perdido: $1.89) → Siguiente Apuesta: $1.89 * 0.35 = ~$0.66</li>
                  </ul>
                </p>
                <p className="text-sm mt-2">
                  Este Martingale es más lento en la progresión del stake comparado con factores mayores, lo que puede permitir más 
                  intentos de recuperación antes de alcanzar un Stop Loss alto, pero también significa que la recuperación total 
                  de una pérdida grande requerirá más victorias.
                </p>
              </div>
              
              <div className="mt-6">
                <h4 className="font-medium mb-4">Visualización Riesgo vs. Recompensa</h4>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Meta de Ganancia (Ej: +$2.50 en balance de $50)</span>
                      <span>+$2.50</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-4">
                      <div className="bg-success h-4 rounded-full" style={{ width: '40%' }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Límite de Pérdida (Ej: -$7.50 en balance de $50)</span>
                      <span className="text-danger">-$7.50</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-4">
                      <div className="bg-danger h-4 rounded-full" style={{ width: '60%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }
    
    if (bot.id === "13") {
      // AlphaBot
      return <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgos (¡Definida por USTED!)
              </CardTitle>
            </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm">
              El AlphaBot requiere que <strong>USTED</strong> defina sus límites. La gestión de riesgo es <strong>CRUCIAL</strong>, 
              especialmente con este Martingale.
            </p>
            
            <div>
              <h3 className="font-medium mb-2">Meta Ganancia (Stop Win)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define el objetivo de ganancia para cerrar la sesión con beneficio.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 1% a 3% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Win $0.50 a $1.50.
                    Metas menores son más fáciles de alcanzar antes de ciclos de pérdida.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Moderado: 3% a 5% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Win $1.50 a $2.50.
                  </p>
                </div>
                </div>
              </div>
              
            <div className="mt-6">
              <h3 className="font-medium mb-2">Límite Pérdidas (Stop Loss)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define el límite máximo de pérdida antes de que el robot detenga las operaciones.
                <strong> ¡NUNCA opere sin un Stop Loss definido!</strong>
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 5% a 10% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Loss $2.50 a $5.00.
                    <strong> CRÍTICO con este Martingale: Use un Stop Loss MUY CONSERVADOR.</strong>
                  </p>
                </div>
                
                <div className="border border-warning/30 rounded-lg p-4">
                  <h4 className="font-medium text-warning mb-2">Moderado (Alto Riesgo): 10% a 15% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Loss $5.00 a $7.50.
                    <strong> ATENCIÓN: El Martingale -1.07 puede consumir su Stop Loss muy rápidamente.</strong>
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Valor Inicial de la Orden</h3>
              <div className="border border-success/30 rounded-lg p-4">
                <h4 className="font-medium text-success mb-2">Recomendado: $0.35</h4>
                <p className="text-xs text-muted-foreground">
                  Mantener este valor bajo es vital debido a la agresividad del Martingale.
                </p>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Cantidad de Ticks (Duración)</h3>
                <p className="text-sm text-muted-foreground">
                El robot internamente opera con 1 tick para "Digits Over/Under", independientemente del valor ingresado 
                aquí (la interfaz lo solicita, pero el tipo de contrato fija la duración).
                </p>
              </div>
              
            <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-6">
              <h4 className="font-medium mb-2 text-primary">Recomendación de Capital</h4>
              <p className="text-sm">
                Mínimo de $50 USD. Sin embargo, debido al Martingale EXTREMADAMENTE AGRESIVO, un capital mayor 
                ($75-$100+) es altamente recomendado para dar algún margen al Stop Loss, incluso si es conservador.
              </p>
            </div>
          </CardContent>
        </Card>;
    }
    
    // Default content for other bots
    return <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info size={18} /> Estrategia Explicada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              El robot <strong>{bot.name}</strong> utiliza una estrategia de {bot.strategy} 
              para operar en los mercados.
            </p>
            
            <div className="bg-secondary/50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Detalles de la Estrategia</h4>
                <p className="text-sm text-muted-foreground">
                {bot.description}
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
              <ChartLine size={18} /> Rendimiento Esperado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-8">
                <h4 className="font-medium mb-4">Precisión por Operación</h4>
                <div className="grid grid-cols-1 gap-8">
                  <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Asertividad Diaria" yAxisLabel="Precisión %" />
                </div>
            </div>
          </CardContent>
        </Card>
      </div>;
  };

  // Special content for bot risk management
  const renderBotSpecificRiskManagement = () => {
    if (bot.id === "9") {
      // SMA Trend Follower
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgos Recomendada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">🛡️ Gestión de Riesgos Recomendada (¡ESENCIAL!)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                El Martingale es una estrategia de <strong>ALTO RIESGO</strong>. ¡Adminístrela con sabiduría!
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">🛡️ Stop Loss (Límite de Pérdida)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>¡NUNCA OPERE SIN UN STOP LOSS!</strong>
                    <br />
                    Establezca un valor pequeño en relación a su banca total (ej: 2% a 5% por sesión).
                    <br />
                    <em>Ejemplo:</em> Banca de $100, Stop Loss de $5.
                </p>
              </div>
              
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">🎯 Stop Win (Meta de Ganancia)</h4>
                  <p className="text-xs text-muted-foreground">
                    Establezca una meta realista, generalmente menor o igual a su Stop Loss.
                    <br />
                    <em>Ejemplo:</em> Stop Loss $5, Stop Win de $2 a $5.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💵 Valor de la Orden Inicial</h4>
                  <p className="text-xs text-muted-foreground">
                    Comience con el valor recomendado de <strong>0.35 USD</strong>.
                </p>
              </div>
              
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏱️ Cantidad de Ticks</h4>
                  <p className="text-xs text-muted-foreground">
                    Para "Higher/Lower" en <code>R_100</code> con SMAs, duraciones entre <strong>5</strong> y <strong>15 ticks</strong> suelen ser un buen punto de partida para pruebas. Ajuste según sus resultados.
                  </p>
                    </div>
                    </div>
                  </div>
          </CardContent>
        </Card>;
    }
    
    if (bot.id === "14") {
      // NexusBot
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgos Recomendada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
                  <div>
              <h3 className="font-medium mb-2">🛡️ Gestión de Riesgos Recomendada (ESSENCIAL!)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                El Martingale es una estrategia de <strong>ALTO RIESGO</strong>. ¡Adminístrela con sabiduría!
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">🛡️ Stop Loss (Límite de Pérdida)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>¡NUNCA OPERE SIN UN STOP LOSS!</strong>
                    <br />
                    Establezca un valor pequeño en relación a su banca total (ej: 2% a 5% por sesión).
                    <br />
                    <em>Ejemplo:</em> Banca de $100, Stop Loss de $5.
                  </p>
                    </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">🎯 Stop Win (Meta de Ganancia)</h4>
                  <p className="text-xs text-muted-foreground">
                    Establezca una meta realista, generalmente menor o igual a su Stop Loss.
                    <br />
                    <em>Ejemplo:</em> Stop Loss $5, Stop Win de $2 a $5.
                  </p>
                    </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💵 Valor de la Orden Inicial</h4>
                  <p className="text-xs text-muted-foreground">
                    Comience con el valor recomendado de <strong>0.35 USD</strong>.
                  </p>
                  </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏱️ Cantidad de Ticks</h4>
                  <p className="text-xs text-muted-foreground">
                    Para "Higher/Lower" en <code>R_100</code> con SMAs, duraciones entre <strong>5</strong> y <strong>15 ticks</strong> suelen ser un buen punto de partida para pruebas. Ajuste según sus resultados.
                  </p>
                </div>
              </div>
              

              </div>
            </CardContent>
        </Card>;
    }
    
    if (bot.id === "12") {
      // XBot
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgos Recomendada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">🛡️ Gestión de Riesgos Recomendada (ESSENCIAL!)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                El Martingale es una estrategia de <strong>ALTO RIESGO</strong>. ¡Adminístrela con sabiduría!
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">🛡️ Stop Loss (Límite de Pérdida)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>¡NUNCA OPERE SIN UN STOP LOSS!</strong>
                    <br />
                    Establezca un valor pequeño en relación a su banca total (ej: 2% a 5% por sesión).
                    <br />
                    <em>Ejemplo:</em> Banca de $100, Stop Loss de $5.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">🎯 Stop Win (Meta de Ganancia)</h4>
                  <p className="text-xs text-muted-foreground">
                    Establezca una meta realista, generalmente menor o igual a su Stop Loss.
                    <br />
                    <em>Ejemplo:</em> Stop Loss $5, Stop Win de $2 a $5.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💵 Valor de la Orden Inicial</h4>
                  <p className="text-xs text-muted-foreground">
                    Comience con el valor recomendado de <strong>0.35 USD</strong>.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏱️ Cantidad de Ticks</h4>
                  <p className="text-xs text-muted-foreground">
                    Para "Higher/Lower" en <code>R_100</code> con SMAs, duraciones entre <strong>5</strong> y <strong>15 ticks</strong> suelen ser un buen punto de partida para pruebas. Ajuste según sus resultados.
                  </p>
                </div>
              </div>
              

            </div>
          </CardContent>
        </Card>;
    }
    
    if (bot.id === "11") {
      // Quantum Bot
      return <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgos Preconfigurada
              </CardTitle>
            </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">⚙️ Gestión de Riesgos (Preconfigurada)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                El <strong>Quantum Bot</strong> ya viene con configuraciones de riesgo definidas:
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">💰 Meta Ganancia (Stop Win)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>$20 USD</strong>
                    <br />
                    El robot detendrá las operaciones automáticamente al alcanzar este valor de ganancia.
                  </p>
                </div>
                
                <div className="border border-danger/30 rounded-lg p-4">
                  <h4 className="font-medium text-danger mb-2">💸 Límite de Pérdida (Stop Loss)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>$20 USD</strong>
                    <br />
                    El robot detendrá las operaciones automáticamente al alcanzar este valor de pérdida.
                  </p>
              </div>
              
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💲 Valor Inicial de la Orden</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>$0.35 USD</strong>
                    <br />
                    Este es el stake fijo para cada operación. Al no usar Martingale, el valor permanece constante independientemente del resultado.
                  </p>
                </div>
              
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏲️ Cantidad de Ticks (Duración)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>1 tick</strong>
                    <br />
                    Las operaciones son de muy corta duración, con contratos de apenas 1 tick.
                </p>
              </div>
              </div>
              
              <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-6">
                <h4 className="font-medium mb-2 text-primary">✅ Recomendación de Capital</h4>
                <p className="text-sm">
                  Sugerimos operar este robot con cuentas a partir de <strong>$50 USD</strong> para tener un margen adecuado 
                  con el Stop Loss preconfigurado. Al no usar Martingale, es menos arriesgado que otros bots.
                </p>
              </div>
              

              </div>
            </CardContent>
        </Card>;
    }
    
    if (bot.id === "8") {
      // Optin Trade
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgo Recomendada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">🛡️ Gestión de Riesgo Recomendada (¡CRUCIAL!)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                La estrategia de Martingale, especialmente la forma agresiva implementada en este robot cuando las pérdidas se acumulan, es de <strong>ALTO RIESGO</strong>.
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">🛡️ Stop Loss (Límite de Pérdidas)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>¡NUNCA opere sin un Stop Loss definido!</strong>
                    <br />
                    <strong>Recomendación:</strong> Defina un valor que represente un pequeño porcentaje de su capital total (ej: 2% a 5% de su capital <em>por sesión</em>).
                    <br />
                    <em>Ejemplo:</em> Si su capital es de $100, un Stop Loss de $5 (5%) es un buen punto de partida.
                    <br />
                    Este valor debe ser el máximo que está dispuesto a perder en una sesión de trading con este robot.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">🎯 Stop Win (Meta de Ganancia)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>Recomendación:</strong> Defina una meta realista, generalmente menor o igual a su Stop Loss.
                    <br />
                    <em>Ejemplo:</em> Si su Stop Loss es $5, un Stop Win de $2 a $5 puede ser adecuado.
                    <br />
                    Alcanzar pequeñas metas de forma consistente es más sostenible.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💵 Valor de la Operación Inicial</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>Recomendación:</strong> Use el menor valor posible que el broker permite (ej: $0.35) o un porcentaje muy pequeño de su capital (ej: 0.5% a 1%).
                    <br />
                    Recuerde que este valor puede aumentar significativamente con el Martingale.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏱️ Cantidad de Ticks</h4>
                  <p className="text-xs text-muted-foreground">
                    Los contratos "Run High/Run Low" son sensibles a la duración.
                    <br />
                    <strong>Duraciones menores (1-3 ticks)</strong> son más arriesgadas, pero pueden tener payouts mayores y se alinean con la naturaleza de "escape rápido" del precio.
                    <br />
                    <strong>Duraciones mayores (4-5+ ticks)</strong> dan más tiempo para que el precio se mueva, pero pueden tener payouts diferentes y la efectividad del SMA puede variar. Pruebe para encontrar el ideal para <code>R_100</code>.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>;
    }
    
    if (bot.id === "13") {
      // AlphaBot
      return <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestión de Riesgos (¡Definida por USTED!)
              </CardTitle>
            </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm">
              El AlphaBot requiere que <strong>USTED</strong> defina sus límites. La gestión de riesgo es <strong>CRUCIAL</strong>, 
              especialmente con este Martingale.
            </p>
            
            <div>
              <h3 className="font-medium mb-2">Meta Ganancia (Stop Win)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define el objetivo de ganancia para cerrar la sesión con beneficio.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 1% a 3% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Win $0.50 a $1.50.
                    Metas menores son más fáciles de alcanzar antes de ciclos de pérdida.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Moderado: 3% a 5% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Win $1.50 a $2.50.
                  </p>
                </div>
                </div>
              </div>
              
            <div className="mt-6">
              <h3 className="font-medium mb-2">Límite Pérdidas (Stop Loss)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define el límite máximo de pérdida antes de que el robot detenga las operaciones.
                <strong> ¡NUNCA opere sin un Stop Loss definido!</strong>
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 5% a 10% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Loss $2.50 a $5.00.
                    <strong> CRÍTICO con este Martingale: Use un Stop Loss MUY CONSERVADOR.</strong>
                  </p>
                </div>
                
                <div className="border border-warning/30 rounded-lg p-4">
                  <h4 className="font-medium text-warning mb-2">Moderado (Alto Riesgo): 10% a 15% del capital</h4>
                  <p className="text-xs text-muted-foreground">
                    Ej: Capital $50, Stop Loss $5.00 a $7.50.
                    <strong> ATENCIÓN: El Martingale -1.07 puede consumir su Stop Loss muy rápidamente.</strong>
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Valor Inicial de la Orden</h3>
              <div className="border border-success/30 rounded-lg p-4">
                <h4 className="font-medium text-success mb-2">Recomendado: $0.35</h4>
                <p className="text-xs text-muted-foreground">
                  Mantener este valor bajo es vital debido a la agresividad del Martingale.
                </p>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Cantidad de Ticks (Duración)</h3>
                <p className="text-sm text-muted-foreground">
                El robot internamente opera con 1 tick para "Digits Over/Under", independientemente del valor ingresado 
                aquí (la interfaz lo solicita, pero el tipo de contrato fija la duración).
                </p>
              </div>
              
            <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-6">
              <h4 className="font-medium mb-2 text-primary">Recomendación de Capital</h4>
              <p className="text-sm">
                Mínimo de $50 USD. Sin embargo, debido al Martingale EXTREMADAMENTE AGRESIVO, un capital mayor 
                ($75-$100+) es altamente recomendado para dar algún margen al Stop Loss, incluso si es conservador.
              </p>
            </div>
          </CardContent>
        </Card>;
    }
    
    if (bot.id === "10") {
      // Hunter Pro
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestão de Risco Recomendada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">🛡️ Gestão de Risco Recomendada (ESSENCIAL!)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                O Martingale é uma estratégia de <strong>ALTO RISCO</strong>. Gerencie com sabedoria!
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">🛡️ Stop Loss (Limite de Perdas)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>NUNCA OPERE SEM UM STOP LOSS!</strong>
                    <br />
                    Defina um valor pequeno em relação à sua banca total (ex: 2% a 5% por sessão).
                    <br />
                    <em>Exemplo:</em> Banca de $100, Stop Loss de $5.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">🎯 Stop Win (Meta de Lucro)</h4>
                  <p className="text-xs text-muted-foreground">
                    Defina uma meta realista, geralmente menor ou igual ao seu Stop Loss.
                    <br />
                    <em>Exemplo:</em> Stop Loss $5, Stop Win de $2 a $5.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💵 Valor da Operação Inicial</h4>
                  <p className="text-xs text-muted-foreground">
                    Comece com o valor recomendado de <strong>0.35 USD</strong>.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏱️ Quantidade de Tique-Taques</h4>
                  <p className="text-xs text-muted-foreground">
                    Para "Higher/Lower" no <code>R_100</code> com SMAs, durações entre <strong>5</strong> e <strong>15 ticks</strong> costumam ser um bom ponto de partida para testes. Ajuste conforme seus resultados.
                  </p>
                </div>
              </div>
              

              </div>
            </CardContent>
        </Card>;
    }
          
    // Default instructions for other bots
    return <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
            <Info size={18} /> Instrucciones de Uso
              </CardTitle>
            </CardHeader>
            <CardContent>
          <div className="space-y-6">
            <h3 className="font-medium">Como utilizar el {bot.name}</h3>
            
            <ol className="list-decimal list-inside space-y-4 text-sm">
              
              
              
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Gestión de Riesgos Preconfigurada</span>
                <p className="mt-1 text-muted-foreground pl-5">Configure Stop win y Stop Loss de acuerdo con su gestión de riesgos</p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Actívelo en la Cuenta Demo</span>
                <p className="mt-1 text-muted-foreground pl-5">Actívelo primero en la cuenta demo. Si después de activarlo en la cuenta demo el robot tiene una alta tasa de assertividad, significa que está en una buena sesión de mercado y puede migrar a la real.</p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Ejecute el robot</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Inicie las operaciones y monitoree el desempeño regularmente.
                </p>
              </li>
            </ol>
            

          </div>
        </CardContent>
      </Card>;
  };

  // Instructions content
  const renderBotInstructions = () => {
    if (bot.id === "10") {
      // Hunter Pro
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info size={18} /> Instrucciones de Uso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <h3 className="font-medium">🚀 Modo de Uso (Deriv Bot / Binary Bot)</h3>
              
              <ol className="list-decimal list-inside space-y-4 text-sm">
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Acceda a la plataforma</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <a href="https://track.deriv.be/_XZsgLOqstMrrhBvO3lYd_WNd7ZgqdRLk/1/" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                      Deriv Bot (DBot)
                    </a> o Binary Bot.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Inicie sesión</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Inicie sesión (Cuenta Demo o Real).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Haga clic en "Importar"</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Haga clic en "<strong>Importar</strong>" (o "Load").
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Cargue el archivo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Cargue el archivo <code>.xml</code> del <strong>Hunter Pro</strong>.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Ajuste las configuraciones</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <strong>AJUSTE LAS CONFIGURACIONES</strong> (<code>Meta Ganancia</code>, <code>Límite Pérdidas</code>, <code>Valor Inicial de la Orden</code>, <code>Cantidad de Ticks</code>) según su gestión de riesgo.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Ejecute el robot</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Haga clic en "<strong>Ejecutar</strong>" (o "Run").
                  </p>
                </li>
              </ol>
              

            </div>
          </CardContent>
        </Card>;
    }
    
    if (bot.id === "14") {
      // NexusBot
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info size={18} /> Instrucciones de Uso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <h3 className="font-medium">🚀 Modo de Uso (Deriv Bot / Binary Bot)</h3>
              
              <ol className="list-decimal list-inside space-y-4 text-sm">
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Acceda a la plataforma</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <a href="https://drive.google.com/file/d/14_70F4k4QyZg__HJXglE94QJduQvOvay/view?usp=sharing" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                      Haga clic aquí para acceder a la plataforma Deriv
                    </a>
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Inicie sesión en su cuenta</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Inicie sesión en su cuenta Deriv (Demo o Real).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Importe el robot</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    En el menú superior, haga clic en "<strong>Importar</strong>" (o "Load" en Binary Bot).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Cargue el archivo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Localice el archivo <code>.xml</code> del robot <strong>Nexus Bot</strong> en su computadora y cárguelo.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Verifique la carga</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    El robot aparecerá en el área de trabajo de la plataforma.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Configure los parámetros</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Antes de iniciar, <strong>revise y ajuste las configuraciones</strong> (<code>Meta Ganancia</code>, <code>Límite Pérdidas</code>, <code>Valor Inicial de la Orden</code>, <code>Cantidad de Ticks</code>) según su gestión de riesgo.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Ejecute el robot</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Haga clic en el botón "<strong>Ejecutar</strong>" (o "Run") para iniciar el robot.
                  </p>
                </li>
              </ol>
              

            </div>
          </CardContent>
        </Card>;
    }

    if (bot.id === "11") {
      // Quantum Bot
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info size={18} /> Instrucciones de Uso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <h3 className="font-medium">🚀 Modo de Uso (Deriv Bot / Binary Bot)</h3>
              
              <ol className="list-decimal list-inside space-y-4 text-sm">
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Acceda a la plataforma</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <a href="https://track.deriv.be/_XZsgLOqstMrrhBvO3lYd_WNd7ZgqdRLk/1/" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                      Deriv Bot (DBot)
                    </a> o Binary Bot.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Inicie sesión</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Inicie sesión en su cuenta Deriv (Demo o Real).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Importe el robot</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    En el menú superior, haga clic en "<strong>Importar</strong>" (o "Load" en Binary Bot).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Cargue el archivo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Localice el archivo <code>.xml</code> del robot <strong>Quantum Bot</strong> en su computadora y cárguelo.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Verifique la carga</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    El robot aparecerá en el área de trabajo de la plataforma.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Configure los parámetros</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    El Quantum Bot ya viene con configuraciones predefinidas: <code>Meta Ganancia</code> y <code>Límite Pérdidas</code> de $20 USD, <code>Valor Inicial de la Orden</code> de $0.35 USD, y <code>Cantidad de Ticks</code> de 1 tick. Puede ajustar estos valores según su preferencia.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Seleccione el activo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Asegúrese de seleccionar el índice sintético <strong>R_100</strong> en la plataforma, ya que este robot está optimizado específicamente para este activo.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Ejecute el robot</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Haga clic en el botón "<strong>Ejecutar</strong>" (o "Run") para iniciar el robot.
                  </p>
                </li>
              </ol>
              

              </div>
            </CardContent>
        </Card>;
    }

    // Default instructions for other bots
    return <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Info size={18} /> Instrucciones de Uso
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <h3 className="font-medium">Como utilizar el {bot.name}</h3>
            
            <ol className="list-decimal list-inside space-y-4 text-sm">
              
              
              
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Gestión de Riesgos Preconfigurada</span>
                <p className="mt-1 text-muted-foreground pl-5">Configure Stop win y Stop Loss de acuerdo con su gestión de riesgos</p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Actívelo en la Cuenta Demo</span>
                <p className="mt-1 text-muted-foreground pl-5">Actívelo primero en la cuenta demo. Si después de activarlo en la cuenta demo el robot tiene una alta tasa de assertividad, significa que está en una buena sesión de mercado y puede migrar a la real.</p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Ejecute el robot</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Inicie las operaciones y monitoree el desempeño regularmente.
                </p>
              </li>
            </ol>
            

          </div>
        </CardContent>
      </Card>;
  };
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Investment Risk Warning Banner */}
      <div className="lg:col-span-3">
        <InvestmentWarningBanner />
      </div>
      
      {/* Left Column - Main Info */}
      <div className="lg:col-span-2 space-y-6">
        {/* Header Card */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-2xl">{bot.name}</CardTitle>
                <CardDescription>{bot.description}</CardDescription>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-sm font-medium">Versión {bot.version}</span>
                <span className="text-xs text-muted-foreground">Actualizado el {new Date(bot.updatedAt).toLocaleDateString('es-ES')}</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Precisión</span>
                <span className={`text-lg font-semibold ${getAccuracyColor(bot.accuracy)}`}>{bot.accuracy}%</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Expectativa</span>
                <span className="text-lg font-semibold">{bot.expectancy}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Operaciones</span>
                <span className="text-lg font-semibold">{bot.operations.toLocaleString()}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Factor de Lucro</span>
                <span className="text-lg font-semibold">{bot.profitFactor}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Drawdown Máx</span>
                <span className="text-lg font-semibold">{bot.drawdown}%</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Nivel de Riesgo</span>
                <span className={`text-lg font-semibold px-2 py-0.5 rounded-full ${getRiskColor(bot.riskLevel)}`}>
                  {bot.riskLevel}/10
                </span>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {bot.tradedAssets.map(asset => <span key={asset} className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">
                  {asset}
                </span>)}
            </div>
            
            <div className="flex justify-between items-center">
              <div>
                <span className="flex items-center gap-1 text-sm">
                  <span className="text-xs py-1 px-2 bg-primary/10 text-primary rounded-full">
                    {bot.id === "11" || bot.strategy === "Sin Martingale" ? "Sin Martingale" : bot.strategy}
                  </span>
                  <span className="text-muted-foreground ml-2">por {bot.author}</span>
                </span>
              </div>
              <div className="flex gap-2">
                <a 
                  href="https://deriv.com/es/?referrer=&t=-VSPRsvvDZV3lsRC_ilxPmNd7ZgqdRLk&utm_campaign=MyAffiliates&utm_content=&utm_medium=affiliate&utm_source=affiliate_223442"
                  className="flex items-center gap-1 bg-gradient-to-r from-green-500 to-green-700 text-white px-4 py-2 rounded-md hover:opacity-90 transition-opacity"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <span>Abrir Broker</span>
                </a>
                {bot.id === "14" ? (
                <a 
                  href="https://drive.google.com/file/d/1y2EkNlVY3BSDbDk_4zrprEIs-gSN8x-V/view?usp=sharing"
                  className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "wolf-bot" && bot.downloadUrl ? (
                <a
                  href={bot.downloadUrl}
                  className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "apalancamiento-100x" && bot.downloadUrl ? (
                <a
                  href={bot.downloadUrl}
                  className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "12" ? (
                <a 
                  href="https://drive.google.com/file/d/1zA_tgqK8MPNM9DTiNgXkYg63qqo5c0RF/view?usp=sharing"                   className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"                  target="_blank"                   rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "10" ? (
                <a 
                  href="https://drive.google.com/file/d/1DZ6U83PvpSN0fcEMAyuUYMw4smHWjkar/view?usp=sharing"                   className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"                  target="_blank"                   rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
                            ) : bot.id === "8" ? (                <a                   href="https://drive.google.com/file/d/1cG2XqdS2POuU_z3CGcw6-zCFEQrf94XF/view?usp=sharing"                   className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"                  target="_blank"                   rel="noopener noreferrer"                >                  <Download size={16} />                  <span>Descargar</span>                </a>
              ) : bot.id === "13" ? (
                <a 
                  href="https://drive.google.com/file/d/1Umsz_dpqkev3hMV2DPNlb1blk0Dx30jI/view?usp=sharing"                   className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"                  target="_blank"                   rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "11" ? (
                <a 
                  href="https://drive.google.com/file/d/1wLaL17gPUh_q5Gb1f3SX-bUr1KhBVHnW/view?usp=sharing"                   className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"                  target="_blank"                   rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "9" ? (
                <a 
                  href="https://drive.google.com/file/d/12FQo062Uxh10MCCwohJeNC0npHrbydcJ/view?usp=sharing"                   className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"                  target="_blank"                   rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "15" ? (
                <a 
                  href="https://drive.google.com/file/d/1yIP682tCkfM0ZTb1_vOF9uxkJsTO9sa0/view?usp=sharing"
                  className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : bot.id === "16" ? (
                <a 
                  href="https://drive.google.com/file/d/1IXDg2wcI5w9rxymwVID6aycJ8QU8tgdR/view?usp=sharing"
                  className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Descargar</span>
                </a>
              ) : (
                <button className="flex items-center gap-1 bg-primary text-black px-4 py-2 rounded-md hover:bg-primary/90 transition-colors">
                  <Download size={16} />
                  <span>Descargar</span>
                </button>
              )}
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          <button onClick={() => setActiveTab('overview')} className={`px-4 py-2 ${activeTab === 'overview' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}>
            Visión General
          </button>
          <button onClick={() => setActiveTab('riskManagement')} className={`px-4 py-2 ${activeTab === 'riskManagement' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}>
            Gestión de Riesgos
          </button>
          <button onClick={() => setActiveTab('instructions')} className={`px-4 py-2 ${activeTab === 'instructions' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}>
            Instrucciones
          </button>
        </div>
        
        {/* Tab Content */}
        <div className="min-h-[400px]">
          {activeTab === 'overview' && renderBotSpecificOverview()}
          {activeTab === 'riskManagement' && renderBotSpecificRiskManagement()}
          {activeTab === 'instructions' && renderBotInstructions()}
        </div>
      </div>
      
      {/* Right Column - Additional Info */}
      <div className="space-y-6">
        {/* Accuracy Chart Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Histórico de Asertividad</CardTitle>
            <CardDescription>Desempeño del bot en los últimos 12 meses</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            <PerformanceChart data={generatePerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="" yAxisLabel="Precisión %" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Instrucciones de Uso</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-sm mb-1">Mercados</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? "Optimizado específicamente para el índice sintético R_100 de Deriv." : `Optimizado para ${bot.tradedAssets.join(', ')}.`}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Timeframes</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? "Ultra corto plazo (1-5 ticks). Ideal para contratos Run High/Run Low." : "Múltiples timeframes, de corto a medio plazo."}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Capital Recomendado</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? "Mínimo 20x el valor del Stop Loss elegido, debido al sistema Martingale." : "Depende de su tolerancia al riesgo y configuraciones."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Bots Relacionados</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {bot.id === "8" ? <>
                <li className="flex justify-between items-center">
                  <span className="text-sm">MovingAverage Crossover Pro</span>
                  <a href="/bot/1" className="text-xs text-primary hover:text-primary/80 flex items-center gap-1">
                    Ver <ArrowRight size={12} />
                  </a>
                </li>
                <li className="flex justify-between items-center">
                  <span className="text-sm">Impulso Contrário Pro</span>
                  <a href="/bot/7" className="text-xs text-primary hover:text-primary/80 flex items-center gap-1">
                    Ver <ArrowRight size={12} />
                  </a>
                </li>
                </> : <>
                <li className="flex justify-between items-center">
                  <span className="text-sm">Martingale Recovery</span>
                  <a href="#" className="text-xs text-primary hover:text-primary/80 flex items-center gap-1">
                    Ver <ArrowRight size={12} />
                  </a>
                </li>
                <li className="flex justify-between items-center">
                  <span className="text-sm">RSI Reversal</span>
                  <a href="#" className="text-xs text-primary hover:text-primary/80 flex items-center gap-1">
                    Ver <ArrowRight size={12} />
                  </a>
                </li>
                </>}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default BotDetailView;
    