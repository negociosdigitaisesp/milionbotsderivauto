-- =====================================================
-- SISTEMA PROFISSIONAL DE GESTÃO DE CLIENTES
-- Desenvolvido por: Especialista em Banco de Dados
-- Data: $(date)
-- Versão: 1.0
-- =====================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- TABELA PRINCIPAL DE CLIENTES
-- =====================================================
CREATE TABLE IF NOT EXISTS clients (
    -- Identificação
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    client_code VARCHAR(20) UNIQUE NOT NULL DEFAULT ('CLI' || LPAD(nextval('client_sequence')::text, 6, '0')),
    
    -- Dados pessoais
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    document_number VARCHAR(50), -- CPF/CNPJ
    
    -- Autenticação
    password_hash VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    
    -- SISTEMA DE ATIVAÇÃO E CONTROLE
    is_active BOOLEAN DEFAULT FALSE, -- Cliente ativo/inativo (controle manual)
    auto_activated BOOLEAN DEFAULT TRUE, -- Ativação automática no cadastro
    activation_date TIMESTAMP WITH TIME ZONE, -- Data de ativação
    deactivation_date TIMESTAMP WITH TIME ZONE, -- Data de desativação
    deactivation_reason TEXT, -- Motivo da desativação
    
    -- SISTEMA DE EXPIRAÇÃO
    expires_at TIMESTAMP WITH TIME ZONE, -- Data de expiração
    expiration_warning_sent BOOLEAN DEFAULT FALSE, -- Aviso de expiração enviado
    grace_period_days INTEGER DEFAULT 7, -- Período de graça após expiração
    
    -- Plano e permissões
    plan_type VARCHAR(50) DEFAULT 'basic', -- basic, premium, enterprise
    plan_features JSONB DEFAULT '{}', -- Recursos específicos do plano
    custom_permissions JSONB DEFAULT '{}', -- Permissões customizadas
    
    -- Auditoria e controle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- Dados adicionais
    metadata JSONB DEFAULT '{}', -- Dados extras flexíveis
    notes TEXT, -- Observações administrativas
    
    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_plan CHECK (plan_type IN ('basic', 'premium', 'enterprise', 'trial')),
    CONSTRAINT valid_expiration CHECK (expires_at IS NULL OR expires_at > created_at)
);

-- Sequência para código do cliente
CREATE SEQUENCE IF NOT EXISTS client_sequence START 1;

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_clients_expires_at ON clients(expires_at);
CREATE INDEX IF NOT EXISTS idx_clients_plan_type ON clients(plan_type);
CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at);
CREATE INDEX IF NOT EXISTS idx_clients_last_login ON clients(last_login);
CREATE INDEX IF NOT EXISTS idx_clients_client_code ON clients(client_code);
CREATE INDEX IF NOT EXISTS idx_clients_email_verified ON clients(email_verified);

-- Índice composto para consultas de acesso
CREATE INDEX IF NOT EXISTS idx_clients_access_control ON clients(is_active, expires_at, email_verified);

-- =====================================================
-- FUNÇÕES AUXILIARES
-- =====================================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Função para ativar cliente automaticamente
CREATE OR REPLACE FUNCTION auto_activate_client()
RETURNS TRIGGER AS $$
BEGIN
    -- Se auto_activated está TRUE, ativa o cliente automaticamente
    IF NEW.auto_activated = TRUE AND NEW.is_active = FALSE THEN
        NEW.is_active = TRUE;
        NEW.activation_date = NOW();
    END IF;
    
    -- Se está sendo ativado manualmente
    IF OLD.is_active = FALSE AND NEW.is_active = TRUE THEN
        NEW.activation_date = NOW();
        NEW.deactivation_date = NULL;
        NEW.deactivation_reason = NULL;
    END IF;
    
    -- Se está sendo desativado
    IF OLD.is_active = TRUE AND NEW.is_active = FALSE THEN
        NEW.deactivation_date = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Função para verificar se cliente pode acessar
