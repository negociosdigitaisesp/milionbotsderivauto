/**
 * Função assíncrona para buscar estatísticas avançadas dos bots de trading
 * 
 * Esta função utiliza o Supabase RPC (Remote Procedure Call) para chamar
 * uma função PostgreSQL que calcula estatísticas detalhadas de risco e
 * performance dos bots de trading.
 * 
 * @returns {Promise<Array>} Array com estatísticas dos bots ou array vazio em caso de erro
 * 
 * Exemplo do formato dos dados retornados:
 * [
 *   {
 *     "nome_bot": "bot_ai_2_0",
 *     "total_operacoes": 150,
 *     "lucro_total": 245.50,
 *     "taxa_vitoria": 0.67,
 *     "maior_sequencia_vitorias": 8,
 *     "maior_sequencia_derrotas": 5,
 *     "drawdown_maximo": -89.30,
 *     "lucro_medio_por_operacao": 1.64,
 *     "desvio_padrao_lucros": 12.45,
 *     "sharpe_ratio": 0.13,
 *     "profit_factor": 1.25,
 *     "recovery_factor": 2.75,
 *     "ultima_operacao": "2024-01-15T10:30:00Z"
 *   },
 *   {
 *     "nome_bot": "bot_quantum_fixed_stake",
 *     "total_operacoes": 98,
 *     "lucro_total": 189.20,
 *     "taxa_vitoria": 0.61,
 *     "maior_sequencia_vitorias": 6,
 *     "maior_sequencia_derrotas": 7,
 *     "drawdown_maximo": -125.80,
 *     "lucro_medio_por_operacao": 1.93,
 *     "desvio_padrao_lucros": 15.67,
 *     "sharpe_ratio": 0.12,
 *     "profit_factor": 1.18,
 *     "recovery_factor": 1.50,
 *     "ultima_operacao": "2024-01-15T09:45:00Z"
 *   }
 * ]
 */
async function buscarEstatisticasAvancadas() {
    try {
        // Chama a função RPC do PostgreSQL para obter estatísticas detalhadas
        // A função get_bot_statistics calcula métricas avançadas de risco e performance
        const { data, error } = await supabase
            .rpc('get_bot_statistics') // Nome da função PostgreSQL
            .order('lucro_total', { ascending: false }); // Ordena por lucro total (maior para menor)
        
        // Verifica se houve erro na chamada RPC
        if (error) {
            console.error('❌ Erro ao buscar estatísticas avançadas dos bots:', error.message);
            console.error('🔍 Detalhes do erro:', error);
            
            // Retorna array vazio em caso de erro para evitar quebra da aplicação
            return [];
        }
        
        // Log de sucesso com informações sobre os dados retornados
        console.log(`✅ Estatísticas avançadas carregadas com sucesso! Total de bots: ${data?.length || 0}`);
        
        // Retorna os dados das estatísticas ordenados por lucro total
        return data || [];
        
    } catch (exception) {
        // Captura erros de rede, conexão ou outros erros não relacionados ao Supabase
        console.error('💥 Erro inesperado ao buscar estatísticas:', exception.message);
        console.error('🔍 Stack trace:', exception);
        
        // Retorna array vazio para manter a consistência da interface
        return [];
    }
}

/**
 * Exemplo de uso da função:
 * 
 * // Chamada básica
 * const estatisticas = await buscarEstatisticasAvancadas();
 * console.log('Estatísticas dos bots:', estatisticas);
 * 
 * // Uso em componente React/Vue
 * useEffect(() => {
 *     const carregarEstatisticas = async () => {
 *         const dados = await buscarEstatisticasAvancadas();
 *         setEstatisticas(dados);
 *     };
 *     carregarEstatisticas();
 * }, []);
 * 
 * // Processamento dos dados
 * estatisticas.forEach(bot => {
 *     console.log(`Bot: ${bot.nome_bot}`);
 *     console.log(`Lucro Total: $${bot.lucro_total}`);
 *     console.log(`Taxa de Vitória: ${(bot.taxa_vitoria * 100).toFixed(1)}%`);
 *     console.log(`Sharpe Ratio: ${bot.sharpe_ratio}`);
 * });
 */

// Exporta a função para uso em módulos ES6
export { buscarEstatisticasAvancadas };

// Exporta como default também para compatibilidade
export default buscarEstatisticasAvancadas;