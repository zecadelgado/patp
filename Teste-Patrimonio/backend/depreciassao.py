from __future__ import annotations

import datetime

from collections import defaultdict
from typing import Dict, List, Optional

import mysql.connector
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from database_manager import DatabaseManager


class DepreciacaoController:
    """Controller responsável por orquestrar a tela de depreciação."""

    VIDA_UTIL_ANOS = 5

    def __init__(self, widget: QWidget, db_manager: DatabaseManager) -> None:
        self.widget = widget
        self.db_manager = db_manager

        self._input_patrimonio: Optional[QLineEdit] = self.widget.findChild(QLineEdit, "le_patrimonio")
        self._combo_categoria: Optional[QComboBox] = self.widget.findChild(QComboBox, "cb_categoria")
        self._btn_filtrar: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_filtrar")
        self._btn_limpar: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_limpar")
        self._table: Optional[QTableWidget] = self.widget.findChild(QTableWidget, "tbl_dep")

        self._setup_table()
        self._connect_signals()
        self.refresh()

    # ------------------------------------------------------------------ #
    # Setup helpers
    # ------------------------------------------------------------------ #
    def _setup_table(self) -> None:
        if not self._table:
            return
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Patrimônio", "Competência", "Valor", "Acumulado"]
        )
        header = self._table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
        v_header = self._table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def _connect_signals(self) -> None:
        if self._btn_filtrar:
            self._btn_filtrar.clicked.connect(self._apply_filters)
        if self._btn_limpar:
            self._btn_limpar.clicked.connect(self._clear_filters)
        if self._input_patrimonio:
            self._input_patrimonio.returnPressed.connect(self._apply_filters)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        self._load_categorias()
        self._populate_table()

    # ------------------------------------------------------------------ #
    # Loading helpers
    # ------------------------------------------------------------------ #
    def _load_categorias(self) -> None:
        if not self._combo_categoria:
            return
        current_value = self._combo_categoria.currentData() if self._combo_categoria.count() else None
        self._combo_categoria.clear()
        self._combo_categoria.addItem("Todas as categorias", None)
        try:
            rows = self.db_manager.fetch_all(
                "SELECT id_categoria, nome_categoria FROM categorias ORDER BY nome_categoria"
            )
        except mysql.connector.Error as err:
            QMessageBox.warning(
                self.widget,
                "Categorias",
                f"Não foi possível carregar as categorias.\n{err}",
            )
            self._combo_categoria.setEnabled(False)
            return
        else:
            self._combo_categoria.setEnabled(True)

        for row in rows:
            categoria_id = row.get("id_categoria")
            nome = row.get("nome_categoria")
            if categoria_id is None or not nome:
                continue
            self._combo_categoria.addItem(str(nome), categoria_id)

        if current_value is not None:
            index = self._combo_categoria.findData(current_value)
            if index >= 0:
                self._combo_categoria.setCurrentIndex(index)

    def _populate_table(self) -> None:
        if not self._table:
            return

        dados = self._buscar_depreciacoes()
        self._table.setRowCount(0)
        self._table.setRowCount(len(dados))

        for row_index, item in enumerate(dados):
            patrimonio = item.get("patrimonio") or "-"
            categoria = item.get("categoria")
            competencia = item.get("competencia")
            valor = item.get("valor")
            acumulado = item.get("acumulado")

            patrimonio_text = patrimonio
            if categoria:
                patrimonio_text = f"{patrimonio} ({categoria})"

            competencia_text = self._format_competencia(competencia)
            valor_text = self._format_currency(valor)
            acumulado_text = self._format_currency(acumulado)

            self._set_table_item(row_index, 0, patrimonio_text)
            self._set_table_item(row_index, 1, competencia_text)
            self._set_table_item(row_index, 2, valor_text, align_right=True)
            self._set_table_item(row_index, 3, acumulado_text, align_right=True)

        self._table.resizeColumnsToContents()

    def _buscar_depreciacoes(self) -> List[Dict[str, object]]:
        filtros = []
        parametros: List[object] = []

        texto_busca = self._input_patrimonio.text().strip() if self._input_patrimonio else ""
        if texto_busca:
            filtros.append("p.nome LIKE %s")
            parametros.append(f"%{texto_busca}%")

        categoria_id = None
        if self._combo_categoria and self._combo_categoria.currentIndex() > 0:
            categoria_id = self._combo_categoria.currentData()
            if categoria_id:
                filtros.append("p.id_categoria = %s")
                parametros.append(categoria_id)

        where_clause = ""
        if filtros:
            where_clause = " WHERE " + " AND ".join(filtros)

        query = f"""
            SELECT
                p.id_patrimonio,
                p.nome AS patrimonio_nome,
                c.nome_categoria,
                d.data_depreciacao,
                d.valor_depreciado,
                d.valor_atual
            FROM depreciacoes d
            INNER JOIN patrimonios p ON p.id_patrimonio = d.id_patrimonio
            LEFT JOIN categorias c ON c.id_categoria = p.id_categoria
            {where_clause}
            ORDER BY p.nome, d.data_depreciacao
        """

        try:
            rows = self.db_manager.fetch_all(query, tuple(parametros) if parametros else None)
        except mysql.connector.Error as err:
            QMessageBox.critical(
                self.widget,
                "Depreciação",
                f"Não foi possível carregar as depreciações.\n{err}",
            )
            rows = []

        if rows:
            dados = self._formatar_resultados_depreciacoes(rows)
            ids_existentes = set()
            for row in rows:
                raw_id = row.get("id_patrimonio")
                if raw_id is None:
                    continue
                try:
                    ids_existentes.add(int(raw_id))
                except (TypeError, ValueError):
                    continue
            adicionais = self._buscar_depreciacoes_virtual(where_clause, parametros, ids_existentes)
            return dados + adicionais

        return self._buscar_depreciacoes_virtual(where_clause, parametros)

    def _buscar_depreciacoes_virtual(
        self, where_clause: str, parametros: List[object], ignorar_ids: Optional[set[int]] = None
    ) -> List[Dict[str, object]]:
        query = f"""
            SELECT
                p.id_patrimonio,
                p.nome AS patrimonio_nome,
                p.valor_compra,
                p.data_aquisicao,
                c.nome_categoria
            FROM patrimonios p
            LEFT JOIN categorias c ON c.id_categoria = p.id_categoria
            {where_clause}
            ORDER BY p.nome
        """

        try:
            rows = self.db_manager.fetch_all(query, tuple(parametros) if parametros else None)
        except mysql.connector.Error as err:
            QMessageBox.critical(
                self.widget,
                "Depreciação",
                f"Não foi possível calcular a depreciação.\n{err}",
            )
            return []

        dados: List[Dict[str, object]] = []
        competencia = datetime.date.today().replace(day=1)
        for row in rows:
            nome = row.get("patrimonio_nome")
            categoria = row.get("nome_categoria")
            valor_compra = row.get("valor_compra")
            data_aquisicao = row.get("data_aquisicao")
            patrimonio_id = row.get("id_patrimonio")
            try:
                patrimonio_id_int = int(patrimonio_id) if patrimonio_id is not None else None
            except (TypeError, ValueError):
                patrimonio_id_int = None
            if ignorar_ids and patrimonio_id_int in ignorar_ids:
                continue
            if valor_compra is None:
                continue

            valor_atual = self._calcular_valor_atual(data_aquisicao, float(valor_compra))
            depreciado = max(0.0, float(valor_compra) - valor_atual)
            valor_mensal = float(valor_compra) / (self.VIDA_UTIL_ANOS * 12)

            dados.append(
                {
                    "patrimonio": nome,
                    "categoria": categoria,
                    "competencia": competencia,
                    "valor": valor_mensal,
                    "acumulado": depreciado,
                }
            )

        return dados

    # ------------------------------------------------------------------ #
    # Formatting helpers
    # ------------------------------------------------------------------ #
    def _formatar_resultados_depreciacoes(self, rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
        acumulado_por_patrimonio: Dict[int, float] = defaultdict(float)
        resultado: List[Dict[str, object]] = []

        for row in rows:
            patrimonio_id = row.get("id_patrimonio")
            valor_mensal = row.get("valor_depreciado")
            competencia = row.get("data_depreciacao")
            categoria = row.get("nome_categoria")
            nome = row.get("patrimonio_nome")

            if patrimonio_id is None:
                continue

            valor_float = float(valor_mensal or 0.0)
            acumulado_por_patrimonio[patrimonio_id] += valor_float

            resultado.append(
                {
                    "patrimonio": nome,
                    "categoria": categoria,
                    "competencia": competencia,
                    "valor": valor_float,
                    "acumulado": acumulado_por_patrimonio[patrimonio_id],
                }
            )

        return resultado

    @staticmethod
    def _format_currency(value: Optional[float]) -> str:
        try:
            return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return "R$ 0,00"

    @staticmethod
    def _format_competencia(value: object) -> str:
        if isinstance(value, datetime.datetime):
            value = value.date()
        if isinstance(value, datetime.date):
            return value.strftime("%m/%Y")
        if isinstance(value, str) and value:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
                try:
                    parsed = datetime.datetime.strptime(value, fmt)
                    return parsed.strftime("%m/%Y")
                except ValueError:
                    continue
        return "-"

    def _set_table_item(self, row: int, column: int, text: str, align_right: bool = False) -> None:
        if not self._table:
            return
        item = QTableWidgetItem(text)
        flags = item.flags() & ~Qt.ItemFlag.ItemIsEditable
        item.setFlags(flags)
        alignment = Qt.AlignmentFlag.AlignVCenter
        alignment |= Qt.AlignmentFlag.AlignRight if align_right else Qt.AlignmentFlag.AlignLeft
        item.setTextAlignment(int(alignment))
        self._table.setItem(row, column, item)

    def _calcular_valor_atual(self, data_aquisicao: object, valor_compra: float) -> float:
        if not valor_compra:
            return 0.0

        if isinstance(data_aquisicao, datetime.datetime):
            data_base = data_aquisicao.date()
        elif isinstance(data_aquisicao, datetime.date):
            data_base = data_aquisicao
        elif isinstance(data_aquisicao, str) and data_aquisicao:
            data_base = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    data_base = datetime.datetime.strptime(data_aquisicao, fmt).date()
                    break
                except ValueError:
                    continue
        else:
            data_base = None

        if not data_base:
            return float(valor_compra)

        hoje = datetime.date.today()
        dias_em_uso = (hoje - data_base).days
        if dias_em_uso <= 0:
            return float(valor_compra)

        taxa_anual = 1 / self.VIDA_UTIL_ANOS
        anos_passados = dias_em_uso / 365.25
        depreciacao_acumulada = float(valor_compra) * taxa_anual * anos_passados
        depreciacao_acumulada = min(depreciacao_acumulada, float(valor_compra))
        return max(0.0, float(valor_compra) - depreciacao_acumulada)

    # ------------------------------------------------------------------ #
    # UI events
    # ------------------------------------------------------------------ #
    def _apply_filters(self) -> None:
        self._populate_table()

    def _clear_filters(self) -> None:
        if self._input_patrimonio:
            self._input_patrimonio.clear()
        if self._combo_categoria:
            self._combo_categoria.setCurrentIndex(0)
        self._populate_table()


__all__ = ["DepreciacaoController"]
