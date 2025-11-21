-- ========================================================================
-- Script de Migração: Inclusão do papel MASTER
-- Data: 2026-01-01
-- Descrição: Ajusta a coluna usuarios.nivel_acesso para aceitar o novo
--            papel 'master' e orienta a promoção de pelo menos um usuário.
-- ========================================================================

USE neobenesys;  -- Ajuste o nome do banco conforme necessário

-- 1) Atualizar o tipo do campo para incluir o valor 'master'
ALTER TABLE usuarios
MODIFY COLUMN nivel_acesso ENUM('master', 'admin', 'user') NOT NULL DEFAULT 'user'
COMMENT 'Define o nível de acesso: master, admin ou user';

-- 2) (Opcional, mas recomendado) Promover um usuário existente a MASTER
--    Substitua o critério do WHERE pelo usuário que deve administrar o sistema.
--    Execute apenas uma das instruções abaixo, conforme o identificador que preferir.
--    UPDATE usuarios SET nivel_acesso = 'master' WHERE email = 'admin@seudominio.com';
--    UPDATE usuarios SET nivel_acesso = 'master' WHERE id_usuario = 1;

-- 3) Verifique o resultado após a promoção
-- SELECT id_usuario, nome, email, nivel_acesso FROM usuarios WHERE nivel_acesso = 'master';

-- ========================================================================
-- FIM DO SCRIPT
-- ========================================================================
