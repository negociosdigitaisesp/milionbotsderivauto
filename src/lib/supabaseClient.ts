import { createClient, SupabaseClientOptions } from '@supabase/supabase-js'

// These variables should be in a .env.local file in the project root
const supabaseUrl = import.meta.env ? import.meta.env.VITE_SUPABASE_URL : process.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env ? import.meta.env.VITE_SUPABASE_ANON_KEY : process.env.VITE_SUPABASE_ANON_KEY
const supabaseDebug = import.meta.env ? import.meta.env.VITE_SUPABASE_DEBUG === 'true' : false

// Validate configuration
const isValidUrl = (url: string | undefined): boolean => {
  if (!url) return false;
  try {
    new URL(url);
    return true;
  } catch (e) {
    return false;
  }
};

// Validate JWT format for anon key
const isValidJWT = (token: string | undefined): boolean => {
  if (!token) return false;
  // Basic JWT format check: should have three parts separated by dots
  const parts = token.split('.');
  return parts.length === 3;
};

// Check configuration and warn if not set correctly
if (!supabaseUrl || !supabaseAnonKey) {
  console.error('⚠️ Error: Supabase environment variables are not configured!');
  console.error('Make sure to create a .env.local file with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY');
} else if (!isValidUrl(supabaseUrl as string)) {
  console.error('⚠️ Error: VITE_SUPABASE_URL is not a valid URL!');
} else if (!isValidJWT(supabaseAnonKey as string)) {
  console.error('⚠️ Error: VITE_SUPABASE_ANON_KEY is not a valid JWT format!');
} else {
  console.log('Supabase configuration detected:', 
    supabaseDebug ? 
      `${supabaseUrl} (Debug Mode)` : 
      `${supabaseUrl.toString().substring(0, 15)}... (Production Mode)`);
}

// Enhanced error logging and request tracking
const enhancedFetch = (...args: Parameters<typeof fetch>): Promise<Response> => {
  const url = args[0] instanceof Request ? args[0].url : args[0].toString();
  const method = args[0] instanceof Request ? args[0].method : (args[1]?.method || 'GET');
  
  // Log request in debug mode
  if (supabaseDebug) {
    const requestId = `req_${Math.random().toString(36).substring(2, 9)}`;
    console.log(`🔄 [${requestId}] Supabase API Request: ${method} ${url.split('?')[0]}`);
    
    // Add timing for performance tracking
    const startTime = performance.now();
    
    return fetch(...args)
      .then(response => {
        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);
        
        if (!response.ok) {
          console.error(`❌ [${requestId}] Supabase API Error (${duration}ms):`, {
            status: response.status,
            statusText: response.statusText,
            url: response.url.split('?')[0],
            method
          });
        } else {
          console.log(`✅ [${requestId}] Supabase API Success (${duration}ms): ${method} ${url.split('?')[0]}`);
        }
        return response;
      })
      .catch(error => {
        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);
        
        console.error(`❌ [${requestId}] Supabase Fetch Error (${duration}ms):`, {
          error: error.message || error,
          url: url.split('?')[0],
          method
        });
        throw error;
      });
  }
  
  // Regular fetch without logging for production
  return fetch(...args)
    .catch(error => {
      console.error('Supabase Fetch Error:', error);
      throw error;
    });
};

// Create Supabase client with enhanced configuration
const supabaseOptions: SupabaseClientOptions<any> = {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    flowType: 'pkce',  // Use PKCE flow for better security
    storageKey: 'supabase.auth.token',
    debug: supabaseDebug
  },
  global: {
    fetch: enhancedFetch
  },
  // Add retry functionality
  db: {
    schema: 'public'
  },
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  }
}

export const supabase = createClient(
  supabaseUrl || '', 
  supabaseAnonKey || '', 
  supabaseOptions
)

// Add event listeners for auth state
supabase.auth.onAuthStateChange((event, session) => {
  if (supabaseDebug) {
    console.log(`🔐 Auth State Change: ${event}`, session ? 'Session present' : 'No session');
  }
  
  if (event === 'SIGNED_IN') {
    console.log('User signed in successfully');
    // Add custom analytics or tracking here if needed
  } else if (event === 'SIGNED_OUT') {
    console.log('User signed out');
    // Clean up any user-specific data in the client
  } else if (event === 'PASSWORD_RECOVERY') {
    console.log('Password recovery flow initiated');
  } else if (event === 'USER_UPDATED') {
    console.log('User information updated');
  } else if (event === 'TOKEN_REFRESHED') {
    console.log('Auth token refreshed');
  }
})

// Utility function to check if the instance is properly configured
export const isSupabaseConfigured = (): boolean => {
  return !!supabaseUrl && 
         !!supabaseAnonKey && 
         supabaseUrl !== 'undefined' && 
         supabaseAnonKey !== 'undefined' &&
         isValidUrl(supabaseUrl as string);
}

// Helper function to detect demo mode
export const isSupabaseDemoMode = !isSupabaseConfigured()

// Test the connection on initialization to detect errors early
if (isSupabaseConfigured() && supabaseDebug) {
  console.log('🔄 Testing Supabase connection...');
  supabase.auth.getSession()
    .then(({ data, error }) => {
      if (error) {
        console.error('❌ Supabase connection test failed:', error);
      } else {
        console.log('✅ Supabase connection test succeeded', 
          data.session ? 
            `Active session for ${data.session.user.email}` : 
            'No active session');
      }
    })
    .catch(err => {
      console.error('❌ Unexpected error testing Supabase connection:', err);
    });
} 

// Helper function to handle common Supabase errors
export const handleSupabaseError = (error: any): string => {
  if (!error) return 'Unknown error';
  
  // Common Supabase error codes and user-friendly messages
  const errorMessages: Record<string, string> = {
    'auth/invalid-email': 'El correo electrónico no es válido',
    'auth/user-not-found': 'Usuario no encontrado',
    'auth/wrong-password': 'Contraseña incorrecta',
    'auth/email-already-in-use': 'Este correo ya está registrado',
    'auth/weak-password': 'La contraseña es demasiado débil',
    'auth/popup-closed-by-user': 'Inicio de sesión cancelado',
    'auth/unauthorized': 'No autorizado, por favor inicie sesión nuevamente',
    'auth/requires-recent-login': 'Esta operación requiere un inicio de sesión reciente',
  };
  
  const code = error.code || '';
  const message = error.message || 'An error occurred';
  
  // Return a user-friendly message if available, otherwise the original message
  return errorMessages[code] || message;
}; 
