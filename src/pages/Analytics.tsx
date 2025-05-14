import React, { useState } from 'react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Sector
} from 'recharts';
import { ChartLine, ArrowUpRight, ArrowDownRight, ArrowUp, ArrowDown, Filter, Calendar, TrendingUp, Target, Activity, Award } from 'lucide-react';
import PerformanceChart from '../components/PerformanceChart';
import { bots, dashboardStats, performanceData } from '../lib/mockData';
import { cn } from '../lib/utils';

// Generate assertiveness data by category
const assertivenessByStrategy = [
  { name: 'Martingale', value: 58, count: 3 },
  { name: 'Grid Trading', value: 62, count: 5 },
  { name: 'Moving Average', value: 71, count: 2 },
  { name: 'Trend Following', value: 64, count: 4 },
  { name: 'RSI', value: 68, count: 3 },
  { name: 'Scalping', value: 55, count: 2 },
];

// Historical assertiveness over time periods for all bots
const historicalData = [
  { name: 'Jan', average: 52, highest: 68, lowest: 42 },
  { name: 'Fev', average: 55, highest: 70, lowest: 45 },
  { name: 'Mar', average: 59, highest: 75, lowest: 47 },
  { name: 'Abr', average: 57, highest: 72, lowest: 46 },
  { name: 'Mai', average: 61, highest: 78, lowest: 51 },
  { name: 'Jun', average: 65, highest: 82, lowest: 53 },
  { name: 'Jul', average: 68, highest: 85, lowest: 55 },
  { name: 'Ago', average: 63, highest: 81, lowest: 50 },
  { name: 'Set', average: 67, highest: 84, lowest: 54 },
  { name: 'Out', average: 71, highest: 87, lowest: 58 },
  { name: 'Nov', average: 68, highest: 86, lowest: 56 },
  { name: 'Dez', average: 72, highest: 89, lowest: 60 },
];

// Top performer data
const topPerformers = bots
  .sort((a, b) => b.accuracy - a.accuracy)
  .slice(0, 5)
  .map(bot => ({
    name: bot.name,
    accuracy: bot.accuracy,
    operations: bot.operations,
    strategy: bot.strategy
  }));

// Distribution of bot assertiveness
const botAssertiveness = [
  { name: '40-50%', value: bots.filter(bot => bot.accuracy >= 40 && bot.accuracy < 50).length },
  { name: '50-60%', value: bots.filter(bot => bot.accuracy >= 50 && bot.accuracy < 60).length },
  { name: '60-70%', value: bots.filter(bot => bot.accuracy >= 60 && bot.accuracy < 70).length },
  { name: '70-80%', value: bots.filter(bot => bot.accuracy >= 70 && bot.accuracy < 80).length },
  { name: '80-90%', value: bots.filter(bot => bot.accuracy >= 80 && bot.accuracy < 90).length },
  { name: '90-100%', value: bots.filter(bot => bot.accuracy >= 90 && bot.accuracy <= 100).length },
];

// Radar data for comparing bot capabilities
const radarData = [
  { subject: 'Assertividade', A: 85, B: 65, C: 75, fullMark: 100 },
  { subject: 'Consistência', A: 80, B: 70, C: 60, fullMark: 100 },
  { subject: 'Volume', A: 65, B: 90, C: 75, fullMark: 100 },
  { subject: 'Gestão de Risco', A: 90, B: 60, C: 75, fullMark: 100 },
  { subject: 'Rentabilidade', A: 70, B: 75, C: 80, fullMark: 100 },
  { subject: 'Adaptabilidade', A: 60, B: 80, C: 70, fullMark: 100 },
];

// Active shape for interactive pie chart
const renderActiveShape = (props: any) => {
  const RADIAN = Math.PI / 180;
  const { cx, cy, midAngle, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
  const sin = Math.sin(-RADIAN * midAngle);
  const cos = Math.cos(-RADIAN * midAngle);
  const sx = cx + (outerRadius + 10) * cos;
  const sy = cy + (outerRadius + 10) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;
  const ex = mx + (cos >= 0 ? 1 : -1) * 22;
  const ey = my;
  const textAnchor = cos >= 0 ? 'start' : 'end';

  return (
    <g>
      <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill} className="text-sm font-medium">
        {payload.name}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
      <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
      <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
      <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill="#999" className="text-xs">{`${value} bots`}</text>
      <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} dy={18} textAnchor={textAnchor} fill="#999" className="text-xs">
        {`(${(percent * 100).toFixed(2)}%)`}
      </text>
    </g>
  );
};

