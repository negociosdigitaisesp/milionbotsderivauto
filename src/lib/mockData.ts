
// Mock data for the TradeBots Dashboard

export interface Bot {
  id: string;
  name: string;
  description: string;
  strategy: string;
  accuracy: number;
  downloads: number;
  imageUrl: string;
  createdAt: string;
  updatedAt: string;
  version: string;
  author: string;
  profitFactor: number;
  expectancy: number;
  drawdown: number;
  riskLevel: number;
  tradedAssets: string[];
  code: string;
}

export interface PerformanceData {
  date: string;
  value: number;
}

// Generate some performance data
const generatePerformanceData = (length: number, isPositive: boolean, startValue: number): PerformanceData[] => {
  const data: PerformanceData[] = [];
  let current = startValue;
  
  for (let i = 0; i < length; i++) {
    // Generate a date that's i days ago from today
    const date = new Date();
    date.setDate(date.getDate() - (length - i));
    
    // Generate a value that trends upward or downward slightly
    const variation = Math.random() * 5;
    if (isPositive) {
      current += variation;
    } else {
      current -= variation;
      if (current < 0) current = 0; // Prevent negative values
    }
    
    data.push({
      date: date.toISOString().split('T')[0],
      value: parseFloat(current.toFixed(2))
    });
  }
  
  return data;
};

// Example strategy code snippets
const strategyCode = {
  movingAverage: `// Moving Average Crossover Strategy
function initialize() {
  // Define indicators
  this.fastMA = SMA(14);
  this.slowMA = SMA(28);
}

function onTick(tick) {
  // Calculate indicators
  const fastValue = this.fastMA.calculate(tick.close);
  const slowValue = this.slowMA.calculate(tick.close);
  
  // Trading logic
  if (fastValue > slowValue && !this.position) {
    // Bullish crossover - Buy signal
    this.buy(tick.symbol, 1);
  } else if (fastValue < slowValue && this.position > 0) {
    // Bearish crossover - Sell signal
    this.sell(tick.symbol, 1);
  }
}`,
  
  gridTrading: `// Grid Trading Strategy
function initialize() {
  // Strategy parameters
  this.gridSize = 10;      // Number of grid levels
  this.gridSpacing = 50;   // Price difference between grid levels
  this.basePrice = 1000;   // Base price for grid calculation
  this.grids = [];
  
  // Create grid levels
  this.setupGrids();
}

function setupGrids() {
  for (let i = 0; i < this.gridSize; i++) {
    const buyLevel = this.basePrice - (i * this.gridSpacing);
    const sellLevel = this.basePrice + (i * this.gridSpacing);
    
    this.grids.push({
      buyLevel: buyLevel,
      sellLevel: sellLevel,
      isBuyActive: true,
      isSellActive: true
    });
  }
}

function onTick(tick) {
  const price = tick.close;
  
  // Check each grid level
  for (const grid of this.grids) {
    // Buy orders
    if (price <= grid.buyLevel && grid.isBuyActive) {
      this.buy(tick.symbol, 0.1);
      grid.isBuyActive = false;
    }
    
    // Sell orders
    if (price >= grid.sellLevel && grid.isSellActive) {
      this.sell(tick.symbol, 0.1);
      grid.isSellActive = false;
    }
    
    // Reset grid levels
    if (price > grid.buyLevel + this.gridSpacing) {
      grid.isBuyActive = true;
    }
    
    if (price < grid.sellLevel - this.gridSpacing) {
      grid.isSellActive = true;
    }
  }
}`,
  
  rsi: `// RSI Strategy with trend confirmation
function initialize() {
  this.rsi = RSI(14);
  this.ema = EMA(100);
  
  this.oversold = 30;
  this.overbought = 70;
}

function onTick(tick) {
  const price = tick.close;
  const rsiValue = this.rsi.calculate(price);
  const emaValue = this.ema.calculate(price);
  
  // RSI oversold and price above EMA - bullish
  if (rsiValue <= this.oversold && price > emaValue && !this.position) {
    this.buy(tick.symbol, 1);
    this.setStopLoss(price * 0.95); // 5% stop loss
  }
  
  // RSI overbought and price below EMA - bearish
  if (rsiValue >= this.overbought && price < emaValue && this.position > 0) {
    this.sell(tick.symbol, 1);
  }
}`,

  martingale: `// Martingale Strategy
function initialize() {
  this.baseLot = 0.01;        // Starting lot size
  this.maxTrades = 6;         // Maximum number of martingale steps
  this.multiplier = 2.0;      // Size multiplier after loss
  this.takeProfit = 50;       // Take profit in pips
  this.stopLoss = 20;         // Stop loss per trade in pips
  
  this.currentTrade = 0;      // Current trade number
  this.lotSize = this.baseLot;
}

function onTick(tick) {
  // Trading logic (simplified)
  if (!this.position && this.currentTrade < this.maxTrades) {
    // Open a new position
    this.buy(tick.symbol, this.lotSize);
    this.entryPrice = tick.close;
    
    // Set take profit and stop loss
    this.setTakeProfit(this.entryPrice + this.takeProfit * tick.pipValue);
    this.setStopLoss(this.entryPrice - this.stopLoss * tick.pipValue);
  }
}

function onPositionClosed(result) {
  if (result.profit > 0) {
    // Winning trade - reset martingale
    this.currentTrade = 0;
    this.lotSize = this.baseLot;
  } else {
    // Losing trade - increase lot size
    this.currentTrade++;
    this.lotSize *= this.multiplier;
  }
}`,

  arbitrage: `// Triangular Arbitrage Strategy
function initialize() {
  // Define currency pairs to monitor
  this.pairs = [
    { symbol: "EURUSD", bid: 0, ask: 0 },
    { symbol: "GBPUSD", bid: 0, ask: 0 },
    { symbol: "EURGBP", bid: 0, ask: 0 }
  ];
  
  // Minimum profit threshold to execute arbitrage (in pips)
  this.minProfit = 0.5;
}

function onTick(tick) {
  // Update prices for the relevant pair
  for (let pair of this.pairs) {
    if (tick.symbol === pair.symbol) {
      pair.bid = tick.bid;
      pair.ask = tick.ask;
    }
  }
  
  // Check if we have prices for all pairs
  if (this.pairs.every(pair => pair.bid > 0 && pair.ask > 0)) {
    this.checkArbitrage();
  }
}

function checkArbitrage() {
  // Extract prices
  const eurUsdBid = this.pairs[0].bid;
  const eurUsdAsk = this.pairs[0].ask;
  const gbpUsdBid = this.pairs[1].bid;
  const gbpUsdAsk = this.pairs[1].ask;
  const eurGbpBid = this.pairs[2].bid;
  const eurGbpAsk = this.pairs[2].ask;
  
  // Path 1: EUR -> USD -> GBP -> EUR
  const path1 = (1 / eurUsdAsk) * gbpUsdBid * eurGbpBid;
  
  // Path 2: EUR -> GBP -> USD -> EUR
  const path2 = eurGbpBid * (1 / gbpUsdAsk) * eurUsdBid;
  
  // Calculate potential profit
  const profit1 = path1 - 1;
  const profit2 = path2 - 1;
  
  // Execute trades if profit exceeds minimum threshold
  if (profit1 > this.minProfit / 10000) {
    this.executeArbitrage("path1");
  } else if (profit2 > this.minProfit / 10000) {
    this.executeArbitrage("path2");
  }
}

function executeArbitrage(path) {
  // Trading logic to execute the arbitrage
  console.log("Executing arbitrage path: " + path);
  // Implementation details omitted for brevity
}`
};

