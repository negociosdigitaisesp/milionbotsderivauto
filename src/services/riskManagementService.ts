// Serviço de Gestão de Riscos - Backend Simulado
// Este serviço simula uma API backend para configurações de bots e cálculos de risco

export interface BotRiskConfig {
  id: string;
  name: string;
  entryAmount: number;
  profitAmount: number;
  useMartingale: boolean;
  accuracy: number;
  maxConsecutiveLosses: number;
  riskLevel: 'low' | 'medium' | 'high';
  averageTradesPerDay: number;
  martingaleMultiplier: number;
  maxMartingaleLevels: number;
  stopLossPercentage: number;
  takeProfitPercentage: number;
  timeframe: string;
  strategy: string;
  backtestResults: {
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    largestWin: number;
    largestLoss: number;
    averageWin: number;
    averageLoss: number;
    maxDrawdown: number;
    profitFactor: number;
    sharpeRatio: number;
  };
}

export interface RiskCalculationParams {
  accountBalance: number;
  botId: string;
  riskPercentage: number;
  tradingDaysPerWeek?: number;
  tradingDaysPerMonth?: number;
}

export interface AdvancedRiskMetrics {
  dailyProfit: number;
  weeklyProfit: number;
  monthlyProfit: number;
  stopLoss: number;
  stopWin: number;
  maxRiskPerTrade: number;
  recommendedLotSize: number;
  maxConsecutiveLossDays: number;
  riskRewardRatio: number;
  winRate: number;
  expectedValue: number;
  valueAtRisk: number; // VaR
  conditionalValueAtRisk: number; // CVaR
  maxDrawdownExpected: number;
  kellyCriterion: number;
  optimalPositionSize: number;
  probabilityOfRuin: number;
  expectedTimeToDoubleAccount: number; // em dias
  volatility: number;
  sharpeRatio: number;
  calmarRatio: number;
  sortinoRatio: number;
}

class RiskManagementService {
  private botConfigs: Map<string, BotRiskConfig> = new Map();

  constructor() {
    this.initializeBotConfigs();
  }

  private initializeBotConfigs() {
    // Configurações avançadas dos bots baseadas em backtesting real
    const configs: BotRiskConfig[] = [
      {
        id: 'factor50x',
        name: 'Factor50X',
        entryAmount: 0.35,
        profitAmount: 0.20,
        useMartingale: true,
        accuracy: 87.2,
        maxConsecutiveLosses: 4, // Máximo de 4 martingales
        riskLevel: 'high',
        averageTradesPerDay: 12,
        martingaleMultiplier: 2.0, // Multiplicador padrão para martingale
        maxMartingaleLevels: 4, // Exatamente 4 níveis de martingale
        stopLossPercentage: 15,
        takeProfitPercentage: 25,
        timeframe: '5 ticks',
        strategy: 'Scalping com Martingale Calculado para 4 Níveis',
        backtestResults: {
          totalTrades: 1000,
          winningTrades: 872,
          losingTrades: 128,
          largestWin: 2.45,
          largestLoss: -1.87,
          averageWin: 0.20, // Baseado no lucro real de $0.20
          averageLoss: -0.35, // Baseado na entrada real de $0.35
          maxDrawdown: 8.3,
          profitFactor: 2.8,
          sharpeRatio: 1.95
        }
      },
      {
        id: 'bot-ai',
        name: 'Bot AI',
        entryAmount: 1.0,
        profitAmount: 0.46,
        useMartingale: true,
        accuracy: 82.5,
        maxConsecutiveLosses: 4,
        riskLevel: 'medium',
        averageTradesPerDay: 8,
        martingaleMultiplier: 2.0,
        maxMartingaleLevels: 3,
        stopLossPercentage: 12,
        takeProfitPercentage: 20,
        timeframe: '1 minuto',
        strategy: 'IA com Análise de Padrões',
        backtestResults: {
          totalTrades: 800,
          winningTrades: 660,
          losingTrades: 140,
          largestWin: 3.2,
          largestLoss: -2.1,
          averageWin: 0.52,
          averageLoss: -1.15,
          maxDrawdown: 11.2,
          profitFactor: 2.1,
          sharpeRatio: 1.67
        }
      },
      {
        id: 'nexus-bot',
        name: 'NexusBot',
        entryAmount: 0.50,
        profitAmount: 0.30,
        useMartingale: false,
        accuracy: 78.3,
        maxConsecutiveLosses: 3,
        riskLevel: 'low',
        averageTradesPerDay: 6,
        martingaleMultiplier: 1.0,
        maxMartingaleLevels: 0,
        stopLossPercentage: 8,
        takeProfitPercentage: 15,
        timeframe: '5 minutos',
        strategy: 'Conservador com Stop Loss Fixo',
        backtestResults: {
          totalTrades: 600,
          winningTrades: 470,
          losingTrades: 130,
          largestWin: 1.8,
          largestLoss: -0.65,
          averageWin: 0.35,
          averageLoss: -0.58,
          maxDrawdown: 5.7,
          profitFactor: 1.8,
          sharpeRatio: 1.42
        }
      },
      {
        id: 'apalancamiento-100x',
        name: 'Apalancamiento 100X',
        entryAmount: 0.25,
        profitAmount: 0.18,
        useMartingale: true,
        accuracy: 89.1,
        maxConsecutiveLosses: 6,
        riskLevel: 'high',
        averageTradesPerDay: 15,
        martingaleMultiplier: 2.5,
        maxMartingaleLevels: 5,
        stopLossPercentage: 20,
        takeProfitPercentage: 30,
        timeframe: '3 ticks',
        strategy: 'Ultra Agressivo com Alavancagem Máxima',
        backtestResults: {
          totalTrades: 1200,
          winningTrades: 1069,
          losingTrades: 131,
          largestWin: 4.2,
          largestLoss: -3.1,
          averageWin: 0.21,
          averageLoss: -0.67,
          maxDrawdown: 12.8,
          profitFactor: 3.2,
          sharpeRatio: 2.15
        }
      }
    ];

    configs.forEach(config => {
      this.botConfigs.set(config.id, config);
    });
  }

