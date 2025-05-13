// Mock data for the TradeBots Dashboard

export interface Bot {
  id: string;
  name: string;
  description: string;
  strategy: string;
  accuracy: number;
  operations: number; // Changed from downloads to operations
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
  isFavorite?: boolean; // New field for favorites
  ranking?: number; // New field for ranking
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
}`,

  contrarian: `// Impulso Contrário Pro - Contrarian Martingale Strategy
function initialize() {
  // Strategy parameters
  this.baseStake = 0.35;        // Base stake amount
  this.maxLoss = 5.0;           // Max acceptable loss (moderate setting)
  this.targetProfit = 3.0;      // Expected profit (moderate setting)
  this.martingaleFactor = 1.071; // Multiplier for stake after loss
  this.nextCondition = "Rise";  // Initial condition
  
  // Tracking variables
  this.currentBalance = 0;
  this.initialBalance = this.getBalance();
  this.currentStake = this.baseStake;
}

function onTick(tick) {
  // Check if we've reached stop conditions
  if (this.currentBalance <= -this.maxLoss || this.currentBalance >= this.targetProfit) {
    this.stop("Target reached: " + this.currentBalance);
    return;
  }
  
  // Contrarian entry logic
  if (this.nextCondition === "Rise") {
    // If next expected is Rise, we bet on opposite (PUT)
    this.buyPut(tick.symbol, this.currentStake);
  } else {
    // If next expected is Fall, we bet on opposite (CALL)
    this.buyCall(tick.symbol, this.currentStake);
  }
}

function onTradeResult(result) {
  if (result.profit > 0) {
    // Winning trade - reset stake to base amount
    this.currentStake = this.baseStake;
    this.currentBalance += result.profit;
  } else {
    // Losing trade - increase stake using martingale and invert condition
    const loss = Math.abs(result.profit);
    this.currentStake = loss * this.martingaleFactor;
    this.currentBalance += result.profit;
    
    // Alternate condition after a loss
    this.nextCondition = this.nextCondition === "Rise" ? "Fall" : "Rise";
  }
}
`,
  
  smaTrendRunner: `// SMA Trend Runner Pro - SMA Crossover Strategy for Runs Contracts
function initialize() {
  // Define indicators
  this.fastSMA = SMA(1);  // Essentially the current price
  this.slowSMA = SMA(20); // 20-period SMA for trend identification
  
  // Strategy parameters
  this.initialStake = 0.35;        // Initial stake amount
  this.stopLoss = 10.0;            // Max acceptable loss
  this.targetProfit = 5.0;         // Expected profit
  this.ticksDuration = 3;          // Contract duration in ticks
  
  // Tracking variables
  this.totalProfit = 0;
  this.lastTradeResult = null;
  this.waitingForSignal = false;
}

function onTick(tick) {
  // Check if we've reached stop conditions
  if (this.totalProfit <= -this.stopLoss || this.totalProfit >= this.targetProfit) {
    this.stop("Target reached: " + this.totalProfit);
    return;
  }
  
  if (this.waitingForSignal) {
    return; // Skip this tick if we're waiting for signal confirmation
  }
  
  // Calculate indicator values
  const fastValue = this.fastSMA.calculate(tick.close);
  const slowValue = this.slowSMA.calculate(tick.close);
  
  // SMA crossover logic
  if (fastValue > slowValue) {
    // Potential uptrend - Buy RUNHIGH
    this.waitingForSignal = true;
    
    // Wait 1 second for confirmation
    setTimeout(() => {
      // Double-check the signal
      const currentFast = this.fastSMA.calculate(this.getLatestTick().close);
      const currentSlow = this.slowSMA.calculate(this.getLatestTick().close);
      
      if (currentFast > currentSlow) {
        // Signal confirmed - Buy RUNHIGH
        const stakeAmount = this.calculateStake();
        this.buyRunHigh(tick.symbol, stakeAmount, this.ticksDuration);
      }
      this.waitingForSignal = false;
    }, 1000);
  } 
  else if (fastValue < slowValue) {
    // Potential downtrend - Buy RUNLOW
    this.waitingForSignal = true;
    
    // Wait 1 second for confirmation
    setTimeout(() => {
      // Double-check the signal
      const currentFast = this.fastSMA.calculate(this.getLatestTick().close);
      const currentSlow = this.slowSMA.calculate(this.getLatestTick().close);
      
      if (currentFast < currentSlow) {
        // Signal confirmed - Buy RUNLOW
        const stakeAmount = this.calculateStake();
        this.buyRunLow(tick.symbol, stakeAmount, this.ticksDuration);
      }
      this.waitingForSignal = false;
    }, 1000);
  }
}

