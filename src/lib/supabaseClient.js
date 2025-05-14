
import { createClient } from '@supabase/supabase-js'

// Valores predeterminados para desarrollo local - REEMPLAZA ESTOS CON TUS VALORES REALES DE SUPABASE
const DEFAULT_SUPABASE_URL = 'https://example.supabase.co' // URL de ejemplo que funcionará mejor con la validación
const DEFAULT_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' // Clave anónima parcial de ejemplo

// Intentar obtener valores desde variables de entorno
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || DEFAULT_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY

if (supabaseUrl === DEFAULT_SUPABASE_URL) {
  console.warn('⚠️ Usando URL predeterminada de Supabase. Por favor, configura VITE_SUPABASE_URL en tu archivo .env.local.')
}

if (supabaseAnonKey === DEFAULT_SUPABASE_ANON_KEY) {
  console.warn('⚠️ Usando clave anónima predeterminada de Supabase. Por favor, configura VITE_SUPABASE_ANON_KEY en tu archivo .env.local.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
