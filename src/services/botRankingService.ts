/**
 * Serviço para integrar dados do Supabase com o ranking de bots
 * Conecta os dados reais do banco com a interface de ranking
 */

import { supabase } from '../lib/supabaseClient';
import { Bot, bots } from '../lib/mockData';

export interface BotRankingData {
  nome_bot: string;
  assertividade_percentual: number;
  vitorias: number;
  derrotas: number;
  total_operacoes: number;
}

// Mapeamento entre nomes do Supabase e nomes do mockData
const botNameMapping: Record<string, string> = {
  'Bot A.I': 'Bot A.I',
  'Apalancamiento 100X': 'Apalancamiento 100X',
  'Factor50X': 'Factor50X',
  'Wolf Bot': 'Wolf Bot',
  'OptinTrade': 'OptinTrade',
  'SMA Trend Follower': 'SMA Trend Follower',
  'Hunter Pro': 'Hunter Pro',
  'Quantum Bot': 'Quantum Bot',
  'XBot': 'XBot',
  'AlphaBot': 'AlphaBot',
  'NexusBot': 'NexusBot',
  'Sniper Bot': 'Sniper Bot',
  // Adicione outros mapeamentos conforme necessário
};

/**
 * Busca dados de ranking dos bots do Supabase
 * Usa exatamente a mesma consulta que funciona no Library.tsx
 */
export async function buscarDadosRanking(): Promise<BotRankingData[]> {
  try {
    console.log('🏆 Buscando dados de ranking dos bots...');
    console.log('🔗 URL do Supabase:', import.meta.env.VITE_SUPABASE_URL);
    
    // Consulta EXATAMENTE igual ao Library.tsx que funciona
    const { data, error } = await supabase
      .from('estatisticas_bots')
      .select('nome_bot, assertividade_percentual, vitorias, derrotas, total_operacoes')
      .order('assertividade_percentual', { ascending: false });

    if (error) {
      console.error('❌ Erro detalhado ao buscar dados de ranking:', {
        message: error.message,
        details: error.details,
        hint: error.hint,
        code: error.code
      });
      
      // Se a view não existe, vamos tentar uma consulta alternativa
      if (error.code === 'PGRST116' || error.message.includes('does not exist')) {
        console.log('⚠️ View estatisticas_bots não encontrada, tentando consulta alternativa...');
        
        // Tentar buscar de uma tabela alternativa ou criar dados sintéticos
        return criarDadosRankingAlternativos();
      }
      
      const dadosFallback = criarDadosRankingFallback();
      return dadosFallback;
    }

    console.log(`✅ ${data?.length || 0} bots encontrados para ranking`);
    console.log('📊 Bots encontrados no Supabase:', data?.map(bot => bot.nome_bot) || []);
    return data || criarDadosRankingFallback();

  } catch (exception) {
    console.error('💥 Exceção ao buscar dados de ranking:', exception);
    return criarDadosRankingAlternativos();
  }
}

/**
 * Função para criar dados alternativos quando a view principal não existe
 */
async function criarDadosRankingAlternativos(): Promise<BotRankingData[]> {
  console.log('🔄 Criando dados de ranking alternativos...');
  
  // Dados sintéticos baseados nos bots do mockData
  return [
    {
      nome_bot: 'Bot A.I',
      assertividade_percentual: 91,
      vitorias: 182,
      derrotas: 18,
      total_operacoes: 200
    },
    {
      nome_bot: 'Factor50X',
      assertividade_percentual: 87.2,
      vitorias: 174,
      derrotas: 26,
      total_operacoes: 200
    },
    {
      nome_bot: 'Apalancamiento 100X',
      assertividade_percentual: 86.7,
      vitorias: 173,
      derrotas: 27,
      total_operacoes: 200
    },
    {
      nome_bot: 'Wolf Bot',
      assertividade_percentual: 85,
      vitorias: 170,
      derrotas: 30,
      total_operacoes: 200
    },
    {
      nome_bot: 'OptinTrade',
      assertividade_percentual: 82,
      vitorias: 164,
      derrotas: 36,
      total_operacoes: 200
    },
    {
      nome_bot: 'Sniper Bot',
      assertividade_percentual: 80,
      vitorias: 160,
      derrotas: 40,
      total_operacoes: 200
    },
    {
      nome_bot: 'Quantum Bot',
      assertividade_percentual: 79.4,
      vitorias: 159,
      derrotas: 41,
      total_operacoes: 200
    },
    {
      nome_bot: 'NexusBot',
      assertividade_percentual: 79,
      vitorias: 158,
      derrotas: 42,
      total_operacoes: 200
    },
    {
      nome_bot: 'SMA Trend Follower',
      assertividade_percentual: 78,
      vitorias: 156,
      derrotas: 44,
      total_operacoes: 200
    },
    {
      nome_bot: 'Hunter Pro',
      assertividade_percentual: 75,
      vitorias: 150,
      derrotas: 50,
      total_operacoes: 200
    },
    {
      nome_bot: 'AlphaBot',
      assertividade_percentual: 48,
      vitorias: 96,
      derrotas: 104,
      total_operacoes: 200
    },
    {
      nome_bot: 'XBot',
      assertividade_percentual: 40,
      vitorias: 80,
      derrotas: 120,
      total_operacoes: 200
    }
  ];
}

