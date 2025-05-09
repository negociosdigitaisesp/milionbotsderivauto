
import React, { useState } from 'react';
import { ArrowRight, Download, ShieldCheck, ChartLine, Info } from 'lucide-react';
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
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Info size={18} /> Estratégia Explicada
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p>
                    O robô <strong>Impulso Contrário Pro</strong> utiliza uma estratégia de Martingale 
                    com uma lógica contrária inteligente, operando em curtíssimo prazo (1 tick) 
                    no mercado de índices aleatórios R_25.
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-secondary/50 p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Lógica Contrária</h4>
                      <p className="text-sm text-muted-foreground">
                        Se o mercado indicar tendência de subida (<strong>"Rise"</strong>), o robô aposta na 
                        direção oposta (<strong>PUT</strong>). Se indicar queda (<strong>"Fall"</strong>), 
                        aposta em alta (<strong>CALL</strong>).
                      </p>
                    </div>
                    
                    <div className="bg-secondary/50 p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Martingale Adaptado</h4>
                      <p className="text-sm text-muted-foreground">
                        Após uma perda, aumenta a próxima aposta multiplicando o valor perdido por <strong>1.071</strong>. 
                        Após vitória, volta ao valor base de <strong>0.35</strong>.
                      </p>
                    </div>
                  </div>
                  
                  <div className="bg-secondary/50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Alternância de Condição</h4>
                    <p className="text-sm text-muted-foreground">
                      Um diferencial importante: após cada perda, o robô inverte automaticamente sua 
                      condição de análise, adaptando-se às mudanças de comportamento do mercado.
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
                      A assertividade individual é de <strong>47-49%</strong>, um valor esperado 
                      para estratégias Martingale que focam na lucratividade da sequência de operações.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          {activeTab === 'settings' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <ShieldCheck size={18} /> Configurações Recomendadas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-medium mb-2">Stop Loss (Max Acceptable Loss)</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Define o limite máximo de perda antes que o robô pare de operar. 
                    Esta é uma proteção crucial contra perdas excessivas.
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border border-success/30 rounded-lg p-4">
                      <h4 className="font-medium text-success mb-2">Conservador: 3.5</h4>
                      <p className="text-xs text-muted-foreground">
                        Permite cerca de 8 perdas consecutivas antes de parar.
                        Ideal para bancas menores ou testes iniciais.
                      </p>
                    </div>
                    
                    <div className="border border-primary/30 rounded-lg p-4">
                      <h4 className="font-medium text-primary mb-2">Moderado: 5.0</h4>
                      <p className="text-xs text-muted-foreground">
                        Permite cerca de 10 perdas consecutivas.
                        Equilíbrio entre segurança e oportunidade de recuperação.
                      </p>
                    </div>
                    
                    <div className="border border-warning/30 rounded-lg p-4">
                      <h4 className="font-medium text-warning mb-2">Agressivo: 7.5</h4>
                      <p className="text-xs text-muted-foreground">
                        Permite cerca de 12-13 perdas consecutivas.
                        Maior risco, mas maior chance de recuperação em sequências negativas.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2">Stop Win (Expected Profit)</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Define o objetivo de lucro para encerrar as operações. Garante que o robô 
                    pare quando estiver no lucro, evitando a devolução de ganhos.
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border border-success/30 rounded-lg p-4">
                      <h4 className="font-medium text-success mb-2">Conservador: 1.5</h4>
                      <p className="text-xs text-muted-foreground">
                        Aproximadamente 4-5 "ciclos de ganho" líquidos.
                        Rápido de atingir, garante pequenos lucros frequentes.
                      </p>
                    </div>
                    
                    <div className="border border-primary/30 rounded-lg p-4">
                      <h4 className="font-medium text-primary mb-2">Moderado: 3.0</h4>
                      <p className="text-xs text-muted-foreground">
                        Aproximadamente 8-10 "ciclos de ganho" líquidos.
                        Bom alvo para uma sessão de operações.
                      </p>
                    </div>
                    
                    <div className="border border-warning/30 rounded-lg p-4">
                      <h4 className="font-medium text-warning mb-2">Agressivo: 5.0</h4>
                      <p className="text-xs text-muted-foreground">
                        Aproximadamente 14-16 "ciclos de ganho" líquidos.
                        Requer mais tempo/operações para ser atingido.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Progressão de Stake após Perdas</h4>
                  <div className="text-xs space-y-1">
                    <p>Perda 1: 0.35 (stake inicial)</p>
                    <p>Perda 2: ~0.37 (total perdido ~0.72)</p>
                    <p>Perda 3: ~0.40 (total perdido ~1.12)</p>
                    <p>Perda 4: ~0.43 (total perdido ~1.55)</p>
                    <p>Perda 5: ~0.46 (total perdido ~2.01)</p>
                    <p>Perda 10: ~0.65 (total perdido ~4.86)</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          {activeTab === 'code' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Código Fonte</CardTitle>
                <CardDescription>
                  Estratégia Martingale com lógica contrária e alternância de condição
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
                  Otimizado para índices aleatórios, especialmente R_25.
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Timeframes</h4>
                <p className="text-xs text-muted-foreground">
                  Ultra curto prazo (1 tick).
                </p>
              </div>
              
              <div>
                <h4 className="font-medium text-sm mb-1">Capital Recomendado</h4>
                <p className="text-xs text-muted-foreground">
                  Mínimo 20x o valor do Stop Loss escolhido.
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
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Configure o valor base da aposta (0.35 recomendado)</li>
              <li>Defina o Stop Loss conforme seu perfil de risco</li>
              <li>Defina o Stop Win conforme seu objetivo de lucro</li>
              <li>Execute em mercados de índices aleatórios</li>
              <li>Monitore as primeiras operações para garantir funcionamento adequado</li>
            </ol>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Bots Relacionados</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
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
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BotDetailView;
