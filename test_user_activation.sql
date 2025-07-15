-- Script de teste para verificar o fluxo de ativação de usuários
-- Execute este script no Supabase SQL Editor para testar o sistema

-- Primeiro, certifique-se de que a coluna is_active existe
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;

-- Criar índice se não existir
CREATE INDEX IF NOT EXISTS idx_profiles_is_active ON public.profiles(is_active);

-- Inserir usuários de teste (substitua pelos IDs reais dos usuários do seu Supabase Auth)
-- Usuário ativo (exemplo)
INSERT INTO public.profiles (id, email, name, is_active, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000001', -- Substitua pelo ID real
  'usuario.ativo@teste.com',
  'Usuário Ativo',
  true,
  NOW(),
  NOW()
) ON CONFLICT (id) DO UPDATE SET
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- Usuário inativo (exemplo)
INSERT INTO public.profiles (id, email, name, is_active, created_at, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000002', -- Substitua pelo ID real
  'usuario.inativo@teste.com',
  'Usuário Inativo',
  false,
  NOW(),
  NOW()
) ON CONFLICT (id) DO UPDATE SET
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- Consultar todos os usuários e seus status
SELECT 
  id,
  email,
  name,
  is_active,
  created_at,
  updated_at
FROM public.profiles
ORDER BY created_at DESC;

-- Para ativar um usuário específico (substitua o email)
-- UPDATE public.profiles 
-- SET is_active = true, updated_at = NOW() 
-- WHERE email = 'email@do.usuario.com';

-- Para desativar um usuário específico (substitua o email)
-- UPDATE public.profiles 
-- SET is_active = false, updated_at = NOW() 
-- WHERE email = 'email@do.usuario.com';

-- Verificar se a função handle_new_user está configurada corretamente
-- (novos usuários devem ser criados como is_active = false por padrão)
SELECT 
  schemaname,
  tablename,
  attname,
  description
FROM pg_description
JOIN pg_attribute ON pg_description.objoid = pg_attribute.attrelid 
  AND pg_description.objsubid = pg_attribute.attnum
JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
WHERE pg_namespace.nspname = 'public' 
  AND pg_class.relname = 'profiles' 
  AND pg_attribute.attname = 'is_active';