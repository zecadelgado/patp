-- Migração para alinhar centro_custo ao novo modelo de dados
-- Adiciona código único, responsável, flag de ativo e observações

ALTER TABLE centro_custo
    ADD COLUMN IF NOT EXISTS codigo VARCHAR(50) NOT NULL AFTER id_centro_custo,
    ADD UNIQUE INDEX IF NOT EXISTS codigo_UNIQUE (codigo);

ALTER TABLE centro_custo
    ADD COLUMN IF NOT EXISTS responsavel VARCHAR(255) NULL AFTER nome_centro,
    ADD COLUMN IF NOT EXISTS ativo TINYINT(1) NOT NULL DEFAULT 1 AFTER responsavel,
    ADD COLUMN IF NOT EXISTS observacoes TEXT NULL AFTER ativo;

-- Migra texto existente de descricao para observacoes, se aplicável
UPDATE centro_custo
SET observacoes = descricao
WHERE observacoes IS NULL AND descricao IS NOT NULL;
