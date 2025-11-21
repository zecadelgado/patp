CREATE TABLE IF NOT EXISTS itens_nota (
  id_item INT AUTO_INCREMENT PRIMARY KEY,
  id_nota_fiscal INT NOT NULL,
  descricao VARCHAR(255) NOT NULL,
  quantidade INT NOT NULL,
  valor DECIMAL(10,2) NOT NULL,
  ncm VARCHAR(20) NULL,
  cfop VARCHAR(20) NULL,
  CONSTRAINT fk_itens_nota_nota
    FOREIGN KEY (id_nota_fiscal)
    REFERENCES notas_fiscais (id_nota_fiscal)
    ON DELETE CASCADE
);