# Métodos para adicionar ao PatrimonioController
# Copiar e colar no final da classe PatrimonioController

    def _abrir_cadastro_rapido_fornecedor(self, parent_dialog):
        """Abre diálogo de cadastro rápido de fornecedor"""
        dialog = QuickCreateFornecedorDialog(parent_dialog, self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fornecedor_id = dialog.get_fornecedor_id()
            if fornecedor_id:
                # Recarregar combo de fornecedores
                self._populate_fk_combo(
                    self.fornecedor_combo,
                    "Selecione um Fornecedor",
                    "SELECT id_fornecedor, nome_fornecedor FROM fornecedores ORDER BY nome_fornecedor",
                    "id_fornecedor",
                    "nome_fornecedor",
                )
                # Selecionar o fornecedor recém-criado
                for i in range(self.fornecedor_combo.count()):
                    if self.fornecedor_combo.itemData(i) == fornecedor_id:
                        self.fornecedor_combo.setCurrentIndex(i)
                        break
    
    def _abrir_cadastro_rapido_nota(self, parent_dialog):
        """Abre diálogo de cadastro rápido de nota fiscal"""
        dialog = QuickCreateNotaFiscalDialog(parent_dialog, self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            numero_nota = dialog.get_numero_nota()
            if numero_nota:
                # Atualizar campo de número de nota
                self.numero_nota_input.setText(numero_nota)
                QMessageBox.information(
                    parent_dialog,
                    "Nota Fiscal Criada",
                    f"Nota fiscal {numero_nota} criada com sucesso!\n\n"
                    "Os itens da nota poderão ser adicionados depois na tela de Notas Fiscais."
                )
