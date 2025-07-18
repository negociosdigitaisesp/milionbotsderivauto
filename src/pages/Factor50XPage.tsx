import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Zap, 
  Target, 
  Shield, 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  Download,
  ChartLine,
  Info,
  ShieldCheck,
  Star,
  Clock,
  DollarSign,
  BarChart3,
  Gauge,
  Award,
  CheckCircle,
  XCircle,
  PlayCircle,
  Settings,
  Eye,
  Code,
  BookOpen,
  ExternalLink,
  Users,
  Calendar,
  FileText,
  Calculator,
  Lock,
  Bot,
  TrendingDown
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useToast } from '../hooks/use-toast';
import PerformanceChart from '../components/PerformanceChart';
import CodeViewer from '../components/CodeViewer';
import { bots } from '../lib/mockData';

const InvestmentWarningBanner = () => {
  return (
    <div className="mb-8 bg-gradient-to-r from-red-500/10 via-red-500/5 to-red-500/10 border border-red-500/30 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <AlertTriangle className="text-red-500 flex-shrink-0 mt-1" size={24} />
        <div>
          <h3 className="font-bold text-red-700 dark:text-red-400 mb-2 text-lg">
            ⚠️ ALERTA MÁXIMO DE RIESGO
          </h3>
          <p className="text-red-600 dark:text-red-300 text-sm leading-relaxed">
            La estrategia de Martingale es una abordaje de riesgo exponencialmente alto. Aunque busca recuperar pérdidas y generar beneficio, 
            puede resultar en pérdidas rápidas y sustanciales, incluyendo la pérdida total e irrecuperable de su capital. Resultados pasados 
            no son garantía de beneficios futuros. Es imperativo que comience en una cuenta de demostración (DEMO) para dominar la dinámica 
            antes de arriesgar capital real.
          </p>
        </div>
      </div>
    </div>
  );
}