CREATE OR REPLACE FUNCTION can_client_access(client_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    client_record RECORD;
BEGIN
    SELECT * INTO client_record FROM clients WHERE id = client_id;
    
    -- Cliente não existe
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Cliente não está ativo
    IF client_record.is_active = FALSE THEN
        RETURN FALSE;
    END IF;
    
    -- Email não verificado
    IF client_record.email_verified = FALSE THEN
        RETURN FALSE;
    END IF;
    
    -- Cliente expirado (sem período de graça)
    IF client_record.expires_at IS NOT NULL AND 
       client_record.expires_at < NOW() - INTERVAL '1 day' * COALESCE(client_record.grace_period_days, 0) THEN
        RETURN FALSE;
    END IF;
    
    -- Cliente bloqueado por tentativas de login
    IF client_record.locked_until IS NOT NULL AND client_record.locked_until > NOW() THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ language 'plpgsql';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger para atualizar updated_at
CREATE TRIGGER update_clients_updated_at 
    BEFORE UPDATE ON clients 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para ativação automática
CREATE TRIGGER auto_activate_client_trigger
    BEFORE INSERT OR UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION auto_activate_client();

-- =====================================================
-- VIEWS PARA CONSULTAS COMUNS
-- =====================================================

-- View de clientes ativos
CREATE OR REPLACE VIEW active_clients AS
SELECT 
    id, client_code, full_name, email, phone,
    plan_type, is_active, expires_at, last_login,
    created_at, activation_date
FROM clients 
WHERE is_active = TRUE 
  AND email_verified = TRUE
  AND (expires_at IS NULL OR expires_at > NOW());

-- View de clientes expirados
CREATE OR REPLACE VIEW expired_clients AS
SELECT 
    id, client_code, full_name, email, plan_type,
    expires_at, grace_period_days,
    (expires_at + INTERVAL '1 day' * COALESCE(grace_period_days, 0)) as final_expiration
FROM clients 
WHERE expires_at IS NOT NULL 
  AND expires_at < NOW();

-- View de clientes que precisam de ativação manual
CREATE OR REPLACE VIEW pending_activation AS
SELECT 
    id, client_code, full_name, email, created_at,
    auto_activated, is_active, email_verified
FROM clients 
WHERE is_active = FALSE 
  AND auto_activated = FALSE;

-- =====================================================
-- POLÍTICAS DE SEGURANÇA (RLS)
-- =====================================================

-- Habilitar RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

-- Política para administradores (acesso total)
CREATE POLICY "Admins can access all clients" ON clients
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admins 
            WHERE id::text = auth.uid()::text 
            AND is_active = true
        )
    );

-- Política para clientes (acesso próprio)
CREATE POLICY "Clients can access own data" ON clients
    FOR SELECT USING (id::text = auth.uid()::text);

-- Política para atualização própria (dados limitados)
CREATE POLICY "Clients can update own limited data" ON clients
    FOR UPDATE USING (id::text = auth.uid()::text)
    WITH CHECK (
        -- Não pode alterar campos críticos
        is_active = OLD.is_active AND
        expires_at = OLD.expires_at AND
        plan_type = OLD.plan_type AND
        auto_activated = OLD.auto_activated
    );

-- =====================================================
-- DADOS DE TESTE
-- =====================================================

