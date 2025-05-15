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
    // Check if we're in offline mode (using default values)
    const checkOfflineMode = () => {
      const demoToken = localStorage.getItem('supabase.auth.token');
      if (demoToken && demoToken.includes('demo-token')) {
        setIsOfflineMode(true);
        console.info('🔑 Demo mode active: Simulated authentication enabled');
        
        try {
          // Parse the demo token to get user info
          const tokenData = JSON.parse(demoToken);
          if (tokenData && tokenData.user) {
            setUser(tokenData.user as User);
            setSession(tokenData as Session);
          }
        } catch (err) {
          console.error('Error parsing demo token:', err);
          localStorage.removeItem('supabase.auth.token'); // Remove invalid token
        }
      }
    };

    // Get current session
    const getSession = async () => {
      setLoading(true);
      try {
        console.log('Retrieving Supabase session...');
        const { data, error } = await supabase.auth.getSession();
        
        if (!error && data?.session) {
          console.log('Session retrieved successfully');
          setSession(data.session);
          setUser(data.session.user);
          setIsOfflineMode(false);
        } else {
          if (error) {
            console.error('Error retrieving session:', error);
          } else {
            console.warn('No active session found');
          }
          
          // If no valid session, check if we have a refresh token to try
          const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
          if (!refreshError && refreshData?.session) {
            console.log('Session refreshed successfully');
            setSession(refreshData.session);
            setUser(refreshData.session.user);
            setIsOfflineMode(false);
          } else {
            // If still no session, check for offline mode
            checkOfflineMode();
          }
        }
      } catch (err) {
        console.error('Unexpected error retrieving session:', err);
        checkOfflineMode();
      } finally {
        setLoading(false);
      }
    };

    getSession();

    // Set up listener for auth state changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        console.log('Auth state change event:', event);
        
        if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
          console.log('User signed in or token refreshed');
          if (newSession) {
            setSession(newSession);
            setUser(newSession.user);
            setIsOfflineMode(false);
          }
        } else if (event === 'SIGNED_OUT') {
          console.log('User signed out');
          setSession(null);
          setUser(null);
          localStorage.removeItem('supabase.auth.token'); // Clean up any demo tokens
          setIsOfflineMode(false);
        } else if (event === 'USER_UPDATED') {
          console.log('User updated');
          if (newSession) {
            setSession(newSession);
            setUser(newSession.user);
          }
        }
        
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
      
      // Clear any previous session data to avoid conflicts
      await supabase.auth.signOut();
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error('Login error:', error);
        
        // Handle common error cases
        if (error.message.includes('Email not confirmed')) {
          toast.error('Por favor, verifique su correo electrónico para activar su cuenta');
          return { error, success: false };
        }
        
        toast.error(`Error al iniciar sesión: ${error.message}`);
        return { error, success: false };
      }

      // Verify that we have a valid session and user
      if (!data?.session || !data?.user) {
        console.error('Session or user missing after login');
        // If in demo mode, create a fallback session
        if (isSupabaseDemoMode) {
          // Create mock session in localStorage for demo mode
          const mockUser = {
            id: `demo-${Date.now()}`,
            email: email,
            email_confirmed_at: new Date().toISOString(),
            role: 'authenticated',
            app_metadata: {},
            user_metadata: { name: email.split('@')[0] },
            aud: 'authenticated',
            created_at: new Date().toISOString()
          } as User;
          
          const mockSession = {
            access_token: `demo-token-${Date.now()}`,
            refresh_token: `demo-refresh-${Date.now()}`,
            user: mockUser,
            expires_in: 3600,
            token_type: 'bearer'
          } as Session;
          
          localStorage.setItem('supabase.auth.token', JSON.stringify(mockSession));
          setSession(mockSession);
          setUser(mockUser);
          setIsOfflineMode(true);
          toast.success('¡Inicio de sesión exitoso (modo demo)!');
          return { error: null, success: true };
        } else {
          // Try to refresh the session once
          console.log('Attempting to refresh session...');
          const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession();
          
          if (!refreshError && refreshData?.session && refreshData?.user) {
            // Session refreshed successfully
            setSession(refreshData.session);
            setUser(refreshData.user);
            setIsOfflineMode(false);
            toast.success('¡Inicio de sesión exitoso!');
            return { error: null, success: true };
          }
          
          // Check if the account requires email verification
          const { data: userData, error: userError } = await supabase.auth.getUserIdentities();
          if (!userError && userData && userData.identities && userData.identities.length > 0) {
            const identity = userData.identities[0];
            if (identity && !identity.identity_data.email_verified) {
              toast.error('Por favor verifique su correo electrónico para activar su cuenta');
              return { 
                error: { message: 'Email verification required' }, 
                success: false 
              };
            }
          }
          
          toast.error('Error al iniciar sesión: Sesión o usuario no encontrado');
          return { 
            error: { message: 'Auth session or user missing' }, 
            success: false 
          };
        }
      }

      // Successfully authenticated
      setSession(data.session);
      setUser(data.user);
      setIsOfflineMode(false);
      toast.success('¡Inicio de sesión exitoso!');
      return { error: null, success: true };
    } catch (error: any) {
      console.error('Unexpected error during login:', error);
      toast.error(`Ocurrió un error inesperado: ${error.message}`);
      return { error, success: false };
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      setLoading(true);
      
      // In demo mode, simply register without requiring confirmation
      if (isSupabaseDemoMode) {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            // In demo mode we pretend the email is already confirmed
            emailRedirectTo: window.location.origin
          }
        });

        if (error) {
          toast.error(`Error al crear cuenta: ${error.message}`);
          return { error, success: false };
        }

        // In demo mode, we consider registration successful and direct the user
        toast.success('¡Cuenta creada con éxito! Iniciando sesión...');
        await signIn(email, password);
        navigate('/');
        return { error: null, success: true };
      } else {
        // Normal behavior with real Supabase
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            // Fix: ensure the correct redirect URL format matches your app's route
            emailRedirectTo: `${window.location.origin}/auth/callback`,
            data: {
              // Add additional user metadata if needed
              name: email.split('@')[0]
            }
          }
        });

        if (error) {
          console.error('Supabase signup error:', error);
          toast.error(`Error al crear cuenta: ${error.message}`);
          return { error, success: false };
        }

        // Check if email confirmation is needed
        if (data?.user?.identities?.length === 0) {
          toast.error('El correo ya está registrado. Intenta iniciar sesión.');
          return { 
            error: { message: 'Email already registered' }, 
            success: false 
          };
        }
        
        // Add auto-signin attempt for newly registered users
        // This will work if email confirmation is not required in Supabase settings
        if (data?.user) {
          // Check if email is confirmed or confirmation not required
          if (data.user.email_confirmed_at || data.user.confirmed_at) {
            toast.success('¡Cuenta creada! Iniciando sesión automáticamente...');
            // Try to sign in automatically
            const signInResult = await signIn(email, password);
            if (signInResult.success) {
              navigate('/');
              return { error: null, success: true };
            }
          } else {
            // Email confirmation required
            toast.success('¡Cuenta creada! Por favor verifica tu correo electrónico para confirmar.');
            return { error: null, success: true };
          }
        }
        
        return { error: null, success: true };
      }
    } catch (error: any) {
      console.error('Error during signup:', error);
      toast.error(`Error al crear cuenta: ${error.message}`);
      return { error, success: false };
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    try {
      setLoading(true);
      
      // Clear any demo tokens
      if (isOfflineMode) {
        localStorage.removeItem('supabase.auth.token');
        setSession(null);
        setUser(null);
        setIsOfflineMode(false);
        toast.success('Sesión cerrada (modo demo)');
        navigate('/login');
        return;
      }
      
      // Regular signout
      const { error } = await supabase.auth.signOut();
      
      if (error) {
        console.error('Error signing out:', error);
        toast.error(`Error al cerrar sesión: ${error.message}`);
      } else {
        setSession(null);
        setUser(null);
        toast.success('Sesión cerrada exitosamente');
        navigate('/login');
      }
    } catch (error: any) {
      console.error('Unexpected error during sign out:', error);
      toast.error(`Error al cerrar sesión: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        loading,
        signIn,
        signUp,
        signOut,
        isAuthenticated: !!session || isOfflineMode,
        isDemoMode: isSupabaseDemoMode || isOfflineMode
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