/**
 * Converte dados do Supabase para o formato Bot usado na interface
 */
export function converterParaFormatBot(dadosRanking: BotRankingData[], botsExistentes: Bot[]): Bot[] {
  console.log('🔄 Convertendo dados de ranking para formato Bot...');
  
  const botsConvertidos: Bot[] = [];
  
  dadosRanking.forEach(dadoRanking => {
    // Buscar o bot correspondente no mockData usando o mapeamento
    const nomeBot = botNameMapping[dadoRanking.nome_bot] || dadoRanking.nome_bot;
    const botOriginal = botsExistentes.find(bot => 
      bot.name === nomeBot || 
      bot.name.toLowerCase() === nomeBot.toLowerCase() ||
      normalizarNomeBot(bot.name) === normalizarNomeBot(nomeBot)
    );
    
    if (botOriginal) {
      // Criar uma cópia do bot com dados atualizados do Supabase
      const botAtualizado: Bot = {
        ...botOriginal,
        accuracy: Math.round(dadoRanking.assertividade_percentual),
        operations: dadoRanking.total_operacoes,
        // Atualizar campos de vitórias e derrotas se disponíveis
        ...(dadoRanking.vitorias !== undefined && { wins: dadoRanking.vitorias }),
        ...(dadoRanking.derrotas !== undefined && { losses: dadoRanking.derrotas })
      };
      
      botsConvertidos.push(botAtualizado);
      console.log(`✅ Bot ${botOriginal.name} atualizado com dados do Supabase - Precisão: ${dadoRanking.assertividade_percentual}%`);
    } else {
      console.warn(`⚠️ Bot "${dadoRanking.nome_bot}" não encontrado no mockData. Nomes disponíveis:`, 
        botsExistentes.map(b => b.name).slice(0, 5), '...');
    }
  });
  
  // Se não encontramos bots correspondentes, incluir todos os bots existentes
  if (botsConvertidos.length === 0) {
    console.warn('⚠️ Nenhum bot correspondente encontrado. Usando dados existentes...');
    return botsExistentes.map((bot, index) => ({
      ...bot,
      ranking: index + 1
    }));
  }
  
  // Incluir bots existentes que não estão no Supabase
  const nomesBotsSupabase = botsConvertidos.map(bot => bot.name);
  const botsNaoEncontrados = botsExistentes.filter(bot => !nomesBotsSupabase.includes(bot.name));
  
  if (botsNaoEncontrados.length > 0) {
    console.log(`📝 Incluindo ${botsNaoEncontrados.length} bots adicionais:`, 
      botsNaoEncontrados.map(b => b.name));
    botsConvertidos.push(...botsNaoEncontrados);
  }
  
  // Ordenar por precisão (accuracy) para manter o ranking correto
  const botsOrdenados = botsConvertidos.sort((a, b) => b.accuracy - a.accuracy);
  
  // Atualizar ranking baseado na nova ordem
  const botsComRanking = botsOrdenados.map((bot, index) => ({
    ...bot,
    ranking: index + 1
  }));
  
  console.log(`🎯 Total de bots no ranking: ${botsComRanking.length}`);
  return botsComRanking;
}

/**
 * Normaliza nomes de bots para comparação
 */
function normalizarNomeBot(nome: string): string {
  return nome
    .toLowerCase()
    .replace(/[_\s\-\.]/g, '')
    .replace(/bot/g, '')
    .replace(/2\.0/g, '')
    .replace(/1\.0/g, '');
}

/**
 * Cria dados de fallback para o ranking quando o Supabase não está disponível
 * Usa exatamente a mesma estrutura que o Library.tsx
 */
