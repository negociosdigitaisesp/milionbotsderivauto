-- Adicionar coluna last_operations à tabela radar_de_apalancamiento_signals
ALTER TABLE public.radar_de_apalancamiento_signals
ADD COLUMN IF NOT EXISTS last_operations text;

-- Adicionar coluna last_update à tabela radar_de_apalancamiento_signals
ALTER TABLE public.radar_de_apalancamiento_signals
ADD COLUMN IF NOT EXISTS last_update timestamp with time zone;

-- Criar índice para melhorar performance de consultas por last_update
CREATE INDEX IF NOT EXISTS idx_signals_last_update ON public.radar_de_apalancamiento_signals (last_update DESC);

-- Comentário para documentar as colunas
COMMENT ON COLUMN public.radar_de_apalancamiento_signals.last_operations IS 'Armazena as últimas operações em formato de texto';
COMMENT ON COLUMN public.radar_de_apalancamiento_signals.last_update IS 'Timestamp da última atualização do registro';