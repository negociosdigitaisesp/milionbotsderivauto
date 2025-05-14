
-- Criar tabela de perfis de usuário
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT,
  email TEXT,
  phone TEXT,
  company TEXT,
  location TEXT,
  bio TEXT,
  theme TEXT,
  accent_color TEXT,
  animations_enabled BOOLEAN DEFAULT TRUE,
  reduce_motion BOOLEAN DEFAULT FALSE,
  compact_mode BOOLEAN DEFAULT FALSE,
  email_notifications BOOLEAN DEFAULT TRUE,
  push_notifications BOOLEAN DEFAULT TRUE,
  trading_alerts BOOLEAN DEFAULT TRUE,
  news_updates BOOLEAN DEFAULT FALSE,
  critical_alerts_enabled BOOLEAN DEFAULT TRUE,
  sounds_enabled BOOLEAN DEFAULT TRUE,
  language TEXT DEFAULT 'pt-BR',
  time_format TEXT DEFAULT '24h',
  currency TEXT DEFAULT 'BRL',
  date_format TEXT DEFAULT 'DD/MM/YYYY',
  timezone TEXT DEFAULT 'America/Sao_Paulo',
  two_factor_enabled BOOLEAN DEFAULT FALSE,
  session_timeout INTEGER DEFAULT 30,
  ip_whitelisting BOOLEAN DEFAULT FALSE,
  login_notifications BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Configurar RLS (Row Level Security)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Criar políticas de segurança
CREATE POLICY "Usuários podem visualizar apenas seus próprios perfis"
  ON user_profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Usuários podem inserir seus próprios perfis"
  ON user_profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Usuários podem atualizar apenas seus próprios perfis"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = user_id);

-- Trigger para atualizar o campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
