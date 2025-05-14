
import { createClient } from '@supabase/supabase-js'

// Estas variáveis deveriam estar em um arquivo .env.local na raíz do projeto
const supabaseUrl = import.meta.env ? import.meta.env.VITE_SUPABASE_URL : process.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env ? import.meta.env.VITE_SUPABASE_ANON_KEY : process.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('¡Error: las variables de entorno de Supabase no están configuradas!')
  console.error('Asegúrate de crear un archivo .env.local con VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY')
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '') 
