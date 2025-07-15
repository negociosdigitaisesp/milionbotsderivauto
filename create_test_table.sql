-- Migração: Criar tabela de teste
-- Data: $(date)
-- Descrição: Tabela simples para testes

-- Criar tabela de teste
CREATE TABLE IF NOT EXISTS test_table (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índice para melhor performance na coluna name
CREATE INDEX IF NOT EXISTS idx_test_table_name ON test_table(name);

-- Criar índice para melhor performance na coluna created_at
CREATE INDEX IF NOT EXISTS idx_test_table_created_at ON test_table(created_at);

-- Inserir alguns dados de teste
INSERT INTO test_table (name) VALUES 
('Teste 1'),
('Teste 2'),
('Teste 3'),
('Exemplo de Nome'),
('Dados de Teste')
ON CONFLICT (id) DO NOTHING;

-- Comentários na tabela e colunas
COMMENT ON TABLE test_table IS 'Tabela de teste para desenvolvimento';
COMMENT ON COLUMN test_table.id IS 'ID único da entrada (UUID)';
COMMENT ON COLUMN test_table.name IS 'Nome ou descrição do item de teste';
COMMENT ON COLUMN test_table.created_at IS 'Data e hora de criação do registro';

PRINT 'Tabela test_table criada com sucesso!';
PRINT 'Dados de teste inseridos.';
PRINT 'Execute este arquivo no seu projeto Supabase para criar a tabela.';