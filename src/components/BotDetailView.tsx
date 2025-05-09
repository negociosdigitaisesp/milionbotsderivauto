
import React, { useState } from 'react';
import { ArrowRight, Download, ShieldCheck, ChartLine, Info, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import CodeViewer from './CodeViewer';
import { Bot } from '../lib/mockData';

interface BotDetailViewProps {
  bot: Bot;
}

const BotDetailView = ({ bot }: BotDetailViewProps) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'settings' | 'code'>('overview');
  
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

  // Special content for SMA Trend Runner Pro
  const renderBotSpecificOverview = () => {
    if (bot.id === "8") { // SMA Trend Runner Pro
      return (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info size={18} /> Estratégia Explicada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                O robô <strong>SMA Trend Runner Pro</strong> é projetado para o mercado de Índices Sintéticos (R_100) 
                na Deriv. Ele identifica tendências de curtíssimo prazo usando o cruzamento de 
                Médias Móveis Simples (SMA) e opera com contratos do tipo "Runs" (Run High / Run Low).
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Análise de Tendência (SMA)</h4>
                  <p className="text-sm text-muted-foreground">
                    O robô utiliza duas SMAs: uma <strong>Rápida</strong> (período 1) e uma 
                    <strong> Lenta</strong> (período 20). Quando a SMA Rápida cruza acima da SMA Lenta, 
                    ele compra um contrato <strong>RUNHIGH</strong>. Quando cruza abaixo, 
                    compra um contrato <strong>RUNLOW</strong>.
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Sistema de Martingale Especializado</h4>
                  <p className="text-sm text-muted-foreground">
                    Após uma perda, o robô utiliza uma lógica de recuperação especial:
                    se o prejuízo total for pequeno, usa stake fixo de <strong>0.35</strong>; 
                    se for significativo, calcula o próximo stake como <strong>prejuízo total × -0.45</strong>.
                  </p>
                </div>
              </div>
              
              <div className="bg-danger/10 p-4 rounded-lg border border-danger/30">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-danger">
                  <AlertTriangle size={16} />
                  Aviso de Risco Elevado
                </h4>
                <p className="text-sm text-danger/80">
                  Devido à natureza da estratégia de Martingale, especialmente a forma agressiva implementada 
                  quando as perdas se acumulam, este robô apresenta RISCO ELEVADO. É imperativo que você teste
                  exaustivamente em uma conta demonstração antes de considerar o uso em uma conta real.
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ChartLine size={18} /> Performance Esperada
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <h4 className="font-medium mb-2">Precisão por Operação</h4>
                <div className="w-full bg-secondary rounded-full h-4">
                  <div 
                    className="bg-primary h-4 rounded-full" 
                    style={{ width: `${bot.accuracy}%` }}
                  >
                  </div>
                </div>
                <div className="flex justify-between mt-1 text-xs">
                  <span>0%</span>
                  <span className={getAccuracyColor(bot.accuracy)}>
                    {bot.accuracy}% (Assertividade média)
                  </span>
                  <span>100%</span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  A assertividade individual é de <strong>40-55%</strong>, dependendo das condições do mercado.
                  O objetivo do Martingale NÃO é aumentar a taxa de acerto individual, mas sim aumentar 
                  a probabilidade de fechar uma sessão com lucro.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    // Default content for other bots
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info size={18} /> Estratégia Explicada
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              O robô <strong>{bot.name}</strong> utiliza uma estratégia de {bot.strategy} 
              para operar nos mercados.
            </p>
            
            <div className="bg-secondary/50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Detalhes da Estratégia</h4>
              <p className="text-sm text-muted-foreground">
                {bot.description}
              </p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ChartLine size={18} /> Performance Esperada
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <h4 className="font-medium mb-2">Precisão por Operação</h4>
              <div className="w-full bg-secondary rounded-full h-4">
                <div 
                  className="bg-primary h-4 rounded-full" 
                  style={{ width: `${bot.accuracy}%` }}
                >
                </div>
              </div>
              <div className="flex justify-between mt-1 text-xs">
                <span>0%</span>
                <span className={getAccuracyColor(bot.accuracy)}>
                  {bot.accuracy}% (Assertividade média)
                </span>
                <span>100%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  // Special content for SMA Trend Runner Pro settings
  const renderBotSpecificSettings = () => {
    if (bot.id === "8") { // SMA Trend Runner Pro
      return (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Configurações Recomendadas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="font-medium mb-2">Stop Loss (Limite de Perdas)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define o limite máximo de perda antes que o robô pare de operar.
                <strong> NUNCA opere sem um Stop Loss definido!</strong>
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: $3 - $5</h4>
                  <p className="text-xs text-muted-foreground">
                    Para bancas menores ou para quem quer testar com risco mais baixo.
                    Defina de 2% a 5% da sua banca.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Moderado: $5 - $10</h4>
                  <p className="text-xs text-muted-foreground">
                    Um equilíbrio entre segurança e permitir sequências de recuperação.
                    Não mais de 10% da sua banca.
                  </p>
                </div>
                
                <div className="border border-warning/30 rounded-lg p-4">
                  <h4 className="font-medium text-warning mb-2">Agressivo: $10 - $15</h4>
                  <p className="text-xs text-muted-foreground">
                    Maior risco, mas maior chance de recuperação em sequências negativas.
                    Não recomendado para iniciantes.
                  </p>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Stop Win (Meta de Lucro)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define o objetivo de lucro para encerrar as operações. Garante que o robô 
                pare quando estiver no lucro, evitando a devolução de ganhos.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: $1 - $3</h4>
                  <p className="text-xs text-muted-foreground">
                    Rápido de atingir, garante pequenos lucros frequentes.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Moderado: $3 - $5</h4>
                  <p className="text-xs text-muted-foreground">
                    Um bom alvo para uma sessão de operações.
                  </p>
                </div>
                
                <div className="border border-warning/30 rounded-lg p-4">
                  <h4 className="font-medium text-warning mb-2">Agressivo: $5 - $7</h4>
                  <p className="text-xs text-muted-foreground">
                    Requer mais tempo/operações para ser atingido.
                  </p>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Duração do Contrato (em Ticks)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Contratos "Run High/Run Low" são sensíveis à duração.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Durações Curtas: 1-3 ticks</h4>
                  <p className="text-xs text-muted-foreground">
                    Mais arriscadas, mas podem ter payouts maiores e se alinham com a natureza 
                    de "escapada rápida" do preço.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Durações Médias: 4-5+ ticks</h4>
                  <p className="text-xs text-muted-foreground">
                    Dão mais tempo para o preço se mover, mas podem ter payouts diferentes.
                    Teste para encontrar o ideal para R_100.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    // Default settings for other bots
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <ShieldCheck size={18} /> Configurações Recomendadas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-secondary/50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">Parâmetros da Estratégia</h4>
            <p className="text-sm text-muted-foreground">
              Configure os parâmetros de acordo com seu perfil de risco e objetivos de trading.
            </p>
          </div>
        </CardContent>
      </Card>
    );
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
                <span className="text-xs text-muted-foreground">Downloads</span>
                <span className="text-lg font-semibold">{bot.downloads.toLocaleString()}</span>
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
              {bot.tradedAssets.map((asset) => (
                <span key={asset} className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">
                  {asset}
                </span>
              ))}
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
              <button className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors">
                <Download size={16} />
                <span>Download</span>
              </button>
            </div>
          </CardContent>
        </Card>
        
        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          <button 
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 ${activeTab === 'overview' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}
          >
            Visão Geral
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-2 ${activeTab === 'settings' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}
          >
            Configurações
          </button>
          <button 
            onClick={() => setActiveTab('code')}
            className={`px-4 py-2 ${activeTab === 'code' ? 'border-b-2 border-primary' : 'text-muted-foreground'}`}
          >
            Código
          </button>
        </div>
        
        {/* Tab Content */}
        <div className="min-h-[400px]">
          {activeTab === 'overview' && renderBotSpecificOverview()}
          {activeTab === 'settings' && renderBotSpecificSettings()}
          {activeTab === 'code' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Código Fonte</CardTitle>
                <CardDescription>
                  {bot.id === "8" ? "Estratégia SMA para contratos Run High/Run Low com Martingale especializado" : 
                   `Estratégia de ${bot.strategy}`}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CodeViewer code={bot.code} language="javascript" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      
      {/* Right Column - Additional Info */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Aplicação Recomendada</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-sm mb-1">Mercados</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? 
                    "Otimizado especificamente para o índice sintético R_100 da Deriv." : 
                    `Otimizado para ${bot.tradedAssets.join(', ')}.`}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Timeframes</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? 
                    "Ultra curto prazo (1-5 ticks). Ideal para contratos Run High/Run Low." : 
                    "Múltiplos timeframes, de curto a médio prazo."}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Capital Recomendado</h4>
                <p className="text-xs text-muted-foreground">
                  {bot.id === "8" ? 
                    "Mínimo 20x o valor do Stop Loss escolhido, devido ao sistema Martingale." : 
                    "Depende da sua tolerância ao risco e configurações."}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Instruções de Uso</CardTitle>
          </CardHeader>
          <CardContent>
            {bot.id === "8" ? (
              <ol className="list-decimal list-inside space-y-2 text-sm">
                <li>Acesse a plataforma Deriv Bot (DBot) ou Binary Bot</li>
                <li>Importe o arquivo .xml do robô SMA Trend Runner Pro</li>
                <li>Configure os parâmetros (Stop Loss, Stop Win, Valor Inicial)</li>
                <li>Selecione o ativo R_100</li>
                <li>Defina a duração do contrato em ticks (1-5 recomendado)</li>
                <li>Clique em "Executar" para iniciar o robô</li>
                <li>Monitore o desempenho e esteja pronto para intervir se necessário</li>
              </ol>
            ) : (
              <ol className="list-decimal list-inside space-y-2 text-sm">
                <li>Configure o valor base da aposta</li>
                <li>Defina o Stop Loss conforme seu perfil de risco</li>
                <li>Defina o Stop Win conforme seu objetivo de lucro</li>
                <li>Execute nos mercados adequados</li>
                <li>Monitore as operações para garantir funcionamento adequado</li>
              </ol>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Bots Relacionados</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {bot.id === "8" ? (
                <>
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
                </>
              ) : (
                <>
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
                </>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BotDetailView;
