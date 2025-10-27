from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from database_manager import DatabaseManager


class RelatoriosController:
    """Popular os relatórios agregados do sistema."""

    def __init__(self, widget: QWidget, db_manager: DatabaseManager) -> None:
        self.widget = widget
        self.db_manager = db_manager

        self.tbl_por_setor: Optional[QTableWidget] = self.widget.findChild(QTableWidget, "tbl_por_setor")
        self.tbl_por_categoria: Optional[QTableWidget] = self.widget.findChild(QTableWidget, "tbl_por_categoria")
        self.tbl_manutencoes: Optional[QTableWidget] = self.widget.findChild(QTableWidget, "tbl_manutencoes")

        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        self._carregar_por_setor()
        self._carregar_por_categoria()
        self._carregar_manutencoes()

    # ------------------------------------------------------------------ #
    def _carregar_por_setor(self) -> None:
        try:
            rows = self.db_manager.relatorio_por_setor()
        except Exception as exc:  # pragma: no cover - interação com DB
            print(f"[Relatórios] Falha ao carregar relatório por setor: {exc}")
            rows = []
        linhas = [
            [
                row.get("setor") or "-",
                row.get("localizacao") or "-",
                str(row.get("quantidade") or 0),
                self._format_currency(row.get("valor_total")),
            ]
            for row in rows
        ]
        self._popular_tabela(self.tbl_por_setor, linhas)

    def _carregar_por_categoria(self) -> None:
        try:
            rows = self.db_manager.relatorio_por_categoria()
        except Exception as exc:  # pragma: no cover - interação com DB
            print(f"[Relatórios] Falha ao carregar relatório por categoria: {exc}")
            rows = []
        linhas = [
            [
                row.get("categoria") or "-",
                str(row.get("quantidade") or 0),
                self._format_currency(row.get("depreciacao_acumulada")),
            ]
            for row in rows
        ]
        self._popular_tabela(self.tbl_por_categoria, linhas)

    def _carregar_manutencoes(self) -> None:
        try:
            rows = self.db_manager.relatorio_manutencoes()
        except Exception as exc:  # pragma: no cover - interação com DB
            print(f"[Relatórios] Falha ao carregar relatório de manutenções: {exc}")
            rows = []
        linhas = [
            [
                self._format_date(row.get("data_inicio")),
                row.get("nome_patrimonio") or "-",
                row.get("tipo") or "-",
                row.get("responsavel") or "-",
                self._format_currency(row.get("custo")),
            ]
            for row in rows
        ]
        self._popular_tabela(self.tbl_manutencoes, linhas)

    # ------------------------------------------------------------------ #
    def _popular_tabela(self, tabela: Optional[QTableWidget], linhas: List[List[str]]) -> None:
        if not tabela:
            return
        tabela.setRowCount(len(linhas))
        for row_index, linha in enumerate(linhas):
            for col_index, valor in enumerate(linha):
                item = QTableWidgetItem(valor)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if valor.startswith("R$"):
                    item.setTextAlignment(int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                tabela.setItem(row_index, col_index, item)
        tabela.resizeColumnsToContents()

    @staticmethod
    def _format_currency(value: Optional[object]) -> str:
        try:
            return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return "R$ 0,00"

    @staticmethod
    def _format_date(value: Optional[object]) -> str:
        if hasattr(value, "strftime"):
            return value.strftime("%d/%m/%Y")
        return str(value or "-")
