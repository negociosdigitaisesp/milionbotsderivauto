-- ============================================================================
-- SCRIPT SQL PARA ADICIONAR CAMPOS DE MARTINGALE NA TABELA TUNDER_BOT_LOGS
-- ============================================================================
-- Este script adiciona campos para rastrear detalhadamente o sistema Martingale
-- de 5 níveis com multiplicadores [1.0, 2.2, 4.84, 10.648, 23.426]

-- Adicionar campos de Martingale na tabela existente
ALTER TABLE public.tunder_bot_logs 
ADD COLUMN IF NOT EXISTS martingale_level integer DEFAULT 1,
ADD COLUMN IF NOT EXISTS martingale_multiplier double precision DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS consecutive_losses integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS consecutive_wins integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS original_stake double precision DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS martingale_stake double precision DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS total_martingale_investment double precision DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS martingale_sequence_id text DEFAULT NULL,
ADD COLUMN IF NOT EXISTS is_martingale_reset boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS martingale_progression text DEFAULT NULL;

-- Adicionar comentários para documentação
COMMENT ON COLUMN public.tunder_bot_logs.martingale_level IS 'Nível atual do Martingale (1-5)';
COMMENT ON COLUMN public.tunder_bot_logs.martingale_multiplier IS 'Multiplicador aplicado no nível atual';
COMMENT ON COLUMN public.tunder_bot_logs.consecutive_losses IS 'Número de perdas consecutivas';
COMMENT ON COLUMN public.tunder_bot_logs.consecutive_wins IS 'Número de vitórias consecutivas';
COMMENT ON COLUMN public.tunder_bot_logs.original_stake IS 'Stake original antes do Martingale';
COMMENT ON COLUMN public.tunder_bot_logs.martingale_stake IS 'Stake calculado com Martingale';
COMMENT ON COLUMN public.tunder_bot_logs.total_martingale_investment IS 'Investimento total acumulado na sequência Martingale';
COMMENT ON COLUMN public.tunder_bot_logs.martingale_sequence_id IS 'ID único para identificar sequência de Martingale';
COMMENT ON COLUMN public.tunder_bot_logs.is_martingale_reset IS 'Indica se houve reset do Martingale (vitória)';
COMMENT ON COLUMN public.tunder_bot_logs.martingale_progression IS 'JSON com histórico da progressão Martingale';

-- Criar índices para melhor performance nas consultas
CREATE INDEX IF NOT EXISTS idx_tunder_bot_logs_martingale_level ON public.tunder_bot_logs(martingale_level);
CREATE INDEX IF NOT EXISTS idx_tunder_bot_logs_martingale_sequence ON public.tunder_bot_logs(martingale_sequence_id);
CREATE INDEX IF NOT EXISTS idx_tunder_bot_logs_consecutive_losses ON public.tunder_bot_logs(consecutive_losses);
CREATE INDEX IF NOT EXISTS idx_tunder_bot_logs_timestamp_martingale ON public.tunder_bot_logs(timestamp, martingale_level);

-- ============================================================================
-- VIEWS PARA ANÁLISE DE MARTINGALE
-- ============================================================================

-- View para análise de sequências Martingale
CREATE OR REPLACE VIEW public.martingale_sequences AS
SELECT 
    martingale_sequence_id,
    bot_name,
    account_name,
    COUNT(*) as sequence_length,
    MAX(martingale_level) as max_level_reached,
    SUM(stake_value) as total_invested,
    SUM(CASE WHEN operation_result = 'WIN' THEN profit_percentage * stake_value / 100 ELSE -stake_value END) as sequence_profit,
    MIN(timestamp) as sequence_start,
    MAX(timestamp) as sequence_end,
    MAX(CASE WHEN is_martingale_reset = true THEN timestamp END) as reset_timestamp
FROM public.tunder_bot_logs 
WHERE martingale_sequence_id IS NOT NULL
GROUP BY martingale_sequence_id, bot_name, account_name;

-- View para estatísticas de Martingale por bot
CREATE OR REPLACE VIEW public.martingale_stats_by_bot AS
SELECT 
    bot_name,
    account_name,
    COUNT(*) as total_operations,
    COUNT(CASE WHEN martingale_level > 1 THEN 1 END) as martingale_operations,
    ROUND(COUNT(CASE WHEN martingale_level > 1 THEN 1 END) * 100.0 / COUNT(*), 2) as martingale_percentage,
    AVG(martingale_level) as avg_martingale_level,
    MAX(martingale_level) as max_martingale_level,
    MAX(consecutive_losses) as max_consecutive_losses,
    COUNT(CASE WHEN is_martingale_reset = true THEN 1 END) as successful_resets,
    SUM(total_martingale_investment) as total_martingale_invested
FROM public.tunder_bot_logs 
GROUP BY bot_name, account_name;

-- View para análise de performance por nível Martingale
CREATE OR REPLACE VIEW public.martingale_performance_by_level AS
SELECT 
    martingale_level,
    COUNT(*) as operations_count,
    COUNT(CASE WHEN operation_result = 'WIN' THEN 1 END) as wins,
    COUNT(CASE WHEN operation_result = 'LOSS' THEN 1 END) as losses,
    ROUND(COUNT(CASE WHEN operation_result = 'WIN' THEN 1 END) * 100.0 / COUNT(*), 2) as win_rate,
    AVG(stake_value) as avg_stake,
    SUM(stake_value) as total_stake_invested,
    AVG(profit_percentage) as avg_profit_percentage
FROM public.tunder_bot_logs 
GROUP BY martingale_level
ORDER BY martingale_level;

-- ============================================================================
-- FUNÇÕES AUXILIARES
-- ============================================================================

-- Função para gerar ID único de sequência Martingale
CREATE OR REPLACE FUNCTION generate_martingale_sequence_id(
    p_bot_name text,
    p_account_name text,
    p_timestamp timestamp with time zone
) RETURNS text AS $$
BEGIN
    RETURN CONCAT(
        p_bot_name, '_',
        p_account_name, '_',
        EXTRACT(EPOCH FROM p_timestamp)::bigint, '_',
        SUBSTRING(MD5(RANDOM()::text), 1, 8)
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMENTÁRIOS FINAIS
-- ============================================================================
-- Este script adiciona campos completos para rastreamento do sistema Martingale
-- Multiplicadores suportados: [1.0, 2.2, 4.84, 10.648, 23.426]
-- Níveis: 1-5
-- Inclui views para análise e relatórios
-- Otimizado com índices para performance