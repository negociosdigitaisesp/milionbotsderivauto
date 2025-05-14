
import { createClient } from '@supabase/supabase-js'

// Valores predeterminados para modo de demostración (modo offline)
const DEFAULT_SUPABASE_URL = 'https://xyzcompany.supabase.co'
const DEFAULT_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhtdGdqc2ZsYmhic3NwaWVocWNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTU2NzY5OTUsImV4cCI6MjAxMTI1Mjk5NX0.demo_key'

// Intentar obtener valores desde variables de entorno
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || DEFAULT_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY

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
      if (supabaseUrl === DEFAULT_SUPABASE_URL) {
        console.warn('⚠️ Usando modo de demostración (offline) de Supabase. Algunas funciones estarán limitadas.')
        
        // Si es una solicitud de autenticación, simular un éxito para permitir el acceso sin DB
        const url = args[0].toString()
        if (url.includes('/auth/v1')) {
          console.info('🔑 Modo de demostración: Simulando autenticación exitosa')
          
          // Guardar usuario falso en localStorage para simular sesión
          if (url.includes('/signup') || url.includes('/token?grant_type=password')) {
            const demoUser = {
              id: 'demo-user-id',
              email: 'demo@example.com',
              role: 'authenticated'
            }
            localStorage.setItem('supabase.auth.token', JSON.stringify({
              access_token: 'demo-access-token',
              user: demoUser
            }))
          }
          
          // Devolver respuesta simulada para evitar errores
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              access_token: 'demo-access-token',
              refresh_token: 'demo-refresh-token',
              user: { id: 'demo-user-id', email: 'demo@example.com' }
            }),
          })
        }
      }
      
      // Para solicitudes reales, continuar normalmente
      return fetch(...args)
    }
  }
})

// Mostrar advertencias claras en la consola
if (supabaseUrl === DEFAULT_SUPABASE_URL) {
  console.warn('⚠️ IMPORTANTE: Estás utilizando una URL de Supabase de demostración. Para habilitar la funcionalidad completa:')
  console.warn('1. Crea un proyecto en https://supabase.com')
  console.warn('2. Configura las variables de entorno VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY en un archivo .env.local')
  console.warn('3. Reinicia la aplicación')
}

if (supabaseAnonKey === DEFAULT_SUPABASE_ANON_KEY) {
  console.warn('⚠️ Usando clave anónima predeterminada de Supabase.')
}