// Bot mock data
export const bots: Bot[] = [
  {
    id: "1",
    name: "MovingAverage Crossover Pro",
    description: "Trading bot that uses fast and slow moving averages to identify trend changes and generate buy/sell signals.",
    strategy: "Seguidor de Tendência",
    accuracy: 68,
    downloads: 1254,
    imageUrl: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=500&auto=format&fit=crop",
    createdAt: "2023-09-15",
    updatedAt: "2024-03-20",
    version: "2.1.0",
    author: "TradingLab",
    profitFactor: 1.8,
    expectancy: 0.45,
    drawdown: 15,
    riskLevel: 3,
    tradedAssets: ["BTC/USD", "ETH/USD", "S&P 500", "EUR/USD"],
    code: strategyCode.movingAverage
  },
  {
    id: "2",
    name: "Grid Master",
    description: "Grid trading strategy that places buy and sell orders at regular price intervals to profit from market volatility.",
    strategy: "Grid Trading",
    accuracy: 75,
    downloads: 987,
    imageUrl: "https://images.unsplash.com/photo-1642790551116-18e150f248e7?q=80&w=500&auto=format&fit=crop",
    createdAt: "2023-11-05",
    updatedAt: "2024-02-18",
    version: "1.5.0",
    author: "GridMasters",
    profitFactor: 2.1,
    expectancy: 0.62,
    drawdown: 12,
    riskLevel: 2,
    tradedAssets: ["BTC/USD", "ETH/USD", "XRP/USD"],
    code: strategyCode.gridTrading
  },
  {
    id: "3",
    name: "RSI Reversal",
    description: "Uses RSI (Relative Strength Index) to identify overbought and oversold conditions to find potential market reversals.",
    strategy: "Retorno à Média",
    accuracy: 63,
    downloads: 875,
    imageUrl: "https://images.unsplash.com/photo-1640340434855-6084b1f4901c?q=80&w=500&auto=format&fit=crop",
    createdAt: "2023-12-10",
    updatedAt: "2024-04-05",
    version: "1.2.0",
    author: "QuantTraders",
    profitFactor: 1.6,
    expectancy: 0.38,
    drawdown: 18,
    riskLevel: 4,
    tradedAssets: ["EUR/USD", "GBP/USD", "USD/JPY", "Gold"],
    code: strategyCode.rsi
  },
  {
    id: "4",
    name: "Martingale Recovery",
    description: "Advanced martingale strategy that increases position size after losses to recover previous losses plus a small profit.",
    strategy: "Martingale",
    accuracy: 52,
    downloads: 543,
    imageUrl: "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=500&auto=format&fit=crop",
    createdAt: "2024-01-20",
    updatedAt: "2024-03-10",
    version: "1.0.0",
    author: "RiskMasters",
    profitFactor: 1.3,
    expectancy: 0.25,
    drawdown: 35,
    riskLevel: 7,
    tradedAssets: ["EUR/USD", "USD/CAD", "AUD/USD"],
    code: strategyCode.martingale
  },
  {
    id: "5",
    name: "Crypto Arbitrage Hunter",
    description: "Identifies and exploits price differences between cryptocurrency exchanges for risk-free profit opportunities.",
    strategy: "Arbitragem",
    accuracy: 89,
    downloads: 1432,
    imageUrl: "https://images.unsplash.com/photo-1620321023374-d1a68fbc720d?q=80&w=500&auto=format&fit=crop",
    createdAt: "2023-08-05",
    updatedAt: "2024-04-15",
    version: "3.2.1",
    author: "ArbitrageAI",
    profitFactor: 3.2,
    expectancy: 0.85,
    drawdown: 8,
    riskLevel: 2,
    tradedAssets: ["BTC/USD", "ETH/USD", "BTC/EUR", "ETH/EUR"],
    code: strategyCode.arbitrage
  },
  {
    id: "6",
    name: "Bollinger Breakout",
    description: "Identifies breakouts from Bollinger Bands to capture strong momentum moves with trailing stop loss.",
    strategy: "Breakout",
    accuracy: 58,
    downloads: 687,
    imageUrl: "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=500&auto=format&fit=crop",
    createdAt: "2024-02-15",
    updatedAt: "2024-04-10",
    version: "1.1.0",
    author: "MomentumLab",
    profitFactor: 1.7,
    expectancy: 0.42,
    drawdown: 22,
    riskLevel: 5,
    tradedAssets: ["EUR/USD", "USD/JPY", "S&P 500", "Gold"],
    code: strategyCode.movingAverage // Reusing code for simplicity
  }
];

