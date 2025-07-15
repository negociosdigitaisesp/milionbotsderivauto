-- Migração: Adicionar coluna is_active à tabela profiles
-- Data: $(date)
-- Descrição: Adiciona controle de ativação para usuários

-- Adicionar coluna is_active à tabela profiles
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;

-- Comentário na coluna
COMMENT ON COLUMN public.profiles.is_active IS 'Indica se o usuário está ativo e pode acessar o sistema';

-- Criar índice para melhor performance nas consultas
CREATE INDEX IF NOT EXISTS idx_profiles_is_active ON public.profiles(is_active);

-- Atualizar usuários existentes para ativo (opcional - remova se quiser que sejam inativos por padrão)
-- UPDATE public.profiles SET is_active = true WHERE is_active IS NULL;

-- Função para definir novos usuários como inativos por padrão
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, name, avatar_url, is_active)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    NEW.raw_user_meta_data->>'avatar_url',
    false  -- Novos usuários começam inativos
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Política RLS para permitir que usuários vejam seu próprio status is_active
CREATE POLICY "Users can view their own is_active status"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

-- Comentários para documentação
COMMENT ON TABLE public.profiles IS 'Tabela de perfis de usuários com controle de ativação';
COMMENT ON COLUMN public.profiles.is_active IS 'Controla se o usuário pode acessar o sistema após autenticação';

-- Log da migração
INSERT INTO public.migration_log (migration_name, executed_at, description)
VALUES (
  'add_is_active_to_profiles',
  NOW(),
  'Adicionada coluna is_active para controle de ativação de usuários'
) ON CONFLICT DO NOTHING;

-- Criar tabela de log de migrações se não existir
CREATE TABLE IF NOT EXISTS public.migration_log (
  id SERIAL PRIMARY KEY,
  migration_name VARCHAR(255) UNIQUE NOT NULL,
  executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  description TEXT
);