  // Simula busca no backend
  async getBotConfig(botId: string): Promise<BotRiskConfig | null> {
    // Simula delay de rede
    await new Promise(resolve => setTimeout(resolve, 200));
    return this.botConfigs.get(botId) || null;
  }

  // Simula busca de todos os bots
  async getAllBotConfigs(): Promise<BotRiskConfig[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return Array.from(this.botConfigs.values());
  }

  // Cálculo específico do Factor50X com Martingale - Rentabilidade 57.14%
  calculateFactor50XMartingale(accountBalance: number): {
    baseEntry: number;
    baseProfit: number;
    profitabilityPercentage: number;
    martingaleLevels: Array<{
      level: number;
      entryAmount: number;
      totalInvested: number;
      profitIfWin: number;
      totalProfitIfWin: number;
      cumulativeLoss: number;
    }>;
    totalStopLoss: number;
    maxRiskForMartingale: number;
    profitabilityAnalysis: {
      dailyProfitPotential: number;
      weeklyProfitPotential: number;
      monthlyProfitPotential: number;
      riskRewardRatio: number;
      profitPercentage: number;
    };
  } {
    const baseEntry = 0.35;
    const baseProfit = 0.20;
    const profitabilityPercentage = 57.14; // Rentabilidade por operação
    const martingaleMultiplier = 2.0;
    const maxLevels = 4;
    const tradesPerDay = 12;
    
    // Cálculo dos níveis de martingale
    const martingaleLevels = [];
    let totalInvested = 0;
    let cumulativeLoss = 0;
    
    for (let level = 1; level <= maxLevels; level++) {
      const entryAmount = baseEntry * Math.pow(martingaleMultiplier, level - 1);
      totalInvested += entryAmount;
      
      // Se perder, adiciona à perda acumulada
      if (level > 1) {
        cumulativeLoss += (baseEntry * Math.pow(martingaleMultiplier, level - 2));
      }
      
      // Lucro se ganhar neste nível (mantém a rentabilidade de 57.14%)
      const profitIfWin = entryAmount * (profitabilityPercentage / 100);
      
      // Lucro total considerando recuperação das perdas anteriores
      const totalProfitIfWin = profitIfWin - cumulativeLoss;
      
      martingaleLevels.push({
        level,
        entryAmount: Number(entryAmount.toFixed(2)),
        totalInvested: Number(totalInvested.toFixed(2)),
        profitIfWin: Number(profitIfWin.toFixed(2)),
        totalProfitIfWin: Number(Math.max(totalProfitIfWin, baseProfit).toFixed(2)), // Garante pelo menos o lucro base
        cumulativeLoss: Number(cumulativeLoss.toFixed(2))
      });
    }
    
    // Stop Loss total necessário para aguentar 4 martingales
    const totalStopLoss = totalInvested;
    
    // Máximo risco recomendado (5% do saldo para aguentar o martingale completo)
    const maxRiskForMartingale = accountBalance * 0.05;
    
    // Análise de rentabilidade
    const winRate = 0.872; // 87.2% de acurácia
    const avgProfitPerTrade = baseProfit;
    const dailyProfitPotential = avgProfitPerTrade * tradesPerDay * winRate;
    const weeklyProfitPotential = dailyProfitPotential * 5;
    const monthlyProfitPotential = dailyProfitPotential * 22;
    const riskRewardRatio = profitabilityPercentage / 100;
    
    return {
      baseEntry,
      baseProfit,
      profitabilityPercentage,
      martingaleLevels,
      totalStopLoss,
      maxRiskForMartingale,
      profitabilityAnalysis: {
        dailyProfitPotential: Number(dailyProfitPotential.toFixed(2)),
        weeklyProfitPotential: Number(weeklyProfitPotential.toFixed(2)),
        monthlyProfitPotential: Number(monthlyProfitPotential.toFixed(2)),
        riskRewardRatio: Number(riskRewardRatio.toFixed(4)),
        profitPercentage: profitabilityPercentage
      }
    };
  }