// Dashboard stats
export const dashboardStats = {
  totalBots: bots.length,
  totalDownloads: bots.reduce((sum, bot) => sum + bot.downloads, 0),
  averageAccuracy: Math.round(bots.reduce((sum, bot) => sum + bot.accuracy, 0) / bots.length),
  activeUsers: 587,
  growth: 12.5
};

// Performance data for charts
export const performanceData = {
  profitLoss: generatePerformanceData(30, true, 1000),
  accuracy: generatePerformanceData(30, true, 50),
  volatility: generatePerformanceData(30, false, 40)
};

// Filter options
export const filterOptions = {
  strategies: [
    { label: "Seguidor de Tendência", value: "Seguidor de Tendência" },
    { label: "Grid Trading", value: "Grid Trading" },
    { label: "Retorno à Média", value: "Retorno à Média" },
    { label: "Martingale", value: "Martingale" },
    { label: "Arbitragem", value: "Arbitragem" },
    { label: "Breakout", value: "Breakout" },
    { label: "Scalping", value: "Scalping" },
  ],
  assets: [
    { label: "BTC/USD", value: "BTC/USD" },
    { label: "ETH/USD", value: "ETH/USD" },
    { label: "EUR/USD", value: "EUR/USD" },
    { label: "GBP/USD", value: "GBP/USD" },
    { label: "S&P 500", value: "S&P 500" },
    { label: "Gold", value: "Gold" },
  ]
};