const Factor50XPage = () => {
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<'conservador' | 'intermedio' | 'hard'>('intermedio');
  const { toast } = useToast();
  
  // Encontrar el bot Factor50X
  const factor50XBot = bots.find(bot => bot.id === 'factor50x');

  // Información del bot Factor50X desde mockData
  const botInfo = {
    id: 'factor50x',
    name: 'Factor50X',
    description: 'Bot avanzado de apalancamiento 50x especializado en análisis de momentum y volatilidad. Combina indicadores técnicos sofisticados con gestión inteligente de riesgo para maximizar oportunidades en mercados de alta frecuencia.',
    strategy: 'Momentum & Volatilidad',
    accuracy: 87.2,
    operations: 0,
    version: '1.0.0',
    author: 'Factor Trading Systems',
    profitFactor: 2.8,
    expectancy: 38.5,
    drawdown: 24.2,
    riskLevel: 9,
    tradedAssets: ['R_100', 'R_75', 'Volatility_Index'],
    downloadUrl: 'https://drive.google.com/file/d/1FUH0Hf4rwVxhdt7L7M9o22pRn-uxON7v/view?usp=sharing'
  };

  if (!factor50XBot) {
    return (
      <div className="container max-w-7xl mx-auto py-8 px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Bot no encontrado</h1>
          <Link to="/bots-apalancamiento" className="text-primary hover:text-primary/80">
            Volver a Bots de Apalancamiento
          </Link>
        </div>
      </div>
    );
  }

  // Generate performance data
  const generatePerformanceData = (baseAccuracy: number) => {
    const data = [];
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    let currentValue = baseAccuracy;
    for (let i = 0; i < 12; i++) {
      const variation = Math.floor(Math.random() * 7) - 3;
      currentValue = Math.max(75, Math.min(95, baseAccuracy + variation));
      data.push({
        date: months[i],
        value: currentValue
      });
    }
    return data;
  };

  // Configuraciones de riesgo dinamicas
  const riskConfigurations = {
    conservador: {
      title: 'Nivel 1: Gestión Conservadora',
      description: 'Para quienes están comenzando, poseen un capital inicial menor (ej: $30) y priorizan la supervivencia en el mercado por encima de beneficios rápidos.',
      idealFor: 'Principiantes, cuentas pequeñas ($30-$100)',
      potentialGain: 'Moderado',
      drawdownLevel: 'Bajo',
      volatilityTolerance: 'Limitada',
      color: 'emerald',
      url: 'https://drive.google.com/file/d/1TDEHyAJAbRb2UklYfVWbebn95sK4iIwF/view?usp=sharing',
      martingaleFactor: 2.4,
      stopLoss: 19.67,
      stopWin: 4.00,
      idealCapital: '$30+',
      audience: 'Principiantes, cuentas pequeñas ($30-$100), traders que priorizan la preservación del capital.',
      riskLevel: 'EXTREMO (para la cuenta mínima)',
      entries: [
        { level: 1, value: 0.35, risk: 0.35 },
        { level: 2, value: 0.84, risk: 1.19 },
        { level: 3, value: 2.02, risk: 3.21 },
        { level: 4, value: 4.84, risk: 8.05 },
        { level: 5, value: 11.62, risk: 19.67 },
        { level: 6, value: 'NO PERMITIDA', risk: 'TRAVA DE SEGURIDAD MÁXIMA' }
      ],
      explanation: 'Utiliza el factor estándar del robot (~2.4) con un límite de 5 entradas totales. El enfoque es evitar las entradas de valor más alto que pueden agotar una cuenta pequeña rápidamente.'
    },
    intermedio: {
      title: 'Nivel 2: Gestión Intermedia',
      description: 'Para operadores con más experiencia y capital, que buscan metas de beneficio diarias elevadas y comprenden el riesgo proporcionalmente mayor.',
      idealFor: 'Traders con experiencia, cuentas medianas ($120+)',
      potentialGain: 'Alto',
      drawdownLevel: 'Moderado',
      volatilityTolerance: 'Equilibrada',
      color: 'yellow',
      url: 'https://drive.google.com/file/d/1kSjL11iJ5CisATXhiAEoR_xQTqy_zLy2/view?usp=sharing',
      martingaleFactor: 2.5,
      stopLoss: 22.68,
      stopWin: 50.00,
      idealCapital: '$120+',
      audience: 'Traders con experiencia, cuentas medianas ($120-$500), buscan equilibrio riesgo-retorno.',
      riskLevel: 'MUY ALTO',
      entries: [
        { level: 1, value: 0.35, risk: 0.35 },
        { level: 2, value: 0.88, risk: 1.23 },
        { level: 3, value: 2.20, risk: 3.43 },
        { level: 4, value: 5.50, risk: 8.93 },
        { level: 5, value: 13.75, risk: 22.68 },
        { level: 6, value: 'NO PERMITIDA', risk: 'TRAVA DE SEGURIDAD MÁXIMA' }
      ],
      explanation: 'Aumentamos el factor de multiplicación para 2.5, lo que acelera el valor de las entradas. El Stop Win es agresivo ($50), exigiendo un tiempo de operación mayor y, consecuentemente, aumentando la exposición al riesgo de un ciclo de pérdidas.'
    },
    hard: {
      title: 'Nivel 3: Gestión Arriesgada',
      description: 'Exclusivamente para operadores profesionales con capital sustancial que pueden asumir pérdidas significativas. Configuración de "todo o nada" para intentar un apalancamiento rápido.',
      idealFor: 'Traders profesionales, cuentas grandes ($1000+)',
      potentialGain: 'Muy Alto',
      drawdownLevel: 'Alto',
      volatilityTolerance: 'Máxima',
      color: 'red',
      url: 'https://drive.google.com/file/d/1-rEBgpWlq30Fdi-FSHCiTpnvPLTxggYk/view?usp=sharing',
      martingaleFactor: 6.1,
      stopLoss: 94.78,
      stopWin: 100.00,
      idealCapital: '$1000+',
      audience: 'Traders experimentados, cuentas grandes ($1000+), alta tolerancia al riesgo.',
      riskLevel: '"TODO O NADA" / PROFESIONAL',
      entries: [
        { level: 1, value: 0.35, risk: 0.35 },
        { level: 2, value: 2.13, risk: 2.48 },
        { level: 3, value: 13.00, risk: 15.48 },
        { level: 4, value: 79.30, risk: 94.78 },
        { level: 5, value: 'NO PERMITIDA', risk: 'TRAVA DE SEGURIDAD ACTIVADA' }
      ],
      explanation: 'La progresión es explosiva (0.35 -> 2.13 -> 13.00...). Para mantener la pérdida máxima por debajo de $200, es fundamental limitar el número de entradas, pues el valor de la 5ª entrada por sí sola ya superaría ese límite.'
    }
  };

  const handleDownload = () => {
    const config = riskConfigurations[selectedRiskLevel];
    toast({
      title: "Descarga iniciada",
      description: `Descargando configuración ${config.title} de Factor50X`,
      duration: 3000
    });
    window.open(config.url, '_blank');
  };

  return (
    <div className="container max-w-7xl mx-auto py-8 px-4 space-y-8">
      <div className="flex items-center gap-4 mb-8">
        <Link 
          to="/bots-apalancamiento" 
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={20} />
          <span>Volver a Bots de Apalancamiento</span>
        </Link>
      </div>

      <InvestmentWarningBanner />

      {/* Bot Information Header */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-zinc-900 rounded-2xl p-8 text-white mb-8">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/20 rounded-xl">
              <Bot className="h-8 w-8 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-2">{botInfo.name}</h1>
              <p className="text-zinc-300 text-lg">{botInfo.strategy}</p>
            </div>
          </div>
          <Badge variant="destructive" className="text-sm px-3 py-1">
            Riesgo Nivel {botInfo.riskLevel}/10
          </Badge>
        </div>
        
        <p className="text-zinc-200 mb-6 leading-relaxed">
          {botInfo.description}
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-black/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="h-4 w-4 text-green-400" />
              <span className="text-sm text-zinc-400">Precisión</span>
            </div>
            <p className="text-xl font-bold text-green-400">{botInfo.accuracy}%</p>
          </div>
          <div className="bg-black/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-blue-400" />
              <span className="text-sm text-zinc-400">Factor Profit</span>
            </div>
            <p className="text-xl font-bold text-blue-400">{botInfo.profitFactor}</p>
          </div>
          <div className="bg-black/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-yellow-400" />
              <span className="text-sm text-zinc-400">Expectativa</span>
            </div>
            <p className="text-xl font-bold text-yellow-400">{botInfo.expectancy}%</p>
          </div>
          <div className="bg-black/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-4 w-4 text-red-400" />
              <span className="text-sm text-zinc-400">Drawdown</span>
            </div>
            <p className="text-xl font-bold text-red-400">{botInfo.drawdown}%</p>
          </div>
        </div>
      </div>

      {/* Configuraciones Disponibles - Destacado al frente */}
      <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10 mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-2xl">
            <Shield className="h-6 w-6 text-primary" />
            Configuraciones Disponibles
          </CardTitle>
          <CardDescription className="text-lg">
            Selecciona el nivel de riesgo que mejor se adapte a tu perfil de trading
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Segmented Control */}
          <div className="bg-[#1C1C1E] rounded-lg p-1">
            <div className="grid grid-cols-3 gap-1">
              {Object.keys(riskConfigurations).map((level) => (
                <button
                  key={level}
                  onClick={() => setSelectedRiskLevel(level as 'conservador' | 'intermedio' | 'hard')}
                  className={`
                    py-3 px-4 rounded-md text-sm font-medium transition-all
                    ${selectedRiskLevel === level
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted/50'
                    }
                  `}
                >
                  {level === 'conservador' ? 'Conservador' : level === 'intermedio' ? 'Intermedio' : 'Arriesgado'}
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Content */}
          <div className="space-y-6">
            <div className="flex items-start gap-3">
              <div className={`p-3 rounded-lg ${
                selectedRiskLevel === 'conservador' ? 'bg-green-100 text-green-600' :
                selectedRiskLevel === 'intermedio' ? 'bg-yellow-100 text-yellow-600' :
                'bg-red-100 text-red-600'
              }`}>
                {selectedRiskLevel === 'conservador' ? <Shield className="h-6 w-6" /> :
                 selectedRiskLevel === 'intermedio' ? <Target className="h-6 w-6" /> :
                 <Zap className="h-6 w-6" />}
              </div>
              <div>
                <h3 className="font-semibold text-xl">{riskConfigurations[selectedRiskLevel].title}</h3>
                <p className="text-muted-foreground text-lg">{riskConfigurations[selectedRiskLevel].description}</p>
              </div>
            </div>

            {/* Key Metrics - Destacados */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
                <DollarSign className="h-6 w-6 mx-auto mb-2 text-green-600" />
                <p className="text-sm text-green-700 font-medium">Capital Ideal</p>
                <p className="font-bold text-xl text-green-800">{riskConfigurations[selectedRiskLevel].idealCapital}</p>
              </div>
              <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
                <AlertTriangle className="h-6 w-6 mx-auto mb-2 text-red-600" />
                <p className="text-sm text-red-700 font-medium">Stop Loss</p>
                <p className="font-bold text-xl text-red-800">${riskConfigurations[selectedRiskLevel].stopLoss}</p>
              </div>
              <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                <Target className="h-6 w-6 mx-auto mb-2 text-blue-600" />
                <p className="text-sm text-blue-700 font-medium">Stop Win</p>
                <p className="font-bold text-xl text-blue-800">${riskConfigurations[selectedRiskLevel].stopWin}</p>
              </div>
              <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
                <TrendingUp className="h-6 w-6 mx-auto mb-2 text-purple-600" />
                <p className="text-sm text-purple-700 font-medium">Factor Martingale</p>
                <p className="font-bold text-xl text-purple-800">{riskConfigurations[selectedRiskLevel].martingaleFactor}</p>
              </div>
            </div>

            {/* Configuration Table */}
            <div className="bg-muted/50 rounded-lg p-6">
              <h4 className="font-semibold text-lg mb-4 flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Tabla de Entradas y Riesgos
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#3A3A3C]">
                      <th className="text-left py-2 px-2">Nivel (Error)</th>
                      <th className="text-left py-2 px-2">Valor de Entrada</th>
                      <th className="text-left py-2 px-2">Pérdida Acumulada (Riesgo Máximo)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskConfigurations[selectedRiskLevel].entries.map((entry, index) => (
                      <tr key={index} className="border-b border-[#3A3A3C] last:border-0">
                        <td className="py-2 px-2">{index + 1}ª Entrada</td>
                        <td className="py-2 px-2">
                          {typeof entry.value === 'number' ? `$${entry.value.toFixed(2)}` : entry.value}
                        </td>
                        <td className="py-2 px-2">
                          {typeof entry.risk === 'number' ? `$${entry.risk.toFixed(2)}` : entry.risk}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Download Button - Prominente */}
            <div className="flex justify-center pt-6">
              <button
                onClick={handleDownload}
                className="px-12 py-4 text-xl font-semibold bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg rounded-lg text-primary-foreground flex items-center gap-3 transition-all"
              >
                <Download className="h-6 w-6" />
                Descargar {riskConfigurations[selectedRiskLevel].title}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Tabs defaultValue="strategy" className="lg:col-span-3">
          <TabsList className="grid grid-cols-3 rounded-xl bg-background p-1">
            <TabsTrigger value="strategy">Estrategia</TabsTrigger>
            <TabsTrigger value="instructions">Instrucciones</TabsTrigger>
            <TabsTrigger value="code">Código</TabsTrigger>
          </TabsList>

          <TabsContent value="strategy" className="space-y-6">
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-zinc-900 p-8 text-white">
              <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-transparent"></div>
              <div className="relative z-10">
                <h2 className="text-2xl font-bold mb-4">Factor50X - Bot de Apalancamiento 50x</h2>
                <p className="text-zinc-200 mb-4">
                  Creemos que el conocimiento es la herramienta más poderosa de un inversor. Esta guía fue meticulosamente diseñada para que comprenda a fondo nuestra estrategia y pueda configurar el robot de acuerdo con su perfil de riesgo y sus objetivos financieros.
                </p>
                <div className="mt-6">
                  <h3 className="text-xl font-semibold mb-3">Los 4 Pilares de Su Estrategia</h3>
                  <ul className="space-y-2">
                    <li className="flex items-start gap-2">
                      <DollarSign className="h-5 w-5 text-primary mt-0.5" />
                      <span><strong>Entrada Inicial:</strong> El valor base con que el robot inicia cada ciclo ($0,35).</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <TrendingUp className="h-5 w-5 text-primary mt-0.5" />
                      <span><strong>Factor de Martingale:</strong> El multiplicador agresivo que eleva el valor de la operación tras una pérdida.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Shield className="h-5 w-5 text-primary mt-0.5" />
                      <span><strong>Stop Loss (Límite de Pérdida Diario):</strong> Su seguro. Es la pérdida máxima que acepta en un día. Al ser alcanzado, el robot PARA inmediatamente.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Target className="h-5 w-5 text-primary mt-0.5" />
                      <span><strong>Stop Win (Meta de Beneficio Diario):</strong> Su objetivo de ganancias. Al ser alcanzado, el robot PARA para garantizar los beneficios del día.</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>


          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Factor50XPage;