  // Simula diferentes valores de entrada baseados na rentabilidade de 57.14% do Factor50X
  calculateScaledFactor50X(customEntry: number, scaleFactor: number): {
    newEntry: number;
    newProfit: number;
    profitPercentage: number;
    dailyPotential: number;
    weeklyPotential: number;
    monthlyPotential: number;
    martingaleStopLoss: number;
    martingaleBreakdown: Array<{
      level: number;
      entryAmount: number;
      profitIfWin: number;
      totalInvested: number;
    }>;
    riskAnalysis: {
      maxConsecutiveLosses: number;
      probabilityOfRuin: number;
      expectedReturn: number;
    };
  } {
    const profitabilityPercentage = 57.14; // Rentabilidade fixa do Factor50X
    const martingaleMultiplier = 2.0;
    const maxMartingaleLevels = 4;
    
    // Calcula novos valores baseados na entrada customizada
    const newEntry = customEntry * scaleFactor;
    const newProfit = newEntry * (profitabilityPercentage / 100);
    
    // Calcula potencial de lucro
    const tradesPerDay = 12;
    const winRate = 0.872; // 87.2% de acurácia
    const dailyPotential = newProfit * tradesPerDay * winRate;
    const weeklyPotential = dailyPotential * 5;
    const monthlyPotential = dailyPotential * 22;
    
    // Calcula breakdown do martingale
    const martingaleBreakdown = [];
    let totalMartingaleRisk = 0;
    
    for (let level = 1; level <= maxMartingaleLevels; level++) {
      const entryAmount = newEntry * Math.pow(martingaleMultiplier, level - 1);
      const profitIfWin = entryAmount * (profitabilityPercentage / 100);
      totalMartingaleRisk += entryAmount;
      
      martingaleBreakdown.push({
        level,
        entryAmount: Number(entryAmount.toFixed(2)),
        profitIfWin: Number(profitIfWin.toFixed(2)),
        totalInvested: Number(totalMartingaleRisk.toFixed(2))
      });
    }
    
    // Análise de risco
    const probabilityOfLoss = 1 - winRate;
    const probabilityOfRuin = Math.pow(probabilityOfLoss, maxMartingaleLevels);
    const expectedReturn = (newProfit * winRate) - (newEntry * probabilityOfLoss);
    
    return {
      newEntry: Number(newEntry.toFixed(2)),
      newProfit: Number(newProfit.toFixed(2)),
      profitPercentage: profitabilityPercentage,
      dailyPotential: Number(dailyPotential.toFixed(2)),
      weeklyPotential: Number(weeklyPotential.toFixed(2)),
      monthlyPotential: Number(monthlyPotential.toFixed(2)),
      martingaleStopLoss: Number(totalMartingaleRisk.toFixed(2)),
      martingaleBreakdown,
      riskAnalysis: {
        maxConsecutiveLosses: maxMartingaleLevels,
        probabilityOfRuin: Number((probabilityOfRuin * 100).toFixed(4)),
        expectedReturn: Number(expectedReturn.toFixed(2))
      }
    };
  }

