/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly VITE_SUPABASE_DEBUG: string
  readonly VITE_DERIV_APP_ID: string
  readonly VITE_DERIV_API_TOKEN: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}