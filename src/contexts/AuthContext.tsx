
import React, { createContext, useState, useEffect, useContext } from 'react';
import { supabase, isSupabaseDemoMode } from '../lib/supabaseClient';
import { Session, User } from '@supabase/supabase-js';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{
    error: any | null;
    success: boolean;
  }>;
  signUp: (email: string, password: string) => Promise<{
    error: any | null;
    success: boolean;
  }>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
  isDemoMode: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOfflineMode, setIsOfflineMode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Verificar si estamos en modo offline (usando valores predeterminados)
    const checkOfflineMode = () => {
      const demoToken = localStorage.getItem('supabase.auth.token');
      if (demoToken && demoToken.includes('demo-token')) {
        setIsOfflineMode(true);
        console.info('🔑 Modo de demostración activo: Autenticación simulada habilitada');
      }
    };

    // Obtener sesión actual
    const getSession = async () => {
      setLoading(true);
      try {
        const { data, error } = await supabase.auth.getSession();
        
        if (!error && data?.session) {
          setSession(data.session);
          setUser(data.session.user);
        } else if (error) {
          console.error('Error al obtener la sesión:', error);
          checkOfflineMode();
        }
      } catch (err) {
        console.error('Error al intentar obtener la sesión:', err);
        checkOfflineMode();
      } finally {
        setLoading(false);
      }
    };

    getSession();

    // Configurar listener para cambios de autenticación
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        console.log('Evento de autenticación:', event);
        setSession(newSession);
        setUser(newSession?.user ?? null);
        setLoading(false);
      }
    );

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      setLoading(true);
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        toast.error(`Error al iniciar sesión: ${error.message}`);
        return { error, success: false };
      }

      toast.success('¡Inicio de sesión exitoso!');
      return { error: null, success: true };
    } catch (error: any) {
      toast.error(`Ocurrió un error inesperado: ${error.message}`);
      return { error, success: false };
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      setLoading(true);
      
      // En modo de demostración, simplemente hacemos el registro sin requerir confirmación
      if (isSupabaseDemoMode) {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            // En modo demo fingimos que el email ya está confirmado
            emailRedirectTo: window.location.origin
          }
        });

        if (error) {
          toast.error(`Error al crear cuenta: ${error.message}`);
          return { error, success: false };
        }

        // En modo demo, consideramos que el registro fue exitoso y dirigimos al usuario directamente
        toast.success('¡Cuenta creada con éxito! Iniciando sesión...');
        await signIn(email, password);
        navigate('/');
        return { error: null, success: true };
      } else {
        // Comportamiento normal con Supabase real
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/login`
          }
        });

        if (error) {
          toast.error(`Error al crear cuenta: ${error.message}`);
          return { error, success: false };
        }

        toast.success('¡Cuenta creada! Por favor verifica tu correo electrónico para confirmar.');
        return { error: null, success: true };
      }
    } catch (error: any) {
      toast.error(`Ocurrió un error inesperado: ${error.message}`);
      return { error, success: false };
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    await supabase.auth.signOut();
    
    // Limpiar datos de modo offline si existen
    localStorage.removeItem('supabase.auth.token');
    
    navigate('/login');
    setLoading(false);
  };

  const value = {
    session,
    user,
    loading,
    signIn,
    signUp,
    signOut,
    isAuthenticated: !!session || isOfflineMode,
    isDemoMode: isSupabaseDemoMode
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