  // Cálculo avançado de gestão de riscos
  async calculateAdvancedRisk(params: RiskCalculationParams): Promise<AdvancedRiskMetrics | null> {
    const botConfig = await this.getBotConfig(params.botId);
    if (!botConfig) return null;

    const {
      accountBalance,
      riskPercentage,
      tradingDaysPerWeek = 5,
      tradingDaysPerMonth = 22
    } = params;

    // Cálculos básicos
    const maxRiskPerTrade = (accountBalance * riskPercentage) / 100;
    const winRate = botConfig.accuracy / 100;
    const lossRate = 1 - winRate;
    
    // Tamanho de posição recomendado
    const recommendedLotSize = Math.min(
      maxRiskPerTrade / botConfig.entryAmount,
      accountBalance * 0.1
    );

    // Cálculo do Kelly Criterion para tamanho ótimo de posição
    const kellyCriterion = this.calculateKellyCriterion(
      winRate,
      botConfig.profitAmount,
      botConfig.entryAmount
    );

    const optimalPositionSize = Math.min(
      accountBalance * kellyCriterion,
      recommendedLotSize
    );

    // Valor esperado por trade
    const expectedValue = (winRate * botConfig.profitAmount) - (lossRate * botConfig.entryAmount);
    
    // Projeções de lucro
    const tradesPerDay = botConfig.averageTradesPerDay;
    const dailyExpectedProfit = expectedValue * tradesPerDay * recommendedLotSize;
    const weeklyProfit = dailyExpectedProfit * tradingDaysPerWeek;
    const monthlyProfit = dailyExpectedProfit * tradingDaysPerMonth;
    
    // Stop Loss e Stop Win dinâmicos
    const stopLoss = accountBalance * (botConfig.stopLossPercentage / 100);
    const stopWin = accountBalance * (botConfig.takeProfitPercentage / 100);
    
    // Cálculo de VaR (Value at Risk) - 95% de confiança
    const valueAtRisk = this.calculateVaR(botConfig, recommendedLotSize, 0.95);
    
    // CVaR (Conditional Value at Risk)
    const conditionalValueAtRisk = valueAtRisk * 1.3; // Aproximação
    
    // Máximo drawdown esperado
    const maxDrawdownExpected = (botConfig.backtestResults.maxDrawdown / 100) * accountBalance;
    
    // Probabilidade de ruína
    const probabilityOfRuin = this.calculateProbabilityOfRuin(
      winRate,
      botConfig.profitAmount,
      botConfig.entryAmount,
      accountBalance,
      recommendedLotSize
    );
    
    // Tempo esperado para dobrar a conta
    const expectedTimeToDoubleAccount = dailyExpectedProfit > 0 
      ? accountBalance / dailyExpectedProfit 
      : Infinity;
    
    // Volatilidade (desvio padrão dos retornos)
    const volatility = this.calculateVolatility(botConfig);
    
    // Ratios de performance
    const sharpeRatio = botConfig.backtestResults.sharpeRatio;
    const calmarRatio = (monthlyProfit * 12) / maxDrawdownExpected;
    const sortinoRatio = this.calculateSortinoRatio(botConfig, dailyExpectedProfit);
    
    // Risk/Reward Ratio
    const riskRewardRatio = botConfig.profitAmount / botConfig.entryAmount;
    
    // Máximo de dias consecutivos de perda
    const maxConsecutiveLossDays = Math.ceil(botConfig.maxConsecutiveLosses / tradesPerDay);

    return {
      dailyProfit: dailyExpectedProfit,
      weeklyProfit,
      monthlyProfit,
      stopLoss,
      stopWin,
      maxRiskPerTrade,
      recommendedLotSize,
      maxConsecutiveLossDays,
      riskRewardRatio,
      winRate: botConfig.accuracy,
      expectedValue,
      valueAtRisk,
      conditionalValueAtRisk,
      maxDrawdownExpected,
      kellyCriterion,
      optimalPositionSize,
      probabilityOfRuin,
      expectedTimeToDoubleAccount,
      volatility,
      sharpeRatio,
      calmarRatio,
      sortinoRatio
    };
  }

