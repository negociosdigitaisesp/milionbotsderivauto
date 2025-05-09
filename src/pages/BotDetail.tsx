
import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Download, Info, Code, ChartBar, Settings, 
  Clock, ChartLine, AlertTriangle, Award, User
} from 'lucide-react';
import CodeViewer from '../components/CodeViewer';
import PerformanceChart from '../components/PerformanceChart';
import { bots, performanceData } from '../lib/mockData';
import { cn } from '../lib/utils';

const BotDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Find the bot from the mock data
  const bot = bots.find(bot => bot.id === id);
  
  if (!bot) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-4">Bot não encontrado</h2>
          <p className="text-muted-foreground mb-6">O bot que você está procurando não existe ou foi removido.</p>
          <Link 
            to="/" 
            className="flex items-center gap-2 text-primary hover:underline"
          >
            <ArrowLeft size={16} />
            Voltar para o Dashboard
          </Link>
        </div>
      </div>
    );
  }
  
  // Download Handler
  const handleDownload = () => {
    // In a real app, this would trigger a download
    alert(`Download iniciado: ${bot.name}`);
  };
  
  return (
    <div className="min-h-screen bg-background animate-fade-in">
      {/* Header with bot info */}
      <header className="bg-secondary p-6 border-b border-border/50">
        <div className="container mx-auto">
          <div className="flex items-center gap-2 mb-6">
            <Link 
              to="/" 
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft size={18} />
            </Link>
            <span className="text-muted-foreground">/</span>
            <span className="text-muted-foreground">Detalhes do Bot</span>
          </div>
          
          <div className="flex flex-col md:flex-row gap-6">
            <div className="md:w-64">
              <img 
                src={bot.imageUrl}
                alt={bot.name}
                className="w-full h-48 object-cover rounded-lg shadow-md"
              />
            </div>
            
            <div className="flex-1">
              <div className="flex flex-wrap gap-2 items-center mb-1">
                <span className="px-2 py-1 text-xs rounded-full bg-primary/10 text-primary">
                  {bot.strategy}
                </span>
                <span className="px-2 py-1 text-xs rounded-full bg-secondary text-muted-foreground border border-border/50">
                  v{bot.version}
                </span>
              </div>
              
              <h1 className="text-2xl font-bold mb-2">{bot.name}</h1>
              <p className="text-muted-foreground mb-4">{bot.description}</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="stat-card p-3">
                  <p className="text-xs text-muted-foreground">Assertividade</p>
                  <p className={cn(
                    "text-lg font-semibold",
                    bot.accuracy >= 60 ? "text-success" : 
                    bot.accuracy >= 40 ? "text-warning" : "text-danger"
                  )}>
                    {bot.accuracy}%
                  </p>
                </div>
                
                <div className="stat-card p-3">
                  <p className="text-xs text-muted-foreground">Fator de Lucro</p>
                  <p className={cn(
                    "text-lg font-semibold",
                    bot.profitFactor >= 2 ? "text-success" : 
                    bot.profitFactor >= 1.5 ? "text-warning" : "text-danger"
                  )}>
                    {bot.profitFactor}
                  </p>
                </div>
                
                <div className="stat-card p-3">
                  <p className="text-xs text-muted-foreground">Drawdown</p>
                  <p className={cn(
                    "text-lg font-semibold",
                    bot.drawdown <= 15 ? "text-success" : 
                    bot.drawdown <= 25 ? "text-warning" : "text-danger"
                  )}>
                    {bot.drawdown}%
                  </p>
                </div>
                
                <div className="stat-card p-3">
                  <p className="text-xs text-muted-foreground">Risco</p>
                  <p className={cn(
                    "text-lg font-semibold",
                    bot.riskLevel <= 3 ? "text-success" : 
                    bot.riskLevel <= 5 ? "text-warning" : "text-danger"
                  )}>
                    {bot.riskLevel}/10
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <button 
                  onClick={handleDownload}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg flex items-center gap-2 hover:bg-primary/90 transition-colors"
                >
                  <Download size={18} />
                  Download Bot
                </button>
                
                <div className="flex items-center gap-2 text-muted-foreground">
                  <User size={16} />
                  <span>Por {bot.author}</span>
                </div>
                
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock size={16} />
                  <span>Atualizado em {new Date(bot.updatedAt).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      {/* Tabs navigation */}
      <nav className="bg-secondary border-b border-border/50">
        <div className="container mx-auto">
          <div className="flex overflow-x-auto">
            <button 
              onClick={() => setActiveTab('overview')}
              className={cn(
                "px-6 py-3 border-b-2 whitespace-nowrap",
                activeTab === 'overview' 
                  ? "border-primary text-foreground" 
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-2">
                <Info size={16} />
                <span>Visão Geral</span>
              </div>
            </button>
            
            <button 
              onClick={() => setActiveTab('code')}
              className={cn(
                "px-6 py-3 border-b-2 whitespace-nowrap",
                activeTab === 'code' 
                  ? "border-primary text-foreground" 
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-2">
                <Code size={16} />
                <span>Código</span>
              </div>
            </button>
            
            <button 
              onClick={() => setActiveTab('performance')}
              className={cn(
                "px-6 py-3 border-b-2 whitespace-nowrap",
                activeTab === 'performance' 
                  ? "border-primary text-foreground" 
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-2">
                <ChartBar size={16} />
                <span>Performance</span>
              </div>
            </button>
            
            <button 
              onClick={() => setActiveTab('settings')}
              className={cn(
                "px-6 py-3 border-b-2 whitespace-nowrap",
                activeTab === 'settings' 
                  ? "border-primary text-foreground" 
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-2">
                <Settings size={16} />
                <span>Configuração</span>
              </div>
            </button>
          </div>
        </div>
      </nav>
      
      {/* Tab content */}
      <section className="py-6">
        <div className="container mx-auto">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-card rounded-lg border border-border/50 p-6">
                  <h2 className="text-lg font-semibold mb-4">Resumo da Estratégia</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium mb-2">Descrição</h3>
                      <p className="text-muted-foreground">{bot.description}</p>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium mb-2">Tipo de Estratégia</h3>
                      <div className="flex items-center gap-2">
                        <Award size={16} className="text-primary" />
                        <p>{bot.strategy}</p>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-sm font-medium mb-2">Ativos Negociados</h3>
                      <div className="flex flex-wrap gap-2">
                        {bot.tradedAssets.map((asset, index) => (
                          <span 
                            key={index}
                            className="px-2 py-1 bg-secondary text-xs rounded-full border border-border/50"
                          >
                            {asset}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-card rounded-lg border border-border/50 p-6">
                  <h2 className="text-lg font-semibold mb-4">Métricas Principais</h2>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Assertividade:</span>
                      <span className={bot.accuracy >= 60 ? "text-success" : bot.accuracy >= 40 ? "text-warning" : "text-danger"}>
                        {bot.accuracy}%
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Fator de Lucro:</span>
                      <span className={bot.profitFactor >= 2 ? "text-success" : bot.profitFactor >= 1.5 ? "text-warning" : "text-danger"}>
                        {bot.profitFactor}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Expectância Matemática:</span>
                      <span className={bot.expectancy >= 0.5 ? "text-success" : bot.expectancy >= 0.2 ? "text-warning" : "text-danger"}>
                        {bot.expectancy}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Drawdown Máximo:</span>
                      <span className={bot.drawdown <= 15 ? "text-success" : bot.drawdown <= 25 ? "text-warning" : "text-danger"}>
                        {bot.drawdown}%
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Nível de Risco:</span>
                      <span className={bot.riskLevel <= 3 ? "text-success" : bot.riskLevel <= 5 ? "text-warning" : "text-danger"}>
                        {bot.riskLevel}/10
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-card rounded-lg border border-border/50 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle size={18} className="text-warning" />
                  <h2 className="text-lg font-semibold">Pontos de Atenção</h2>
                </div>
                
                <div className="space-y-3 text-muted-foreground">
                  <p>• Esta estratégia pode apresentar drawdowns significativos em mercados altamente voláteis.</p>
                  <p>• Recomenda-se utilizar stop loss adequado para gerenciar o risco.</p>
                  <p>• Performance passada não garante resultados futuros.</p>
                  <p>• Considere ajustar os parâmetros de acordo com sua tolerância ao risco.</p>
                </div>
              </div>
            </div>
          )}
          
          {/* Code Tab */}
          {activeTab === 'code' && (
            <div className="space-y-6">
              <div className="bg-card rounded-lg border border-border/50 p-6">
                <h2 className="text-lg font-semibold mb-4">Código do Bot</h2>
                <CodeViewer code={bot.code} />
              </div>
              
              <div className="bg-card rounded-lg border border-border/50 p-6">
                <h2 className="text-lg font-semibold mb-4">Análise do Código</h2>
                
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium mb-2">Indicadores Técnicos Identificados</h3>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-secondary text-xs rounded-full border border-border/50">
                        SMA
                      </span>
                      <span className="px-2 py-1 bg-secondary text-xs rounded-full border border-border/50">
                        EMA
                      </span>
                      <span className="px-2 py-1 bg-secondary text-xs rounded-full border border-border/50">
                        RSI
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium mb-2">Pontos Fortes</h3>
                    <div className="space-y-1 text-muted-foreground">
                      <p>• Implementação clara e estruturada</p>
                      <p>• Boas práticas de gerenciamento de risco</p>
                      <p>• Configurações personalizáveis</p>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium mb-2">Pontos de Melhoria</h3>
                    <div className="space-y-1 text-muted-foreground">
                      <p>• Adicionar validações de entrada</p>
                      <p>• Implementar tratamento de erros</p>
                      <p>• Otimizar para diferentes timeframes</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Performance Tab */}
          {activeTab === 'performance' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PerformanceChart 
                  data={performanceData.profitLoss} 
                  isPositive={true}
                  title="Performance (P&L)"
                  yAxisLabel="Valor ($)"
                />
                <PerformanceChart 
                  data={performanceData.accuracy} 
                  isPositive={true}
                  title="Assertividade"
                  yAxisLabel="%"
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-card rounded-lg border border-border/50 p-6">
                  <h2 className="text-base font-medium mb-4">Estatísticas de Trading</h2>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Total de Trades:</span>
                      <span>157</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Wins:</span>
                      <span className="text-success">{Math.round(bot.accuracy / 100 * 157)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Losses:</span>
                      <span className="text-danger">{157 - Math.round(bot.accuracy / 100 * 157)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Taxa Win/Loss:</span>
                      <span>{(bot.accuracy / (100 - bot.accuracy)).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Profit Factor:</span>
                      <span>{bot.profitFactor}</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-card rounded-lg border border-border/50 p-6">
                  <h2 className="text-base font-medium mb-4">Métricas de Risco</h2>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Drawdown Máximo:</span>
                      <span>{bot.drawdown}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Tempo de Recuperação:</span>
                      <span>21 dias</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Sharpe Ratio:</span>
                      <span>1.75</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Volatilidade:</span>
                      <span>Média</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Correlação com Mercado:</span>
                      <span>0.65</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-card rounded-lg border border-border/50 p-6">
                  <h2 className="text-base font-medium mb-4">Performance por Mercado</h2>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Tendência de alta:</span>
                      <span className="text-success">Muito bom</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Tendência de baixa:</span>
                      <span className="text-warning">Razoável</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Mercado lateral:</span>
                      <span className="text-danger">Fraco</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Alta volatilidade:</span>
                      <span className="text-warning">Razoável</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Baixa volatilidade:</span>
                      <span className="text-success">Bom</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div className="bg-card rounded-lg border border-border/50 p-6">
                <h2 className="text-lg font-semibold mb-4">Parâmetros Configuráveis</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Período da Média Móvel Rápida</label>
                    <input
                      type="number"
                      defaultValue={14}
                      className="w-full py-2 px-3 bg-secondary rounded-md border border-border/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Período recomendado: 5-20</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Período da Média Móvel Lenta</label>
                    <input
                      type="number"
                      defaultValue={28}
                      className="w-full py-2 px-3 bg-secondary rounded-md border border-border/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Período recomendado: 20-50</p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Stop Loss (% do preço)</label>
                    <input
                      type="number"
                      defaultValue={2}
                      step="0.1"
                      className="w-full py-2 px-3 bg-secondary rounded-md border border-border/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Take Profit (% do preço)</label>
                    <input
                      type="number"
                      defaultValue={5}
                      step="0.1"
                      className="w-full py-2 px-3 bg-secondary rounded-md border border-border/50 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                </div>
                
                <div className="mt-6">
                  <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md">
                    Salvar Configurações
                  </button>
                </div>
              </div>
              
              <div className="bg-card rounded-lg border border-border/50 p-6">
                <h2 className="text-lg font-semibold mb-4">Instruções de Uso</h2>
                
                <div className="space-y-4 text-muted-foreground">
                  <p>1. Faça download do bot usando o botão acima.</p>
                  <p>2. Importe o arquivo para sua plataforma de trading (MetaTrader, TradingView, etc).</p>
                  <p>3. Configure os parâmetros de acordo com sua preferência e tolerância a risco.</p>
                  <p>4. Teste o bot em uma conta demo antes de usar com capital real.</p>
                  <p>5. Monitore o desempenho e ajuste os parâmetros conforme necessário.</p>
                </div>
                
                <div className="mt-6 p-4 rounded-md bg-warning/10 border border-warning/30">
                  <div className="flex items-start gap-3">
                    <AlertTriangle size={20} className="text-warning mt-0.5" />
                    <div>
                      <h3 className="font-medium mb-1">Aviso de Risco</h3>
                      <p className="text-sm text-muted-foreground">
                        Trading automatizado envolve riscos significativos. Performance passada não garante resultados futuros.
                        Nunca invista dinheiro que você não pode perder.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default BotDetail;
