// Este arquivo foi removido - serviço da API Deriv descontinuado
// A integração com a Deriv foi removida da aplicação

export interface DerivAccount {
  loginid: string;
  currency: string;
  balance: number;
  country: string;
  email: string;
}

export interface BotConfig {
  name: string;
  symbol: string;
  amount: number;
  duration: number;
  duration_unit: string;
  contract_type: string;
  barrier?: string;
}

export interface TradeResult {
  id: string;
  symbol: string;
  buy_price: number;
  sell_price?: number;
  profit?: number;
  status: 'open' | 'won' | 'lost';
  timestamp: Date;
  contract_id?: string;
}

// Serviço removido - apenas mantendo interfaces para compatibilidade
export const derivApiService = {
  generateAuthUrl: () => '',
  exchangeCodeForToken: () => Promise.resolve(''),
  storeUserToken: () => Promise.resolve(),
  getUserToken: () => Promise.resolve(null),
  hasValidToken: () => Promise.resolve(false),
  removeUserToken: () => Promise.resolve(),
  getAccountInfo: () => Promise.resolve(null),
  getUserActiveBots: () => Promise.resolve([]),
  getTradeHistory: () => Promise.resolve([]),
  activateBot: () => Promise.resolve(),
  deactivateBot: () => Promise.resolve()
};