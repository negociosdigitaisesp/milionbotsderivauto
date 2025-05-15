-- Full Database Setup for Million Bots Platform
-- Execute on your Supabase project: db.xzbuustfkngfonlpsoxw.supabase.co

-- Enable necessary extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schema for application tables (if needed)
CREATE SCHEMA IF NOT EXISTS public;

-- 1. User Profiles Table - Extended user information
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT,
  email TEXT,
  phone TEXT,
  company TEXT,
  location TEXT,
  bio TEXT,
  theme TEXT DEFAULT 'system',
  accent_color TEXT DEFAULT 'blue',
  animations_enabled BOOLEAN DEFAULT TRUE,
  reduce_motion BOOLEAN DEFAULT FALSE,
  compact_mode BOOLEAN DEFAULT FALSE,
  email_notifications BOOLEAN DEFAULT TRUE,
  push_notifications BOOLEAN DEFAULT TRUE,
  trading_alerts BOOLEAN DEFAULT TRUE,
  news_updates BOOLEAN DEFAULT FALSE,
  critical_alerts_enabled BOOLEAN DEFAULT TRUE,
  sounds_enabled BOOLEAN DEFAULT TRUE,
  language TEXT DEFAULT 'es-ES',
  time_format TEXT DEFAULT '24h',
  currency TEXT DEFAULT 'USD',
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

-- 2. Bots Table - Store information about trading bots
CREATE TABLE IF NOT EXISTS public.bots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  strategy TEXT NOT NULL,
  accuracy INTEGER NOT NULL,
  operations INTEGER DEFAULT 0,
  image_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  version TEXT DEFAULT '1.0.0',
  author TEXT,
  profit_factor NUMERIC(5,2) DEFAULT 1.0,
  expectancy NUMERIC(5,2) DEFAULT 0.0,
  drawdown INTEGER DEFAULT 0,
  risk_level INTEGER DEFAULT 5,
  code TEXT,
  usage_instructions TEXT,
  is_favorite BOOLEAN DEFAULT FALSE
);

-- 3. Bot Assets Table - Which assets each bot can trade
CREATE TABLE IF NOT EXISTS public.bot_assets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID NOT NULL REFERENCES public.bots(id) ON DELETE CASCADE,
  asset_name TEXT NOT NULL,
  UNIQUE(bot_id, asset_name)
);

-- 4. User Favorites - Track which bots are favorited by users
CREATE TABLE IF NOT EXISTS public.user_favorites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL REFERENCES public.bots(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, bot_id)
);

-- 5. User Bot Usage - Track bot usage statistics by users
CREATE TABLE IF NOT EXISTS public.user_bot_usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL REFERENCES public.bots(id) ON DELETE CASCADE,
  start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  end_time TIMESTAMP WITH TIME ZONE,
  trades_opened INTEGER DEFAULT 0,
  trades_closed INTEGER DEFAULT 0,
  profit_loss NUMERIC(15,2) DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  losing_trades INTEGER DEFAULT 0
);

-- 6. Analytics Data - Store aggregated analytics data
CREATE TABLE IF NOT EXISTS public.analytics_data (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  bot_id UUID REFERENCES public.bots(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  active_users INTEGER DEFAULT 0,
  total_operations INTEGER DEFAULT 0,
  average_accuracy NUMERIC(5,2) DEFAULT 0,
  UNIQUE(bot_id, date)
);

-- Triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the timestamp trigger to all tables with updated_at
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON public.user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bots_updated_at
  BEFORE UPDATE ON public.bots
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) Policies
-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bot_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_bot_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_data ENABLE ROW LEVEL SECURITY;

-- User Profiles policies
CREATE POLICY "Users can view only their own profiles"
  ON public.user_profiles FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own profiles"
  ON public.user_profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update only their own profiles"
  ON public.user_profiles FOR UPDATE
  USING (auth.uid() = user_id);

-- Bots policies (all users can view, only admin can modify)
CREATE POLICY "Anyone can view bots"
  ON public.bots FOR SELECT
  USING (true);

CREATE POLICY "Only admins can insert bots"
  ON public.bots FOR INSERT
  WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Only admins can update bots"
  ON public.bots FOR UPDATE
  USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Only admins can delete bots"
  ON public.bots FOR DELETE
  USING (auth.jwt() ->> 'role' = 'admin');

-- Bot Assets policies
CREATE POLICY "Anyone can view bot assets"
  ON public.bot_assets FOR SELECT
  USING (true);

