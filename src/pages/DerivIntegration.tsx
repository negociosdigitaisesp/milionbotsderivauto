import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { 
  Link, 
  Unlink, 
  User, 
  DollarSign, 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  Play, 
  Pause,
  Square,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Bot,
  AlertCircle
} from 'lucide-react';
import { derivApiService, DerivAccount, BotConfig, TradeResult } from '../services/derivApiService';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';

const DerivIntegration = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  // Estados
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [account, setAccount] = useState<DerivAccount | null>(null);
  const [activeBots, setActiveBots] = useState<BotConfig[]>([]);
  const [tradeHistory, setTradeHistory] = useState<TradeResult[]>([]);
  const [showBotForm, setShowBotForm] = useState(false);
  
  // Estados do formulário de bot
  const [botForm, setBotForm] = useState({
    name: '',
    symbol: 'R_100',
    amount: 1,
    duration: 5,
    duration_unit: 'ticks',
    contract_type: 'CALL',
    barrier: ''
  });

  useEffect(() => {
    checkConnection();
  }, [user]);

  // Verificar se usuário já está conectado
  const checkConnection = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const hasToken = await derivApiService.hasValidToken(user.id);
      setIsConnected(hasToken);
      
      if (hasToken) {
        await loadAccountData();
        await loadActiveBots();
        await loadTradeHistory();
      }
    } catch (error) {
      console.error('Erro ao verificar conexão:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Conectar com a Deriv
  const handleConnect = () => {
    if (!user) return;
    
    const redirectUri = `${window.location.origin}/deriv/callback`;
    const authUrl = derivApiService.generateAuthUrl(redirectUri);
    window.location.href = authUrl;
  };

  // Desconectar da Deriv
  const handleDisconnect = async () => {
    if (!user) return;
    
    try {
      await derivApiService.removeUserToken(user.id);
      setIsConnected(false);
      setAccount(null);
      setActiveBots([]);
      setTradeHistory([]);
      
      toast({
        title: "Desconectado",
        description: "Sua conta Deriv foi desconectada com sucesso.",
      });
    } catch (error) {
      toast({
        title: "Erro",
        description: "Erro ao desconectar da Deriv.",
        variant: "destructive",
      });
    }
  };

  // Carregar dados da conta
  const loadAccountData = async () => {
    if (!user) return;
    
    try {
      const accountData = await derivApiService.getAccountInfo(user.id);
      setAccount(accountData);
    } catch (error) {
      console.error('Erro ao carregar dados da conta:', error);
    }
  };

  // Carregar bots ativos
  const loadActiveBots = async () => {
    if (!user) return;
    
    try {
      const bots = await derivApiService.getUserActiveBots(user.id);
      setActiveBots(bots);
    } catch (error) {
      console.error('Erro ao carregar bots ativos:', error);
    }
  };

  // Carregar histórico de trades
  const loadTradeHistory = async () => {
    if (!user) return;
    
    try {
      const history = await derivApiService.getTradeHistory(user.id, 20);
      setTradeHistory(history);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    }
  };

  // Ativar bot
  const handleActivateBot = async () => {
    if (!user) return;
    
    try {
      setIsLoading(true);
      await derivApiService.activateBot(user.id, botForm);
      
      toast({
        title: "Bot Ativado",
        description: `Bot ${botForm.name} foi ativado com sucesso.`,
      });
      
      setShowBotForm(false);
      setBotForm({
        name: '',
        symbol: 'R_100',
        amount: 1,
        duration: 5,
        duration_unit: 'ticks',
        contract_type: 'CALL',
        barrier: ''
      });
      
      await loadActiveBots();
    } catch (error) {
      toast({
        title: "Erro",
        description: "Erro ao ativar bot.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Desativar bot
  const handleDeactivateBot = async (botId: string) => {
    if (!user) return;
    
    try {
      await derivApiService.deactivateBot(user.id, botId);
      
      toast({
        title: "Bot Desativado",
        description: "Bot foi desativado com sucesso.",
      });
      
      await loadActiveBots();
    } catch (error) {
      toast({
        title: "Erro",
        description: "Erro ao desativar bot.",
        variant: "destructive",
      });
    }
  };

  // Atualizar dados
  const handleRefresh = async () => {
    await checkConnection();
  };

  const formatCurrency = (value: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: currency
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin" />
          <span className="ml-2">Carregando...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Integração Deriv</h1>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* Status da Conexão */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isConnected ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-500" />
            )}
            Status da Conexão
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isConnected ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Badge variant="default" className="bg-green-500">
                  <Link className="h-3 w-3 mr-1" />
                  Conectado
                </Badge>
                <Button onClick={handleDisconnect} variant="outline" size="sm">
                  <Unlink className="h-4 w-4 mr-2" />
                  Desconectar
                </Button>
              </div>
              
              {account && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-sm text-muted-foreground">Login ID</Label>
                    <p className="font-medium">{account.loginid}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Moeda</Label>
                    <p className="font-medium">{account.currency}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Saldo</Label>
                    <p className="font-medium">{account.balance} {account.currency}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">País</Label>
                    <p className="font-medium">{account.country}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Conecte sua conta Deriv para começar a usar os bots de trading.
                </AlertDescription>
              </Alert>
              <Button onClick={handleConnect} className="w-full">
                <Link className="h-4 w-4 mr-2" />
                Conectar com Deriv
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {isConnected && (
        <>
          {/* Gerenciamento de Bots */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  Bots Ativos ({activeBots.length})
                </CardTitle>
                <Button onClick={() => setShowBotForm(true)} size="sm">
                  <Play className="h-4 w-4 mr-2" />
                  Ativar Bot
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {activeBots.length === 0 ? (
                <div className="text-center py-8">
                  <Bot className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Nenhum bot ativo no momento</p>
                  <p className="text-sm text-muted-foreground">Clique em "Ativar Bot" para começar</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activeBots.map((bot, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="space-y-1">
                        <h4 className="font-medium">{bot.name}</h4>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>Símbolo: {bot.symbol}</span>
                          <span>Valor: {bot.amount} {account?.currency}</span>
                          <span>Duração: {bot.duration} {bot.duration_unit}</span>
                          <span>Tipo: {bot.contract_type}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="default" className="bg-green-500">
                          <Activity className="h-3 w-3 mr-1" />
                          Ativo
                        </Badge>
                        <Button 
                          onClick={() => handleDeactivateBot(`${user?.id}_${bot.name}_${Date.now()}`)}
                          variant="outline" 
                          size="sm"
                        >
                          <Pause className="h-4 w-4 mr-2" />
                          Pausar
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Formulário de Ativação de Bot */}
          {showBotForm && (
            <Card>
              <CardHeader>
                <CardTitle>Ativar Novo Bot</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="botName">Nome do Bot</Label>
                    <Input
                      id="botName"
                      value={botForm.name}
                      onChange={(e) => setBotForm({...botForm, name: e.target.value})}
                      placeholder="Ex: Bot Scalping"
                    />
                  </div>
                  <div>
                    <Label htmlFor="symbol">Símbolo</Label>
                    <Select value={botForm.symbol} onValueChange={(value) => setBotForm({...botForm, symbol: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="R_100">Volatility 100 Index</SelectItem>
                        <SelectItem value="R_75">Volatility 75 Index</SelectItem>
                        <SelectItem value="R_50">Volatility 50 Index</SelectItem>
                        <SelectItem value="R_25">Volatility 25 Index</SelectItem>
                        <SelectItem value="R_10">Volatility 10 Index</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="amount">Valor da Operação</Label>
                    <Input
                      id="amount"
                      type="number"
                      min="0.35"
                      step="0.01"
                      value={botForm.amount}
                      onChange={(e) => setBotForm({...botForm, amount: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="duration">Duração</Label>
                    <Input
                      id="duration"
                      type="number"
                      min="1"
                      value={botForm.duration}
                      onChange={(e) => setBotForm({...botForm, duration: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="durationUnit">Unidade de Duração</Label>
                    <Select value={botForm.duration_unit} onValueChange={(value) => setBotForm({...botForm, duration_unit: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ticks">Ticks</SelectItem>
                        <SelectItem value="seconds">Segundos</SelectItem>
                        <SelectItem value="minutes">Minutos</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="contractType">Tipo de Contrato</Label>
                    <Select value={botForm.contract_type} onValueChange={(value) => setBotForm({...botForm, contract_type: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="CALL">Call (Higher)</SelectItem>
                        <SelectItem value="PUT">Put (Lower)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleActivateBot} disabled={isLoading || !botForm.name}>
                    {isLoading ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    Ativar Bot
                  </Button>
                  <Button onClick={() => setShowBotForm(false)} variant="outline">
                    Cancelar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Histórico de Trades */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Histórico de Trades
              </CardTitle>
            </CardHeader>
            <CardContent>
              {tradeHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Nenhum trade realizado ainda</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {tradeHistory.map((trade) => (
                    <div key={trade.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-full ${
                          trade.status === 'won' ? 'bg-green-100 text-green-600' :
                          trade.status === 'lost' ? 'bg-red-100 text-red-600' :
                          'bg-yellow-100 text-yellow-600'
                        }`}>
                          {trade.status === 'won' ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : trade.status === 'lost' ? (
                            <TrendingDown className="h-4 w-4" />
                          ) : (
                            <Activity className="h-4 w-4" />
                          )}
                        </div>
                        <div>
                           <p className="font-medium">{trade.symbol}</p>
                           <p className="text-sm text-muted-foreground">
                             {formatDateTime(trade.timestamp)}
                           </p>
                         </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">
                          {formatCurrency(trade.buy_price, account?.currency)}
                        </p>
                        {trade.profit && (
                          <p className={`text-sm ${
                            trade.profit > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {trade.profit > 0 ? '+' : ''}{formatCurrency(trade.profit, account?.currency)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Estatísticas Resumidas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 rounded-full">
                    <DollarSign className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total de Trades</p>
                    <p className="text-2xl font-bold">{tradeHistory.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-100 rounded-full">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Trades Ganhos</p>
                    <p className="text-2xl font-bold text-green-600">
                      {tradeHistory.filter(t => t.status === 'won').length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-red-100 rounded-full">
                    <TrendingDown className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Trades Perdidos</p>
                    <p className="text-2xl font-bold text-red-600">
                      {tradeHistory.filter(t => t.status === 'lost').length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Aviso de Segurança */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Aviso de Segurança:</strong> Seus tokens de acesso são armazenados de forma criptografada. 
          Nunca compartilhe suas credenciais da Deriv com terceiros. Esta integração permite que nossa 
          plataforma execute operações em sua conta conforme a configuração dos bots selecionados.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default DerivIntegration;