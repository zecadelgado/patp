from __future__ import annotations

import json
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMessageBox,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from database_manager import DatabaseManager


class AuditoriaController:
    """Sincroniza a UI de auditoria com o banco de dados."""

    TABLE_HEADERS: List[str] = ["Data", "Tabela", "Registro", "Ação", "Usuário"]

    def __init__(self, widget: QWidget, db_manager: DatabaseManager) -> None:
        self.widget = widget
        self.db_manager = db_manager

        self.table: Optional[QTableWidget] = self.widget.findChild(QTableWidget, "tbl_auditoria")
        self.pte_antes: Optional[QPlainTextEdit] = self.widget.findChild(QPlainTextEdit, "pte_antes")
        self.pte_depois: Optional[QPlainTextEdit] = self.widget.findChild(QPlainTextEdit, "pte_depois")

        self._auditorias: List[Dict[str, object]] = []

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
        if self.table:
            self.table.itemSelectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        self._carregar_auditorias()

    def _carregar_auditorias(self) -> None:
        try:
            rows = self.db_manager.list_auditorias()
        except Exception as exc:  # pragma: no cover - interação com DB
            QMessageBox.critical(
                self.widget,
                "Auditoria",
                f"Não foi possível carregar os registros de auditoria.\n{exc}",
            )
            rows = []
        self._auditorias = rows
        self._popular_tabela()

    def _popular_tabela(self) -> None:
        if not self.table:
            return
        self.table.setRowCount(len(self._auditorias))
        for index, row in enumerate(self._auditorias):
            data = row.get("data_auditoria")
            data_str = str(data)
            self._set_item(index, 0, data_str)
            self._set_item(index, 1, str(row.get("tabela_afetada") or "-"))
            self._set_item(index, 2, str(row.get("id_registro_afetado") or "-"))
            self._set_item(index, 3, str(row.get("acao") or "-"))
            self._set_item(index, 4, str(row.get("nome_usuario") or "-"))
        self.table.resizeColumnsToContents()
        if self.table.rowCount():
            self.table.selectRow(0)

    def _set_item(self, row: int, column: int, text: str) -> None:
        if not self.table:
            return
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, column, item)

    # ------------------------------------------------------------------ #
    def _on_selection_changed(self) -> None:
        if not self.table:
            return
        selected = self.table.selectedItems()
        if not selected:
            return
        row_index = selected[0].row()
        if not (0 <= row_index < len(self._auditorias)):
            return
        registro = self._auditorias[row_index]
        self._mostrar_detalhes(registro)

    def _mostrar_detalhes(self, registro: Dict[str, object]) -> None:
        antes = self._formatar_json(registro.get("detalhes_antigos"))
        depois = self._formatar_json(registro.get("detalhes_novos"))
        if self.pte_antes:
            self.pte_antes.setPlainText(antes)
        if self.pte_depois:
            self.pte_depois.setPlainText(depois)

    @staticmethod
    def _formatar_json(valor: object) -> str:
        if valor is None:
            return ""
        if isinstance(valor, (dict, list)):
            return json.dumps(valor, ensure_ascii=False, indent=2)
        if isinstance(valor, str):
            valor = valor.strip()
            if not valor:
                return ""
            try:
                parsed = json.loads(valor)
            except json.JSONDecodeError:
                return valor
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        return str(valor)
