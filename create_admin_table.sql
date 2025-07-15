-- Migração: Criar tabela de administradores
-- Data: $(date)
-- Descrição: Tabela para gerenciar administradores do sistema

-- Criar tabela de administradores
CREATE TABLE IF NOT EXISTS admins (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  role VARCHAR(50) DEFAULT 'admin' CHECK (role IN ('admin', 'super_admin', 'moderator')),
  is_active BOOLEAN DEFAULT true,
  permissions JSONB DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login TIMESTAMP WITH TIME ZONE,
  login_attempts INTEGER DEFAULT 0,
  locked_until TIMESTAMP WITH TIME ZONE
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);
CREATE INDEX IF NOT EXISTS idx_admins_is_active ON admins(is_active);
CREATE INDEX IF NOT EXISTS idx_admins_created_at ON admins(created_at);

-- Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Criar trigger para atualizar updated_at
CREATE TRIGGER update_admins_updated_at 
    BEFORE UPDATE ON admins 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Inserir administradores de teste
INSERT INTO admins (email, password_hash, name, role, permissions) 
VALUES 
(
  'admin@test.com',
  '$2b$10$example.hash.for.testing.purposes.only.replace.with.real.hash',
  'Administrador Principal',
  'super_admin',
  '{"users": ["read", "write", "delete"], "bots": ["read", "write", "delete"], "analytics": ["read"]}'
),
(
  'moderator@test.com',
  '$2b$10$example.hash.for.testing.purposes.only.replace.with.real.hash',
  'Moderador Teste',
  'moderator',
  '{"users": ["read", "write"], "bots": ["read"]}'
),
(
  'admin2@test.com',
  '$2b$10$example.hash.for.testing.purposes.only.replace.with.real.hash',
  'Administrador Secundário',
  'admin',
  '{"users": ["read", "write"], "bots": ["read", "write"]}'
)
ON CONFLICT (email) DO NOTHING;

-- Habilitar RLS (Row Level Security)
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- Política para permitir que administradores vejam apenas seus próprios dados
-- (ou todos se for super_admin)
CREATE POLICY "Admins can view own data or super_admin can view all" ON admins
    FOR SELECT USING (
        auth.uid()::text = id::text OR 
        EXISTS (
            SELECT 1 FROM admins 
            WHERE id::text = auth.uid()::text 
            AND role = 'super_admin' 
            AND is_active = true
        )
    );

-- Política para permitir que apenas super_admins criem novos administradores
CREATE POLICY "Only super_admin can insert" ON admins
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM admins 
            WHERE id::text = auth.uid()::text 
            AND role = 'super_admin' 
            AND is_active = true
        )
    );

-- Política para permitir que administradores atualizem seus próprios dados
-- ou super_admin pode atualizar qualquer um
CREATE POLICY "Admins can update own data or super_admin can update all" ON admins
    FOR UPDATE USING (
        auth.uid()::text = id::text OR 
        EXISTS (
            SELECT 1 FROM admins 
            WHERE id::text = auth.uid()::text 
            AND role = 'super_admin' 
            AND is_active = true
        )
    );

-- Comentários na tabela e colunas
COMMENT ON TABLE admins IS 'Tabela de administradores do sistema Bot Strategy Hub';
COMMENT ON COLUMN admins.id IS 'ID único do administrador (UUID)';
COMMENT ON COLUMN admins.email IS 'Email único do administrador para login';
COMMENT ON COLUMN admins.password_hash IS 'Hash bcrypt da senha do administrador';
COMMENT ON COLUMN admins.name IS 'Nome completo do administrador';
COMMENT ON COLUMN admins.role IS 'Papel do administrador: admin, super_admin, moderator';
COMMENT ON COLUMN admins.is_active IS 'Status ativo/inativo do administrador';
COMMENT ON COLUMN admins.permissions IS 'Permissões específicas em formato JSON';
COMMENT ON COLUMN admins.created_at IS 'Data e hora de criação do registro';
COMMENT ON COLUMN admins.updated_at IS 'Data e hora da última atualização';
COMMENT ON COLUMN admins.last_login IS 'Data e hora do último login';
COMMENT ON COLUMN admins.login_attempts IS 'Número de tentativas de login falhadas';
COMMENT ON COLUMN admins.locked_until IS 'Data até quando a conta está bloqueada';

-- Criar view para dados seguros (sem password_hash)
CREATE OR REPLACE VIEW admin_safe_view AS
SELECT 
    id,
    email,
    name,
    role,
    is_active,
    permissions,
    created_at,
    updated_at,
    last_login,
    login_attempts,
    locked_until
FROM admins;

-- Comentário na view
COMMENT ON VIEW admin_safe_view IS 'View segura da tabela admins sem expor password_hash';

PRINT 'Tabela de administradores criada com sucesso!';
PRINT 'Administradores de teste inseridos:';
PRINT '- admin@test.com (super_admin)';
PRINT '- moderator@test.com (moderator)';
PRINT '- admin2@test.com (admin)';
PRINT 'IMPORTANTE: Altere as senhas antes de usar em produção!';