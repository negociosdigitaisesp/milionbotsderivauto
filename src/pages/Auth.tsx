
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Mail, Lock, Eye, EyeOff, AlertCircle, Info } from 'lucide-react';
import { Alert, AlertDescription } from '../components/ui/alert';

const Auth = () => {
  const [isSignIn, setIsSignIn] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const { signIn, signUp, isDemoMode, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  // Verificar si el usuario ya está autenticado y redirigirlo
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const validateForm = () => {
    if (email.trim() === '') {
      toast.error('Por favor ingrese su correo electrónico');
      return false;
    }
    
    if (!email.includes('@') || !email.includes('.')) {
      toast.error('Por favor ingrese un correo electrónico válido');
      return false;
    }
    
    if (password.trim() === '') {
      toast.error('Por favor ingrese su contraseña');
      return false;
    }
    
    if (password.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);

    try {
      if (isSignIn) {
        const { error, success } = await signIn(email, password);
        if (error) {
          if (error.message === 'Email verification required') {
            toast.info('Verifique su correo electrónico para activar su cuenta');
          } else if (error.message === 'Auth session or user missing' && !isRetrying) {
            // Intento de reintentación automática
            setIsRetrying(true);
            toast.info('Reintentando conexión automáticamente...');
            
            setTimeout(async () => {
              try {
                const retryResult = await signIn(email, password);
                if (retryResult.success) {
                  toast.success('¡Inicio de sesión exitoso!');
                  navigate('/');
                } else {
                  toast.error('Error al iniciar sesión: Por favor intente nuevamente');
                }
              } catch (retryError) {
                console.error('Error en reintento:', retryError);
                toast.error('Error de conexión: Por favor intente más tarde');
              } finally {
                setIsRetrying(false);
                setLoading(false);
              }
            }, 1500);
            
            return; // Salir para dejar que el reintento maneje el resto
          } else {
            toast.error('Error al iniciar sesión: ' + (error.message || 'Verifique sus credenciales'));
          }
        } else if (success) {
          toast.success('¡Inicio de sesión exitoso!');
          navigate('/');
        }
      } else {
        const { error, success } = await signUp(email, password);
        if (error) {
          if (error.message === 'Email already registered') {
            toast.info('Este correo ya está registrado. Intente iniciar sesión.');
            setIsSignIn(true);
          } else {
            toast.error('Error al crear cuenta: ' + (error.message || 'Verifique los datos ingresados'));
          }
        } else if (success) {
          if (isDemoMode) {
            toast.success('¡Cuenta creada con éxito! Iniciando sesión...');
            navigate('/');
          } else {
            toast.success('¡Cuenta creada! Por favor verifique su correo electrónico para confirmar.');
            setIsSignIn(true);
          }
        }
      }
    } catch (error: any) {
      console.error('Error completo:', error);
      toast.error('Ocurrió un error: ' + (error.message || 'Intente nuevamente'));
    } finally {
      if (!isRetrying) {
        setLoading(false);
      }
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
              {isSignIn ? 'Inicie sesión en su cuenta' : 'Cree su cuenta'}
            </p>
          </div>

          {isDemoMode && (
            <Alert className="mb-6 bg-yellow-50 border-yellow-200">
              <Info className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-yellow-700 text-sm">
                Modo demostración activo. Las credenciales se guardan localmente
                y no se requiere verificación de correo.
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Correo electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="su@correo.com"
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Contraseña
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
                  {isRetrying ? 'Reintentando...' : 'Cargando...'}
                </span>
              ) : isSignIn ? (
                'Iniciar sesión'
              ) : (
                'Crear cuenta'
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
                ? '¿No tiene una cuenta? Regístrese ahora'
                : '¿Ya tiene una cuenta? Inicie sesión'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
