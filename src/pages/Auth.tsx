
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';

const Auth = () => {
  const [isSignIn, setIsSignIn] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isSignIn) {
        const { error, success } = await signIn(email, password);
        if (error) {
          toast.error('Erro ao fazer login: ' + error.message);
        } else if (success) {
          toast.success('Login realizado com sucesso!');
          navigate('/');
        }
      } else {
        const { error, success } = await signUp(email, password);
        if (error) {
          toast.error('Erro ao criar conta: ' + error.message);
        } else if (success) {
          toast.success('Conta criada! Por favor verifique seu email para confirmação.');
          setIsSignIn(true);
        }
      }
    } catch (error: any) {
      toast.error('Ocorreu um erro: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleView = () => setIsSignIn(!isSignIn);
  const togglePasswordVisibility = () => setShowPassword(!showPassword);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="bg-card rounded-lg shadow-lg border border-border p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-foreground">Million Bots</h1>
            <p className="text-muted-foreground mt-2">
              {isSignIn ? 'Entre na sua conta' : 'Crie sua conta'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="********"
                  className="pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className="absolute right-3 top-3 text-muted-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <span className="animate-spin mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full"></span>
                  Carregando...
                </span>
              ) : isSignIn ? (
                'Entrar'
              ) : (
                'Criar conta'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <button
              type="button"
              onClick={toggleView}
              className="text-primary hover:text-primary/80 font-medium"
            >
              {isSignIn
                ? 'Não tem uma conta? Crie agora'
                : 'Já tem uma conta? Faça login'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
