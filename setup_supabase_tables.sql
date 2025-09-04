-- =====================================================
-- CONFIGURAÇÃO SUPABASE - NOVA GERAÇÃO DE ROBÔS
-- =====================================================
-- Este arquivo contém os comandos SQL para configurar
-- a infraestrutura da Central de Controle no Supabase
-- =====================================================

-- Tabela de Controle e Status para a NOVA GERAÇÃO de robôs
CREATE TABLE IF NOT EXISTS public.bot_configurations (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Identificação do Bot
    bot_name TEXT NOT NULL UNIQUE,
    bot_version TEXT DEFAULT '1.0',
    
    -- Controle de Estado
    is_active BOOLEAN DEFAULT true,
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    process_id INTEGER,
    status TEXT DEFAULT 'stopped', -- stopped, starting, running, error
    
    -- Parâmetros de Trading
    param_take_profit DECIMAL(10,2) DEFAULT 10.0,
    param_stake_inicial DECIMAL(10,2) DEFAULT 50.0,
    param_max_stake DECIMAL(10,2) DEFAULT 1000.0,
    param_growth_rate DECIMAL(5,2) DEFAULT 2.0,
    param_max_operations INTEGER DEFAULT 10,
    
    -- Configurações Avançadas
    config_json JSONB DEFAULT '{}',
    
    -- Estatísticas
    total_operations INTEGER DEFAULT 0,
    successful_operations INTEGER DEFAULT 0,
    failed_operations INTEGER DEFAULT 0,
    total_profit DECIMAL(15,2) DEFAULT 0.0,
    
    -- Controle de Restart
    restart_count INTEGER DEFAULT 0,
    last_restart TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT bot_configurations_bot_name_key UNIQUE (bot_name)
);

-- Tabela de Logs UNIFICADA para a NOVA GERAÇÃO de robôs
CREATE TABLE IF NOT EXISTS public.bot_operation_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Identificação
    bot_id BIGINT REFERENCES public.bot_configurations(id) ON DELETE CASCADE,
    bot_name TEXT NOT NULL,
    
    -- Dados da Operação
    operation_type TEXT NOT NULL, -- 'BUY', 'SELL', 'HEARTBEAT', 'START', 'STOP', 'ERROR'
    contract_id TEXT,
    stake DECIMAL(10,2),
    payout DECIMAL(10,2),
    profit_loss DECIMAL(10,2),
    
    -- Status e Resultado
    status TEXT NOT NULL, -- 'pending', 'won', 'lost', 'error', 'info'
    result_details JSONB DEFAULT '{}',
    
    -- Contexto Técnico
    signal_data JSONB DEFAULT '{}',
    market_conditions JSONB DEFAULT '{}',
    
    -- Debugging
    error_message TEXT,
    execution_time_ms INTEGER,
    
    -- Índices para Performance
    INDEX idx_bot_operation_logs_bot_id (bot_id),
    INDEX idx_bot_operation_logs_created_at (created_at),
    INDEX idx_bot_operation_logs_operation_type (operation_type),
    INDEX idx_bot_operation_logs_status (status)
);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bot_configurations_updated_at
    BEFORE UPDATE ON public.bot_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Inserir configurações iniciais para os robôs gerenciados
INSERT INTO public.bot_configurations 
(bot_name, param_take_profit, param_stake_inicial, param_max_stake, param_growth_rate, param_max_operations)
VALUES 
('Accumulator', 10.0, 50.0, 1000.0, 2.0, 10),
('Speed Bot', 10.0, 50.0, 800.0, 1.8, 15)
ON CONFLICT (bot_name) DO UPDATE SET
    param_take_profit = EXCLUDED.param_take_profit,
    param_stake_inicial = EXCLUDED.param_stake_inicial,
    param_max_stake = EXCLUDED.param_max_stake,
    param_growth_rate = EXCLUDED.param_growth_rate,
    param_max_operations = EXCLUDED.param_max_operations,
    updated_at = NOW();

-- Verificar se as tabelas foram criadas corretamente
SELECT 
    'bot_configurations' as table_name,
    COUNT(*) as total_bots,
    COUNT(CASE WHEN is_active THEN 1 END) as active_bots
FROM public.bot_configurations
UNION ALL
SELECT 
    'bot_operation_logs' as table_name,
    COUNT(*) as total_logs,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as logs_last_24h
FROM public.bot_operation_logs;

-- =====================================================
-- CONFIGURAÇÃO CONCLUÍDA
-- =====================================================
-- Execute este arquivo no seu Supabase SQL Editor
-- Depois execute: python orchestrator.py
-- =====================================================