/**
 * Função para buscar estatísticas de desempenho dos bots de trading
 * Desenvolvida para uso em dashboard com Supabase
 * 
 * @description Esta função consulta a view 'estatisticas_bots' no Supabase
 * para obter dados de performance dos bots ordenados por lucro total
 * 
 * @returns {Promise<Array>} Array com as estatísticas dos bots ou array vazio em caso de erro
 */
async function buscarEstatisticasBots() {
    try {
        // Log de início da operação para debug
        console.log('🔍 Iniciando busca de estatísticas dos bots...');
        
        // Realizar consulta à view estatisticas_bots no Supabase
        // - .from(): especifica a tabela/view de origem
        // - .select('*'): seleciona todas as colunas disponíveis
        // - .order(): ordena os resultados por lucro_total em ordem decrescente
        const { data, error } = await supabase
            .from('estatisticas_bots')
            .select('*')
            .order('lucro_total', { ascending: false });
        
        // Verificar se ocorreu algum erro durante a consulta
        if (error) {
            // Imprimir erro detalhado no console para debug
            console.error('❌ Erro ao buscar estatísticas dos bots:', error);
            console.error('Detalhes do erro:', {
                message: error.message,
                details: error.details,
                hint: error.hint,
                code: error.code
            });
            
            // Retornar array vazio em caso de falha
            return [];
        }
        
        // Log de sucesso com informações sobre os dados recebidos
        console.log('✅ Estatísticas dos bots carregadas com sucesso!');
        console.log(`📊 Total de bots encontrados: ${data?.length || 0}`);
        
        // Imprimir os dados completos no console para debug
        console.log('📈 Dados das estatísticas dos bots:', data);
        
        // Log adicional com resumo dos dados (se houver dados)
        if (data && data.length > 0) {
            console.log('🏆 Top 3 bots por lucro:');
            data.slice(0, 3).forEach((bot, index) => {
                console.log(`${index + 1}. ${bot.nome_bot}: $${bot.lucro_total}`);
            });
        }
        
        // Retornar os dados obtidos da consulta
        return data || [];
        
    } catch (exception) {
        // Capturar qualquer exceção não prevista
        console.error('💥 Exceção não tratada ao buscar estatísticas:', exception);
        
        // Retornar array vazio em caso de exceção
        return [];
    }
}

// ============================================================================
// EXEMPLO DE USO DA FUNÇÃO
// ============================================================================

/**
 * Exemplo prático de como usar a função buscarEstatisticasBots
 * em um componente ou página do dashboard
 */
async function exemploDeUso() {
    console.log('🚀 Exemplo de uso da função buscarEstatisticasBots');
    
    try {
        // Chamar a função para buscar as estatísticas
        const estatisticas = await buscarEstatisticasBots();
        
        // Verificar se obtivemos dados
        if (estatisticas.length > 0) {
            console.log('📊 Processando estatísticas dos bots...');
            
            // Exemplo: Calcular estatísticas gerais
            const totalBots = estatisticas.length;
            const lucroTotal = estatisticas.reduce((acc, bot) => acc + (bot.lucro_total || 0), 0);
            const melhorBot = estatisticas[0]; // Já ordenado por lucro_total desc
            
            console.log('📈 Resumo das estatísticas:');
            console.log(`   Total de bots: ${totalBots}`);
            console.log(`   Lucro total geral: $${lucroTotal.toFixed(2)}`);
            console.log(`   Melhor bot: ${melhorBot.nome_bot} ($${melhorBot.lucro_total})`);
            
            // Exemplo: Usar os dados em um componente React
            // setEstatisticasBots(estatisticas);
            // setLoading(false);
            
        } else {
            console.log('📭 Nenhuma estatística encontrada');
            // setEstatisticasBots([]);
            // setLoading(false);
        }
        
    } catch (error) {
        console.error('❌ Erro no exemplo de uso:', error);
        // setError('Erro ao carregar estatísticas dos bots');
        // setLoading(false);
    }
}

// ============================================================================
// FUNÇÃO AUXILIAR PARA ATUALIZAÇÃO PERIÓDICA
// ============================================================================

/**
 * Função auxiliar para buscar estatísticas periodicamente
 * Útil para dashboards em tempo real
 * 
 * @param {number} intervaloSegundos - Intervalo em segundos para atualização
 * @param {Function} callback - Função callback para processar os dados
 */
function iniciarAtualizacaoPeriodicaBots(intervaloSegundos = 30, callback = null) {
    console.log(`🔄 Iniciando atualização periódica a cada ${intervaloSegundos} segundos`);
    
    // Buscar dados imediatamente
    buscarEstatisticasBots().then(dados => {
        if (callback) callback(dados);
    });
    
    // Configurar intervalo para atualizações periódicas
    const intervalId = setInterval(async () => {
        console.log('🔄 Atualizando estatísticas dos bots...');
        const dados = await buscarEstatisticasBots();
        if (callback) callback(dados);
    }, intervaloSegundos * 1000);
    
    // Retornar ID do intervalo para poder cancelar depois
    return intervalId;
}

// ============================================================================
// EXPORTAÇÃO PARA USO EM MÓDULOS
// ============================================================================

// Para uso em módulos ES6
// export { buscarEstatisticasBots, iniciarAtualizacaoPeriodicaBots };

// Para uso em Node.js/CommonJS
// module.exports = { buscarEstatisticasBots, iniciarAtualizacaoPeriodicaBots };

// ============================================================================
// EXEMPLO DE INTEGRAÇÃO COM REACT
// ============================================================================

/**
 * Exemplo de como integrar com um componente React
 */
/*
import React, { useState, useEffect } from 'react';

function DashboardBots() {
    const [estatisticas, setEstatisticas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        async function carregarEstatisticas() {
            try {
                setLoading(true);
                const dados = await buscarEstatisticasBots();
                setEstatisticas(dados);
                setError(null);
            } catch (err) {
                setError('Erro ao carregar estatísticas');
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        
        carregarEstatisticas();
        
        // Atualizar a cada 30 segundos
        const interval = setInterval(carregarEstatisticas, 30000);
        
        return () => clearInterval(interval);
    }, []);
    
    if (loading) return <div>Carregando estatísticas...</div>;
    if (error) return <div>Erro: {error}</div>;
    
    return (
        <div>
            <h2>Estatísticas dos Bots</h2>
            {estatisticas.map(bot => (
                <div key={bot.nome_bot}>
                    <h3>{bot.nome_bot}</h3>
                    <p>Lucro Total: ${bot.lucro_total}</p>
                </div>
            ))}
        </div>
    );
}
*/