function calculateStake() {
  // Special Martingale recovery system
  if (this.lastTradeResult && this.lastTradeResult.profit < 0) {
    if (this.totalProfit >= -1) {
      // Small overall loss - use fixed stake
      return 0.35;
    } else {
      // Significant loss - aggressive recovery
      return this.totalProfit * -0.45;
    }
  }
  
  // Default or after win
  return this.initialStake;
}

function onTradeResult(result) {
  this.lastTradeResult = result;
  this.totalProfit += result.profit;
  
  // Log the result
  console.log(\`Trade completed: \${result.type}, Profit: \${result.profit}, Total: \${this.totalProfit}\`);
}
`,
  
  smaTrendFollower: `// SMA Trend Follower - SMA Crossover Strategy for Higher/Lower Contracts
function initialize() {
  // Define indicators
  this.fastSMA = SMA(1);  // Essentially the current price
  this.slowSMA = SMA(20); // 20-period SMA for trend identification
  
  // Strategy parameters
  this.initialStake = 0.35;        // Initial stake amount
  this.stopLoss = 10.0;            // Max acceptable loss
  this.targetProfit = 5.0;         // Expected profit
  this.ticksDuration = 10;         // Contract duration in ticks
  
  // Tracking variables
  this.totalProfit = 0;
  this.lastTradeResult = null;
  this.waitingForSignal = false;
}

function onTick(tick) {
  // Check if we've reached stop conditions
  if (this.totalProfit <= -this.stopLoss || this.totalProfit >= this.targetProfit) {
    this.stop("Target reached: " + this.totalProfit);
    return;
  }
  
  if (this.waitingForSignal) {
    return; // Skip this tick if we're waiting for signal confirmation
  }
  
  // Calculate indicator values
  const fastValue = this.fastSMA.calculate(tick.close);
  const slowValue = this.slowSMA.calculate(tick.close);
  
  // SMA crossover logic
  if (fastValue > slowValue) {
    // Potential uptrend - Buy CALL
    this.waitingForSignal = true;
    
    // Wait 1 second for confirmation
    setTimeout(() => {
      // Double-check the signal
      const currentFast = this.fastSMA.calculate(this.getLatestTick().close);
      const currentSlow = this.slowSMA.calculate(this.getLatestTick().close);
      
      if (currentFast > currentSlow) {
        // Signal confirmed - Buy CALL
        const stakeAmount = this.calculateStake();
        this.buyCall(tick.symbol, stakeAmount, this.ticksDuration);
      }
      this.waitingForSignal = false;
    }, 1000);
  } 
  else if (fastValue < slowValue) {
    // Potential downtrend - Buy PUT
    this.waitingForSignal = true;
    
    // Wait 1 second for confirmation
    setTimeout(() => {
      // Double-check the signal
      const currentFast = this.fastSMA.calculate(this.getLatestTick().close);
      const currentSlow = this.slowSMA.calculate(this.getLatestTick().close);
      
      if (currentFast < currentSlow) {
        // Signal confirmed - Buy PUT
        const stakeAmount = this.calculateStake();
        this.buyPut(tick.symbol, stakeAmount, this.ticksDuration);
      }
      this.waitingForSignal = false;
    }, 1000);
  }
}

function calculateStake() {
  // Special Martingale recovery system
  if (this.lastTradeResult && this.lastTradeResult.profit < 0) {
    if (this.totalProfit >= -1) {
      // Small overall loss - use fixed stake
      return 0.35;
    } else {
      // Significant loss - aggressive recovery
      return this.totalProfit * -0.45;
    }
  }
  
  // Default or after win
  return this.initialStake;
}

function onTradeResult(result) {
  this.lastTradeResult = result;
  this.totalProfit += result.profit;
  
  // Log the result
  console.log(\`Trade completed: \${result.type}, Profit: \${result.profit}, Total: \${this.totalProfit}\`);
}
`,

  hunterPro: `// Hunter Pro - Penultimate Digit Filter with SMA Strategy
function initialize() {
  // Define indicators
  this.fastSMA = SMA(1);  // Current price
  this.slowSMA = SMA(20); // 20-period SMA for trend identification
  
  // Strategy parameters
  this.initialStake = 0.35;        // Initial stake amount
  this.stopLoss = 10.0;            // Max acceptable loss
  this.targetProfit = 5.0;         // Expected profit
  this.ticksDuration = 5;          // Contract duration in ticks
  
  // Tracking variables
  this.totalProfit = 0;
  this.lastTradeResult = null;
  this.waitingForSignal = false;
}

function onTick(tick) {
  // Check if we've reached stop conditions
  if (this.totalProfit <= -this.stopLoss || this.totalProfit >= this.targetProfit) {
    this.stop("Target reached: " + this.totalProfit);
    return;
  }
  
  if (this.waitingForSignal) {
    return; // Skip this tick if we're waiting for signal confirmation
  }
  
  // Get the tick price and extract the penultimate digit
  const price = tick.close;
  const priceStr = price.toFixed(2); // Format to 2 decimal places
  const penultimateDigit = priceStr[priceStr.length - 2];
  
  // Primary filter: Only proceed if the penultimate digit is 7
  if (penultimateDigit !== '7') {
    return; // Skip this tick
  }
  
  // Calculate indicator values for secondary confirmation
  const fastValue = this.fastSMA.calculate(tick.close);
  const slowValue = this.slowSMA.calculate(tick.close);
  
  // SMA crossover logic
  if (fastValue > slowValue) {
    // Potential uptrend - Buy CALL
    this.waitingForSignal = true;
    
    // Wait 1 second for confirmation
    setTimeout(() => {
      // Double-check the signal
      const currentFast = this.fastSMA.calculate(this.getLatestTick().close);
      const currentSlow = this.slowSMA.calculate(this.getLatestTick().close);
      
      if (currentFast > currentSlow) {
        // Signal confirmed - Buy CALL
        const stakeAmount = this.calculateStake();
        this.buyCall(tick.symbol, stakeAmount, this.ticksDuration);
      }
      this.waitingForSignal = false;
    }, 1000);
  } 
  else if (fastValue < slowValue) {
    // Potential downtrend - Buy PUT
    this.waitingForSignal = true;
    
    // Wait 1 second for confirmation
    setTimeout(() => {
      // Double-check the signal
      const currentFast = this.fastSMA.calculate(this.getLatestTick().close);
      const currentSlow = this.slowSMA.calculate(this.getLatestTick().close);
      
      if (currentFast < currentSlow) {
        // Signal confirmed - Buy PUT
        const stakeAmount = this.calculateStake();
        this.buyPut(tick.symbol, stakeAmount, this.ticksDuration);
      }
      this.waitingForSignal = false;
    }, 1000);
  }
}

function calculateStake() {
  // Special Martingale recovery system - more aggressive than other bots
  if (this.lastTradeResult && this.lastTradeResult.profit < 0) {
    if (this.totalProfit >= -1) {
      // Small overall loss - use fixed stake
      return 0.35;
    } else {
      // Significant loss - aggressive recovery (0.5 multiplier instead of 0.45)
      return this.totalProfit * -0.5;
    }
  }
  
  // Default or after win
  return this.initialStake;
}

function onTradeResult(result) {
  this.lastTradeResult = result;
  this.totalProfit += result.profit;
  
  // Log the result
  console.log(\`Trade completed: \${result.type}, Profit: \${result.profit}, Total: \${this.totalProfit}\`);
}
`,

  quantumBot: `// Quantum Bot - Simple Alternating Direction Strategy with Martingale
function initialize() {
  // Strategy parameters
  this.baseStake = 0.35;         // Initial stake amount
  this.stopLoss = 20.0;          // Max acceptable loss
  this.targetProfit = 20.0;      // Expected profit
  this.martingaleFactor = 1.065; // Multiplier for stake after loss
  this.nextCondition = "Rise";   // Initial condition - will alternate on loss
  
  // Tracking variables
  this.totalProfit = 0;
  this.lastTradeResult = null;
  this.currentStake = this.baseStake;
}

function onTick(tick) {
  // Check if we've reached stop conditions
  if (this.totalProfit <= -this.stopLoss || this.totalProfit >= this.targetProfit) {
    this.stop(\`Target reached: \${this.totalProfit}\`);
    return;
  }
  
  // Simple alternating direction strategy
  if (this.nextCondition === "Rise") {
    // Buy CALL (Rise)
    this.buyCall(tick.symbol, this.currentStake, 1); // 1 tick duration
  } else {
    // Buy PUT (Fall)
    this.buyPut(tick.symbol, this.currentStake, 1); // 1 tick duration
  }
}

function onTradeResult(result) {
  if (result.profit > 0) {
    // Winning trade
    this.totalProfit += result.profit;
    this.currentStake = this.baseStake; // Reset to base stake
    // Keep same condition after win
  } else {
    // Losing trade
    this.totalProfit += result.profit;
    const loss = Math.abs(result.profit);
    this.currentStake = loss * this.martingaleFactor; // Martingale increase
    
    // Alternate condition after a loss
    this.nextCondition = this.nextCondition === "Rise" ? "Fall" : "Rise";
  }
  
  // Log the result
  console.log(\`Trade completed: \${result.type}, Profit: \${result.profit}, Total: \${this.totalProfit}, Next: \${this.nextCondition}\`);
}
`
};

// Bot mock data - Filtered to remove specific bots
export const bots: Bot[] = [
  {
    id: "8",
    name: "SMA Trend Runner Pro",
    description: "Bot designed for Synthetic Indices (R_100) using SMA crossover to identify short-term trends and execute Run High/Low contracts with a specialized Martingale recovery system.",
    strategy: "Seguidor de Tendência",
    accuracy: 48,
    operations: 632, // Changed from downloads to operations
    imageUrl: "https://images.unsplash.com/photo-1559526324-593bc073d938?q=80&w=500&auto=format&fit=crop",
    createdAt: "2024-01-10",
    updatedAt: "2024-05-01",
    version: "1.3.2",
    author: "TrendTech Trading",
    profitFactor: 1.6,
    expectancy: 0.38,
    drawdown: 25,
    riskLevel: 7,
    tradedAssets: ["R_100"],
    code: strategyCode.smaTrendRunner,
    isFavorite: false,
    ranking: 3
  },
  {
    id: "9",
    name: "SMA Trend Follower",
    description: "Bot designed for Synthetic Indices (R_100) using SMA crossover to identify short-term trends and execute Higher/Lower contracts with a specialized Martingale recovery system.",
    strategy: "Seguidor de Tendência",
    accuracy: 52,
    operations: 487, // Changed from downloads to operations
    imageUrl: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=500&auto=format&fit=crop",
    createdAt: "2024-02-15",
    updatedAt: "2024-05-07",
    version: "1.2.1",
    author: "TrendTech Trading",
    profitFactor: 1.7,
    expectancy: 0.42,
    drawdown: 22,
    riskLevel: 6,
    tradedAssets: ["R_100"],
    code: strategyCode.smaTrendFollower,
    isFavorite: false,
    ranking: 1
  },
  {
    id: "10",
    name: "Hunter Pro",
    description: "Bot que combina análise do penúltimo dígito do preço tick (filtrado para 7) com estratégia de cruzamento de SMAs para operações Rise/Fall em índices aleatórios, com recuperação Martingale agressiva.",
    strategy: "Digital Filter",
    accuracy: 45,
    operations: 312, // Changed from downloads to operations
    imageUrl: "https://images.unsplash.com/photo-1607799279861-4dd421887fb3?q=80&w=500&auto=format&fit=crop",
    createdAt: "2024-03-15",
    updatedAt: "2024-05-12",
    version: "1.0.0",
    author: "HunterTech Trading",
    profitFactor: 1.5,
    expectancy: 0.38,
    drawdown: 30,
    riskLevel: 8,
    tradedAssets: ["R_100"],
    code: strategyCode.hunterPro,
    isFavorite: false,
    ranking: 4
  },
  {
    id: "11",
    name: "Quantum Bot",
    description: "Bot com estratégia de alternância simples de direção e Martingale. Opera no mercado de índices sintéticos (R_100) com contratos de 1 tick de duração.",
    strategy: "Martingale",
    accuracy: 50,
    operations: 245, // Changed from downloads to operations
    imageUrl: "https://images.unsplash.com/photo-1639762681057-408e52192e55?q=80&w=500&auto=format&fit=crop",
    createdAt: "2024-04-18",
    updatedAt: "2024-05-13",
    version: "1.0.0",
    author: "QuantumTech Trading",
    profitFactor: 1.4,
    expectancy: 0.35,
    drawdown: 28,
    riskLevel: 7,
    tradedAssets: ["R_100"],
    code: strategyCode.quantumBot,
    isFavorite: false,
    ranking: 2
  }
];

// Sort bots by accuracy for ranking
bots.sort((a, b) => b.accuracy - a.accuracy);
bots.forEach((bot, index) => {
  bot.ranking = index + 1;
});

// Dashboard stats
export const dashboardStats = {
  totalBots: bots.length,
  totalOperations: bots.reduce((sum, bot) => sum + bot.operations, 0), // Changed from downloads to operations
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
    { label: "Martingale", value: "Martingale" },
    { label: "Digital Filter", value: "Digital Filter" },
  ],
  assets: [
    { label: "R_25", value: "R_25" },
    { label: "R_50", value: "R_50" },
    { label: "R_75", value: "R_75" },
    { label: "R_100", value: "R_100" },
  ]
};
