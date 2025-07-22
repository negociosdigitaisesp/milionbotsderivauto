import React, { useEffect, useState } from 'react';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';
import { obterEstatisticasBots } from '../services/botStatsService';

export default function SupabaseTest() {
  const [connectionStatus, setConnectionStatus] = useState('Testando...');
  const [botData, setBotData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function testConnection() {
      try {
        // Verificar configuração
        if (!isSupabaseConfigured()) {
          setConnectionStatus('❌ Supabase não configurado');
          setError('Variáveis de ambiente não encontradas');
          return;
        }

        setConnectionStatus('✅ Configuração OK');

        // Testar conexão
        const { data: session, error: authError } = await supabase.auth.getSession();
        
        if (authError) {
          console.error('Erro de autenticação:', authError);
        }

        // Testar busca de dados
        console.log('🔍 Testando busca de estatísticas...');
        const stats = await obterEstatisticasBots();
        setBotData(stats);
        
        if (stats.length > 0) {
          setConnectionStatus('✅ Dados carregados com sucesso');
        } else {
          setConnectionStatus('⚠️ Nenhum dado encontrado');
        }

      } catch (err: any) {
        console.error('Erro no teste:', err);
        setError(err.message);
        setConnectionStatus('❌ Erro na conexão');
      }
    }

    testConnection();
  }, []);

  return (
    <div className="p-6 bg-card rounded-lg border">
      <h3 className="text-lg font-semibold mb-4">Teste de Conexão Supabase</h3>
      
      <div className="space-y-2 mb-4">
        <p><strong>Status:</strong> {connectionStatus}</p>
        <p><strong>URL:</strong> {import.meta.env.VITE_SUPABASE_URL || 'Não configurado'}</p>
        <p><strong>Bots encontrados:</strong> {botData.length}</p>
      </div>

      {error && (
        <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700 mb-4">
          <strong>Erro:</strong> {error}
        </div>
      )}

      {botData.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium mb-2">Dados dos Bots:</h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {botData.map((bot, index) => (
              <div key={index} className="p-2 bg-muted rounded text-sm">
                <strong>{bot.nome_bot}</strong> - 
                Lucro: ${bot.lucro_total?.toFixed(2)} - 
                Taxa: {bot.taxa_vitoria?.toFixed(1)}% - 
                Operações: {bot.total_operacoes}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}