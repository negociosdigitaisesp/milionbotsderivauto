-- Full database setup script for Bot Strategy Hub
-- This script creates all necessary tables and functions for the application

-- Enable the necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create profiles table to store user data
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  website TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  plan_type TEXT DEFAULT 'free' NOT NULL,
  max_bots INTEGER DEFAULT 5,
  credits INTEGER DEFAULT 100,
  last_login TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create bots table to store bot configurations
CREATE TABLE IF NOT EXISTS public.bots (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  platform TEXT NOT NULL,
  strategy_type TEXT NOT NULL,
  configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  last_run TIMESTAMP WITH TIME ZONE,
  is_public BOOLEAN DEFAULT false,
  tags TEXT[] DEFAULT '{}'::text[],
  CONSTRAINT bots_name_user_id_key UNIQUE (name, user_id)
);

-- Create bot_assets table to store images, scripts, and other files
CREATE TABLE IF NOT EXISTS public.bot_assets (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  bot_id UUID REFERENCES public.bots(id) ON DELETE CASCADE NOT NULL,
  asset_type TEXT NOT NULL,
  file_path TEXT NOT NULL,
  content_type TEXT NOT NULL,
  size_kb INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create favorites table to allow users to save favorite bots
CREATE TABLE IF NOT EXISTS public.favorites (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) NOT NULL,
  bot_id UUID REFERENCES public.bots(id) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  CONSTRAINT favorites_user_id_bot_id_key UNIQUE (user_id, bot_id)
);

-- Create analytics_data table to store bot performance metrics
CREATE TABLE IF NOT EXISTS public.analytics_data (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  bot_id UUID REFERENCES public.bots(id) ON DELETE CASCADE NOT NULL,
  date DATE NOT NULL,
  impressions INTEGER DEFAULT 0,
  engagement INTEGER DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  conversions INTEGER DEFAULT 0,
  revenue DECIMAL(10,2) DEFAULT 0,
  cost DECIMAL(10,2) DEFAULT 0,
  platform_data JSONB DEFAULT '{}'::jsonb,
  CONSTRAINT analytics_data_bot_id_date_key UNIQUE (bot_id, date)
);

-- Create bot_activity_log to track actions taken by bots
CREATE TABLE IF NOT EXISTS public.bot_activity_log (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  bot_id UUID REFERENCES public.bots(id) ON DELETE CASCADE NOT NULL,
  activity_type TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  success BOOLEAN NOT NULL
);

-- Create notifications table for user alerts
CREATE TABLE IF NOT EXISTS public.notifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  notification_type TEXT NOT NULL,
  link TEXT,
  related_id UUID
);

-- Function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call handle_new_user function on user creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Function to update user profile on user updates
CREATE OR REPLACE FUNCTION public.handle_user_update()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.profiles
  SET
    email = NEW.email,
    updated_at = now()
  WHERE id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call handle_user_update on user changes
CREATE TRIGGER on_auth_user_updated
  AFTER UPDATE ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_user_update();

-- RLS Policies for profiles table
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id);

-- RLS Policies for bots table
ALTER TABLE public.bots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own bots"
  ON public.bots FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view public bots"
  ON public.bots FOR SELECT
  USING (is_public = true);

CREATE POLICY "Users can create their own bots"
  ON public.bots FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own bots"
  ON public.bots FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own bots"
  ON public.bots FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for bot_assets table
ALTER TABLE public.bot_assets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view assets for their own bots"
  ON public.bot_assets FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.bots
    WHERE bots.id = bot_assets.bot_id AND bots.user_id = auth.uid()
  ));

CREATE POLICY "Users can view assets for public bots"
  ON public.bot_assets FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.bots
    WHERE bots.id = bot_assets.bot_id AND bots.is_public = true
  ));

CREATE POLICY "Users can modify assets for their own bots"
  ON public.bot_assets FOR ALL
  USING (EXISTS (
    SELECT 1 FROM public.bots
    WHERE bots.id = bot_assets.bot_id AND bots.user_id = auth.uid()
  ));

-- RLS Policies for favorites table
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own favorites"
  ON public.favorites FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own favorites"
  ON public.favorites FOR ALL
  USING (auth.uid() = user_id);

-- RLS Policies for analytics_data table
ALTER TABLE public.analytics_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view analytics for their own bots"
  ON public.analytics_data FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.bots
    WHERE bots.id = analytics_data.bot_id AND bots.user_id = auth.uid()
  ));

CREATE POLICY "Users can modify analytics for their own bots"
  ON public.analytics_data FOR ALL
  USING (EXISTS (
    SELECT 1 FROM public.bots
    WHERE bots.id = analytics_data.bot_id AND bots.user_id = auth.uid()
  ));

-- RLS Policies for bot_activity_log table
ALTER TABLE public.bot_activity_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view activity logs for their own bots"
  ON public.bot_activity_log FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.bots
    WHERE bots.id = bot_activity_log.bot_id AND bots.user_id = auth.uid()
  ));

-- RLS Policies for notifications table
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notifications"
  ON public.notifications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications"
  ON public.notifications FOR UPDATE
  USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS bots_user_id_idx ON public.bots (user_id);
CREATE INDEX IF NOT EXISTS bot_assets_bot_id_idx ON public.bot_assets (bot_id);
CREATE INDEX IF NOT EXISTS favorites_user_id_idx ON public.favorites (user_id);
CREATE INDEX IF NOT EXISTS favorites_bot_id_idx ON public.favorites (bot_id);
CREATE INDEX IF NOT EXISTS analytics_data_bot_id_idx ON public.analytics_data (bot_id);
CREATE INDEX IF NOT EXISTS analytics_data_date_idx ON public.analytics_data (date);
CREATE INDEX IF NOT EXISTS bot_activity_log_bot_id_idx ON public.bot_activity_log (bot_id);
CREATE INDEX IF NOT EXISTS notifications_user_id_idx ON public.notifications (user_id);
CREATE INDEX IF NOT EXISTS bots_is_public_idx ON public.bots (is_public) WHERE is_public = true; 