-- User Favorites policies
CREATE POLICY "Users can view only their own favorites"
  ON public.user_favorites FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own favorites"
  ON public.user_favorites FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own favorites"
  ON public.user_favorites FOR DELETE
  USING (auth.uid() = user_id);

-- User Bot Usage policies
CREATE POLICY "Users can view only their own bot usage"
  ON public.user_bot_usage FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own bot usage"
  ON public.user_bot_usage FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own bot usage"
  ON public.user_bot_usage FOR UPDATE
  USING (auth.uid() = user_id);

-- Analytics Data policies
CREATE POLICY "Anyone can view analytics data"
  ON public.analytics_data FOR SELECT
  USING (true);

CREATE POLICY "Only admins can modify analytics data"
  ON public.analytics_data FOR ALL
  USING (auth.jwt() ->> 'role' = 'admin');

-- Supabase Auth Settings
-- IMPORTANT: Execute this in the Supabase SQL Editor
UPDATE auth.config
SET confirm_email_change_email_template = 'Change your email',
    confirmation_template = 'Verify your email',
    security_email_template = 'Security alert',
    recovery_template = 'Reset your password',
    invite_template = 'You have been invited',
    magic_link_template = 'Your login link',
    email_confirm_changes_template = 'Confirm email changes',
    sms_template = 'Your login code',
    external_email_redirect = true,
    enable_confirmations = true,
    enable_phone_signup = true,
    enable_email_signup = true,
    mailer_autoconfirm = false,
    sms_autoconfirm = false,
    double_confirm_changes = true,
    enable_email_password_login = true,
    enable_phone_login = true;

-- Insert sample bot data for testing
INSERT INTO public.bots (id, name, description, strategy, accuracy, operations, version, author, profit_factor, expectancy, drawdown, risk_level, usage_instructions)
VALUES
  (uuid_generate_v4(), 'OptinTrade', 'Bot designed for Synthetic Indices (R_100) using SMA crossover to identify short-term trends and execute Run High/Low contracts with a specialized Martingale recovery system.', 'Seguidor de Tendência', 72, 632, '1.3.2', 'TrendTech Trading', 1.6, 0.38, 25, 7, 'Detailed instructions for OptinTrade bot setup'),
  (uuid_generate_v4(), 'SMA Trend Follower', 'Bot diseñado para Índices Sintéticos (R_100) que utiliza el cruce de SMA para identificar tendencias de corto plazo y ejecutar contratos Higher/Lower con un sistema especializado de recuperación Martingale.', 'Seguidor de Tendencia', 78, 487, '1.2.1', 'TrendTech Trading', 1.7, 0.42, 22, 6, 'Detailed instructions for SMA Trend Follower bot setup'),
  (uuid_generate_v4(), 'Hunter Pro', 'Bot que combina análise do penúltimo dígito do preço tick (filtrado para 7) com estratégia de cruzamento de SMAs para operações Rise/Fall em índices aleatórios, com recuperação Martingale agressiva.', 'Digital Filter', 45, 312, '1.0.0', 'HunterTech Trading', 1.5, 0.38, 30, 8, 'Detailed instructions for Hunter Pro bot setup');

-- Connect bots with their tradable assets
INSERT INTO public.bot_assets (bot_id, asset_name)
SELECT id, 'R_100' FROM public.bots WHERE name = 'OptinTrade'
UNION ALL
SELECT id, 'R_100' FROM public.bots WHERE name = 'SMA Trend Follower'
UNION ALL
SELECT id, 'R_100' FROM public.bots WHERE name = 'Hunter Pro';

-- Instructions
COMMENT ON DATABASE postgres IS 'Million Bots Platform - Trading Bot Management System'; 
COMMENT ON TABLE public.user_profiles IS 'Extended user profile information beyond Supabase auth';
COMMENT ON TABLE public.bots IS 'Trading bot definitions and metadata';
COMMENT ON TABLE public.bot_assets IS 'Assets that each trading bot can trade';
COMMENT ON TABLE public.user_favorites IS 'User-favorited bots for quick access';
COMMENT ON TABLE public.user_bot_usage IS 'Tracking of bot usage by users';
COMMENT ON TABLE public.analytics_data IS 'Aggregated analytics data for dashboards';

-- Important notes for Supabase:
-- 1. Configure Authentication > URL Configuration 
--    Site URL: https://your-domain.com (or http://localhost:5173 for development)
--    Add Redirect URLs:
--    - https://your-domain.com/auth/callback
--    - http://localhost:5173/auth/callback (for development)
-- 
-- 2. In Authentication > Email Templates, ensure templates are properly configured
--    Especially the confirmation email template
-- 
-- 3. For production, consider setting up SMTP for reliable email delivery 