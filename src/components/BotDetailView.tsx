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
                Medias Móviles Simples (SMA) y opera con contratos tipo "Runs" (Run High / Run Low).
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
              
              <div className="bg-danger/10 p-4 rounded-lg border border-danger/30">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-danger">
                  <AlertTriangle size={16} />
                  Aviso de Riesgo Elevado
                </h4>
                <p className="text-sm text-danger/80">
                  Debido a la naturaleza de la estrategia de Martingale, especialmente la forma agresiva implementada 
                  cuando las pérdidas se acumulan, este robot presenta RIESGO ELEVADO. Es imperativo que lo pruebe
                  exhaustivamente en una cuenta demo antes de considerar su uso en una cuenta real.
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
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-warning">
                  <AlertTriangle size={16} />
                  Aviso de Riesgo
                </h4>
                <p className="text-sm text-warning/80">
                  Este robot utiliza un Martingale peculiar, ya que usa un factor negativo y menor que 1 sobre la pérdida total. 
                  Esto significa que la siguiente apuesta será el 35% de la pérdida total, pero como el factor es negativo, intenta "apostar contra" 
                  la pérdida de una forma que puede no ser matemáticamente ideal para una recuperación total inmediata.
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
      return <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info size={18} /> Estrategia Explicada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                El <strong>AlphaBot</strong> es una estrategia automatizada para el Índice Sintético R_100 
                en Deriv. Opera con contratos de Dígitos Over/Under, basando sus predicciones en el análisis 
                de los últimos 10 dígitos de ticks anteriores (convertidos a un patrón binario).
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Análisis de Dígitos (Patrón Binario)</h4>
                  <p className="text-sm text-muted-foreground">
                    El robot recopila los últimos 10 dígitos finales de los precios de los ticks. Para cada dígito:
                    <ul className="list-disc list-inside mt-2">
                      <li>Si es 8 o 9, lo convierte a 1</li>
                      <li>Si es de 0 a 7, lo convierte a 0</li>
                    </ul>
                    Luego, suma estos 10 valores binarios (0s y 1s).
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Definición de la Predicción (Over/Under)</h4>
                  <p className="text-sm text-muted-foreground">
                    <ul className="list-disc list-inside">
                      <li>Suma ≥ 2: Define la "Predicción" como 6 (apuesta en OVER 6)</li>
                      <li>Suma {'<'} 2: Define la "Predicción" como 3 (apuesta en UNDER 3)</li>
                    </ul>
                    <p className="mt-2"><em>Adaptación:</em> Si un dígito específico (0-9) se repite mucho después de pérdidas, la predicción puede ser invertida y el conteo de dígitos reiniciado.</p>
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Tipo de Operación</h4>
                  <p className="text-sm text-muted-foreground">
                    <ul className="list-disc list-inside">
                      <li><strong>DIGITOVER:</strong> Gana si el último dígito es MAYOR que la "Predicción"</li>
                      <li><strong>DIGITUNDER:</strong> Gana si el último dígito es MENOR que la "Predicción"</li>
                      <li>Duración: Fijo en 1 tick</li>
                    </ul>
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Gestión de Apuesta (Martingale Agresivo)</h4>
                  <p className="text-sm text-muted-foreground">
                    <ul className="list-disc list-inside">
                      <li><strong>Después de una Ganancia:</strong> La apuesta vuelve al "Valor Inicial de la Orden"</li>
                      <li><strong>Después de una Pérdida:</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Pequeñas Pérdidas (Pérdida Total ≥ -1 USD): Siguiente apuesta = 0.35 USD</li>
                          <li>Grandes Pérdidas (Pérdida Total &lt; -1 USD): Siguiente apuesta = (Pérdida Total Acumulada * -1.07)</li>
                        </ul>
                      </li>
                    </ul>
                  </p>
                </div>
              </div>
              
              <div className="bg-danger/10 p-4 rounded-lg border border-danger/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-danger">
                  <AlertTriangle size={16} />
                  Aviso de Riesgo Extremo
                </h4>
                <p className="text-sm text-danger/80">
                  Este robot utiliza un Martingale EXTREMADAMENTE AGRESIVO que puede llevar a pérdidas rápidas. 
                  El factor de Martingale de -1.07 sobre la pérdida total acumulada es extremadamente peligroso 
                  y puede consumir su Stop Loss muy rápidamente. Es imperativo que lo pruebe 
                  exhaustivamente en una cuenta demo antes de considerar su uso en una cuenta real.
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
                  La asertividad individual es de <strong>40-50%</strong>, dependiendo de las condiciones del mercado.
                  Alcanzar el Stop Win dependerá de su meta, del payout de las operaciones Over/Under (que varían) 
                  y de la capacidad del Martingale de recuperar pérdidas.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>;
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
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-warning">
                  <AlertTriangle size={16} />
                  Consideraciones Específicas para el Nexus Bot
                </h4>
                <p className="text-sm text-warning/80">
                  El Nexus Bot utiliza un Martingale con factor <strong>-0.35</strong>, que es menos agresivo que otros bots,
                  pero aún así exige cuidado. Las operaciones de 5 minutos de duración significan que los resultados demoran más 
                  para aparecer, así que configure un Stop Loss adecuado para evitar pérdidas mientras espera el cierre de las operaciones.
                </p>
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
              
              <div className="bg-danger/10 p-4 rounded-lg border border-danger/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-danger">
                  <AlertTriangle size={16} />
                  Advertencia de Riesgo Extremo
                </h4>
                <p className="text-sm text-danger/80">
                  Este robot utiliza un factor Martingale de <strong>-1.07</strong>, que es extremadamente agresivo.
                  Además, el XBot tiene la peculiaridad de siempre comprar contratos CALL, independientemente de
                  la tendencia identificada en los indicadores, lo que puede resultar en riesgos adicionales.
                </p>
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
                    Este é o stake base para cada operação. Após perdas, o valor aumentará de acordo com o fator Martingale.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏲️ Quantidade Tique-Taques (Duração)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>1 tick</strong>
                    <br />
                    As operações são de curtíssima duração, com contratos de apenas 1 tick.
                  </p>
                </div>
              </div>
              
              <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-6">
                <h4 className="font-medium mb-2 text-primary">✅ Recomendação de Banca</h4>
                <p className="text-sm">
                  Sugerimos operar este robô com contas a partir de <strong>$50 USD</strong> para ter uma margem adequada 
                  para a estratégia de Martingale e o Stop Loss pré-configurado.
                </p>
              </div>
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 text-warning">⚠️ Importante</h4>
                <p className="text-sm">
                  Este robô utiliza um fator Martingale de <strong>1.065</strong>, que é menos agressivo que outros bots da plataforma.
                  Ainda assim, o Martingale envolve riscos crescentes. Sempre teste em conta demo antes de usar capital real.
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
              <ShieldCheck size={18} /> Gestão de Riscos Recomendada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">🛡️ Gestão de Risco Recomendada (CRUCIAL!)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                A estratégia de Martingale, especialmente a forma agressiva implementada neste robô quando as perdas se acumulam, é de <strong>ALTO RISCO</strong>.
              </p>
              
              <div className="space-y-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">🛡️ Stop Loss (Limite de Perdas)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>NUNCA opere sem um Stop Loss definido!</strong>
                    <br />
                    <strong>Recomendação:</strong> Defina um valor que represente uma pequena porcentagem do seu capital total (ex: 2% a 5% da sua banca <em>por sessão</em>).
                    <br />
                    <em>Exemplo:</em> Se sua banca é $100, um Stop Loss de $5 (5%) é um ponto de partida.
                    <br />
                    Este valor deve ser o máximo que você está disposto a perder em uma sessão de trading com este robô.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">🎯 Stop Win (Meta de Lucro)</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>Recomendação:</strong> Defina uma meta realista, geralmente menor ou igual ao seu Stop Loss.
                    <br />
                    <em>Exemplo:</em> Se seu Stop Loss é $5, um Stop Win de $2 a $5 pode ser adequado.
                    <br />
                    Atingir pequenas metas consistentemente é mais sustentável.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">💵 Valor da Operação Inicial</h4>
                  <p className="text-xs text-muted-foreground">
                    <strong>Recomendação:</strong> Use o menor valor possível que a corretora permite (ex: $0.35) ou uma porcentagem muito pequena da sua banca (ex: 0.5% a 1%).
                    <br />
                    Lembre-se que este valor pode aumentar significativamente com o Martingale.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">⏱️ Quantidade de Tique-Taques</h4>
                  <p className="text-xs text-muted-foreground">
                    Contratos "Run High/Run Low" são sensíveis à duração.
                    <br />
                    <strong>Durações menores (1-3 ticks)</strong> são mais arriscadas, mas podem ter payouts maiores e se alinham com a natureza de "escapada rápida" do preço.
                    <br />
                    <strong>Durações maiores (4-5+ ticks)</strong> dão mais tempo para o preço se mover, mas podem ter payouts diferentes e a efetividade da SMA pode variar. Teste para encontrar o ideal para <code>R_100</code>.
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
              <ShieldCheck size={18} /> Gestão de Riscos (Definida por VOCÊ!)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm">
              O AlphaBot requer que <strong>VOCÊ</strong> defina seus limites. A gestão de risco é <strong>CRUCIAL</strong>, 
              especialmente com este Martingale.
            </p>
            
            <div>
              <h3 className="font-medium mb-2">Meta Lucro (Stop Win)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define o objetivo de ganho para encerrar a sessão com lucro.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 1% a 3% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Win $0.50 a $1.50.
                    Metas menores são mais fáceis de atingir antes de ciclos de perda.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Moderado: 3% a 5% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Win $1.50 a $2.50.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Limite Perdas (Stop Loss)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define o limite máximo de perda antes que o robô pare de operar.
                <strong> NUNCA opere sem um Stop Loss definido!</strong>
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 5% a 10% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Loss $2.50 a $5.00.
                    <strong> CRÍTICO com este Martingale: Use um Stop Loss MUITO CONSERVADOR.</strong>
                  </p>
                </div>
                
                <div className="border border-warning/30 rounded-lg p-4">
                  <h4 className="font-medium text-warning mb-2">Moderado (Alto Risco): 10% a 15% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Loss $5.00 a $7.50.
                    <strong> ATENÇÃO: O Martingale -1.07 pode consumir seu Stop Loss muito rapidamente.</strong>
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Valor Inicial da Ordem</h3>
              <div className="border border-success/30 rounded-lg p-4">
                <h4 className="font-medium text-success mb-2">Recomendado: $0.35</h4>
                <p className="text-xs text-muted-foreground">
                  Manter este valor baixo é vital devido à agressividade do Martingale.
                </p>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Tique-Taques (Duração)</h3>
              <p className="text-sm text-muted-foreground">
                O robô internamente opera com 1 tick para "Digits Over/Under", independentemente do valor inserido 
                aqui (a interface solicita, mas o tipo de contrato fixa a duração).
              </p>
            </div>
            
            <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-6">
              <h4 className="font-medium mb-2 text-primary">Recomendação de Banca</h4>
              <p className="text-sm">
                Mínimo de $50 USD. No entanto, devido ao Martingale EXTREMAMENTE AGRESSIVO, uma banca maior 
                ($75-$100+) é fortemente aconselhada para dar alguma margem ao Stop Loss, mesmo que conservador.
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
              <ShieldCheck size={18} /> Gestão de Riscos Recomendada
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
              
              <div className="bg-danger/10 p-4 rounded-lg border border-danger/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-danger">
                  <AlertTriangle size={16} />
                  Aviso de Risco Elevado
                </h4>
                <p className="text-sm text-danger/80">
                  Este robô utiliza um Martingale com fator <strong>-0.5</strong>, o que significa uma estratégia de recuperação agressiva.
                  Quanto maior for seu prejuízo acumulado, maior será o próximo stake, aumentando significativamente o risco.
                  Nunca opere este robô sem um stop loss adequado.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>;
    }

    // Default instructions for other bots
    return <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Info size={18} /> Instruções de Uso
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <h3 className="font-medium">🚀 Modo de Uso (Deriv Bot / Binary Bot)</h3>
            
            <ol className="list-decimal list-inside space-y-4 text-sm">
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Acesse a plataforma</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  <a href="https://track.deriv.be/_XZsgLOqstMrrhBvO3lYd_WNd7ZgqdRLk/1/" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                    Deriv Bot (DBot)
                  </a> ou Binary Bot.
                </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Faça login</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Faça login (Conta Demo ou Real).
                </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Clique em "Importar"</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Clique em "<strong>Importar</strong>" (ou "Load").
                </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Carregue o arquivo</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Carregue o arquivo <code>.xml</code> do <strong>Hunter Pro</strong>.
                </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Ajuste as configurações</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  <strong>AJUSTE AS CONFIGURAÇÕES</strong> (<code>Meta Lucro</code>, <code>Limite Perdas</code>, <code>Valor Inicial da Ordem</code>, <code>Quantidade Tique-Taques</code>) conforme sua gestão de risco.
                </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Execute o robô</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Clique em "<strong>Executar</strong>" (ou "Run").
                </p>
              </li>
            </ol>
            
            <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
              <h4 className="font-medium mb-2 text-warning">Lembre-se</h4>
              <p className="text-sm">
                Este robô utiliza uma combinação de <strong>filtragem de dígito</strong> e <strong>cruzamento de SMAs</strong> com um Martingale agressivo.
                Sempre teste exaustivamente na conta Demo antes de considerar o uso em conta real.
                Trading automatizado envolve riscos. Nunca invista mais do que pode perder.
              </p>
            </div>
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
              <Info size={18} /> Instruções de Uso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <h3 className="font-medium">🚀 Modo de Uso (Deriv Bot / Binary Bot)</h3>
              
              <ol className="list-decimal list-inside space-y-4 text-sm">
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Acesse a plataforma</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <a href="https://track.deriv.be/_XZsgLOqstMrrhBvO3lYd_WNd7ZgqdRLk/1/" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                      Deriv Bot (DBot)
                    </a> ou Binary Bot.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Faça login</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Faça login (Conta Demo ou Real).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Clique em "Importar"</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Clique em "<strong>Importar</strong>" (ou "Load").
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Carregue o arquivo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Carregue o arquivo <code>.xml</code> do <strong>Hunter Pro</strong>.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Ajuste as configurações</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <strong>AJUSTE AS CONFIGURAÇÕES</strong> (<code>Meta Lucro</code>, <code>Limite Perdas</code>, <code>Valor Inicial da Ordem</code>, <code>Quantidade Tique-Taques</code>) conforme sua gestão de risco.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Execute o robô</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Clique em "<strong>Executar</strong>" (ou "Run").
                  </p>
                </li>
              </ol>
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 text-warning">Lembre-se</h4>
                <p className="text-sm">
                  Este robô utiliza uma combinação de <strong>filtragem de dígito</strong> e <strong>cruzamento de SMAs</strong> com um Martingale agressivo.
                  Sempre teste exaustivamente na conta Demo antes de considerar o uso em conta real.
                  Trading automatizado envolve riscos. Nunca invista mais do que pode perder.
                </p>
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
              <Info size={18} /> Instruções de Uso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <h3 className="font-medium">🚀 Modo de Uso (Deriv Bot / Binary Bot)</h3>
              
              <ol className="list-decimal list-inside space-y-4 text-sm">
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Acesse a plataforma</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    <a href="https://drive.google.com/file/d/14_70F4k4QyZg__HJXglE94QJduQvOvay/view?usp=sharing" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                      Clique aqui para acessar a plataforma Deriv
                    </a>
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Faça login na sua conta</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Faça login na sua conta Deriv (Demo ou Real).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Importe o robô</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    No menu superior, clique em "<strong>Importar</strong>" (ou "Load" no Binary Bot).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Carregue o arquivo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Localize o arquivo <code>.xml</code> do robô <strong>Nexus Bot</strong> no seu computador e carregue-o.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Verifique o carregamento</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    O robô aparecerá na área de trabalho da plataforma.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Configure os parâmetros</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Antes de iniciar, <strong>revise e ajuste as configurações</strong> (<code>Meta Lucro</code>, <code>Limite Perdas</code>, <code>Valor Inicial da Ordem</code>, <code>Quantidade Tique-Taques</code>) conforme sua gestão de risco.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Execute o robô</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Clique no botão "<strong>Executar</strong>" (ou "Run") para iniciar o robô.
                  </p>
                </li>
              </ol>
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 text-warning">Lembre-se</h4>
                <p className="text-sm">
                  O Nexus Bot opera no índice <strong>RDBEAR</strong> com operações de 5 minutos de duração e sistema de venda antecipada.
                  Este robô utiliza um Martingale específico com fator -0.35, que apesar de menos agressivo que outros bots, 
                  ainda envolve riscos significativos. Sempre teste em conta demo antes de usar em conta real.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>;
    }

    // Default instructions for other bots
    return <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Info size={18} /> Instruções de Uso
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <h3 className="font-medium">Como utilizar o {bot.name}</h3>
            
            <ol className="list-decimal list-inside space-y-4 text-sm">
              
              
              
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Gestão de Riscos Pré-Configurada</span>
                <p className="mt-1 text-muted-foreground pl-5">Configure Stop win e Stop Loss de acordo com sua gestão de riscos</p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Ative na Conta Demonstração</span>
                <p className="mt-1 text-muted-foreground pl-5">Ative na conta demo primeiro, se após ativar na conta demo o robô estiver com uma alta taxa de assertividade. Significa que está em uma boa sessão de mercado e você pode migrar para a real.</p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Execute o robô</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Inicie as operações e monitore o desempenho regularmente.
                </p>
              </li>
            </ol>
            
            <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
              <h4 className="font-medium mb-2 text-warning">Importante</h4>
              <p className="text-sm">Nunca ative na conta real, sem testar na conta demonstração. Todas as operações automatizadas envolvem risco. Retornos passados não garantem retorno futuros. Teste o bot em uma conta de demonstração antes de utilizar com capital real.</p>
            </div>
          </div>
        </CardContent>
      </Card>;
  };
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                <span className="text-sm font-medium">Versão {bot.version}</span>
                <span className="text-xs text-muted-foreground">Atualizado em {new Date(bot.updatedAt).toLocaleDateString('pt-BR')}</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Precisão</span>
                <span className={`text-lg font-semibold ${getAccuracyColor(bot.accuracy)}`}>{bot.accuracy}%</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Expectativa</span>
                <span className="text-lg font-semibold">{bot.expectancy}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Operações</span>
                <span className="text-lg font-semibold">{bot.operations.toLocaleString()}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Fator de Lucro</span>
                <span className="text-lg font-semibold">{bot.profitFactor}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Drawdown Máx</span>
                <span className="text-lg font-semibold">{bot.drawdown}%</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xs text-muted-foreground">Nível de Risco</span>
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
                    {bot.strategy}
                  </span>
                  <span className="text-muted-foreground ml-2">por {bot.author}</span>
                </span>
              </div>
              <div className="flex gap-2">
                <a 
                  href="https://deriv.com/pt?referrer=&t=-VSPRsvvDZV3lsRC_ilxPmNd7ZgqdRLk&utm_campaign=MyAffiliates&utm_content=&utm_medium=affiliate&utm_source=affiliate_223442"
                  className="flex items-center gap-1 bg-gradient-to-r from-green-500 to-green-700 text-white px-4 py-2 rounded-md hover:opacity-90 transition-opacity"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <span>Abrir Broker</span>
                </a>
                {bot.id === "14" ? (
                <a 
                  href="https://drive.google.com/file/d/14_70F4k4QyZg__HJXglE94QJduQvOvay/view" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : bot.id === "12" ? (
                <a 
                  href="https://drive.google.com/file/d/1zA_tgqK8MPNM9DTiNgXkYg63qqo5c0RF/view?usp=sharing" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : bot.id === "10" ? (
                <a 
                  href="https://drive.google.com/file/d/1DZ6U83PvpSN0fcEMAyuUYMw4smHWjkar/view?usp=sharing" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : bot.id === "8" ? (
                <a 
                  href="https://drive.google.com/file/d/12MF5CYu2PfvQ2x0A0-6A7vZuQbgbvYSY/view?usp=sharing" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : bot.id === "13" ? (
                <a 
                  href="https://drive.google.com/file/d/1Umsz_dpqkev3hMV2DPNlb1blk0Dx30jI/view?usp=sharing" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : bot.id === "11" ? (
                <a 
                  href="https://drive.google.com/file/d/1wLaL17gPUh_q5Gb1f3SX-bUr1KhBVHnW/view?usp=sharing" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : bot.id === "9" ? (
                <a 
                  href="https://drive.google.com/file/d/17LT_6PZ6rFbVMkppnBCmutn5HAf935gZ/view?usp=sharing" 
                  className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <Download size={16} />
                  <span>Download</span>
                </a>
              ) : (
                <button className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors">
                  <Download size={16} />
                  <span>Download</span>
                </button>
              )}
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          <button onClick={() => setActiveTab('overview')} className={`px-4 py-2 ${activeTab === 'overview' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}>
            Visão Geral
          </button>
          <button onClick={() => setActiveTab('riskManagement')} className={`px-4 py-2 ${activeTab === 'riskManagement' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}>
            Gestão de Riscos
          </button>
          <button onClick={() => setActiveTab('instructions')} className={`px-4 py-2 ${activeTab === 'instructions' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}>
            Instruções
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
            <CardTitle className="text-lg">Histórico de Assertividade</CardTitle>
            <CardDescription>Desempenho do bot nos últimos 12 meses</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            <PerformanceChart data={generatePerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="" yAxisLabel="Precisão %" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Instruções de Uso</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-sm mb-1">Mercados</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? "Otimizado especificamente para o índice sintético R_100 da Deriv." : `Otimizado para ${bot.tradedAssets.join(', ')}.`}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Timeframes</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? "Ultra curto prazo (1-5 ticks). Ideal para contratos Run High/Run Low." : "Múltiplos timeframes, de curto a médio prazo."}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Capital Recomendado</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? "Mínimo 20x o valor do Stop Loss escolhido, devido ao sistema Martingale." : "Depende da sua tolerância ao risco e configurações."}
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
