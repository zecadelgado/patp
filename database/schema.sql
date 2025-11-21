CREATE SCHEMA IF NOT EXISTS `patrimonio_ideau` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `patrimonio_ideau` ;

CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`usuarios` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `senha` VARCHAR(255) NOT NULL,
  `nivel_acesso` ENUM('master', 'admin', 'user') NOT NULL DEFAULT 'user',
  `data_criacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`categorias` (
  `id_categoria` INT NOT NULL AUTO_INCREMENT,
  `nome_categoria` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  PRIMARY KEY (`id_categoria`),
  UNIQUE INDEX `nome_categoria_UNIQUE` (`nome_categoria` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`fornecedores` (
  `id_fornecedor` INT NOT NULL AUTO_INCREMENT,
  `nome_fornecedor` VARCHAR(255) NOT NULL,
  `cnpj` VARCHAR(18) NULL,
  `contato` VARCHAR(255) NULL,
  `telefone` VARCHAR(20) NULL,
  `email` VARCHAR(255) NULL,
  PRIMARY KEY (`id_fornecedor`),
  UNIQUE INDEX `cnpj_UNIQUE` (`cnpj` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`setores_locais` (
  `id_setor_local` INT NOT NULL AUTO_INCREMENT,
  `nome_setor_local` VARCHAR(255) NOT NULL,
  `localizacao` VARCHAR(255) NULL,
  `descricao` TEXT NULL,
  PRIMARY KEY (`id_setor_local`),
  UNIQUE INDEX `nome_setor_local_UNIQUE` (`nome_setor_local` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`patrimonios` (
  `id_patrimonio` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  `numero_serie` VARCHAR(255) NULL,
  `valor_compra` DECIMAL(10,2) NULL,
  `quantidade` INT NOT NULL DEFAULT 1,
  `numero_nota` VARCHAR(50) NULL,
  `data_aquisicao` DATE NULL,
  `estado_conservacao` ENUM('novo', 'bom', 'regular', 'ruim') NULL,
  `id_categoria` INT NOT NULL,
  `id_fornecedor` INT NULL,
  `id_setor_local` INT NOT NULL,
  `status` ENUM('ativo', 'baixado', 'em_manutencao','desaparecido') NOT NULL DEFAULT 'ativo',
  `data_cadastro` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_patrimonio`),
  UNIQUE INDEX `numero_serie_UNIQUE` (`numero_serie` ASC) VISIBLE,
  INDEX `fk_patrimonios_categorias_idx` (`id_categoria` ASC) VISIBLE,
  INDEX `fk_patrimonios_fornecedores1_idx` (`id_fornecedor` ASC) VISIBLE,
  INDEX `fk_patrimonios_setores_locais1_idx` (`id_setor_local` ASC) VISIBLE,
  CONSTRAINT `fk_patrimonios_categorias`
    FOREIGN KEY (`id_categoria`)
    REFERENCES `patrimonio_ideau`.`categorias` (`id_categoria`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_fornecedores1`
    FOREIGN KEY (`id_fornecedor`)
    REFERENCES `patrimonio_ideau`.`fornecedores` (`id_fornecedor`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_setores_locais1`
    FOREIGN KEY (`id_setor_local`)
    REFERENCES `patrimonio_ideau`.`setores_locais` (`id_setor_local`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`movimentacoes` (
  `id_movimentacao` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `id_usuario` INT NOT NULL,
  `tipo_movimentacao` ENUM('entrada', 'saida', 'transferencia', 'manutencao', 'baixa') NOT NULL,
  `data_movimentacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `origem` VARCHAR(255) NULL,
  `destino` VARCHAR(255) NULL,
  `observacoes` TEXT NULL,
  PRIMARY KEY (`id_movimentacao`),
  INDEX `fk_movimentacoes_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  INDEX `fk_movimentacoes_usuarios1_idx` (`id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_movimentacoes_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_movimentacoes_usuarios1`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `patrimonio_ideau`.`usuarios` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`manutencoes` (
  `id_manutencao` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_inicio` DATE NOT NULL,
  `data_fim` DATE NULL,
  `descricao` TEXT NULL,
  `custo` DECIMAL(10,2) NULL,
  `responsavel` VARCHAR(255) NULL,
  `status` ENUM('pendente', 'em_andamento', 'concluida', 'cancelada') NOT NULL DEFAULT 'pendente',
  PRIMARY KEY (`id_manutencao`),
  INDEX `fk_manutencoes_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_manutencoes_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`depreciacoes` (
  `id_depreciacao` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_depreciacao` DATE NOT NULL,
  `valor_depreciado` DECIMAL(10,2) NOT NULL,
  `valor_atual` DECIMAL(10,2) NOT NULL,
  `metodo_depreciacao` VARCHAR(255) NULL,
  PRIMARY KEY (`id_depreciacao`),
  INDEX `fk_depreciacoes_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_depreciacoes_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`anexos` (
  `id_anexo` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `nome_arquivo` VARCHAR(255) NOT NULL,
  `caminho_arquivo` VARCHAR(255) NOT NULL,
  `tipo_arquivo` VARCHAR(45) NULL,
  `data_upload` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_anexo`),
  INDEX `fk_anexos_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_anexos_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`notas_fiscais` (
  `id_nota_fiscal` INT NOT NULL AUTO_INCREMENT,
  `numero_nota` VARCHAR(255) NOT NULL,
  `data_emissao` DATE NOT NULL,
  `valor_total` DECIMAL(10,2) NOT NULL,
  `id_fornecedor` INT NOT NULL,
  `caminho_arquivo_nf` VARCHAR(255) NULL,
  PRIMARY KEY (`id_nota_fiscal`),
  UNIQUE INDEX `numero_nota_UNIQUE` (`numero_nota` ASC) VISIBLE,
  INDEX `fk_notas_fiscais_fornecedores1_idx` (`id_fornecedor` ASC) VISIBLE,
  CONSTRAINT `fk_notas_fiscais_fornecedores1`
    FOREIGN KEY (`id_fornecedor`)
    REFERENCES `patrimonio_ideau`.`fornecedores` (`id_fornecedor`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`itens_nota_fiscal` (
  `id_item_nf` INT NOT NULL AUTO_INCREMENT,
  `id_nota_fiscal` INT NOT NULL,
  `id_patrimonio` INT NOT NULL,
  `quantidade` INT NOT NULL,
  `valor_unitario` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_item_nf`),
  INDEX `fk_itens_nota_fiscal_notas_fiscais1_idx` (`id_nota_fiscal` ASC) VISIBLE,
  INDEX `fk_itens_nota_fiscal_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_itens_nota_fiscal_notas_fiscais1`
    FOREIGN KEY (`id_nota_fiscal`)
    REFERENCES `patrimonio_ideau`.`notas_fiscais` (`id_nota_fiscal`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_itens_nota_fiscal_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`auditorias` (
  `id_auditoria` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NOT NULL,
  `data_auditoria` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `acao` VARCHAR(255) NOT NULL,
  `tabela_afetada` VARCHAR(255) NULL,
  `id_registro_afetado` INT NULL,
  `detalhes_antigos` JSON NULL,
  `detalhes_novos` JSON NULL,
  PRIMARY KEY (`id_auditoria`),
  INDEX `fk_auditorias_usuarios1_idx` (`id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_auditorias_usuarios1`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `patrimonio_ideau`.`usuarios` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`garantias` (
  `id_garantia` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_inicio` DATE NOT NULL,
  `data_fim` DATE NULL,
  `termos` TEXT NULL,
  `documento_garantia` VARCHAR(255) NULL,
  PRIMARY KEY (`id_garantia`),
  INDEX `fk_garantias_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_garantias_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`baixas` (
  `id_baixa` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_baixa` DATE NOT NULL,
  `motivo` VARCHAR(255) NOT NULL,
  `valor_residual` DECIMAL(10,2) NULL,
  `documento_baixa` VARCHAR(255) NULL,
  PRIMARY KEY (`id_baixa`),
  INDEX `fk_baixas_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_baixas_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`centro_custo` (
  `id_centro_custo` INT NOT NULL AUTO_INCREMENT,
  `nome_centro` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  PRIMARY KEY (`id_centro_custo`),
  UNIQUE INDEX `nome_centro_UNIQUE` (`nome_centro` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`patrimonios_centro_custo` (
  `id_patrimonio` INT NOT NULL,
  `id_centro_custo` INT NOT NULL,
  `data_associacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_patrimonio`, `id_centro_custo`),
  INDEX `fk_patrimonios_has_centro_custo_centro_custo1_idx` (`id_centro_custo` ASC) VISIBLE,
  INDEX `fk_patrimonios_has_centro_custo_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_patrimonios_has_centro_custo_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_has_centro_custo_centro_custo1`
    FOREIGN KEY (`id_centro_custo`)
    REFERENCES `patrimonio_ideau`.`centro_custo` (`id_centro_custo`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE SCHEMA IF NOT EXISTS `patrimonio_ideau` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `patrimonio_ideau` ;

CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`usuarios` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `senha` VARCHAR(255) NOT NULL,
  `nivel_acesso` ENUM('master', 'admin', 'user') NOT NULL DEFAULT 'user',
  `data_criacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`categorias` (
  `id_categoria` INT NOT NULL AUTO_INCREMENT,
  `nome_categoria` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  PRIMARY KEY (`id_categoria`),
  UNIQUE INDEX `nome_categoria_UNIQUE` (`nome_categoria` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`fornecedores` (
  `id_fornecedor` INT NOT NULL AUTO_INCREMENT,
  `nome_fornecedor` VARCHAR(255) NOT NULL,
  `cnpj` VARCHAR(18) NULL,
  `contato` VARCHAR(255) NULL,
  `telefone` VARCHAR(20) NULL,
  `email` VARCHAR(255) NULL,
  PRIMARY KEY (`id_fornecedor`),
  UNIQUE INDEX `cnpj_UNIQUE` (`cnpj` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`setores_locais` (
  `id_setor_local` INT NOT NULL AUTO_INCREMENT,
  `nome_setor_local` VARCHAR(255) NOT NULL,
  `localizacao` VARCHAR(255) NULL,
  `descricao` TEXT NULL,
  PRIMARY KEY (`id_setor_local`),
  UNIQUE INDEX `nome_setor_local_UNIQUE` (`nome_setor_local` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`patrimonios` (
  `id_patrimonio` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  `numero_serie` VARCHAR(255) NULL,
  `valor_compra` DECIMAL(10,2) NULL,
  `data_aquisicao` DATE NULL,
  `estado_conservacao` ENUM('novo', 'bom', 'regular', 'ruim') NULL,
  `id_categoria` INT NOT NULL,
  `id_fornecedor` INT NULL,
  `id_setor_local` INT NOT NULL,
  `status` ENUM('ativo', 'baixado', 'em_manutencao', 'desaparecido') NOT NULL DEFAULT 'ativo',
  `data_cadastro` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_patrimonio`),
  UNIQUE INDEX `numero_serie_UNIQUE` (`numero_serie` ASC) VISIBLE,
  INDEX `fk_patrimonios_categorias_idx` (`id_categoria` ASC) VISIBLE,
  INDEX `fk_patrimonios_fornecedores1_idx` (`id_fornecedor` ASC) VISIBLE,
  INDEX `fk_patrimonios_setores_locais1_idx` (`id_setor_local` ASC) VISIBLE,
  CONSTRAINT `fk_patrimonios_categorias`
    FOREIGN KEY (`id_categoria`)
    REFERENCES `patrimonio_ideau`.`categorias` (`id_categoria`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_fornecedores1`
    FOREIGN KEY (`id_fornecedor`)
    REFERENCES `patrimonio_ideau`.`fornecedores` (`id_fornecedor`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_setores_locais1`
    FOREIGN KEY (`id_setor_local`)
    REFERENCES `patrimonio_ideau`.`setores_locais` (`id_setor_local`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`movimentacoes` (
  `id_movimentacao` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `id_usuario` INT NOT NULL,
  `tipo_movimentacao` ENUM('entrada', 'saida', 'transferencia', 'manutencao', 'baixa') NOT NULL,
  `data_movimentacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `origem` VARCHAR(255) NULL,
  `destino` VARCHAR(255) NULL,
  `observacoes` TEXT NULL,
  PRIMARY KEY (`id_movimentacao`),
  INDEX `fk_movimentacoes_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  INDEX `fk_movimentacoes_usuarios1_idx` (`id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_movimentacoes_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_movimentacoes_usuarios1`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `patrimonio_ideau`.`usuarios` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`manutencoes` (
  `id_manutencao` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_inicio` DATE NOT NULL,
  `data_fim` DATE NULL,
  `descricao` TEXT NULL,
  `custo` DECIMAL(10,2) NULL,
  `responsavel` VARCHAR(255) NULL,
  `status` ENUM('pendente', 'em_andamento', 'concluida', 'cancelada') NOT NULL DEFAULT 'pendente',
  PRIMARY KEY (`id_manutencao`),
  INDEX `fk_manutencoes_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_manutencoes_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`depreciacoes` (
  `id_depreciacao` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_depreciacao` DATE NOT NULL,
  `valor_depreciado` DECIMAL(10,2) NOT NULL,
  `valor_atual` DECIMAL(10,2) NOT NULL,
  `metodo_depreciacao` VARCHAR(255) NULL,
  PRIMARY KEY (`id_depreciacao`),
  INDEX `fk_depreciacoes_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_depreciacoes_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`anexos` (
  `id_anexo` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `nome_arquivo` VARCHAR(255) NOT NULL,
  `caminho_arquivo` VARCHAR(255) NOT NULL,
  `tipo_arquivo` VARCHAR(45) NULL,
  `data_upload` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_anexo`),
  INDEX `fk_anexos_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_anexos_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`notas_fiscais` (
  `id_nota_fiscal` INT NOT NULL AUTO_INCREMENT,
  `numero_nota` VARCHAR(255) NOT NULL,
  `data_emissao` DATE NOT NULL,
  `valor_total` DECIMAL(10,2) NOT NULL,
  `id_fornecedor` INT NOT NULL,
  `caminho_arquivo_nf` VARCHAR(255) NULL,
  PRIMARY KEY (`id_nota_fiscal`),
  UNIQUE INDEX `numero_nota_UNIQUE` (`numero_nota` ASC) VISIBLE,
  INDEX `fk_notas_fiscais_fornecedores1_idx` (`id_fornecedor` ASC) VISIBLE,
  CONSTRAINT `fk_notas_fiscais_fornecedores1`
    FOREIGN KEY (`id_fornecedor`)
    REFERENCES `patrimonio_ideau`.`fornecedores` (`id_fornecedor`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`itens_nota_fiscal` (
  `id_item_nf` INT NOT NULL AUTO_INCREMENT,
  `id_nota_fiscal` INT NOT NULL,
  `id_patrimonio` INT NOT NULL,
  `quantidade` INT NOT NULL,
  `valor_unitario` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_item_nf`),
  INDEX `fk_itens_nota_fiscal_notas_fiscais1_idx` (`id_nota_fiscal` ASC) VISIBLE,
  INDEX `fk_itens_nota_fiscal_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_itens_nota_fiscal_notas_fiscais1`
    FOREIGN KEY (`id_nota_fiscal`)
    REFERENCES `patrimonio_ideau`.`notas_fiscais` (`id_nota_fiscal`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_itens_nota_fiscal_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`auditorias` (
  `id_auditoria` INT NOT NULL AUTO_INCREMENT,
  `id_usuario` INT NOT NULL,
  `data_auditoria` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `acao` VARCHAR(255) NOT NULL,
  `tabela_afetada` VARCHAR(255) NULL,
  `id_registro_afetado` INT NULL,
  `detalhes_antigos` JSON NULL,
  `detalhes_novos` JSON NULL,
  PRIMARY KEY (`id_auditoria`),
  INDEX `fk_auditorias_usuarios1_idx` (`id_usuario` ASC) VISIBLE,
  CONSTRAINT `fk_auditorias_usuarios1`
    FOREIGN KEY (`id_usuario`)
    REFERENCES `patrimonio_ideau`.`usuarios` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`garantias` (
  `id_garantia` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_inicio` DATE NOT NULL,
  `data_fim` DATE NULL,
  `termos` TEXT NULL,
  `documento_garantia` VARCHAR(255) NULL,
  PRIMARY KEY (`id_garantia`),
  INDEX `fk_garantias_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_garantias_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`baixas` (
  `id_baixa` INT NOT NULL AUTO_INCREMENT,
  `id_patrimonio` INT NOT NULL,
  `data_baixa` DATE NOT NULL,
  `motivo` VARCHAR(255) NOT NULL,
  `valor_residual` DECIMAL(10,2) NULL,
  `documento_baixa` VARCHAR(255) NULL,
  PRIMARY KEY (`id_baixa`),
  INDEX `fk_baixas_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_baixas_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`centro_custo` (
  `id_centro_custo` INT NOT NULL AUTO_INCREMENT,
  `nome_centro` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  PRIMARY KEY (`id_centro_custo`),
  UNIQUE INDEX `nome_centro_UNIQUE` (`nome_centro` ASC) VISIBLE)
ENGINE = InnoDB;


CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`patrimonios_centro_custo` (
  `id_patrimonio` INT NOT NULL,
  `id_centro_custo` INT NOT NULL,
  `data_associacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_patrimonio`, `id_centro_custo`),
  INDEX `fk_patrimonios_has_centro_custo_centro_custo1_idx` (`id_centro_custo` ASC) VISIBLE,
  INDEX `fk_patrimonios_has_centro_custo_patrimonios1_idx` (`id_patrimonio` ASC) VISIBLE,
  CONSTRAINT `fk_patrimonios_has_centro_custo_patrimonios1`
    FOREIGN KEY (`id_patrimonio`)
    REFERENCES `patrimonio_ideau`.`patrimonios` (`id_patrimonio`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_has_centro_custo_centro_custo1`
    FOREIGN KEY (`id_centro_custo`)
    REFERENCES `patrimonio_ideau`.`centro_custo` (`id_centro_custo`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`patrimonios` (
  `id_patrimonio` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `descricao` TEXT NULL,
  `numero_serie` VARCHAR(255) NULL,
  `valor_compra` DECIMAL(10,2) NOT NULL,
  `quantidade` INT NOT NULL DEFAULT 1,
  `numero_nota` VARCHAR(50) NULL,
  `valor_atual` DECIMAL(10,2) NOT NULL, -- NOVO: Valor atual após depreciação
  `data_aquisicao` DATE NOT NULL, -- Data de compra
  `estado_conservacao` ENUM('novo', 'bom', 'regular', 'ruim') NULL,
  `id_categoria` INT NOT NULL,
  `id_fornecedor` INT NULL,
  `id_setor_local` INT NOT NULL,
  `status` ENUM('ativo', 'baixado', 'em_manutencao','desaparecido') NOT NULL DEFAULT 'ativo',
  `data_baixa` DATE NULL, -- NOVO: Data da baixa
  `data_cadastro` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_patrimonio`),
  UNIQUE INDEX `numero_serie_UNIQUE` (`numero_serie` ASC) VISIBLE,
  INDEX `fk_patrimonios_categorias_idx` (`id_categoria` ASC) VISIBLE,
  INDEX `fk_patrimonios_fornecedores1_idx` (`id_fornecedor` ASC) VISIBLE,
  INDEX `fk_patrimonios_setores_locais1_idx` (`id_setor_local` ASC) VISIBLE,
  CONSTRAINT `fk_patrimonios_categorias`
    FOREIGN KEY (`id_categoria`)
    REFERENCES `patrimonio_ideau`.`categorias` (`id_categoria`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_fornecedores1`
    FOREIGN KEY (`id_fornecedor`)
    REFERENCES `patrimonio_ideau`.`fornecedores` (`id_fornecedor`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_patrimonios_setores_locais1`
    FOREIGN KEY (`id_setor_local`)
    REFERENCES `patrimonio_ideau`.`setores_locais` (`id_setor_local`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;

CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`patrimonios` (
  `id_patrimonio` INT NOT NULL AUTO_INCREMENT,
  `valor_compra` DECIMAL(10,2) NOT NULL,
  `quantidade` INT NOT NULL DEFAULT 1,
  `numero_nota` VARCHAR(50) NULL,
  `valor_atual` DECIMAL(10,2) NOT NULL, -- NOVO: Valor atual após depreciação
  `data_aquisicao` DATE NOT NULL, -- Data de compra
  `status` ENUM('ativo', 'baixado', 'em_manutencao','desaparecido') NOT NULL DEFAULT 'ativo',
  `data_baixa` DATE NULL, -- NOVO: Data da baixa
);

INSERT INTO `patrimonio_ideau`.`categorias` (`nome_categoria`, `descricao`) VALUES
('Eletronico', 'Categoria fixa Eletronico.'),
('Imobilizado', 'Categoria fixa Imobilizado.'),
('Movel', 'Categoria fixa Movel.'),
('Utilitarios', 'Categoria fixa Utilitarios.');
