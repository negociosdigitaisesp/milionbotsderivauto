import React from 'react';
import { Bot, Target, BarChart3, Activity, Award, Shield, Zap, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface BotStats {
  nome_bot: string;
  lucro_total: number;
  total_operacoes: number;
  vitorias: number;
  derrotas: number;
  taxa_vitoria?: number;
  assertividade_percentual?: number;
  maior_lucro?: number;
  maior_perda?: number;
  created_at?: string;
  updated_at?: string;
}

interface BotPerformanceCardProps {
  bot: BotStats;
  index?: number;
  periodoSelecionado?: string;
}

const BotPerformanceCard = ({ bot, periodoSelecionado }: BotPerformanceCardProps) => {
  const navigate = useNavigate();
  
  // Configuração de assertividades específicas por bot
  const getBotSpecificData = (botName: string) => {
    const normalizedName = botName.toLowerCase().replace(/[_\s]/g, '');
    
    const botConfigs: { [key: string]: { assertividade: number; route: string } } = {
      'quantumbotfixedstake': { assertividade: 85.2, route: '/bot/11' },
      'quantumbot': { assertividade: 85.2, route: '/bot/11' },
      'botapalancamiento': { assertividade: 78.9, route: '/apalancamiento-100x' },
      'apalancamiento': { assertividade: 78.9, route: '/apalancamiento-100x' },
      'botai2.0': { assertividade: 82.1, route: '/bot/16' },
      'botai': { assertividade: 82.1, route: '/bot/16' },
      'factor50xconservador': { assertividade: 91.5, route: '/factor50x' },
      'factor50x': { assertividade: 91.5, route: '/factor50x' },
      'wolfbot2.0': { assertividade: 87.3, route: '/bot/wolf-bot' },
      'wolfbot': { assertividade: 87.3, route: '/bot/wolf-bot' },
      'sniperbotmartingale': { assertividade: 79.8, route: '/bot/15' },
      'sniperbot': { assertividade: 79.8, route: '/bot/15' },
      'nexusbot': { assertividade: 83.7, route: '/bot/14' },
      'bkbot1.0': { assertividade: 88.5, route: '/bk-bot' },
      'bkbot': { assertividade: 88.5, route: '/bk-bot' }
    };
    
    return botConfigs[normalizedName] || { assertividade: bot.assertividade_percentual, route: '/' };
  };

  const botData = getBotSpecificData(bot.nome_bot);
  
  // Extrair dados do bot
  const vitorias = bot.vitorias;
  const derrotas = bot.derrotas;
  const totalOperacoes = bot.total_operacoes;
  
  // Usar o win rate real calculado a partir das vitórias e total de operações
  const winRate = totalOperacoes > 0 ? (vitorias / totalOperacoes) * 100 : 0;
  const assertividade = winRate; // Usar o win rate como assertividade

  // Função para obter cor baseada na performance
  const getProgressColor = (accuracy: number) => {
    if (accuracy >= 80) return 'from-emerald-500 to-emerald-600';
    if (accuracy >= 70) return 'from-blue-500 to-blue-600';
    if (accuracy >= 60) return 'from-yellow-500 to-yellow-600';
    return 'from-orange-500 to-orange-600';
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-emerald-500';
    if (accuracy >= 70) return 'text-blue-500';
    if (accuracy >= 60) return 'text-yellow-500';
    return 'text-orange-500';
  };



  const handleDownloadBot = (botName: string) => {
    const botData = getBotSpecificData(botName);
    console.log(`Navegando para: ${botData.route} - Bot: ${botName}`);
    navigate(botData.route);
  };

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-6 shadow-lg transition-all duration-300 hover:shadow-2xl hover:border-primary/40 hover:-translate-y-1">
      {/* Borda superior com gradiente baseado na performance */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${getProgressColor(assertividade)}`}></div>
      
      {/* Badge de certificação */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        {assertividade >= 90 && (
          <div className="bg-yellow-500/10 backdrop-blur-sm border border-yellow-500/20 text-yellow-500 text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1">
            <Shield size={10} />
            Pro
          </div>
        )}
      </div>
      
      {/* Cabeçalho do card */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center border border-primary/20">
            <Bot className="text-primary" size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-card-foreground mb-1">{bot.nome_bot.replace(/_/g, ' ')}</h3>
          </div>
        </div>
        
        {/* Indicadores de status */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex items-center gap-1 bg-emerald-500/10 px-2 py-1 rounded-full">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-emerald-500 font-medium">Online</span>
          </div>
        </div>
      </div>
      
      {/* Porcentagem de assertividade */}
      <div className="text-center mb-6 relative">
        <div className="relative inline-block">
          <div className={`text-5xl font-extrabold mb-2 ${getAccuracyColor(assertividade)} relative z-10`}>
            {assertividade.toFixed(1)}%
          </div>
          {/* Círculo decorativo de fundo */}
          <div className={`absolute inset-0 w-20 h-20 mx-auto rounded-full bg-gradient-to-br ${getProgressColor(assertividade)} opacity-10 blur-xl`}></div>
        </div>
        <p className="text-sm text-muted-foreground font-medium">Tasa de Asertividad</p>
      </div>
      
      {/* Barra de progresso */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground">Performance</span>
          <span className="text-xs font-medium text-foreground">{assertividade.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-secondary/50 rounded-full h-3 overflow-hidden shadow-inner border border-border/30">
          <div 
            className={`h-3 rounded-full bg-gradient-to-r ${getProgressColor(assertividade)} transition-all duration-1000 ease-out relative`}
            style={{ width: `${assertividade}%` }}
          >
            {/* Efeito shimmer */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
            {/* Indicador de posição */}
            <div className="absolute right-1 top-1/2 transform -translate-y-1/2 w-1 h-1 bg-white rounded-full shadow-sm"></div>
          </div>
        </div>
      </div>
      
      {/* Estatísticas detalhadas - Layout reorganizado */}
      <div className="space-y-3 mb-4">
        {/* Linha 1: Victorias e Derrotas lado a lado */}
        <div className="grid grid-cols-2 gap-3">
          <div className="text-center p-3 bg-gradient-to-br from-emerald-500/5 to-emerald-500/10 rounded-lg border border-emerald-500/20">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Target size={12} className="text-emerald-500" />
              <span className="text-lg font-bold text-emerald-500">{vitorias}</span>
            </div>
            <div className="text-xs text-muted-foreground font-medium">Victorias</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-orange-500/5 to-orange-500/10 rounded-lg border border-orange-500/20">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Activity size={12} className="text-orange-500" />
              <span className="text-lg font-bold text-orange-500">{derrotas}</span>
            </div>
            <div className="text-xs text-muted-foreground font-medium">Derrotas</div>
          </div>
        </div>
        
        {/* Linha 2: Total de operações */}
        <div className="text-center p-3 bg-gradient-to-br from-primary/5 to-primary/10 rounded-lg border border-primary/20">
          <div className="flex items-center justify-center gap-1 mb-1">
            <BarChart3 size={12} className="text-primary" />
            <span className="text-lg font-bold text-primary">{totalOperacoes}</span>
          </div>
          <div className="text-xs text-muted-foreground font-medium">Total de Operaciones</div>
        </div>
      </div>
      
      {/* Footer profissional */}
      <div className="pt-4 border-t border-border/30">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${assertividade >= 80 ? 'bg-emerald-500' : assertividade >= 70 ? 'bg-primary' : assertividade >= 60 ? 'bg-blue-500' : 'bg-orange-500'} animate-pulse`}></div>
            <span className="text-xs text-muted-foreground font-medium">
              {assertividade >= 80 ? 'Excelente' : assertividade >= 70 ? 'Muy Bueno' : assertividade >= 60 ? 'Bueno' : 'Regular'}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Zap size={12} />
            <span>Activo</span>
          </div>
        </div>
        
        {/* Métricas adicionais */}
        <div className="grid grid-cols-2 gap-3 text-xs mb-4">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Win Rate:</span>
            <span className="font-semibold text-foreground">{((vitorias / totalOperacoes) * 100).toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Resultado:</span>
            <span className="font-semibold text-emerald-500">
              {totalOperacoes > 100 ? 'Sin Martingale' : totalOperacoes > 50 ? 'Media' : 'Básica'}
            </span>
          </div>
        </div>
        
        {/* Botão de ação */}
        <button
          onClick={() => handleDownloadBot(bot.nome_bot)}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 hover:from-emerald-500/20 hover:to-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/30 rounded-lg transition-all duration-300 group"
        >
          <span className="text-sm font-medium text-emerald-500">Descargar Bot</span>
          <Download size={14} className="text-emerald-500 group-hover:translate-y-1 transition-transform duration-200" />
        </button>
      </div>
    </div>
  );
};

export default BotPerformanceCard;