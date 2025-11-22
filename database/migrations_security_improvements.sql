-- ========================================================================
-- Script de Migração: Melhorias de Segurança e Funcionalidades - NeoBenesys
-- Data: 2025-11-17
-- Descrição: Alterações no banco de dados para suportar as melhorias
--            implementadas no sistema (hash de senhas, campo ativo, 
--            tipo de manutenção, centro de custo em NF, etc.)
-- ========================================================================

-- IMPORTANTE: Execute este script em um ambiente de teste primeiro!
-- Faça backup do banco de dados antes de executar em produção!

USE neobenesys;  -- Ajuste o nome do banco conforme necessário

-- ========================================================================
-- 1. TABELA USUARIOS - Campo 'ativo' e ajuste de senha
-- ========================================================================

-- Adicionar coluna 'ativo' se não existir
ALTER TABLE usuarios 
ADD COLUMN IF NOT EXISTS ativo TINYINT(1) NOT NULL DEFAULT 1 
COMMENT 'Indica se o usuário está ativo (1) ou inativo (0)';

-- Aumentar tamanho da coluna senha para suportar hash bcrypt (60 caracteres)
ALTER TABLE usuarios 
MODIFY COLUMN senha VARCHAR(255) NOT NULL 
COMMENT 'Senha do usuário (hash bcrypt)';

-- Criar índice no email se não existir (para melhorar performance e garantir unicidade)
CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- ========================================================================
-- 2. TABELA MANUTENCOES - Campo 'tipo_manutencao'
-- ========================================================================

-- Adicionar coluna 'tipo_manutencao' se não existir
ALTER TABLE manutencoes 
ADD COLUMN IF NOT EXISTS tipo_manutencao VARCHAR(50) NULL 
COMMENT 'Tipo da manutenção (Preventiva, Corretiva, etc.)';

-- ========================================================================
-- 3. TABELA NOTAS_FISCAIS - Campo 'id_centro_custo'
-- ========================================================================

-- Adicionar coluna 'id_centro_custo' se não existir
ALTER TABLE notas_fiscais
ADD COLUMN IF NOT EXISTS id_centro_custo INT NULL
COMMENT 'Referência ao centro de custo';

-- Adicionar índice e chave estrangeira para centro_custo
CREATE INDEX IF NOT EXISTS idx_notas_centro_custo ON notas_fiscais(id_centro_custo);
ALTER TABLE notas_fiscais
DROP FOREIGN KEY IF EXISTS fk_notas_fiscais_centro_custo,
ADD CONSTRAINT fk_notas_fiscais_centro_custo
FOREIGN KEY (id_centro_custo) REFERENCES centro_custo(id_centro_custo)
ON DELETE SET NULL ON UPDATE CASCADE;

-- ========================================================================
-- 3.1 TABELA CENTRO_CUSTO - Campo 'ativo'
-- ========================================================================

-- Adicionar coluna 'ativo' para habilitar filtros de itens ativos
ALTER TABLE centro_custo
ADD COLUMN IF NOT EXISTS ativo TINYINT(1) NOT NULL DEFAULT 1
COMMENT 'Indica se o centro de custo está ativo (1) ou inativo (0)';

-- Opcional: garantir índice para pesquisas por ativos
CREATE INDEX IF NOT EXISTS idx_centro_custo_ativo ON centro_custo(ativo);

-- ========================================================================
-- 4. TABELA FORNECEDORES - Índice único em CNPJ
-- ========================================================================

-- Criar índice único no CNPJ se não existir (para evitar duplicatas)
-- Ajuste o nome da coluna conforme seu banco (cnpj, cpf_cnpj, etc.)
CREATE UNIQUE INDEX IF NOT EXISTS idx_fornecedores_cnpj ON fornecedores(cnpj);

-- ========================================================================
-- 5. TABELA AUDITORIAS - Verificar estrutura
-- ========================================================================

-- A tabela auditorias deve ter a seguinte estrutura mínima:
-- Se a tabela não existir, descomente e ajuste o código abaixo:

/*
CREATE TABLE IF NOT EXISTS auditorias (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    data_auditoria DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tabela_afetada VARCHAR(100) NOT NULL,
    id_registro_afetado INT NOT NULL,
    acao VARCHAR(20) NOT NULL COMMENT 'CREATE, UPDATE ou DELETE',
    id_usuario INT NOT NULL,
    detalhes TEXT NULL COMMENT 'Detalhes da operação em formato JSON ou texto',
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    INDEX idx_auditorias_data (data_auditoria),
    INDEX idx_auditorias_tabela (tabela_afetada),
    INDEX idx_auditorias_usuario (id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
*/

-- ========================================================================
-- 6. VERIFICAÇÕES E AJUSTES FINAIS
-- ========================================================================

-- Atualizar usuários existentes para ficarem ativos por padrão
UPDATE usuarios SET ativo = 1 WHERE ativo IS NULL OR ativo = 0;

-- ========================================================================
-- 7. OBSERVAÇÕES IMPORTANTES
-- ========================================================================

/*
ATENÇÃO: MIGRAÇÃO DE SENHAS

As senhas existentes no banco estão em texto puro e precisam ser migradas
para hash bcrypt. O sistema implementa migração automática:

1. Quando um usuário fizer login com senha em texto puro, o sistema:
   - Valida a senha
   - Gera o hash bcrypt
   - Atualiza automaticamente no banco
   
2. Após a primeira autenticação de cada usuário, a senha estará em hash.

3. Para forçar a migração de todas as senhas imediatamente, você pode:
   - Criar um script Python que leia todos os usuários e gere os hashes
   - Ou aguardar que cada usuário faça login naturalmente

IMPORTANTE: Não é possível reverter senhas de hash para texto puro!
Certifique-se de que todos os usuários saibam suas senhas antes da migração.
*/

-- ========================================================================
-- FIM DO SCRIPT
-- ========================================================================

-- Verificar se as alterações foram aplicadas
SELECT 'Migração concluída! Verifique os logs acima para confirmar.' AS status;
