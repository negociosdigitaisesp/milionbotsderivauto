
import { createClient } from '@supabase/supabase-js'

// Valores predeterminados para modo de demostración (modo offline)
const DEFAULT_SUPABASE_URL = 'https://xyzcompany.supabase.co'
const DEFAULT_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhtdGdqc2ZsYmhic3NwaWVocWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTU2NzY5OTUsImV4cCI6MjAxMTI1Mjk5NX0.demo_key'

// Intentar obtener valores desde variables de entorno
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || DEFAULT_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY

// Determinar si estamos en modo de demostración
const isDemoMode = supabaseUrl === DEFAULT_SUPABASE_URL || supabaseAnonKey === DEFAULT_SUPABASE_ANON_KEY

// Mejorar persistencia para modo demo
const DEMO_STORAGE_KEY = 'supabase.auth.token'

// Crear cliente de Supabase con manejo de errores mejorado
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  },
  global: {
    fetch: (...args) => {
      // Si estamos en modo de demostración, simular un inicio de sesión local
      if (isDemoMode) {
        console.warn('⚠️ Usando modo de demostración (offline) de Supabase. Algunas funciones estarán limitadas.')
        
        // Si es una solicitud de autenticación, simular un éxito para permitir el acceso sin DB
        const url = args[0].toString()
        if (url.includes('/auth/v1')) {
          console.info('🔑 Modo de demostración: Simulando autenticación exitosa')
          
          // Prevenir logout en modo demo
          if (url.includes('/logout')) {
            const storedSession = localStorage.getItem(DEMO_STORAGE_KEY)
            if (storedSession) {
              // Simular éxito de logout pero mantener la sesión
              localStorage.removeItem(DEMO_STORAGE_KEY)
              
              // Devolver respuesta simulada de logout exitoso
              return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ message: "Success" }),
              })
            }
          }
          
          // Simular confirmación de correo y autenticación exitosa
          if (url.includes('/signup')) {
            const requestBody = JSON.parse(args[1]?.body || '{}');
            const email = requestBody.email || 'demo@example.com';
            
            // Crear usuario simulado con email confirmado automáticamente
            const demoUser = {
              id: `demo-${Date.now()}`,
              email: email,
              email_confirmed_at: new Date().toISOString(),
              role: 'authenticated',
              confirmed_at: new Date().toISOString()
            }
            
            // Crear sesión simulada
            const sessionData = {
              access_token: `demo-token-${Date.now()}`,
              refresh_token: `demo-refresh-${Date.now()}`,
              user: demoUser,
              expires_in: 3600 * 24 * 7, // 7 días
              token_type: 'bearer'
            };
            
            // Guardar en localStorage para simular sesión activa
            localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(sessionData))
            
            // Devolver respuesta simulada de registro exitoso
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve({
                user: demoUser,
                session: sessionData
              }),
            })
          }
          
          // Manejar inicio de sesión
          if (url.includes('/token?grant_type=password')) {
            const requestBody = JSON.parse(args[1]?.body || '{}');
            const email = requestBody.email || 'demo@example.com';
            
            // Crear usuario simulado
            const demoUser = {
              id: `demo-${Date.now()}`,
              email: email,
              email_confirmed_at: new Date().toISOString(),
              role: 'authenticated',
              confirmed_at: new Date().toISOString(),
              app_metadata: {},
              user_metadata: { name: email.split('@')[0] },
              aud: 'authenticated',
              created_at: new Date().toISOString()
            }
            
            // Crear sesión simulada
            const sessionData = {
              access_token: `demo-token-${Date.now()}`,
              refresh_token: `demo-refresh-${Date.now()}`,
              user: demoUser,
              expires_in: 3600 * 24 * 7, // 7 días
              token_type: 'bearer'
            };
            
            // Guardar en localStorage para simular sesión activa
            localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(sessionData))
            
            // Devolver respuesta simulada
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve(sessionData),
            })
          }
          
          // Gestionar verificación y recuperación de sesión
          if (url.includes('/user')) {
            const storedSession = localStorage.getItem(DEMO_STORAGE_KEY)
            if (storedSession) {
              try {
                const session = JSON.parse(storedSession)
                console.info('🔑 Modo de demostración: Usando sesión almacenada')
                
                return Promise.resolve({
                  ok: true,
                  json: () => Promise.resolve({
                    data: { user: session.user }
                  }),
                })
              } catch (e) {
                console.error('Error al recuperar sesión demo:', e)
              }
            }
          }
          
          // Gestionar obtener sesión
          if (url.includes('/session')) {
            const storedSession = localStorage.getItem(DEMO_STORAGE_KEY)
            if (storedSession) {
              try {
                const sessionData = JSON.parse(storedSession)
                console.info('🔑 Modo de demostración: Recuperando sesión guardada')
                
                return Promise.resolve({
                  ok: true,
                  json: () => Promise.resolve({
                    data: { session: sessionData }
                  }),
                })
              } catch (e) {
                console.error('Error al recuperar sesión demo:', e)
              }
            }
          }
        }
      }
      
      // Para solicitudes reales, continuar normalmente
      return fetch(...args)
    }
  }
})

// Exportar la variable que indica si estamos en modo de demostración
export const isSupabaseDemoMode = isDemoMode

// Mostrar advertencias claras en la consola
if (isDemoMode) {
  console.warn('⚠️ IMPORTANTE: Estás utilizando Supabase en modo de demostración. Para habilitar la funcionalidad completa:')
  console.warn('1. Crea un proyecto en https://supabase.com')
  console.warn('2. Configura las variables de entorno VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY en un archivo .env.local')
  console.warn('3. Reinicia la aplicación')
}
