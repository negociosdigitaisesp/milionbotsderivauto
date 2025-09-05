-- Adicionar coluna strategy_used à tabela radar_de_apalancamiento_signals
-- Esta coluna armazena qual estratégia foi utilizada pelo sistema de portfólio

ALTER TABLE public.radar_de_apalancamiento_signals 
ADD COLUMN IF NOT EXISTS strategy_used TEXT NULL;

-- Comentário para documentar a coluna
COMMENT ON COLUMN public.radar_de_apalancamiento_signals.strategy_used IS 'Estratégia utilizada pelo sistema de portfólio (PREMIUM_RECOVERY, MOMENTUM_CONTINUATION, etc.)';

-- Verificar se a coluna foi adicionada
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'radar_de_apalancamiento_signals' 
AND column_name = 'strategy_used';