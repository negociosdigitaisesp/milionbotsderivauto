/**
 * Configuração do Cliente Supabase para Realtime Updates
 * 
 * Este arquivo configura o cliente Supabase com as credenciais necessárias
 * e habilita as funcionalidades de realtime para o sistema de radar.
 */

import { createClient } from '@supabase/supabase-js';

// Configurações do Supabase
// IMPORTANTE: Em produção, use variáveis de ambiente
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'YOUR_SUPABASE_URL';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'YOUR_SUPABASE_ANON_KEY';

// Verificar se as credenciais estão configuradas
if (!supabaseUrl || supabaseUrl === 'YOUR_SUPABASE_URL') {
    console.error('❌ SUPABASE_URL não configurada. Configure a variável de ambiente REACT_APP_SUPABASE_URL');
}

if (!supabaseAnonKey || supabaseAnonKey === 'YOUR_SUPABASE_ANON_KEY') {
    console.error('❌ SUPABASE_ANON_KEY não configurada. Configure a variável de ambiente REACT_APP_SUPABASE_ANON_KEY');
}

// Criar cliente Supabase com configurações otimizadas para realtime
const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    realtime: {
        // Configurações específicas para realtime
        params: {
            eventsPerSecond: 10, // Limitar eventos por segundo
        },
    },
    auth: {
        // Configurações de autenticação se necessário
        persistSession: true,
        autoRefreshToken: true,
    },
    db: {
        // Configurações do banco de dados
        schema: 'public',
    },
});

// Função para testar conexão com Supabase
export const testSupabaseConnection = async () => {
    try {
        console.log('🔄 Testando conexão com Supabase...');
        
        // Testar conexão básica
        const { data, error } = await supabase
            .from('radar_de_apalancamiento_signals')
            .select('count')
            .limit(1);
        
        if (error) {
            console.error('❌ Erro na conexão com Supabase:', error.message);
            return false;
        }
        
        console.log('✅ Conexão com Supabase estabelecida com sucesso');
        return true;
        
    } catch (err) {
        console.error('❌ Erro ao testar conexão:', err.message);
        return false;
    }
};

// Função para verificar se realtime está funcionando
export const testRealtimeConnection = () => {
    return new Promise((resolve) => {
        console.log('🔄 Testando conexão realtime...');
        
        const channel = supabase.channel('test-connection');
        
        const timeout = setTimeout(() => {
            console.log('⚠️ Timeout na conexão realtime');
            supabase.removeChannel(channel);
            resolve(false);
        }, 5000);
        
        channel.subscribe((status) => {
            clearTimeout(timeout);
            
            if (status === 'SUBSCRIBED') {
                console.log('✅ Conexão realtime estabelecida com sucesso');
                supabase.removeChannel(channel);
                resolve(true);
            } else if (status === 'SUBSCRIPTION_ERROR') {
                console.error('❌ Erro na conexão realtime');
                supabase.removeChannel(channel);
                resolve(false);
            }
        });
    });
};

// Função para obter estatísticas da tabela radar_de_apalancamiento_signals
export const getRadarTableStats = async () => {
    try {
        const { data, error } = await supabase
            .from('radar_de_apalancamiento_signals')
            .select('bot_name, is_safe_to_operate, created_at')
            .order('created_at', { ascending: false });
        
        if (error) throw error;
        
        const stats = {
            totalRecords: data.length,
            uniqueBots: new Set(data.map(record => record.bot_name)).size,
            activeBots: data.filter(record => record.is_safe_to_operate).length,
            riskBots: data.filter(record => !record.is_safe_to_operate).length,
            lastUpdate: data.length > 0 ? data[0].created_at : null
        };
        
        console.log('📊 Estatísticas da tabela radar:', stats);
        return stats;
        
    } catch (err) {
        console.error('❌ Erro ao obter estatísticas:', err.message);
        return null;
    }
};

// Função para limpar dados antigos (opcional)
export const cleanupOldRecords = async (daysToKeep = 7) => {
    try {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
        
        const { data, error } = await supabase
            .from('radar_de_apalancamiento_signals')
            .delete()
            .lt('created_at', cutoffDate.toISOString());
        
        if (error) throw error;
        
        console.log(`🧹 Limpeza concluída. Registros removidos: ${data?.length || 0}`);
        return data?.length || 0;
        
    } catch (err) {
        console.error('❌ Erro na limpeza de dados:', err.message);
        return 0;
    }
};

// Exportar cliente principal
export default supabase;

/**
 * Exemplo de uso das funções utilitárias:
 * 
 * import supabase, { 
 *     testSupabaseConnection, 
 *     testRealtimeConnection, 
 *     getRadarTableStats 
 * } from './supabaseClient';
 * 
 * // Testar conexões na inicialização da aplicação
 * async function initializeApp() {
 *     const dbConnected = await testSupabaseConnection();
 *     const realtimeConnected = await testRealtimeConnection();
 *     
 *     if (dbConnected && realtimeConnected) {
 *         console.log('🚀 Aplicação inicializada com sucesso');
 *         
 *         // Obter estatísticas iniciais
 *         await getRadarTableStats();
 *     } else {
 *         console.error('❌ Falha na inicialização da aplicação');
 *     }
 * }
 * 
 * initializeApp();
 */

/**
 * Configuração do arquivo .env para React:
 * 
 * REACT_APP_SUPABASE_URL=https://your-project.supabase.co
 * REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here
 * 
 * Para Next.js, use:
 * NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
 * NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
 */