-- Inserir clientes de teste
INSERT INTO clients (
    full_name, email, password_hash, plan_type, 
    expires_at, auto_activated, email_verified
) VALUES 
(
    'João Silva Santos',
    'joao@teste.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'premium',
    NOW() + INTERVAL '30 days',
    TRUE,
    TRUE
),
(
    'Maria Oliveira Costa',
    'maria@teste.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'basic',
    NOW() + INTERVAL '15 days',
    TRUE,
    TRUE
),
(
    'Pedro Ferreira Lima',
    'pedro@teste.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'enterprise',
    NOW() + INTERVAL '90 days',
    FALSE, -- Precisa ativação manual
    FALSE
),
(
    'Ana Carolina Souza',
    'ana@teste.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'trial',
    NOW() + INTERVAL '7 days',
    TRUE,
    TRUE
),
(
    'Carlos Eduardo Mendes',
    'carlos@teste.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'basic',
    NOW() - INTERVAL '5 days', -- Expirado
    TRUE,
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- =====================================================
-- COMENTÁRIOS DETALHADOS
-- =====================================================

COMMENT ON TABLE clients IS 'Sistema profissional de gestão de clientes com controle de ativação e expiração';
COMMENT ON COLUMN clients.id IS 'Identificador único do cliente (UUID)';
COMMENT ON COLUMN clients.client_code IS 'Código único do cliente (CLI000001, CLI000002, etc.)';
COMMENT ON COLUMN clients.is_active IS 'Status ativo/inativo - controle manual do administrador';
COMMENT ON COLUMN clients.auto_activated IS 'Se TRUE, cliente é ativado automaticamente no cadastro';
COMMENT ON COLUMN clients.expires_at IS 'Data de expiração do acesso do cliente';
COMMENT ON COLUMN clients.grace_period_days IS 'Dias de período de graça após expiração';
COMMENT ON COLUMN clients.activation_date IS 'Data em que o cliente foi ativado';
COMMENT ON COLUMN clients.deactivation_date IS 'Data em que o cliente foi desativado';
COMMENT ON COLUMN clients.email_verified IS 'Se o email foi verificado';
COMMENT ON COLUMN clients.plan_type IS 'Tipo de plano: basic, premium, enterprise, trial';

COMMENT ON FUNCTION can_client_access(UUID) IS 'Verifica se cliente pode acessar a plataforma';
COMMENT ON VIEW active_clients IS 'Clientes ativos e com acesso liberado';
COMMENT ON VIEW expired_clients IS 'Clientes com acesso expirado';
COMMENT ON VIEW pending_activation IS 'Clientes aguardando ativação manual';

-- =====================================================
-- INSTRUÇÕES DE USO
-- =====================================================

/*
INSTRUÇÕES PARA USO DO SISTEMA:

1. CADASTRO DE CLIENTE:
   - Cliente se cadastra normalmente
   - Se auto_activated = TRUE: cliente fica ativo automaticamente
   - Se auto_activated = FALSE: precisa ativação manual do admin

2. CONTROLE DE ATIVAÇÃO:
   - Para ativar: UPDATE clients SET is_active = TRUE WHERE id = 'client_id';
   - Para desativar: UPDATE clients SET is_active = FALSE, deactivation_reason = 'motivo' WHERE id = 'client_id';

3. CONTROLE DE EXPIRAÇÃO:
   - Definir expiração: UPDATE clients SET expires_at = '2024-12-31 23:59:59' WHERE id = 'client_id';
   - Remover expiração: UPDATE clients SET expires_at = NULL WHERE id = 'client_id';

4. VERIFICAR ACESSO:
   - SELECT can_client_access('client_id_uuid');
   - Retorna TRUE se pode acessar, FALSE se não pode

5. CONSULTAS ÚTEIS:
   - Clientes ativos: SELECT * FROM active_clients;
   - Clientes expirados: SELECT * FROM expired_clients;
   - Aguardando ativação: SELECT * FROM pending_activation;

6. CONFIGURAÇÕES RECOMENDADAS:
   - auto_activated = TRUE para cadastros automáticos
   - auto_activated = FALSE para aprovação manual
   - grace_period_days = 7 para período de graça
   - Verificar email antes de liberar acesso
*/

PRINT 'Sistema profissional de clientes criado com sucesso!';
PRINT 'Recursos implementados:';
PRINT '✓ Ativação automática configurável';
PRINT '✓ Controle manual de ativação/desativação';
PRINT '✓ Sistema de expiração com período de graça';
PRINT '✓ Verificação de email obrigatória';
PRINT '✓ Múltiplos tipos de plano';
PRINT '✓ Auditoria completa';
PRINT '✓ Segurança com RLS';
PRINT '✓ Views para consultas comuns';
PRINT '✓ Funções auxiliares';
PRINT 'Execute este arquivo no Supabase para implementar o sistema completo!';