-- Script para atualizar a tabela strategy_results_tracking
-- Adiciona as colunas necessárias para o sistema de rastreamento refatorado

-- Adicionar coluna para resultado da primeira operação
ALTER TABLE strategy_results_tracking 
ADD COLUMN IF NOT EXISTS operation_1_result TEXT;

-- Adicionar coluna para resultado da segunda operação
ALTER TABLE strategy_results_tracking 
ADD COLUMN IF NOT EXISTS operation_2_result TEXT;

-- Adicionar coluna para indicar se o padrão foi bem-sucedido
ALTER TABLE strategy_results_tracking 
ADD COLUMN IF NOT EXISTS pattern_success BOOLEAN;

-- Adicionar coluna para timestamp de conclusão
ALTER TABLE strategy_results_tracking 
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;

-- Modificar a coluna strategy_confidence para aceitar valores decimais
ALTER TABLE strategy_results_tracking 
ALTER COLUMN strategy_confidence TYPE DECIMAL;

-- Adicionar comentários para documentação
COMMENT ON COLUMN strategy_results_tracking.operation_1_result IS 'Resultado da primeira operação monitorada (V para WIN, D para LOSS)';
COMMENT ON COLUMN strategy_results_tracking.operation_2_result IS 'Resultado da segunda operação monitorada (V para WIN, D para LOSS)';
COMMENT ON COLUMN strategy_results_tracking.pattern_success IS 'True se ambas as operações foram WIN (V,V)';
COMMENT ON COLUMN strategy_results_tracking.completed_at IS 'Timestamp de quando o rastreamento foi finalizado';

-- Verificar a estrutura atualizada da tabela
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'strategy_results_tracking' 
ORDER BY ordinal_position;