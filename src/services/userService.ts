
import { supabase } from '../lib/supabaseClient';

export interface UserProfile {
  id?: string;
  user_id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  location?: string;
  bio?: string;
  theme?: 'light' | 'dark' | 'system';
  accent_color?: string;
  animations_enabled?: boolean;
  reduce_motion?: boolean;
  compact_mode?: boolean;
  email_notifications?: boolean;
  push_notifications?: boolean;
  trading_alerts?: boolean;
  news_updates?: boolean;
  critical_alerts_enabled?: boolean;
  sounds_enabled?: boolean;
  language?: string;
  time_format?: '12h' | '24h';
  currency?: string;
  date_format?: string;
  timezone?: string;
  two_factor_enabled?: boolean;
  session_timeout?: number;
  ip_whitelisting?: boolean;
  login_notifications?: boolean;
  updated_at?: string;
  created_at?: string;
}

export async function getUserProfile(userId: string) {
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', userId)
    .single();

  if (error && error.code !== 'PGRST116') {
    console.error('Erro ao buscar perfil do usuário:', error);
    throw error;
  }

  return data;
}

export async function createUserProfile(profile: UserProfile) {
  const { data, error } = await supabase
    .from('user_profiles')
    .insert([profile])
    .select();

  if (error) {
    console.error('Erro ao criar perfil do usuário:', error);
    throw error;
  }

  return data[0];
}

export async function updateUserProfile(profile: UserProfile) {
  const { data, error } = await supabase
    .from('user_profiles')
    .update(profile)
    .eq('user_id', profile.user_id)
    .select();

  if (error) {
    console.error('Erro ao atualizar perfil do usuário:', error);
    throw error;
  }

  return data[0];
}

export async function saveUserProfile(profile: UserProfile) {
  // Verificar se o perfil já existe
  const existingProfile = await getUserProfile(profile.user_id);
  
  if (existingProfile) {
    return updateUserProfile({
      ...existingProfile,
      ...profile,
      updated_at: new Date().toISOString()
    });
  } else {
    return createUserProfile({
      ...profile,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });
  }
}
