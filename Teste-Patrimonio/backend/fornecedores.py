from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import mysql.connector
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableView,
    QTextEdit,
    QWidget,
)


@dataclass
class _ColumnConfig:
    name: str
    header: str
    visible: bool = True


class FornecedoresController:
    def __init__(self, widget: QWidget, db_manager):
        self.widget = widget
        self.db_manager = db_manager
        self.current_id: Optional[int] = None
        self._table_rows: List[Dict] = []
        self._table_headers: List[_ColumnConfig] = []
        self._table_model: Optional[QStandardItemModel] = None
        self._ready = False

        self.btn_novo: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_novo")
        self.btn_salvar: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_salvar")
        self.btn_excluir: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_excluir")
        self.btn_buscar: Optional[QPushButton] = self.widget.findChild(QPushButton, "btn_buscar")
        self.txt_buscar: Optional[QLineEdit] = self.widget.findChild(QLineEdit, "txt_buscar")

        self.tab_widget: Optional[QTabWidget] = self.widget.findChild(QTabWidget, "tab_widget")
        self.tab_form: Optional[QWidget] = self.widget.findChild(QWidget, "tab_dados")

        self._fields_line_edit: Dict[str, Optional[QLineEdit]] = {
            "nome": self.widget.findChild(QLineEdit, "txt_razao_social"),
            "cnpj": self.widget.findChild(QLineEdit, "txt_cnpj"),
            "inscricao_estadual": self.widget.findChild(QLineEdit, "txt_inscricao_estadual"),
            "contato": self.widget.findChild(QLineEdit, "txt_contato"),
            "telefone": self.widget.findChild(QLineEdit, "txt_telefone"),
            "email": self.widget.findChild(QLineEdit, "txt_email"),
        }
        self._field_observacoes: Optional[QTextEdit] = self.widget.findChild(QTextEdit, "txt_observacoes")
        self._table_view: Optional[QTableView] = self.widget.findChild(QTableView, "tbl_fornecedores")

        self._columns: Dict[str, Optional[str]] = {}
        self._discover_columns()
        self._setup_table_model()
        self._connect_signals()
        self._set_buttons_state()

        if self._ready:
            self.refresh()

    # ------------------------------------------------------------------ #
    # Setup helpers
    def _discover_columns(self):
        self._ready = False
        available: List[str] = []
        cursor = None

        try:
            conn = self._ensure_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM fornecedores")
            available = [row[0] for row in cursor.fetchall()]
        except mysql.connector.Error as err:
            QMessageBox.critical(self.widget, "Fornecedores", f"Não foi possível ler as colunas de fornecedores.\n{err}")
            return
        finally:
            if cursor:
                cursor.close()

        def pick(*candidates, default=None):
            for candidate in candidates:
                if candidate in available:
                    return candidate
            return default

        self._columns = {
            "id": pick("id_fornecedor", "id", default=None),
            "nome": pick("nome_fornecedor", "razao_social", "nome", default=None),
            "cnpj": pick("cnpj", "cpf_cnpj", default=None),
            "inscricao_estadual": pick("inscricao_estadual", "inscricao_est", "ie", default=None),
            "contato": pick("contato", "responsavel", default=None),
            "telefone": pick("telefone", "fone", "celular", default=None),
            "email": pick("email", "mail", default=None),
            "observacoes": pick("observacoes", "observacao", "obs", "descricao", default=None),
        }

        if not self._columns["id"] or not self._columns["nome"]:
            QMessageBox.critical(
                self.widget,
                "Fornecedores",
                "Estrutura da tabela 'fornecedores' não possui colunas obrigatórias (id/nome).",
            )
            return

        self._table_headers = [
            _ColumnConfig(self._columns["id"], "ID", visible=False),
            _ColumnConfig(self._columns["nome"], "Fornecedor"),
        ]
        for key, header in [
            ("cnpj", "CNPJ"),
            ("contato", "Contato"),
            ("telefone", "Telefone"),
            ("email", "E-mail"),
        ]:
            column_name = self._columns.get(key)
            if column_name:
                self._table_headers.append(_ColumnConfig(column_name, header))

        self._ready = True

    def _setup_table_model(self):
        if not self._table_view:
            return
        self._table_model = QStandardItemModel(self._table_view)
        headers = [config.header for config in self._table_headers]
        self._table_model.setHorizontalHeaderLabels(headers)
        self._table_view.setModel(self._table_model)
        for index, config in enumerate(self._table_headers):
            self._table_view.setColumnHidden(index, not config.visible)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

    def _connect_signals(self):
        if self.btn_novo:
            self.btn_novo.clicked.connect(self._handle_novo)
        if self.btn_salvar:
            self.btn_salvar.clicked.connect(self._handle_salvar)
        if self.btn_excluir:
            self.btn_excluir.clicked.connect(self._handle_excluir)
        if self.btn_buscar:
            self.btn_buscar.clicked.connect(self._handle_buscar)
        if self.txt_buscar:
            self.txt_buscar.returnPressed.connect(self._handle_buscar)
        if self._table_view:
            self._table_view.clicked.connect(self._on_table_clicked)
            self._table_view.doubleClicked.connect(self._on_table_double_clicked)

    # ------------------------------------------------------------------ #
    # Event handlers
    def _handle_novo(self):
        if not self._ready:
            return
        self.current_id = None
        self._clear_form()
        if self._table_view:
            self._table_view.clearSelection()
        if self._fields_line_edit["nome"]:
            self._fields_line_edit["nome"].setFocus()
        self._switch_to_form()
        self._set_buttons_state()

    def _handle_salvar(self):
        if not self._ready:
            return
        data, error = self._collect_form_data()
        if error:
            QMessageBox.warning(self.widget, "Fornecedores", error)
            return
        if not data:
            return

        cursor = None
        conn = None
        try:
            conn = self._ensure_connection()
            cursor = conn.cursor()
            if self.current_id is None:
                columns_fragment = ", ".join(f"`{col}`" for col in data.keys())
                values_fragment = ", ".join(["%s"] * len(data))
                sql = f"INSERT INTO fornecedores ({columns_fragment}) VALUES ({values_fragment})"
                cursor.execute(sql, tuple(data.values()))
                conn.commit()
                self.current_id = cursor.lastrowid
                QMessageBox.information(self.widget, "Fornecedores", "Fornecedor cadastrado com sucesso.")
            else:
                set_fragment = ", ".join(f"`{col}` = %s" for col in data.keys())
                sql = f"UPDATE fornecedores SET {set_fragment} WHERE `{self._columns['id']}` = %s"
                params = list(data.values())
                params.append(self.current_id)
                cursor.execute(sql, tuple(params))
                conn.commit()
                QMessageBox.information(self.widget, "Fornecedores", "Fornecedor atualizado com sucesso.")
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            QMessageBox.critical(self.widget, "Fornecedores", f"Erro ao salvar fornecedor.\n{err}")
            return
        finally:
            if cursor:
                cursor.close()

        self.refresh()
        self._switch_to_form()
        self._set_buttons_state()

    def _handle_excluir(self):
        if not self._ready or not self.current_id:
            QMessageBox.warning(self.widget, "Fornecedores", "Selecione um fornecedor para excluir.")
            return

        resposta = QMessageBox.question(
            self.widget,
            "Excluir fornecedor",
            "Deseja realmente excluir o fornecedor selecionado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resposta != QMessageBox.Yes:
            return

        cursor = None
        conn = None
        try:
            conn = self._ensure_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM fornecedores WHERE `{self._columns['id']}` = %s",
                (self.current_id,),
            )
            conn.commit()
            QMessageBox.information(self.widget, "Fornecedores", "Fornecedor excluído com sucesso.")
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            QMessageBox.critical(self.widget, "Fornecedores", f"Erro ao excluir fornecedor.\n{err}")
            return
        finally:
            if cursor:
                cursor.close()

        self.current_id = None
        self._clear_form()
        self.refresh()
        self._set_buttons_state()

    def _handle_buscar(self):
        if not self._ready:
            return
        termo = self.txt_buscar.text().strip() if self.txt_buscar else ""
        self.refresh(termo)

    def _on_table_clicked(self, index):
        if not self._ready:
            return
        self._load_row(index.row(), focus_form=False)

    def _on_table_double_clicked(self, index):
        if not self._ready:
            return
        self._load_row(index.row(), focus_form=True)

    # ------------------------------------------------------------------ #
    # Core operations
    def refresh(self, search_term: Optional[str] = None):
        if not self._ready:
            return

        if search_term is None and self.txt_buscar:
            search_term = self.txt_buscar.text().strip()

        rows = self._fetch_rows(search_term)
        self._table_rows = rows
        if not self._table_model:
            return

        self._table_model.setRowCount(0)
        for row_data in rows:
            items: List[QStandardItem] = []
            for config in self._table_headers:
                value = row_data.get(config.name)
                text = "" if value is None else str(value)
                item = QStandardItem(text)
                if config.name == self._columns["id"]:
                    item.setData(row_data.get(config.name), Qt.UserRole)
                items.append(item)
            self._table_model.appendRow(items)

        if self._table_view:
            self._table_view.resizeColumnsToContents()

        self._restore_selection()
        self._set_buttons_state()

    def _fetch_rows(self, search_term: Optional[str]) -> List[Dict]:
        columns_fragment = ", ".join(f"`{config.name}`" for config in self._table_headers)
        sql = f"SELECT {columns_fragment} FROM fornecedores"
        params: List[str] = []
        if search_term:
            like = f"%{search_term}%"
            filters = [f"`{self._columns['nome']}` LIKE %s"]
            params.append(like)
            cnpj_column = self._columns.get("cnpj")
            if cnpj_column:
                filters.append(f"`{cnpj_column}` LIKE %s")
                params.append(like)
            sql += " WHERE " + " OR ".join(filters)
        sql += f" ORDER BY `{self._columns['nome']}`"
        return self.db_manager.fetch_all(sql, tuple(params) if params else None)

    def _load_row(self, row_index: int, focus_form: bool):
        if row_index < 0 or row_index >= len(self._table_rows):
            return

        record = self._table_rows[row_index]
        record_id = record.get(self._columns["id"])
        if record_id is None:
            return

        detalhes = self._fetch_fornecedor_by_id(record_id)
        if not detalhes:
            QMessageBox.warning(self.widget, "Fornecedores", "Não foi possível obter os dados do fornecedor selecionado.")
            return

        self.current_id = record_id
        self._populate_form(detalhes)
        self._set_buttons_state()
        if focus_form:
            self._switch_to_form()

    def _fetch_fornecedor_by_id(self, record_id: int) -> Optional[Dict]:
        conn = self._ensure_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                f"SELECT * FROM fornecedores WHERE `{self._columns['id']}` = %s",
                (record_id,),
            )
            return cursor.fetchone()
        except mysql.connector.Error as err:
            QMessageBox.critical(self.widget, "Fornecedores", f"Erro ao consultar fornecedor.\n{err}")
            return None
        finally:
            if cursor:
                cursor.close()

    # ------------------------------------------------------------------ #
    # Form helpers
    def _collect_form_data(self):
        data: Dict[str, Optional[str]] = {}

        nome_widget = self._fields_line_edit.get("nome")
        nome_valor = nome_widget.text().strip() if nome_widget else ""
        if not nome_valor:
            return None, "Informe o nome ou razão social do fornecedor."
        data[self._columns["nome"]] = nome_valor

        def set_line_value(field_key: str, transformer=None):
            column = self._columns.get(field_key)
            widget = self._fields_line_edit.get(field_key)
            if not column or widget is None:
                return
            valor = widget.text()
            if transformer:
                valor = transformer(valor)
            valor = valor.strip()
            data[column] = valor if valor else None

        set_line_value("cnpj", self._normalize_mask_text)
        set_line_value("inscricao_estadual", self._normalize_mask_text)
        set_line_value("contato")
        set_line_value("telefone", self._normalize_mask_text)
        set_line_value("email")

        observacoes_col = self._columns.get("observacoes")
        if observacoes_col and self._field_observacoes:
            texto = self._field_observacoes.toPlainText().strip()
            data[observacoes_col] = texto if texto else None

        return data, None

    def _populate_form(self, dados: Dict):
        for key, widget in self._fields_line_edit.items():
            if widget is None:
                continue
            column = self._columns.get(key)
            valor = dados.get(column) if column else ""
            widget.setText("" if valor is None else str(valor))
        if self._field_observacoes:
            coluna = self._columns.get("observacoes")
            valor_obs = dados.get(coluna) if coluna else ""
            self._field_observacoes.setPlainText("" if valor_obs is None else str(valor_obs))

    def _clear_form(self):
        for widget in self._fields_line_edit.values():
            if widget is not None:
                widget.clear()
        if self._field_observacoes:
            self._field_observacoes.clear()

    def _restore_selection(self):
        if not self._table_view or self.current_id is None:
            return
        for row_index, row_data in enumerate(self._table_rows):
            if str(row_data.get(self._columns["id"])) == str(self.current_id):
                self._table_view.selectRow(row_index)
                return

    def _switch_to_form(self):
        if self.tab_widget and self.tab_form:
            self.tab_widget.setCurrentWidget(self.tab_form)

    def _set_buttons_state(self):
        can_edit = self._ready
        has_selection = can_edit and self.current_id is not None

        if self.btn_novo:
            self.btn_novo.setEnabled(can_edit)
        if self.btn_salvar:
            self.btn_salvar.setEnabled(can_edit)
        if self.btn_excluir:
            self.btn_excluir.setEnabled(has_selection)

    # ------------------------------------------------------------------ #
    # Utility helpers
    def _ensure_connection(self):
        conn = self.db_manager.connection
        if not conn or not conn.is_connected():
            if not self.db_manager.connect():
                raise mysql.connector.Error(msg="Não foi possível estabelecer conexão com o banco de dados.")
            conn = self.db_manager.connection
        return conn

    @staticmethod
    def _normalize_mask_text(text: str) -> str:
        cleaned = text.replace("_", "").strip()
        if not cleaned:
            return ""
        alnum = "".join(ch for ch in cleaned if ch.isalnum())
        return cleaned if alnum else ""
