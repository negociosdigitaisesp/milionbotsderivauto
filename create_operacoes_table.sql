-- Script SQL para criar a tabela de operações no Supabase
-- Execute este script no SQL Editor do Supabase

-- Criar tabela para armazenar operações dos bots
CREATE TABLE IF NOT EXISTS operacoes (
    id SERIAL PRIMARY KEY,
    nome_bot VARCHAR(100) NOT NULL,
    lucro DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_operacoes_nome_bot ON operacoes(nome_bot);
CREATE INDEX IF NOT EXISTS idx_operacoes_timestamp ON operacoes(timestamp);
CREATE INDEX IF NOT EXISTS idx_operacoes_created_at ON operacoes(created_at);

-- Adicionar comentários para documentação
COMMENT ON TABLE operacoes IS 'Tabela para armazenar resultados das operações dos bots de trading';
COMMENT ON COLUMN operacoes.nome_bot IS 'Nome identificador do bot que executou a operação';
COMMENT ON COLUMN operacoes.lucro IS 'Valor do lucro ou prejuízo da operação';
COMMENT ON COLUMN operacoes.timestamp IS 'Timestamp da operação';
COMMENT ON COLUMN operacoes.created_at IS 'Timestamp de criação do registro';

-- Verificar se a tabela foi criada
SELECT 'Tabela operacoes criada com sucesso!' as status;