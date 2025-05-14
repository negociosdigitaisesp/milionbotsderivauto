
import { createClient } from '@supabase/supabase-js'

// Default values for local development - REPLACE THESE WITH YOUR ACTUAL SUPABASE VALUES
const DEFAULT_SUPABASE_URL = 'https://your-supabase-project-url.supabase.co'
const DEFAULT_SUPABASE_ANON_KEY = 'your-supabase-anon-key'

// Try to get values from environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || DEFAULT_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY

if (supabaseUrl === DEFAULT_SUPABASE_URL) {
  console.warn('⚠️ Using default Supabase URL. Please set VITE_SUPABASE_URL in your .env.local file.')
}

if (supabaseAnonKey === DEFAULT_SUPABASE_ANON_KEY) {
  console.warn('⚠️ Using default Supabase Anon Key. Please set VITE_SUPABASE_ANON_KEY in your .env.local file.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey) 
