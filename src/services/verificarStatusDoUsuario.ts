import { supabase } from '../lib/supabaseClient';

/**
 * Verifica o status de acesso do usuário através da API do Supabase
 * @param userId - ID do usuário autenticado
 * @param authToken - Token de autenticação (JWT) do usuário
 * @returns Promise com o status is_active do usuário
 */
export async function verificarStatusDoUsuario(userId: string, authToken: string) {
  const projectUrl = 'https://xwclmxjeombwabfdvyij.supabase.co';
  const anonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3Y2xteGplb21id2FiZmR2eWlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MjY0NTQsImV4cCI6MjA2ODEwMjQ1NH0.lB4EBPozpPUJS0oI5wpatJdo_HCTcuDRFmd42b_7i9U';
  
  const url = `${projectUrl}/rest/v1/profiles?select=is_active&id=eq.${userId}`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'apikey': anonKey,
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erro na API: ${response.status} - ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data || data.length === 0) {
      throw new Error('Usuário não encontrado');
    }
    
    return {
      success: true,
      isActive: data[0].is_active,
      data: data[0]
    };
    
  } catch (error) {
    console.error('Erro ao verificar status do usuário:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Erro desconhecido',
      isActive: false
    };
  }
}

/**
 * Versão alternativa usando o cliente Supabase (mais simples)
 * @param userId - ID do usuário autenticado
 * @returns Promise com o status is_active do usuário
 */
export async function verificarStatusDoUsuarioSupabase(userId: string) {
  try {
    const { data, error } = await supabase
      .from('profiles')
      .select('is_active')
      .eq('id', userId)
      .single();
    
    if (error) {
      throw error;
    }
    
    return {
      success: true,
      isActive: data?.is_active || false,
      data
    };
    
  } catch (error) {
    console.error('Erro ao verificar status do usuário (Supabase):', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Erro desconhecido',
      isActive: false
    };
  }
}