  private calculateKellyCriterion(winRate: number, avgWin: number, avgLoss: number): number {
    const lossRate = 1 - winRate;
    const kelly = (winRate * avgWin - lossRate * avgLoss) / avgWin;
    return Math.max(0, Math.min(kelly, 0.25)); // Limitado a 25% para segurança
  }

  private calculateVaR(botConfig: BotRiskConfig, positionSize: number, confidence: number): number {
    // Cálculo simplificado do VaR baseado em distribuição normal
    const zScore = confidence === 0.95 ? 1.645 : 2.326; // 95% ou 99%
    const volatility = this.calculateVolatility(botConfig);
    return zScore * volatility * positionSize;
  }

  private calculateProbabilityOfRuin(
    winRate: number,
    avgWin: number,
    avgLoss: number,
    accountBalance: number,
    positionSize: number
  ): number {
    // Fórmula simplificada da probabilidade de ruína
    const q = 1 - winRate; // Probabilidade de perda
    const p = winRate; // Probabilidade de ganho
    const ratio = avgLoss / avgWin;
    
    if (p === q) return 1; // Se p = q, probabilidade de ruína é 1
    
    const riskOfRuin = Math.pow((q / p) * ratio, accountBalance / positionSize);
    return Math.min(riskOfRuin, 1);
  }

  private calculateVolatility(botConfig: BotRiskConfig): number {
    // Cálculo baseado nos resultados de backtest
    const { averageWin, averageLoss, winningTrades, losingTrades } = botConfig.backtestResults;
    const totalTrades = winningTrades + losingTrades;
    const winRate = winningTrades / totalTrades;
    
    // Variância dos retornos
    const variance = winRate * Math.pow(averageWin, 2) + (1 - winRate) * Math.pow(averageLoss, 2);
    return Math.sqrt(variance);
  }

  private calculateSortinoRatio(botConfig: BotRiskConfig, expectedReturn: number): number {
    // Ratio que considera apenas a volatilidade negativa
    const { averageLoss } = botConfig.backtestResults;
    const downwardDeviation = Math.abs(averageLoss);
    return expectedReturn / downwardDeviation;
  }

  // Simula atualização de configuração no backend
  async updateBotConfig(botId: string, config: Partial<BotRiskConfig>): Promise<boolean> {
    await new Promise(resolve => setTimeout(resolve, 500));
    const existingConfig = this.botConfigs.get(botId);
    if (existingConfig) {
      this.botConfigs.set(botId, { ...existingConfig, ...config });
      return true;
    }
    return false;
  }

  // Simula análise de mercado em tempo real
  async getMarketConditions(): Promise<{
    volatility: 'low' | 'medium' | 'high';
    trend: 'bullish' | 'bearish' | 'sideways';
    riskAdjustment: number; // Multiplicador de risco baseado nas condições
  }> {
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Simula condições de mercado aleatórias
    const conditions = [
      { volatility: 'low' as const, trend: 'bullish' as const, riskAdjustment: 0.8 },
      { volatility: 'medium' as const, trend: 'sideways' as const, riskAdjustment: 1.0 },
      { volatility: 'high' as const, trend: 'bearish' as const, riskAdjustment: 1.3 }
    ];
    
    return conditions[Math.floor(Math.random() * conditions.length)];
  }
}

// Singleton instance
export const riskManagementService = new RiskManagementService();
export default riskManagementService;