const Analytics = () => {
  const [activeIndex, setActiveIndex] = useState(0);

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  // Calculate overall metrics
  const averageAssertiveness = Math.round(bots.reduce((sum, bot) => sum + bot.accuracy, 0) / bots.length);
  const highestAssertiveness = Math.max(...bots.map(bot => bot.accuracy));
  const lowestAssertiveness = Math.min(...bots.map(bot => bot.accuracy));
  const totalOperations = bots.reduce((sum, bot) => sum + bot.operations, 0);

  // Monthly change in assertiveness (positive or negative)
  const monthlyChange = historicalData[historicalData.length - 1].average - historicalData[historicalData.length - 2].average;
  
  return (
    <div className="container max-w-7xl mx-auto py-8 px-4 animate-in fade-in duration-500">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Análisis de Asertividad</h1>
            <p className="text-muted-foreground">Análisis detallado del rendimiento de los bots de trading</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-card border border-border rounded-lg px-4 py-2 flex items-center gap-2">
              <Calendar size={16} className="text-muted-foreground" />
              <span className="text-sm">Últimos 12 meses</span>
            </div>
            <div className="bg-card border border-border rounded-lg px-4 py-2 flex items-center gap-2">
              <Filter size={16} className="text-muted-foreground" />
              <span className="text-sm">Todos los bots</span>
            </div>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Asertividad Media</p>
                <h3 className="text-2xl font-bold">{averageAssertiveness}%</h3>
              </div>
              <div className="p-2 bg-primary/10 rounded-lg">
                <ChartLine size={20} className="text-primary" />
              </div>
            </div>
            <div className={cn(
              "flex items-center text-xs",
              monthlyChange >= 0 ? "text-green-500" : "text-red-500"
            )}>
              {monthlyChange >= 0 ? (
                <ArrowUpRight size={14} className="mr-1" />
              ) : (
                <ArrowDownRight size={14} className="mr-1" />
              )}
              <span>{Math.abs(monthlyChange).toFixed(1)}% en relación al mes anterior</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Mejor Asertividad</p>
                <h3 className="text-2xl font-bold">{highestAssertiveness}%</h3>
              </div>
              <div className="p-2 bg-emerald-100 rounded-lg">
                <ArrowUp size={20} className="text-emerald-600" />
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              <span>Top performer: {topPerformers[0].name}</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Menor Asertividad</p>
                <h3 className="text-2xl font-bold">{lowestAssertiveness}%</h3>
              </div>
              <div className="p-2 bg-rose-100 rounded-lg">
                <ArrowDown size={20} className="text-rose-600" />
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              <span>Mejora necesaria en {bots.filter(bot => bot.accuracy === lowestAssertiveness).length} bots</span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Total de Operaciones</p>
                <h3 className="text-2xl font-bold">{totalOperations.toLocaleString()}</h3>
              </div>
              <div className="p-2 bg-primary/10 rounded-lg">
                <Activity size={20} className="text-primary" />
              </div>
            </div>
            <div className="text-xs text-muted-foreground">
              <span>Promedio de {Math.round(totalOperations / bots.length)} por bot</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Historical Assertiveness Chart */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Histórico de Asertividad</h2>
            <div className="flex items-center gap-2 text-xs">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-primary"></div>
                <span>Media</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-green-500/60"></div>
                <span>Máxima</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full bg-amber-500/60"></div>
                <span>Mínima</span>
              </div>
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={historicalData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#999' }} />
                <YAxis domain={[40, 100]} tick={{ fontSize: 12, fill: '#999' }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(24, 24, 27, 0.9)', 
                    borderColor: 'rgba(63, 63, 70, 0.5)',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }} 
                  itemStyle={{ color: '#f1f5f9' }}
                  labelStyle={{ color: '#e2e8f0', fontWeight: 'bold', marginBottom: '0.5rem' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="average"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="highest"
                  stroke="#22c55e"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="lowest"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Strategy Performance Chart */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Asertividad por Estrategia</h2>
            <div className="text-xs text-muted-foreground">
              Basado en datos de {bots.length} bots activos
            </div>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={assertivenessByStrategy}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#999' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#999' }} />
                <Tooltip
                  contentStyle={{ 
                    backgroundColor: 'rgba(24, 24, 27, 0.9)', 
                    borderColor: 'rgba(63, 63, 70, 0.5)',
                    borderRadius: '0.5rem',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value, name, props) => {
                    if (name === 'value') {
                      return [`${value}%`, 'Asertividad'];
                    }
                    return [value, name];
                  }}
                  labelFormatter={(value) => `Estrategia: ${value}`}
                />
                <Legend formatter={(value) => value === 'value' ? 'Asertividad (%)' : value} />
                <Bar 
                  dataKey="value" 
                  name="Assertividad" 
                  radius={[5, 5, 0, 0]}
                >
                  {assertivenessByStrategy.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.value >= 65 ? "var(--primary)" : 
                            entry.value >= 55 ? "#9333ea" : "#f97316"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Second Row of Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Top Performers */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-6">Top Performers</h2>
          <div className="space-y-4">
            {topPerformers.map((bot, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-full text-white font-bold text-sm",
                  index === 0 ? "bg-amber-500" : 
                  index === 1 ? "bg-zinc-400" : 
                  index === 2 ? "bg-amber-700" : "bg-primary/60"
                )}>
                  {index + 1}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">{bot.name}</h3>
                  <p className="text-xs text-muted-foreground">{bot.strategy} • {bot.operations} operaciones</p>
                </div>
                <div className={cn(
                  "text-sm font-semibold rounded-full px-3 py-1",
                  bot.accuracy >= 70 ? "bg-green-500/10 text-green-500" :
                  bot.accuracy >= 60 ? "bg-blue-500/10 text-blue-500" :
                  "bg-amber-500/10 text-amber-500"
                )}>
                  {bot.accuracy}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Distribution Chart */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Distribuição de Assertividade</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  activeIndex={activeIndex}
                  activeShape={renderActiveShape}
                  data={botAssertiveness}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  fill="var(--primary)"
                  dataKey="value"
                  onMouseEnter={onPieEnter}
                >
                  {botAssertiveness.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={
                        index === 5 ? "#10b981" : // 90-100%
                        index === 4 ? "#059669" : // 80-90%
                        index === 3 ? "#0284c7" : // 70-80%
                        index === 2 ? "#6366f1" : // 60-70%
                        index === 1 ? "#8b5cf6" : // 50-60%
                        "#f97316"                  // 40-50%
                      } 
                    />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            {botAssertiveness.map((entry, index) => (
              <div key={index} className="flex items-center gap-1 text-xs">
                <div className="w-3 h-3 rounded-full" style={{ 
                  backgroundColor: 
                    index === 5 ? "#10b981" : 
                    index === 4 ? "#059669" : 
                    index === 3 ? "#0284c7" :
                    index === 2 ? "#6366f1" :
                    index === 1 ? "#8b5cf6" :
                    "#f97316"
                }}></div>
                <span>{entry.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Radar Comparison Chart */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Análise Comparativa</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.2)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#999', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Radar name="Alpha Bot" dataKey="A" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.3} />
                <Radar name="Beta Bot" dataKey="B" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                <Radar name="Gamma Bot" dataKey="C" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
                <Legend />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(24, 24, 27, 0.9)', 
                    borderColor: 'rgba(63, 63, 70, 0.5)',
                    borderRadius: '0.5rem' 
                  }} 
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bot Performance Matrix */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Matriz de Performance</h2>
          <div className="flex items-center gap-2">
            <div className="bg-primary/10 text-primary px-3 py-1 rounded-md text-xs font-medium flex items-center gap-1">
              <Target size={14} />
              <span>Performance vs. Operações</span>
            </div>
          </div>
        </div>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <PerformanceChart 
              data={performanceData.accuracy} 
              isPositive={true}
              title="Assertividade ao Longo do Tempo"
              yAxisLabel="%"
              showAverage={true}
              animationActive={true}
            />
          </ResponsiveContainer>
        </div>
      </div>

      {/* Insights Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-6 border border-primary/20">
          <TrendingUp size={24} className="text-primary mb-4" />
          <h3 className="text-lg font-semibold mb-2">Tendencias Observadas</h3>
          <p className="text-sm text-muted-foreground mb-2">La asertividad media de los bots ha crecido en los últimos 6 meses, con un aumento del 20% en el período.</p>
          <p className="text-xs">Las estrategias de Moving Average presentaron los mejores resultados.</p>
        </div>
        
        <div className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-6 border border-primary/20">
          <Target size={24} className="text-primary mb-4" />
          <h3 className="text-lg font-semibold mb-2">Oportunidades de Mejora</h3>
          <p className="text-sm text-muted-foreground mb-2">Bots con estrategia Scalping presentan potencial para optimización, con asertividad actual del 55%.</p>
          <p className="text-xs">Recomendación: ajustar parámetros de entrada y salida.</p>
        </div>
        
        <div className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-6 border border-primary/20">
          <Award size={24} className="text-primary mb-4" />
          <h3 className="text-lg font-semibold mb-2">Próximos Pasos</h3>
          <p className="text-sm text-muted-foreground mb-2">Implementar análisis de correlación entre asertividad y rentabilidad para determinar eficiencia real.</p>
          <p className="text-xs">Desarrollar sistema de alerta para caídas en la asertividad.</p>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 