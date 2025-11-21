-- ============================================================================
-- MIGRAÇÃO: Adicionar campos faltantes na tabela manutencoes
-- Versão: 2.3
-- Data: 19/11/2025
-- Descrição: Adiciona campos tipo_manutencao e empresa para completar funcionalidade
-- ============================================================================

USE patrimonio_ideau;

-- 1. Adicionar coluna tipo_manutencao (se não existir)
-- Tipos comuns: preventiva, corretiva, preditiva, emergencial
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'patrimonio_ideau' 
  AND TABLE_NAME = 'manutencoes' 
  AND COLUMN_NAME = 'tipo_manutencao';

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE manutencoes ADD COLUMN tipo_manutencao ENUM(''preventiva'', ''corretiva'', ''preditiva'', ''emergencial'', ''outro'') NULL DEFAULT NULL AFTER id_patrimonio',
    'SELECT ''Coluna tipo_manutencao já existe'' AS mensagem');
    
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. Adicionar coluna empresa (se não existir)
-- Campo para registrar empresa terceirizada que realizou a manutenção
SELECT COUNT(*) INTO @col_exists2
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = 'patrimonio_ideau' 
  AND TABLE_NAME = 'manutencoes' 
  AND COLUMN_NAME = 'empresa';

SET @sql2 = IF(@col_exists2 = 0,
    'ALTER TABLE manutencoes ADD COLUMN empresa VARCHAR(255) NULL DEFAULT NULL AFTER custo',
    'SELECT ''Coluna empresa já existe'' AS mensagem');
    
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- 3. Adicionar índice para melhorar performance de consultas
SELECT COUNT(*) INTO @idx_exists
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'patrimonio_ideau' 
  AND TABLE_NAME = 'manutencoes' 
  AND INDEX_NAME = 'idx_data_inicio';

SET @sql3 = IF(@idx_exists = 0,
    'CREATE INDEX idx_data_inicio ON manutencoes(data_inicio DESC)',
    'SELECT ''Índice idx_data_inicio já existe'' AS mensagem');
    
PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- 4. Adicionar índice para status
SELECT COUNT(*) INTO @idx_exists2
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'patrimonio_ideau' 
  AND TABLE_NAME = 'manutencoes' 
  AND INDEX_NAME = 'idx_status';

SET @sql4 = IF(@idx_exists2 = 0,
    'CREATE INDEX idx_status ON manutencoes(status)',
    'SELECT ''Índice idx_status já existe'' AS mensagem');
    
PREPARE stmt4 FROM @sql4;
EXECUTE stmt4;
DEALLOCATE PREPARE stmt4;

-- 5. Verificar estrutura final
SELECT 
    'Estrutura da tabela manutencoes atualizada com sucesso!' AS mensagem,
    (SELECT COUNT(*) FROM information_schema.COLUMNS 
     WHERE TABLE_SCHEMA = 'patrimonio_ideau' 
       AND TABLE_NAME = 'manutencoes') AS total_colunas;

-- 6. Mostrar colunas da tabela
SHOW COLUMNS FROM manutencoes;

-- ============================================================================
-- FIM DA MIGRAÇÃO
-- ============================================================================

-- ROLLBACK (se necessário):
-- ALTER TABLE manutencoes DROP COLUMN tipo_manutencao;
-- ALTER TABLE manutencoes DROP COLUMN empresa;
-- DROP INDEX idx_data_inicio ON manutencoes;
-- DROP INDEX idx_status ON manutencoes;
