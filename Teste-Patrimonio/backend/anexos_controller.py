from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from database_manager import DatabaseManager


class AnexosController:
    """Controlador da tela de anexos."""

    TABLE_HEADERS: List[str] = [
        "Entidade",
        "ID",
        "Nome",
        "Caminho",
        "Tamanho",
        "MIME",
        "Criado em",
    ]

    def __init__(self, widget: QWidget, db_manager: DatabaseManager) -> None:
        self.widget = widget
        self.db_manager = db_manager

        self.cb_entidade: Optional[QComboBox] = self.widget.findChild(QComboBox, "cb_entidade")
        self.sb_entidade_id: Optional[QSpinBox] = self.widget.findChild(QSpinBox, "sb_entidade_id")
        self.le_arquivo: Optional[QLineEdit] = self.widget.findChild(QLineEdit, "le_arquivo")
        self.table: Optional[QTableWidget] = self.widget.findChild(QTableWidget, "tbl_anexos")

        self.btn_add: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_add")
        self.btn_remover: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_remover")
        self.btn_atualizar: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_atualizar")

        self._setup_table()
        self._connect_signals()
        self.refresh()

    # ------------------------------------------------------------------ #
    def _setup_table(self) -> None:
        if not self.table:
            return
        self.table.setColumnCount(len(self.TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        header = self.table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
        vheader = self.table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def _connect_signals(self) -> None:
        if self.btn_add:
            self.btn_add.clicked.connect(self._adicionar_anexo)
        if self.btn_remover:
            self.btn_remover.clicked.connect(self._remover_anexo)
        if self.btn_atualizar:
            self.btn_atualizar.clicked.connect(self.refresh)
        if self.sb_entidade_id:
            self.sb_entidade_id.valueChanged.connect(self.refresh)

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        entidade = self.cb_entidade.currentText() if self.cb_entidade else "patrimonio"
        if entidade != "patrimonio":
            QMessageBox.information(
                self.widget,
                "Anexos",
                "No momento apenas anexos de patrimônio são suportados.",
            )
            if self.cb_entidade:
                index = self.cb_entidade.findText("patrimonio", Qt.MatchFlag.MatchFixedString)
                if index >= 0:
                    self.cb_entidade.setCurrentIndex(index)
        self._carregar_anexos()

    def _carregar_anexos(self) -> None:
        if not self.table:
            return
        patrimonio_id = self.sb_entidade_id.value() if self.sb_entidade_id else 0
        rows = []
        mensagem: Optional[str] = None
        if patrimonio_id > 0:
            try:
                rows = self.db_manager.list_anexos(patrimonio_id)
            except Exception as exc:  # pragma: no cover - interação com DB
                QMessageBox.critical(
                    self.widget,
                    "Anexos",
                    f"Não foi possível carregar os anexos.\n{exc}",
                )
                mensagem = "Não foi possível carregar os anexos."
            if not rows and mensagem is None:
                mensagem = "Nenhum anexo encontrado para o patrimônio informado."
        else:
            mensagem = "Informe o ID do patrimônio para visualizar os anexos."

        self._preencher_tabela(rows, mensagem)

    def _preencher_tabela(
        self, rows: List[dict], mensagem: Optional[str] = None
    ) -> None:
        if not self.table:
            return
        self.table.setRowCount(0)
        if not rows:
            self.table.setRowCount(1)
            texto = mensagem or "Nenhum anexo encontrado."
            self._set_item(0, 0, texto)
            for column in range(1, len(self.TABLE_HEADERS)):
                self._set_item(0, column, "")
            self.table.resizeColumnsToContents()
            return

        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            entidade = "patrimonio"
            entidade_id = row.get("id_patrimonio")
            nome = row.get("nome_arquivo")
            caminho = row.get("caminho_arquivo")
            tamanho = row.get("tamanho_arquivo") or row.get("tamanho")
            mime = row.get("tipo_arquivo")
            criado = row.get("data_upload")

            self._set_item(row_index, 0, entidade, id_anexo=row.get("id_anexo"))
            self._set_item(row_index, 1, str(entidade_id or "-"))
            self._set_item(row_index, 2, str(nome or "-"))
            self._set_item(row_index, 3, str(caminho or "-"))
            self._set_item(row_index, 4, self._formatar_tamanho(tamanho))
            self._set_item(row_index, 5, str(mime or "-"))
            self._set_item(row_index, 6, str(criado or "-"))
        self.table.resizeColumnsToContents()

    def _set_item(self, row: int, column: int, text: str, id_anexo: Optional[int] = None) -> None:
        if not self.table:
            return
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if id_anexo is not None:
            item.setData(Qt.ItemDataRole.UserRole, int(id_anexo))
        self.table.setItem(row, column, item)

    # ------------------------------------------------------------------ #
    def _adicionar_anexo(self) -> None:
        if not self.cb_entidade or self.cb_entidade.currentText() != "patrimonio":
            QMessageBox.warning(
                self.widget,
                "Anexos",
                "Somente anexos de patrimônio podem ser cadastrados.",
            )
            return
        if not self.sb_entidade_id:
            return
        patrimonio_id = self.sb_entidade_id.value()
        if patrimonio_id <= 0:
            QMessageBox.warning(self.widget, "Anexos", "Informe o ID do patrimônio.")
            return
        arquivo_path = self.le_arquivo.text().strip() if self.le_arquivo else ""
        if not arquivo_path:
            arquivo_path, _ = QFileDialog.getOpenFileName(
                self.widget,
                "Selecionar arquivo",
                str(Path.home()),
            )
            if not arquivo_path:
                return
            if self.le_arquivo:
                self.le_arquivo.setText(arquivo_path)
        path = Path(arquivo_path)
        if not path.exists() or not path.is_file():
            QMessageBox.warning(
                self.widget,
                "Anexos",
                "Arquivo inválido selecionado.",
            )
            return
        tamanho = path.stat().st_size
        mime, _ = mimetypes.guess_type(str(path))

        dados = {
            "id_patrimonio": patrimonio_id,
            "nome_arquivo": path.name,
            "caminho_arquivo": str(path),
            "tipo_arquivo": mime or "application/octet-stream",
            "tamanho_arquivo": tamanho,
        }
        try:
            self.db_manager.create_anexo(dados)
        except Exception as exc:  # pragma: no cover - interação com DB
            QMessageBox.critical(self.widget, "Anexos", f"Não foi possível salvar o anexo.\n{exc}")
            return
        QMessageBox.information(self.widget, "Anexos", "Anexo salvo com sucesso.")
        self.refresh()

    def _remover_anexo(self) -> None:
        if not self.table:
            return
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self.widget, "Anexos", "Selecione um anexo para remover.")
            return
        item = selected[0]
        anexo_id = item.data(Qt.ItemDataRole.UserRole)
        if not anexo_id:
            QMessageBox.warning(self.widget, "Anexos", "Não foi possível identificar o anexo.")
            return
        resposta = QMessageBox.question(
            self.widget,
            "Anexos",
            "Deseja realmente remover o anexo selecionado?",
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db_manager.delete_anexo(int(anexo_id))
        except Exception as exc:  # pragma: no cover - interação com DB
            QMessageBox.critical(self.widget, "Anexos", f"Não foi possível remover o anexo.\n{exc}")
            return
        self.refresh()

    # ------------------------------------------------------------------ #
    @staticmethod
    def _formatar_tamanho(tamanho: Optional[object]) -> str:
        try:
            valor = float(tamanho)
        except (TypeError, ValueError):
            return "-"
        unidades = ["B", "KB", "MB", "GB"]
        indice = 0
        while valor >= 1024 and indice < len(unidades) - 1:
            valor /= 1024
            indice += 1
        return f"{valor:.2f} {unidades[indice]}"
