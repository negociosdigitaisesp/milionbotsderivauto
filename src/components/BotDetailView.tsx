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

  // Special content for bots
  const renderBotSpecificOverview = () => {
    if (bot.id === "14") {
      // NexusBot
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
                O <strong>NexusBot</strong> opera no Índice Sintético <strong>RDBEAR</strong> (Random Daily Bear Market Index) 
                da Deriv. Sua estratégia é baseada na análise sequencial de múltiplos ticks anteriores para identificar 
                um padrão de alta ou baixa, realizando operações "Rise/Fall" (Sobe/Desce) com duração de 5 minutos.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Análise de Tendência (Sequência de Ticks)</h4>
                  <p className="text-sm text-muted-foreground">
                    O robô coleta os últimos 9 ticks e analisa padrões específicos:
                    <ul className="list-disc list-inside mt-2">
                      <li><strong>Sinal de Compra "PUT" (Desce):</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Se o Tick 5 > Tick 4, E</li>
                          <li>Se o Tick 4 > Tick 3, E</li>
                          <li>Se o Tick 3 > Tick 2, E</li>
                          <li>Se o Tick 1 < Tick 2 (indicando uma possível reversão após uma sequência de alta)</li>
                        </ul>
                      </li>
                      <li className="mt-2"><strong>Sinal de Compra "CALL" (Sobe):</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Se o Tick 5 < Tick 4, E</li>
                          <li>Se o Tick 4 < Tick 3, E</li>
                          <li>Se o Tick 3 < Tick 2, E</li>
                          <li>Se o Tick 1 > Tick 2 (indicando uma possível reversão após uma sequência de baixa)</li>
                        </ul>
                      </li>
                    </ul>
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Gerenciamento Durante a Operação</h4>
                  <p className="text-sm text-muted-foreground">
                    <strong>Venda Antecipada:</strong> Após a compra, se o contrato estiver disponível para venda:
                    <ul className="list-disc list-inside mt-2">
                      <li>Se o lucro atual da venda for maior que <strong>(Valor da Compra / 100) * 5</strong> (ou seja, 5% do valor da aposta), o robô vende o contrato no mercado.</li>
                    </ul>
                  </p>
                  <div className="mt-3">
                    <h5 className="font-medium text-sm">Tipo de Operação:</h5>
                    <p className="text-sm text-muted-foreground">
                      <ul className="list-disc list-inside mt-1">
                        <li>Contratos "Rise/Fall" (Sobe/Desce)</li>
                        <li>Duração: Fixo em <strong>5 minutos</strong></li>
                      </ul>
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-secondary/50 p-4 rounded-lg mt-4">
                <h4 className="font-medium mb-2">Gerenciamento de Aposta (Martingale Específico)</h4>
                <p className="text-sm text-muted-foreground">
                  <ul className="list-disc list-inside">
                    <li><strong>Após Vitória:</strong> A próxima aposta retorna ao "Valor Inicial da Ordem" definido pelo usuário.</li>
                    <li><strong>Após Perda:</strong>
                      <ul className="list-disc list-inside ml-4 mt-1">
                        <li><strong>Pequenas Perdas</strong> (Prejuízo Total ≥ -1.4 USD): A próxima aposta é fixada em <strong>0.35 USD</strong>.</li>
                        <li><strong>Grandes Perdas</strong> (Prejuízo Total < -1.4 USD): A próxima aposta é calculada como <strong>(Prejuízo Total Acumulado * -0.35)</strong>.</li>
                      </ul>
                    </li>
                  </ul>
                </p>
              </div>
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-warning">
                  <AlertTriangle size={16} />
                  Aviso de Risco
                </h4>
                <p className="text-sm text-warning/80">
                  Este robô utiliza um Martingale peculiar, pois usa um fator negativo e menor que 1 sobre o prejuízo total. 
                  Isso significa que a próxima aposta será 35% do prejuízo total, mas como o fator é negativo, ele tenta "apostar contra" 
                  o prejuízo de uma forma que pode não ser matematicamente ideal para recuperação total imediata.
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ChartLine size={18} /> Projeções de Lucros e Riscos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-8">
                <h4 className="font-medium mb-4">Precisão por Operação</h4>
                <div className="grid grid-cols-1 gap-8">
                  <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Assertividade Diária" yAxisLabel="Precisão %" />
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  A assertividade individual é de <strong>45-50%</strong>, dependendo das condições do mercado.
                  Operações de 5 minutos podem ter payouts interessantes se a tendência se confirmar.
                  A venda antecipada (se lucrativa) pode garantir pequenos ganhos antes do vencimento do contrato.
                </p>
              </div>
              
              <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-4">
                <h4 className="font-medium mb-2 text-primary">Exemplo de Risco com Martingale</h4>
                <p className="text-sm">
                  O Martingale com fator <strong>-0.35</strong> sobre o prejuízo total é incomum. Exemplo:
                  <ul className="list-disc list-inside mt-2">
                    <li>Perda 1 (Stake $0.35): $0.35 (Total Perdido: $0.35) → Próxima Aposta: $0.35</li>
                    <li>Perda 2 (Stake $0.35): $0.35 (Total Perdido: $0.70) → Próxima Aposta: $0.35</li>
                    <li>Perda 3 (Stake $0.35): $0.35 (Total Perdido: $1.05) → Próxima Aposta: $0.35</li>
                    <li>Perda 4 (Stake $0.35): $0.35 (Total Perdido: $1.40) → Próxima Aposta: $1.40 * 0.35 = ~$0.49</li>
                    <li>Perda 5 (Stake $0.49): $0.49 (Total Perdido: $1.89) → Próxima Aposta: $1.89 * 0.35 = ~$0.66</li>
                  </ul>
                </p>
                <p className="text-sm mt-2">
                  Este Martingale é mais lento na progressão do stake comparado a fatores maiores, o que pode permitir mais 
                  tentativas de recuperação antes de atingir um Stop Loss alto, mas também significa que a recuperação total 
                  de um prejuízo grande levará mais vitórias.
                </p>
              </div>
              
              <div className="mt-6">
                <h4 className="font-medium mb-4">Visualização Risco vs. Recompensa</h4>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Meta de Lucro (Ex: +$2.50 em banca de $50)</span>
                      <span>+$2.50</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-4">
                      <div className="bg-success h-4 rounded-full" style={{ width: '40%' }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Limite de Perda (Ex: -$7.50 em banca de $50)</span>
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
        </div>;
    }
    
    if (bot.id === "13") {
      // AlphaBot
      return <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info size={18} /> Estratégia Explicada
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                O <strong>AlphaBot</strong> é uma estratégia automatizada para o Índice Sintético R_100 
                na Deriv. Ele opera com contratos de Dígitos Over/Under, baseando suas previsões na análise 
                dos últimos 10 dígitos de ticks anteriores (convertidos para um padrão binário).
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Análise de Dígitos (Padrão Binário)</h4>
                  <p className="text-sm text-muted-foreground">
                    O robô coleta os últimos 10 dígitos finais dos preços dos ticks. Para cada dígito:
                    <ul className="list-disc list-inside mt-2">
                      <li>Se for 8 ou 9, converte para 1</li>
                      <li>Se for de 0 a 7, converte para 0</li>
                    </ul>
                    Em seguida, soma esses 10 valores binários (0s e 1s).
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Definição da Previsão (Over/Under)</h4>
                  <p className="text-sm text-muted-foreground">
                    <ul className="list-disc list-inside">
                      <li>Soma ≥ 2: Define a "Previsão" como 6 (aposta em OVER 6)</li>
                      <li>Soma &lt; 2: Define a "Previsão" como 3 (aposta em UNDER 3)</li>
                    </ul>
                    <p className="mt-2"><em>Adaptação:</em> Se um dígito específico (0-9) se repetir muito após perdas, a previsão pode ser invertida e a contagem de dígitos zerada.</p>
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Tipo de Operação</h4>
                  <p className="text-sm text-muted-foreground">
                    <ul className="list-disc list-inside">
                      <li><strong>DIGITOVER:</strong> Ganha se o último dígito for MAIOR que a "Previsão"</li>
                      <li><strong>DIGITUNDER:</strong> Ganha se o último dígito for MENOR que a "Previsão"</li>
                      <li>Duração: Fixo em 1 tick</li>
                    </ul>
                  </p>
                </div>
                
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Gerenciamento de Aposta (Martingale Agressivo)</h4>
                  <p className="text-sm text-muted-foreground">
                    <ul className="list-disc list-inside">
                      <li><strong>Após Vitória:</strong> A aposta retorna ao "Valor Inicial da Ordem"</li>
                      <li><strong>Após Perda:</strong>
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Pequenas Perdas (Prejuízo Total ≥ -1 USD): Próxima aposta = 0.35 USD</li>
                          <li>Grandes Perdas (Prejuízo Total &lt; -1 USD): Próxima aposta = (Prejuízo Total Acumulado * -1.07)</li>
                        </ul>
                      </li>
                    </ul>
                  </p>
                </div>
              </div>
              
              <div className="bg-danger/10 p-4 rounded-lg border border-danger/30 mt-4">
                <h4 className="font-medium mb-2 flex items-center gap-2 text-danger">
                  <AlertTriangle size={16} />
                  Aviso de Risco Extremo
                </h4>
                <p className="text-sm text-danger/80">
                  Este robô utiliza um Martingale EXTREMAMENTE AGRESSIVO que pode levar a perdas rápidas. 
                  O fator de Martingale de -1.07 sobre o prejuízo total acumulado é extremamente perigoso 
                  e pode consumir seu Stop Loss muito rapidamente. É imperativo que você teste 
                  exaustivamente em uma conta demonstração antes de considerar o uso em uma conta real.
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ChartLine size={18} /> Projeções de Lucros e Riscos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-8">
                <h4 className="font-medium mb-4">Precisão por Operação</h4>
                <div className="grid grid-cols-1 gap-8">
                  <PerformanceChart data={generateDailyPerformanceData(bot.accuracy)} isPositive={bot.accuracy > 45} title="Assertividade Diária" yAxisLabel="Precisão %" />
                </div>
                <p className="mt-4 text-sm text-muted-foreground">
                  A assertividade individual é de <strong>40-50%</strong>, dependendo das condições do mercado.
                  Alcançar o Stop Win dependerá da sua meta, do payout das operações Over/Under (que variam) 
                  e da capacidade do Martingale de recuperar perdas.
                </p>
              </div>
              
              <div className="bg-warning/10 p-4 rounded-lg border border-warning/30 mt-4">
                <h4 className="font-medium mb-2 text-warning">Risco Elevado (Martingale Extremo)</h4>
                <p className="text-sm">
                  O fator de Martingale de -1.07 sobre o prejuízo total acumulado é extremamente perigoso.
                  <strong> Exemplo de Risco:</strong> Se seu Stop Loss for $5 e o prejuízo acumulado atingir -$4, 
                  a próxima aposta será $4 * 1.07 = $4.28. Se esta perder, o prejuízo total será $4 + $4.28 = $8.28, 
                  ultrapassando seu Stop Loss de $5 em uma única operação de Martingale.
                </p>
                <p className="text-sm mt-2">
                  Isso significa que 2-3 perdas consecutivas, uma vez que o prejuízo começa a acumular, 
                  podem levar a perdas que <strong>EXCEDEM SEU STOP LOSS CONFIGURADO</strong>.
                </p>
              </div>
              
              <div className="mt-6">
                <h4 className="font-medium mb-4">Visualização Risco vs. Recompensa</h4>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Meta de Lucro (Ex: +$2.50 em banca de $50)</span>
                      <span>+$2.50</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-4">
                      <div className="bg-success h-4 rounded-full" style={{ width: '33%' }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Limite de Perda (Ex: -$5.00 em banca de $50)</span>
                      <span className="text-danger">-$5.00</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-4 relative">
                      <div className="bg-danger h-4 rounded-full" style={{ width: '66%' }}></div>
                      <div className="absolute -bottom-6 right-0 text-xs text-danger">Risco de ser ultrapassado pelo Martingale!</div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>;
    }
    
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

  // Special content for bot risk management
  const renderBotSpecificRiskManagement = () => {
    if (bot.id === "14") {
      // NexusBot
      return <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ShieldCheck size={18} /> Gestão de Riscos (Definida por VOCÊ!)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <p className="text-sm">
              O NexusBot requer que <strong>VOCÊ</strong> defina seus limites. Uma gestão de risco cuidadosa é essencial.
            </p>
            
            <div>
              <h3 className="font-medium mb-2">Meta Lucro (Stop Win)</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Define o objetivo de ganho para encerrar a sessão com lucro.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-success/30 rounded-lg p-4">
                  <h4 className="font-medium text-success mb-2">Conservador: 2% a 5% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Win $1.00 a $2.50.
                    Contratos de 5 minutos podem levar tempo para se desenvolver; metas realistas são importantes.
                  </p>
                </div>
                
                <div className="border border-primary/30 rounded-lg p-4">
                  <h4 className="font-medium text-primary mb-2">Moderado: 5% a 10% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Win $2.50 a $5.00.
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
                  <h4 className="font-medium text-success mb-2">Conservador: 10% a 15% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Loss $5.00 a $7.50.
                    O Martingale <strong>-0.35</strong> é menos agressivo no aumento do stake do que fatores maiores, mas ainda pode acumular perdas.
                  </p>
                </div>
                
                <div className="border border-warning/30 rounded-lg p-4">
                  <h4 className="font-medium text-warning mb-2">Moderado (Risco Médio): 15% a 25% da banca</h4>
                  <p className="text-xs text-muted-foreground">
                    Ex: Banca $50, Stop Loss $7.50 a $12.50.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Valor Inicial da Ordem</h3>
              <div className="border border-success/30 rounded-lg p-4">
                <h4 className="font-medium text-success mb-2">Recomendado: $0.35</h4>
                <p className="text-xs text-muted-foreground">
                  É uma boa base para o Martingale e para a gestão de risco.
                </p>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-medium mb-2">Duração do Contrato</h3>
              <p className="text-sm text-muted-foreground">
                O robô opera com contratos de 5 minutos de duração para "Rise/Fall" (Sobe/Desce).
              </p>
            </div>
            
            <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 mt-6">
              <h4 className="font-medium mb-2 text-primary">Recomendação de Banca</h4>
              <p className="text-sm">
                Mínimo de <strong>$50 USD</strong>. Considerando a duração de 5 minutos e o Martingale (mesmo que menos agressivo no fator), 
                uma banca com alguma folga para o Stop Loss é preferível.
              </p>
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
            <h4 className="font-medium mb-2">A Gestão de Riscos já vem pré-configurada</h4>
            <p className="text-sm text-muted-foreground">Esse robô é ideal para quem quer lucrar $20 dólares por dia e perder $20 dólare</p>
          </div>
          
          <div>
            <h3 className="font-medium mb-2">Stop Loss Padrão - $20 USD</h3>
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
            <h3 className="font-medium mb-2">Stop Win Padrão - $20 USD</h3>
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
                <span className="font-medium">Gestão de Riscos Pré-Configurada</span>
                <p className="mt-1 text-muted-foreground pl-5">O robô já vem com stop loss e stop win automáticos.</p>
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
