import { supabase } from '../lib/supabaseClient';

// Interfaces para tipagem
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

// Função simples de criptografia (em produção, use crypto-js ou similar)
const encryptToken = (token: string): string => {
  // Implementação básica - em produção use AES ou similar
  return btoa(unescape(encodeURIComponent(token + '_encrypted_' + Date.now())));
};

const decryptToken = (encryptedToken: string): string => {
  try {
    const decoded = decodeURIComponent(escape(atob(encryptedToken)));
    return decoded.split('_encrypted_')[0];
  } catch {
    return encryptedToken; // Fallback para tokens não criptografados
  }
};

class DerivApiService {
  private readonly APP_ID = import.meta.env.VITE_DERIV_APP_ID || '85515';
  private readonly API_TOKEN = import.meta.env.VITE_DERIV_API_TOKEN || 'R9mD6PO5A1x7rz5';
  private readonly OAUTH_URL = 'https://oauth.deriv.com/oauth2/authorize';
  private readonly TOKEN_URL = 'https://oauth.deriv.com/oauth2/token';
  private readonly WS_URL = 'wss://ws.binaryws.com/websockets/v3';
  
  // Headers padrão para simular navegador e evitar bloqueio do Cloudflare
  private readonly DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  };

  // Gerar URL de autorização OAuth
  generateAuthUrl(redirectUri: string): string {
    // DEPURAÇÃO: Verificar o APP_ID sendo usado
    console.log('🔍 DEPURAÇÃO - APP_ID no derivApiService:', this.APP_ID);
    console.log('🔍 DEPURAÇÃO - Variável de ambiente direta:', import.meta.env.VITE_DERIV_APP_ID);
    
    const params = new URLSearchParams({
      app_id: this.APP_ID,
      l: 'PT',
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'read,trade'
    });
    
    const finalUrl = `${this.OAUTH_URL}?${params.toString()}`;
    console.log('🔍 DEPURAÇÃO - URL final gerada:', finalUrl);
    
    return finalUrl;
  }

  // Trocar código de autorização por token de acesso
  async exchangeCodeForToken(code: string, redirectUri: string): Promise<string> {
    try {
      const response = await fetch(this.TOKEN_URL, {
        method: 'POST',
        headers: {
          ...this.DEFAULT_HEADERS,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          grant_type: 'authorization_code',
          client_id: this.APP_ID,
          code: code,
          redirect_uri: redirectUri
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(`OAuth Error: ${data.error_description || data.error}`);
      }

      return data.access_token;
    } catch (error) {
      console.error('Erro ao trocar código por token:', error);
      throw error;
    }
  }

  // Armazenar token do usuário de forma criptografada
  async storeUserToken(userId: string, token: string): Promise<void> {
    try {
      const encryptedToken = encryptToken(token);
      
      const { error } = await supabase
        .from('deriv_tokens')
        .upsert({
          user_id: userId,
          encrypted_token: encryptedToken
        });

      if (error) throw error;
    } catch (error) {
      console.error('Erro ao armazenar token:', error);
      throw error;
    }
  }

  // Recuperar token do usuário
  async getUserToken(userId: string): Promise<string | null> {
    try {
      const { data, error } = await supabase
        .from('deriv_tokens')
        .select('encrypted_token')
        .eq('user_id', userId)
        .single();

      if (error || !data) return null;

      return decryptToken(data.encrypted_token);
    } catch (error) {
      console.error('Erro ao recuperar token:', error);
      return null;
    }
  }

  // Conectar WebSocket com autorização e headers apropriados
  async connectWebSocket(userId: string): Promise<WebSocket | null> {
    try {
      const token = await this.getUserToken(userId);
      if (!token) throw new Error('Token não encontrado');

      // Criar WebSocket com headers apropriados
      const ws = new WebSocket(`${this.WS_URL}?app_id=${this.APP_ID}`, [], {
        headers: this.DEFAULT_HEADERS
      } as any);
      
      return new Promise((resolve, reject) => {
        ws.onopen = () => {
          // Autorizar a sessão
          ws.send(JSON.stringify({
            authorize: token
          }));
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.msg_type === 'authorize') {
            if (data.error) {
              reject(new Error(data.error.message));
            } else {
              resolve(ws);
            }
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        setTimeout(() => {
          reject(new Error('Timeout na conexão WebSocket'));
        }, 15000); // Aumentado para 15 segundos
      });
    } catch (error) {
      console.error('Erro ao conectar WebSocket:', error);
      return null;
    }
  }

  // Fazer chamada HTTP para API REST da Deriv (se necessário)
  private async makeApiCall(endpoint: string, data: any = null): Promise<any> {
    try {
      const options: RequestInit = {
        method: data ? 'POST' : 'GET',
        headers: {
          ...this.DEFAULT_HEADERS,
          'Content-Type': 'application/json'
        }
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(endpoint, options);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro na chamada da API:', error);
      throw error;
    }
  }

  // Obter informações da conta
  async getAccountInfo(userId: string): Promise<DerivAccount | null> {
    try {
      const ws = await this.connectWebSocket(userId);
      if (!ws) return null;

      return new Promise((resolve, reject) => {
        ws.send(JSON.stringify({
          get_account_status: 1
        }));

        const messageHandler = (event: MessageEvent) => {
          const data = JSON.parse(event.data);
          
          if (data.msg_type === 'get_account_status') {
            if (data.error) {
              reject(new Error(data.error.message));
            } else {
              const account: DerivAccount = {
                loginid: data.get_account_status.loginid || 'N/A',
                currency: data.get_account_status.currency || 'USD',
                balance: data.get_account_status.balance || 0,
                country: data.get_account_status.country || 'N/A',
                email: data.get_account_status.email || 'N/A'
              };
              resolve(account);
            }
            ws.close();
          }
        };

        ws.onmessage = messageHandler;

        setTimeout(() => {
          ws.close();
          reject(new Error('Timeout ao obter informações da conta'));
        }, 10000);
      });
    } catch (error) {
      console.error('Erro ao obter informações da conta:', error);
      return null;
    }
  }

  // Ativar bot (salvar configuração no banco)
  async activateBot(userId: string, botConfig: BotConfig): Promise<string> {
    try {
      const botId = `${userId}_${botConfig.name}_${Date.now()}`;
      
      const { error } = await supabase
        .from('active_bots')
        .insert({
          id: botId,
          user_id: userId,
          name: botConfig.name,
          symbol: botConfig.symbol,
          amount: botConfig.amount,
          duration: botConfig.duration,
          duration_unit: botConfig.duration_unit,
          contract_type: botConfig.contract_type,
          barrier: botConfig.barrier,
          is_active: true
        });

      if (error) throw error;

      // Log da ativação
      await this.logBotActivity(userId, botId, 'activated', { config: botConfig });

      return botId;
    } catch (error) {
      console.error('Erro ao ativar bot:', error);
      throw error;
    }
  }

  // Desativar bot
  async deactivateBot(userId: string, botId: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('active_bots')
        .update({ is_active: false })
        .eq('id', botId)
        .eq('user_id', userId);

      if (error) throw error;

      // Log da desativação
      await this.logBotActivity(userId, botId, 'deactivated', {});
    } catch (error) {
      console.error('Erro ao desativar bot:', error);
      throw error;
    }
  }

  // Obter bots ativos do usuário
  async getUserActiveBots(userId: string): Promise<BotConfig[]> {
    try {
      const { data, error } = await supabase
        .from('active_bots')
        .select('*')
        .eq('user_id', userId)
        .eq('is_active', true);

      if (error) throw error;

      return data?.map(bot => ({
        name: bot.name,
        symbol: bot.symbol,
        amount: bot.amount,
        duration: bot.duration,
        duration_unit: bot.duration_unit,
        contract_type: bot.contract_type,
        barrier: bot.barrier
      })) || [];
    } catch (error) {
      console.error('Erro ao obter bots ativos:', error);
      return [];
    }
  }

  // Obter histórico de trades
  async getTradeHistory(userId: string, limit: number = 50): Promise<TradeResult[]> {
    try {
      const { data, error } = await supabase
        .from('trade_history')
        .select('*')
        .eq('user_id', userId)
        .order('timestamp', { ascending: false })
        .limit(limit);

      if (error) throw error;

      return data?.map(trade => ({
        id: trade.id,
        symbol: trade.symbol,
        buy_price: trade.buy_price,
        sell_price: trade.sell_price,
        profit: trade.profit,
        status: trade.status,
        timestamp: new Date(trade.timestamp),
        contract_id: trade.contract_id
      })) || [];
    } catch (error) {
      console.error('Erro ao obter histórico de trades:', error);
      return [];
    }
  }

  // Registrar atividade do bot
  private async logBotActivity(userId: string, botId: string, action: string, details: any): Promise<void> {
    try {
      await supabase
        .from('bot_activity_logs')
        .insert({
          user_id: userId,
          bot_id: botId,
          action,
          details
        });
    } catch (error) {
      console.error('Erro ao registrar atividade do bot:', error);
    }
  }

  // Verificar se usuário tem token válido
  async hasValidToken(userId: string): Promise<boolean> {
    const token = await this.getUserToken(userId);
    return token !== null;
  }

  // Remover token do usuário
  async removeUserToken(userId: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('deriv_tokens')
        .delete()
        .eq('user_id', userId);

      if (error) throw error;
    } catch (error) {
      console.error('Erro ao remover token:', error);
      throw error;
    }
  }

  // Validar conexão com a API da Deriv
  async validateConnection(userId: string): Promise<boolean> {
    try {
      const ws = await this.connectWebSocket(userId);
      if (!ws) return false;

      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          ws.close();
          resolve(false);
        }, 5000);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.msg_type === 'authorize' && !data.error) {
            clearTimeout(timeout);
            ws.close();
            resolve(true);
          }
        };

        ws.onerror = () => {
          clearTimeout(timeout);
          resolve(false);
        };
      });
    } catch (error) {
      console.error('Erro ao validar conexão:', error);
      return false;
    }
  }
}

export const derivApiService = new DerivApiService();