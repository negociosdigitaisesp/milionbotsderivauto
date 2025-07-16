import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Button } from '../components/ui/button';
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { derivApiService } from '../services/derivApiService';
import { useAuth } from '../contexts/AuthContext';

const DerivCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processando autorização...');

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // Verificar se o usuário está logado
      if (!user) {
        setStatus('error');
        setMessage('Você precisa estar logado para conectar com a Deriv.');
        return;
      }

      // Obter parâmetros da URL
      const code = searchParams.get('code');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      if (error) {
        setStatus('error');
        setMessage(`Erro na autorização: ${errorDescription || error}`);
        return;
      }

      if (!code) {
        setStatus('error');
        setMessage('Código de autorização não encontrado.');
        return;
      }

      // Processar o token - trocar código por token de acesso
      setMessage('Trocando código por token de acesso...');
      
      const redirectUri = `${window.location.origin}/deriv/callback`;
      const accessToken = await derivApiService.exchangeCodeForToken(code, redirectUri);

      // Armazenar o token
      setMessage('Salvando token de acesso...');
      await derivApiService.storeUserToken(user.id, accessToken);

      setStatus('success');
      setMessage('Conta Deriv conectada com sucesso!');

      // Redirecionar após 3 segundos
      setTimeout(() => {
        navigate('/deriv-integration');
      }, 3000);

    } catch (error) {
      console.error('Erro no callback:', error);
      setStatus('error');
      setMessage('Erro ao processar autorização: ' + (error as Error).message);
    }
  };

  const handleRetry = () => {
    setStatus('processing');
    setMessage('Tentando novamente...');
    handleCallback();
  };

  const handleGoBack = () => {
    navigate('/deriv-integration');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            {status === 'processing' && <RefreshCw className="h-5 w-5 animate-spin" />}
            {status === 'success' && <CheckCircle className="h-5 w-5 text-green-500" />}
            {status === 'error' && <AlertCircle className="h-5 w-5 text-red-500" />}
            Autorização Deriv
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert className={
            status === 'success' ? 'border-green-500/50 bg-green-50' :
            status === 'error' ? 'border-red-500/50 bg-red-50' :
            'border-blue-500/50 bg-blue-50'
          }>
            <AlertDescription className={
              status === 'success' ? 'text-green-700' :
              status === 'error' ? 'text-red-700' :
              'text-blue-700'
            }>
              {message}
            </AlertDescription>
          </Alert>

          {status === 'success' && (
            <div className="text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                Redirecionando para o painel de integração...
              </p>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-2">
              <Button onClick={handleRetry} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Tentar Novamente
              </Button>
              <Button onClick={handleGoBack} variant="outline" className="w-full">
                Voltar ao Painel
              </Button>
            </div>
          )}

          {status === 'processing' && (
            <div className="text-center">
              <div className="animate-pulse space-y-2">
                <div className="h-2 bg-muted rounded w-3/4 mx-auto"></div>
                <div className="h-2 bg-muted rounded w-1/2 mx-auto"></div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DerivCallback;