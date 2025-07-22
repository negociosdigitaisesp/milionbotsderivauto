import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { toast } from 'sonner';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [message, setMessage] = useState('Procesando su confirmación...');
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Track callback processing for analytics/debugging
    const callbackStartTime = performance.now();
    console.log('Auth callback initiated, processing URL parameters');
    
    // Handle the auth callback to confirm user email
    const handleAuthCallback = async () => {
      try {
        setIsProcessing(true);
        
        // First check if we have auth parameters in the URL hash (PKCE flow)
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');
        const type = hashParams.get('type');
        const error = hashParams.get('error');
        const errorDescription = hashParams.get('error_description');
        
        // Check for errors in hash params
        if (error) {
          console.error('Auth error from hash:', error, errorDescription);
          setError(`Error en la autenticación: ${errorDescription || error}`);
          setMessage(`Error en la autenticación: ${errorDescription || error}`);
          toast.error(`Error: ${errorDescription || error}`);
          
          setTimeout(() => navigate('/login'), 3000);
          return;
        }
        
        // If we have an access token in the hash params, use it to set a session
        if (accessToken) {
          console.log('Access token found in URL hash, setting session...');
          
          const { error: sessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken || '',
          });
          
          if (sessionError) {
            console.error('Error setting session from hash params:', sessionError);
            setError('Error al confirmar su cuenta. Por favor intente nuevamente.');
            setMessage('Error al confirmar su cuenta. Por favor intente nuevamente.');
            toast.error('Error al confirmar su cuenta');
            
            setTimeout(() => navigate('/login'), 3000);
            return;
          }
          
          // Get the updated session after setting it
          const { data: updatedSession, error: getUserError } = await supabase.auth.getSession();
          
          if (getUserError || !updatedSession.session) {
            console.error('Error getting updated session after setting access token:', getUserError);
            setError('Error al recuperar su sesión después de la confirmación.');
            toast.error('Error al confirmar su cuenta');
            
            setTimeout(() => navigate('/login'), 3000);
            return;
          }
          
          // If this was an email confirmation, signup, or password recovery
          if (type === 'signup' || type === 'recovery' || type === 'email_change') {
            console.log(`Auth action "${type}" completed successfully`);
            
            if (type === 'signup') {
              setMessage('¡Su cuenta ha sido confirmada correctamente!');
              toast.success('¡Cuenta confirmada con éxito!');
            } else if (type === 'recovery') {
              setMessage('¡Contraseña actualizada correctamente!');
              toast.success('¡Contraseña actualizada!');
            } else if (type === 'email_change') {
              setMessage('¡Correo electrónico actualizado correctamente!');
              toast.success('¡Correo electrónico actualizado!');
            }
            
            // Redirect to library (ranking) after successful action
        setTimeout(() => navigate('/'), 2000);
            return;
          } else {
            // For other auth actions
            console.log('Authentication action completed successfully');
            setMessage('Autenticación completada. Redirigiendo...');
            toast.success('Autenticación exitosa');
            
            // Redirect to library (ranking)
        setTimeout(() => navigate('/'), 2000);
            return;
          }
        }
        
        // If no hash params with tokens, check the URL params (old flow or custom redirects)
        const urlParams = new URLSearchParams(window.location.search);
        const urlError = urlParams.get('error');
        const urlErrorDescription = urlParams.get('error_description');
        const urlType = urlParams.get('type');
        
        // Check for errors in URL query params
        if (urlError) {
          console.error('Auth error from URL params:', urlError, urlErrorDescription);
          setError(`Error en la autenticación: ${urlErrorDescription || urlError}`);
          setMessage(`Error en la autenticación: ${urlErrorDescription || urlError}`);
          toast.error(`Error: ${urlErrorDescription || urlError}`);
          
          setTimeout(() => navigate('/login'), 3000);
          return;
        }
        
        // Try to get the current session as a fallback
        const { data: sessionData } = await supabase.auth.getSession();
        
        // If we have a session, redirect to the library (ranking)
        if (sessionData.session) {
          console.log('Existing session found, redirecting to library');
          setMessage('Sesión existente encontrada. Redirigiendo...');
          toast.success('Iniciando sesión con su cuenta existente');
          
          // Redirect to library (ranking)
          setTimeout(() => navigate('/'), 2000);
          return;
        }
        
        // No tokens or session found, redirect to login
        console.log('No authentication information found');
        setMessage('No se encontró información de autenticación. Redirigiendo al inicio de sesión...');
        toast.error('No se pudo completar la autenticación');
        
        setTimeout(() => navigate('/login'), 2000);
      } catch (error: any) {
        const callbackEndTime = performance.now();
        const duration = (callbackEndTime - callbackStartTime).toFixed(2);
        
        console.error(`Auth callback failed after ${duration}ms:`, error);
        setError('Ocurrió un error inesperado. Redirigiendo al inicio de sesión...');
        setMessage('Ocurrió un error inesperado. Redirigiendo al inicio de sesión...');
        toast.error('Error al procesar la autenticación');
        
        // Redirect to login
        setTimeout(() => navigate('/login'), 3000);
      } finally {
        const callbackEndTime = performance.now();
        const duration = (callbackEndTime - callbackStartTime).toFixed(2);
        
        console.log(`Auth callback processing completed in ${duration}ms`);
        setIsProcessing(false);
      }
    };
    
    handleAuthCallback();
  }, [navigate]);
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 space-y-4 bg-card rounded-lg shadow-md border border-border">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Confirmación de Cuenta</h1>
          <div className="mt-6">
            {isProcessing && (
              <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
            )}
            <p className={`text-muted-foreground ${error ? 'text-red-500' : ''}`}>{message}</p>
            
            {error && (
              <div className="mt-4">
                <p className="text-sm text-muted-foreground">
                  Si continúa teniendo problemas, por favor póngase en contacto con soporte 
                  o intente <button 
                    onClick={() => navigate('/login')} 
                    className="text-primary underline hover:text-primary/80"
                  >
                    iniciar sesión
                  </button> nuevamente.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthCallback;