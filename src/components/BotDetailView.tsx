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
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
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
        date: `Dia ${i}`,
        value: currentValue
      });
    }
    return data;
  };

  // Special content for SMA Trend Runner Pro
  const renderBotSpecificOverview = () => {
    if (bot.id === "8") {
      // SMA Trend Runner Pro
      return <div className="space-y-6">
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
              <div className="mb-8">
                <h4 className="font-medium mb-4">Precisão por Operação</h4>
                <div className="grid grid-cols-1 gap-8">
                  <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Assertividade Diária" yAxisLabel="Precisão %" />
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  A assertividade individual é de <strong>40-55%</strong>, dependendo das condições do mercado.
                  O objetivo do Martingale NÃO é aumentar a taxa de acerto individual, mas sim aumentar 
                  a probabilidade de fechar uma sessão com lucro.
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
            <div className="mb-8">
              <h4 className="font-medium mb-4">Precisão por Operação</h4>
              <div className="grid grid-cols-1 gap-8">
                <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Assertividade Diária" yAxisLabel="Precisão %" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>;
  };

  // Special content for SMA Trend Runner Pro risk management
  const renderBotSpecificRiskManagement = () => {
    if (bot.id === "8") {
      // SMA Trend Runner Pro
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestão de Riscos Recomendada
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
        </Card>;
    }

    // Default risk management for other bots
    return <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <ShieldCheck size={18} /> Gestão de Riscos Recomendada
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-secondary/50 p-4 rounded-lg">
            <h4 className="font-medium mb-2">Valor del Operacão </h4>
            <p className="text-sm text-muted-foreground">Recomendamos colocar 0.35 como valor inicial</p>
          </div>
          
          <div>
            <h3 className="font-medium mb-2">Stop Loss Recomendado</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border border-success/30 rounded-lg p-4">
                <h4 className="font-medium text-success mb-2">Conservador</h4>
                <p className="text-xs text-muted-foreground">
                  2-5% da sua banca por sessão de trading.
                </p>
              </div>
              
              <div className="border border-primary/30 rounded-lg p-4">
                <h4 className="font-medium text-primary mb-2">Moderado</h4>
                <p className="text-xs text-muted-foreground">
                  5-8% da sua banca por sessão de trading.
                </p>
              </div>
              
              <div className="border border-warning/30 rounded-lg p-4">
                <h4 className="font-medium text-warning mb-2">Agressivo</h4>
                <p className="text-xs text-muted-foreground">
                  8-10% da sua banca por sessão de trading.
                </p>
              </div>
            </div>
          </div>
          
          <div>
            <h3 className="font-medium mb-2">Stop Win Recomendado</h3>
            <p className="text-sm text-muted-foreground mb-2">
              Defina uma meta realista para garantir lucros consistentes.
            </p>
            <div className="border border-primary/30 rounded-lg p-4">
              <p className="text-xs text-muted-foreground">
                Recomendamos definir uma meta de lucro diária entre 3-8% da sua banca,
                dependendo do seu perfil de risco. Quando atingida, encerre as operações
                para o dia para proteger seus ganhos.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>;
  };

  // Instructions content
  const renderBotInstructions = () => {
    if (bot.id === "8") {
      // SMA Trend Runner Pro
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info size={18} /> Instruções de Uso
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <h3 className="font-medium">Passo a Passo para Operar com o {bot.name}</h3>
              
              <ol className="list-decimal list-inside space-y-4 text-sm">
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Preparação da Plataforma</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Acesse a plataforma Deriv Bot (DBot) ou Binary Bot e faça login na sua conta.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Importação do Robô</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Clique em "Importar" no menu superior e selecione o arquivo .xml do robô SMA Trend Runner Pro.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Configuração dos Parâmetros</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Defina o Stop Loss, Stop Win e Valor Inicial conforme recomendações da aba "Gestão de Riscos".
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Seleção do Ativo</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Selecione o ativo R_100 (Índice Sintético 100) da lista de ativos disponíveis.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Definição da Duração</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Configure a duração do contrato em ticks (recomendado: 1-5 ticks).
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Execução do Robô</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Clique em "Executar" para iniciar as operações automatizadas.
                  </p>
                </li>
                
                <li className="p-3 bg-secondary/20 rounded-lg">
                  <span className="font-medium">Monitoramento</span>
                  <p className="mt-1 text-muted-foreground pl-5">
                    Acompanhe o desempenho do robô e esteja pronto para intervir se necessário.
                  </p>
                </li>
              </ol>
              
              <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-4">
                <h4 className="font-medium mb-2 text-primary">Dica Profissional</h4>
                <p className="text-sm">
                  Recomendamos começar com uma conta demonstração para familiarizar-se com o comportamento
                  do robô em diferentes condições de mercado antes de usar capital real.
                </p>
              </div>
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 text-warning">Lembre-se</h4>
                <p className="text-sm">
                  Trading automatizado envolve riscos. Mesmo com as melhores configurações,
                  perdas são possíveis. Nunca invista mais do que pode perder e sempre use
                  os limites de Stop Loss recomendados.
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
                <span className="font-medium">Defina sua Meta de Lucro</span>
                <p className="mt-1 text-muted-foreground pl-5">Configure seu objetivo de lucro para a sessão de trading. </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Defina o Stop Loss</span>
                <p className="mt-1 text-muted-foreground pl-5">
                  Configure um limite de perdas conforme seu perfil de risco.
                </p>
              </li>
              
              <li className="p-3 bg-secondary/20 rounded-lg">
                <span className="font-medium">Defina o Valor Inicial</span>
                <p className="mt-1 text-muted-foreground pl-5">Recomendamos colocar 0.35</p>
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
  return <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
              <button className="flex items-center gap-1 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90 transition-colors">
                <Download size={16} />
                <span>Download</span>
              </button>
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
    </div>;
};
export default BotDetailView;