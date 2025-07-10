
-- Admin Panel Database Setup - Controle de Acesso e Aprovação de Usuários
-- Execute este script no Supabase SQL Editor

-- 1. Adicionar campos necessários na tabela profiles (se não existirem)
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user')),
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending' CHECK (status IN ('active', 'inactive', 'pending', 'expired')),
ADD COLUMN IF NOT EXISTS full_name TEXT,
ADD COLUMN IF NOT EXISTS expiration_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES public.profiles(id);

-- 2. Definir o usuário administrador principal
UPDATE public.profiles 
SET role = 'admin', status = 'active', approved_at = NOW()
WHERE email = 'brendacostatrader@gmail.com';

-- 3. Criar função para verificar se usuário é admin
CREATE OR REPLACE FUNCTION public.is_admin(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.profiles 
    WHERE id = user_id 
    AND role = 'admin' 
    AND status = 'active'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Criar função para verificar se usuário específico é admin
CREATE OR REPLACE FUNCTION public.is_admin_by_email(user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.profiles 
    WHERE email = user_email 
    AND role = 'admin' 
    AND status = 'active'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Atualizar função de criação de usuário para status 'pending'
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, role, status)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    CASE 
      WHEN NEW.email = 'brendacostatrader@gmail.com' THEN 'admin'
      ELSE 'user'
    END,
    CASE 
      WHEN NEW.email = 'brendacostatrader@gmail.com' THEN 'active'
      ELSE 'pending'
    END
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. Atualizar políticas RLS para profiles
DROP POLICY IF EXISTS "Users can view their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Admins can update all profiles" ON public.profiles;

-- Usuários podem ver apenas seu próprio perfil
CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

-- Usuários podem atualizar apenas seu próprio perfil (campos limitados)
CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Admins podem ver todos os perfis
CREATE POLICY "Admins can view all profiles"
  ON public.profiles FOR SELECT
  USING (public.is_admin(auth.uid()));

-- Admins podem atualizar todos os perfis
CREATE POLICY "Admins can update all profiles"
  ON public.profiles FOR UPDATE
  USING (public.is_admin(auth.uid()));

-- 7. Criar view para estatísticas administrativas
CREATE OR REPLACE VIEW public.admin_stats AS
SELECT
  COUNT(*) as total_users,
  COUNT(*) FILTER (WHERE status = 'active') as active_users,
  COUNT(*) FILTER (WHERE status = 'pending') as pending_users,
  COUNT(*) FILTER (WHERE status = 'inactive') as inactive_users,
  COUNT(*) FILTER (WHERE status = 'expired') as expired_users,
  COUNT(*) FILTER (WHERE role = 'admin') as admin_users,
  COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as new_users_30d
FROM public.profiles;

-- Política para view de estatísticas (apenas admins)
CREATE POLICY "Admins can view stats"
  ON public.admin_stats FOR SELECT
  USING (public.is_admin(auth.uid()));

-- 8. Criar função para aprovar usuário
CREATE OR REPLACE FUNCTION public.approve_user(target_user_id UUID)
RETURNS VOID AS $$
BEGIN
  -- Verificar se o usuário atual é admin
  IF NOT public.is_admin(auth.uid()) THEN
    RAISE EXCEPTION 'Acesso negado: apenas administradores podem aprovar usuários';
  END IF;
  
  -- Aprovar o usuário
  UPDATE public.profiles 
  SET 
    status = 'active',
    approved_at = NOW(),
    approved_by = auth.uid()
  WHERE id = target_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. Inserir dados de exemplo se necessário (apenas para desenvolvimento)
DO $$
BEGIN
  -- Verificar se o admin principal existe
  IF NOT EXISTS (SELECT 1 FROM public.profiles WHERE email = 'brendacostatrader@gmail.com') THEN
    -- Se não existir, criar uma entrada temporária (será substituída quando o usuário se registrar)
    INSERT INTO public.profiles (id, email, full_name, role, status, created_at)
    VALUES (
      gen_random_uuid(),
      'brendacostatrader@gmail.com',
      'Brenda Costa Trader',
      'admin',
      'active',
      NOW()
    );
  END IF;
END $$;

-- 10. Comentários para documentação
COMMENT ON FUNCTION public.is_admin IS 'Verifica se um usuário específico é administrador ativo';
COMMENT ON FUNCTION public.approve_user IS 'Função para aprovar usuários (apenas admins)';
COMMENT ON VIEW public.admin_stats IS 'Estatísticas para o painel administrativo';
