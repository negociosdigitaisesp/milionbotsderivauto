-- Tabela para armazenar tokens criptografados da Deriv
CREATE TABLE IF NOT EXISTS deriv_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Tabela para bots ativos
CREATE TABLE IF NOT EXISTS active_bots (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    duration INTEGER NOT NULL,
    duration_unit TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    barrier TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela para histórico de trades
CREATE TABLE IF NOT EXISTS trade_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    bot_id TEXT NOT NULL REFERENCES active_bots(id) ON DELETE CASCADE,
    contract_id TEXT NOT NULL,
    buy_price DECIMAL(10,2) NOT NULL,
    sell_price DECIMAL(10,2),
    profit DECIMAL(10,2),
    status TEXT NOT NULL CHECK (status IN ('open', 'won', 'lost')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol TEXT NOT NULL,
    contract_type TEXT NOT NULL
);

-- Tabela para configurações de bot por usuário
CREATE TABLE IF NOT EXISTS user_bot_configs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    bot_name TEXT NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, bot_name)
);

-- Tabela para logs de atividade dos bots
CREATE TABLE IF NOT EXISTS bot_activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    bot_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_deriv_tokens_user_id ON deriv_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_active_bots_user_id ON active_bots(user_id);
CREATE INDEX IF NOT EXISTS idx_active_bots_is_active ON active_bots(is_active);
CREATE INDEX IF NOT EXISTS idx_trade_history_user_id ON trade_history(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_history_bot_id ON trade_history(bot_id);
CREATE INDEX IF NOT EXISTS idx_trade_history_timestamp ON trade_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_bot_configs_user_id ON user_bot_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_bot_activity_logs_user_id ON bot_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_bot_activity_logs_timestamp ON bot_activity_logs(timestamp DESC);

-- RLS (Row Level Security) policies
ALTER TABLE deriv_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_bot_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_activity_logs ENABLE ROW LEVEL SECURITY;

-- Políticas para deriv_tokens
CREATE POLICY "Users can only access their own tokens" ON deriv_tokens
    FOR ALL USING (auth.uid() = user_id);

-- Políticas para active_bots
CREATE POLICY "Users can only access their own bots" ON active_bots
    FOR ALL USING (auth.uid() = user_id);

-- Políticas para trade_history
CREATE POLICY "Users can only access their own trade history" ON trade_history
    FOR ALL USING (auth.uid() = user_id);

-- Políticas para user_bot_configs
CREATE POLICY "Users can only access their own bot configs" ON user_bot_configs
    FOR ALL USING (auth.uid() = user_id);

-- Políticas para bot_activity_logs
CREATE POLICY "Users can only access their own activity logs" ON bot_activity_logs
    FOR ALL USING (auth.uid() = user_id);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar updated_at
CREATE TRIGGER update_deriv_tokens_updated_at BEFORE UPDATE ON deriv_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_active_bots_updated_at BEFORE UPDATE ON active_bots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_bot_configs_updated_at BEFORE UPDATE ON user_bot_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();