-- =====================================================
-- CONFIGURAÇÃO COMPLETA DAS TABELAS DE TRACKING
-- Sistema de Rastreamento de Sinais e Estratégias
-- =====================================================

-- 1. Tabela de Sinais do Scalping Bot
CREATE TABLE IF NOT EXISTS public.scalping_signals (
    id SERIAL PRIMARY KEY,
    bot_name TEXT NOT NULL DEFAULT 'Scalping Bot',
    should_operate BOOLEAN NOT NULL DEFAULT true,
    strategy TEXT NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    reason TEXT NOT NULL,
    wins_consecutivos INTEGER DEFAULT 0,
    losses_ultimas_15 INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabela de Rastreamento de Resultados de Estratégias
CREATE TABLE IF NOT EXISTS public.strategy_results_tracking (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES public.scalping_signals(id) ON DELETE CASCADE,
    strategy_name TEXT NOT NULL,
    confidence_level DECIMAL(5,2) NOT NULL,
    operation_1_result TEXT, -- 'V' para WIN, 'D' para LOSS
    operation_2_result TEXT, -- 'V' para WIN, 'D' para LOSS
    pattern_success BOOLEAN, -- true se ambas operações foram WIN
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'COMPLETED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 3. Tabela de Logs de Operações (se não existir)
CREATE TABLE IF NOT EXISTS public.scalping_accumulator_bot_logs (
    id SERIAL PRIMARY KEY,
    bot_name TEXT NOT NULL,
    operation_result TEXT NOT NULL, -- 'V' para WIN, 'D' para LOSS
    operation_id TEXT,
    stake DECIMAL(10,2),
    payout DECIMAL(10,2),
    profit_loss DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabela de Sinais do Radar de Apalancamiento (compatibilidade)
CREATE TABLE IF NOT EXISTS public.radar_de_apalancamiento_signals (
    id SERIAL PRIMARY KEY,
    bot_name TEXT NOT NULL,
    is_safe_to_operate BOOLEAN NOT NULL,
    reason TEXT NOT NULL,
    strategy_used TEXT,
    strategy_confidence DECIMAL(5,2),
    tracking_id INTEGER,
    operations_after_pattern INTEGER DEFAULT 0,
    losses_in_last_10_ops INTEGER DEFAULT 0,
    wins_in_last_5_ops INTEGER DEFAULT 0,
    historical_accuracy DECIMAL(5,2) DEFAULT 0,
    last_pattern_found TEXT,
    auto_disable_after_ops INTEGER DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Índices para Performance
CREATE INDEX IF NOT EXISTS idx_scalping_signals_created_at ON public.scalping_signals(created_at);
CREATE INDEX IF NOT EXISTS idx_scalping_signals_strategy ON public.scalping_signals(strategy);
CREATE INDEX IF NOT EXISTS idx_strategy_tracking_signal_id ON public.strategy_results_tracking(signal_id);
CREATE INDEX IF NOT EXISTS idx_strategy_tracking_status ON public.strategy_results_tracking(status);
CREATE INDEX IF NOT EXISTS idx_bot_logs_created_at ON public.scalping_accumulator_bot_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_bot_logs_bot_name ON public.scalping_accumulator_bot_logs(bot_name);

-- 6. Comentários para Documentação
COMMENT ON TABLE public.scalping_signals IS 'Sinais gerados pelo Scalping Bot com estratégias de alta assertividade';
COMMENT ON TABLE public.strategy_results_tracking IS 'Rastreamento de resultados das estratégias para análise de eficácia';
COMMENT ON TABLE public.scalping_accumulator_bot_logs IS 'Logs de operações do bot para análise histórica';

COMMENT ON COLUMN public.strategy_results_tracking.operation_1_result IS 'Resultado da primeira operação monitorada (V para WIN, D para LOSS)';
COMMENT ON COLUMN public.strategy_results_tracking.operation_2_result IS 'Resultado da segunda operação monitorada (V para WIN, D para LOSS)';
COMMENT ON COLUMN public.strategy_results_tracking.pattern_success IS 'True se ambas as operações foram WIN (V,V)';
COMMENT ON COLUMN public.strategy_results_tracking.completed_at IS 'Timestamp de quando o rastreamento foi finalizado';

-- 7. Função para Atualizar Timestamp Automaticamente
CREATE OR REPLACE FUNCTION update_completed_at_on_status_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Se o status mudou para COMPLETED, atualizar completed_at
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. Trigger para Atualizar completed_at Automaticamente
DROP TRIGGER IF EXISTS trigger_update_completed_at ON public.strategy_results_tracking;
CREATE TRIGGER trigger_update_completed_at
    BEFORE UPDATE ON public.strategy_results_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_completed_at_on_status_change();

-- 9. Inserir Dados de Teste (Opcional)
-- INSERT INTO public.scalping_signals (strategy, confidence, reason) 
-- VALUES ('PRECISION_SURGE', 95.0, 'Teste inicial do sistema');

-- 10. Verificação Final
SELECT 
    'scalping_signals' as tabela,
    COUNT(*) as registros
FROM public.scalping_signals
UNION ALL
SELECT 
    'strategy_results_tracking' as tabela,
    COUNT(*) as registros
FROM public.strategy_results_tracking
UNION ALL
SELECT 
    'scalping_accumulator_bot_logs' as tabela,
    COUNT(*) as registros
FROM public.scalping_accumulator_bot_logs;

-- =====================================================
-- CONFIGURAÇÃO COMPLETA!
-- Execute este script no SQL Editor do Supabase
-- =====================================================