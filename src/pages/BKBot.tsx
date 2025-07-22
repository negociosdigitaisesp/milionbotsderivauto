import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Bot, Shield, Target, TrendingUp, Clock, Star, Award, ChartLine } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const BKBot = () => {
  const navigate = useNavigate();

  const handleDownload = () => {
    window.open('https://drive.google.com/file/d/14-IUlPjA2N5Pi-_CpJ5K-YLKUiGni8kR/view?usp=sharing', '_blank');
  };

  const handleBack = () => {
    navigate('/');
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <Button 
          variant="ghost" 
          onClick={handleBack}
          className="mb-4 hover:bg-primary/10"
        >
          <ArrowLeft size={16} className="mr-2" />
          Volver a la Biblioteca
        </Button>
        
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-slate-900 via-slate-700 to-zinc-600 flex items-center justify-center">
            <Bot className="text-white" size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground">BK BOT 1.0</h1>
            <p className="text-muted-foreground">Bot de Trading Avanzado con Análisis de Patrones</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Target className="text-primary" size={20} />
                <div>
                  <p className="text-sm text-muted-foreground">Precisión</p>
                  <p className="text-xl font-bold text-success">78.5%</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="text-primary" size={20} />
                <div>
                  <p className="text-sm text-muted-foreground">Operaciones</p>
                  <p className="text-xl font-bold">2,847</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Shield className="text-primary" size={20} />
                <div>
                  <p className="text-sm text-muted-foreground">Riesgo</p>
                  <Badge variant="outline" className="text-warning border-warning/30">Medio</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Clock className="text-primary" size={20} />
                <div>
                  <p className="text-sm text-muted-foreground">Timeframe</p>
                  <p className="text-xl font-bold">1m - 5m</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Bot Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot size={20} />
                Descripción del Bot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground leading-relaxed">
                El <strong>BK BOT 1.0</strong> es un sistema de trading automatizado diseñado para operar en mercados de alta volatilidad. 
                Utiliza algoritmos avanzados de análisis de patrones y gestión de riesgo adaptativa para maximizar las oportunidades de trading.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Star className="text-primary" size={16} />
                    Características Principales
                  </h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Análisis de patrones en tiempo real</li>
                    <li>• Sistema Martingale adaptativo</li>
                    <li>• Gestión automática de riesgo</li>
                    <li>• Pausa inteligente por volatilidad</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Award className="text-primary" size={16} />
                    Activos Recomendados
                  </h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Volatility 75 Index</li>
                    <li>• Volatility 100 Index</li>
                    <li>• Boom 1000 Index</li>
                    <li>• Crash 1000 Index</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Strategy Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ChartLine size={20} />
                Estrategia de Trading
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-primary mb-2">🎯 Análisis de Patrones</h4>
                  <p className="text-sm text-muted-foreground">
                    El bot analiza patrones de precios históricos y identifica oportunidades de entrada basadas en 
                    tendencias de corto plazo y reversiones de mercado.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-primary mb-2">⚖️ Gestión de Riesgo</h4>
                  <p className="text-sm text-muted-foreground">
                    Implementa un sistema de martingale adaptativo que ajusta el tamaño de las posiciones según 
                    el rendimiento reciente y las condiciones del mercado.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-primary mb-2">🛡️ Protección de Capital</h4>
                  <p className="text-sm text-muted-foreground">
                    Sistema de pausa automática que detiene el trading durante períodos de alta volatilidad 
                    o después de una secuencia de pérdidas para proteger el capital.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Download Section */}
        <div className="space-y-6">
          {/* Download Card */}
          <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
            <CardHeader className="text-center">
              <CardTitle className="text-xl">Descargar BK BOT 1.0</CardTitle>
              <CardDescription>
                Obtén acceso completo al bot y comienza a operar
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center space-y-4">
                <div className="w-20 h-20 mx-auto rounded-full bg-primary/20 flex items-center justify-center">
                  <Download className="text-primary" size={32} />
                </div>
                
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Archivo incluye:
                  </p>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    <li>• Código fuente del bot</li>
                    <li>• Manual de instalación</li>
                    <li>• Configuraciones recomendadas</li>
                    <li>• Guía de uso paso a paso</li>
                  </ul>
                </div>
                
                <Button 
                  onClick={handleDownload}
                  className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-3"
                  size="lg"
                >
                  <Download size={20} className="mr-2" />
                  Descargar
                </Button>
                
                <p className="text-xs text-muted-foreground">
                  Compatible con Deriv Bot y Binary Bot
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Requirements Card */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Requisitos</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Plataforma:</h4>
                <p className="text-sm text-muted-foreground">Deriv Bot / Binary Bot</p>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Capital Mínimo:</h4>
                <p className="text-sm text-muted-foreground">$100 USD recomendado</p>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Experiencia:</h4>
                <p className="text-sm text-muted-foreground">Principiante a Intermedio</p>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Tiempo de Configuración:</h4>
                <p className="text-sm text-muted-foreground">5-10 minutos</p>
              </div>
            </CardContent>
          </Card>

          {/* Warning Card */}
          <Card className="border-warning/20 bg-warning/5">
            <CardHeader>
              <CardTitle className="text-lg text-warning flex items-center gap-2">
                <Shield size={18} />
                Aviso Importante
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                El trading automatizado conlleva riesgos. Asegúrate de entender completamente 
                el funcionamiento del bot y nunca inviertas más de lo que puedes permitirte perder.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default BKBot;