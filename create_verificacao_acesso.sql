-- Migração: Criar tabela verificacao_acesso
-- Descrição: Tabela para verificação de acesso com RLS

CREATE TABLE IF NOT EXISTS public.verificacao_acesso (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  pode_entrar BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Habilitar RLS
ALTER TABLE public.verificacao_acesso ENABLE ROW LEVEL SECURITY;

-- Política de bloqueio inicial
CREATE POLICY "Bloqueio_Total_Inicial" ON public.verificacao_acesso
FOR SELECT USING (FALSE);