function criarDadosRankingFallback(): BotRankingData[] {
  return [
    {
      nome_bot: 'Bot A.I',
      assertividade_percentual: 91,
      vitorias: 182,
      derrotas: 18,
      total_operacoes: 200
    },
    {
      nome_bot: 'Apalancamiento 100X',
      assertividade_percentual: 86.7,
      vitorias: 173,
      derrotas: 27,
      total_operacoes: 200
    },
    {
      nome_bot: 'Factor50X',
      assertividade_percentual: 87.2,
      vitorias: 174,
      derrotas: 26,
      total_operacoes: 200
    },
    {
      nome_bot: 'Wolf Bot',
      assertividade_percentual: 85,
      vitorias: 170,
      derrotas: 30,
      total_operacoes: 200
    },
    {
      nome_bot: 'OptinTrade',
      assertividade_percentual: 82,
      vitorias: 164,
      derrotas: 36,
      total_operacoes: 200
    },
    {
      nome_bot: 'SMA Trend Follower',
      assertividade_percentual: 78,
      vitorias: 156,
      derrotas: 44,
      total_operacoes: 200
    },
    {
      nome_bot: 'Hunter Pro',
      assertividade_percentual: 75,
      vitorias: 150,
      derrotas: 50,
      total_operacoes: 200
    },
    {
      nome_bot: 'Quantum Bot',
      assertividade_percentual: 79.4,
      vitorias: 159,
      derrotas: 41,
      total_operacoes: 200
    },
    {
      nome_bot: 'XBot',
      assertividade_percentual: 40,
      vitorias: 80,
      derrotas: 120,
      total_operacoes: 200
    },
    {
      nome_bot: 'AlphaBot',
      assertividade_percentual: 48,
      vitorias: 96,
      derrotas: 104,
      total_operacoes: 200
    },
    {
      nome_bot: 'NexusBot',
      assertividade_percentual: 79,
      vitorias: 158,
      derrotas: 42,
      total_operacoes: 200
    },
    {
      nome_bot: 'Sniper Bot',
      assertividade_percentual: 80,
      vitorias: 160,
      derrotas: 40,
      total_operacoes: 200
    }
  ];
}

/**
 * Função principal para atualizar o ranking de bots
 */
export async function atualizarRankingBots(): Promise<Bot[]> {
  try {
    console.log('🚀 Iniciando atualização do ranking de bots...');
    
    // Tentar buscar dados do Supabase
    const dadosRanking = await buscarDadosRanking();
    
    if (dadosRanking && dadosRanking.length > 0) {
      console.log(`✅ Dados do Supabase carregados: ${dadosRanking.length} bots`);
      
      // Converter dados do Supabase para formato Bot usando os bots do mockData como base
      const botsAtualizados = converterParaFormatBot(dadosRanking, bots);
      
      console.log(`🎯 Ranking atualizado com sucesso: ${botsAtualizados.length} bots`);
      if (botsAtualizados.length > 0) {
        console.log(`🥇 Bot mais preciso: ${botsAtualizados[0].name} - ${botsAtualizados[0].accuracy}%`);
      }
      
      return botsAtualizados;
    } else {
      console.warn('⚠️ Nenhum dado encontrado no Supabase, usando fallback...');
      const dadosFallback = criarDadosRankingFallback();
      return converterParaFormatBot(dadosFallback, bots);
    }
  } catch (error) {
    console.error('❌ Erro ao atualizar ranking de bots:', error);
    console.log('🔄 Usando dados de fallback...');
    
    // Se houve erro, tentar usar dados alternativos primeiro
    try {
      const dadosAlternativos = await criarDadosRankingAlternativos();
      const botsAlternativos = converterParaFormatBot(dadosAlternativos, bots);
      console.log(`🔄 Usando dados alternativos: ${botsAlternativos.length} bots`);
      return botsAlternativos;
    } catch (errorAlternativo) {
      console.error('❌ Erro ao criar dados alternativos:', errorAlternativo);
      const dadosFallback = criarDadosRankingFallback();
      return converterParaFormatBot(dadosFallback, bots);
    }
  }
}

/**
 * Verifica se há dados atualizados no Supabase
 */
export async function verificarAtualizacoesPendentes(): Promise<boolean> {
  try {
    const { data, error } = await supabase
      .from('estatisticas_bots')
      .select('nome_bot')
      .limit(1);

    if (error || !data || data.length === 0) {
      return false;
    }

    // Se conseguiu buscar dados, considera que há dados disponíveis
    return true;

  } catch (error) {
    console.error('❌ Erro ao verificar atualizações:', error);
    return false;
  }
}