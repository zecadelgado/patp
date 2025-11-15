from __future__ import annotations

import json
import mimetypes
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import mysql.connector # ignore
from mysql.connector import errorcode

from config_db import get_connection


class DatabaseManager:
    """Encapsula as interações com o banco de dados."""

    _ANEXO_CONFIG: Dict[str, Dict[str, Any]] = {
        "patrimonio": {
            "table": "anexos",
            "pk": "id_anexo",
            "columns": {
                "entidade_id": "id_patrimonio",
                "nome_arquivo": "nome_arquivo",
                "caminho_arquivo": "caminho_arquivo",
                "tipo_arquivo": "tipo_arquivo",
                "tamanho_arquivo": "tamanho_arquivo",
                "data_upload": "data_upload",
            },
            "joins": [
                "INNER JOIN patrimonios p ON p.id_patrimonio = a.id_patrimonio",
            ],
            "extra_select": [
                "p.nome AS nome_entidade",
            ],
            "order_by": "a.data_upload DESC",
        },
        "manutencao": {
            "table": "anexos_manutencoes",
            "pk": "id_anexo",
            "columns": {
                "entidade_id": "id_manutencao",
                "nome_arquivo": "nome_arquivo",
                "caminho_arquivo": "caminho_arquivo",
                "tipo_arquivo": "tipo_arquivo",
                "tamanho_arquivo": "tamanho_arquivo",
                "data_upload": "data_upload",
            },
            "joins": [
                "INNER JOIN manutencoes m ON m.id_manutencao = a.id_manutencao",
            ],
            "extra_select": [
                "m.descricao AS nome_entidade",
            ],
            "order_by": "a.data_upload DESC",
        },
        "nota_fiscal": {
            "table": "anexos_notas_fiscais",
            "pk": "id_anexo",
            "columns": {
                "entidade_id": "id_nota_fiscal",
                "nome_arquivo": "nome_arquivo",
                "caminho_arquivo": "caminho_arquivo",
                "tipo_arquivo": "tipo_arquivo",
                "tamanho_arquivo": "tamanho_arquivo",
                "data_upload": "data_upload",
            },
            "joins": [
                "INNER JOIN notas_fiscais nf ON nf.id_nota_fiscal = a.id_nota_fiscal",
            ],
            "extra_select": [
                "nf.numero_nota AS nome_entidade",
            ],
            "order_by": "a.data_upload DESC",
        },
    }

    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = get_connection()
            print("Conexao com o banco de dados estabelecida com sucesso!")
            return True
        except mysql.connector.Error as err:
            print(f"Erro ao conectar ao banco de dados: {err}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexao com o banco de dados encerrada.")

    def _ensure_connection(self):
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                raise mysql.connector.Error(msg="Nao foi possivel conectar ao banco de dados.")

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = None
                return result
            else:
                self.connection.commit()
                return cursor.rowcount
        except mysql.connector.Error as err:
            print(f"Erro ao executar a query: {err}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def fetch_all(self, query, params=None) -> List[dict]:
        result = self.execute_query(query, params, fetch_all=True)
        return result if result is not None else []

    def fetch_one(self, query, params=None) -> Optional[dict]:
        return self.execute_query(query, params, fetch_one=True)

    def get_user_by_email(self, email):
        query = "SELECT * FROM usuarios WHERE email = %s"
        return self.execute_query(query, (email,), fetch_one=True)

    def verify_password(self, email, password):
        user = self.get_user_by_email(email)
        if user and user['senha'] == password:
            return user
        return None

    def get_table_columns(self, table: str) -> List[str]:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def create_user(self, nome, email, password, nivel_acesso: str = "user", ativo: Optional[bool] = None):
        if self.get_user_by_email(email):
            return None

        columns = ["nome", "email", "senha", "nivel_acesso"]
        values: List[Any] = [nome, email, password, nivel_acesso]

        try:
            available = set(self.get_table_columns("usuarios"))
        except mysql.connector.Error:
            available = {"nome", "email", "senha", "nivel_acesso"}

        if "ativo" in available and ativo is not None:
            columns.append("ativo")
            values.append(1 if ativo else 0)

        insert_sql = f"INSERT INTO usuarios ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
        rows = self.execute_query(insert_sql, tuple(values))
        if not rows:
            return None
        return self.get_user_by_email(email)

    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        if not data:
            return False

        allowed: Sequence[str]
        try:
            allowed = self.get_table_columns("usuarios")
        except mysql.connector.Error:
            allowed = ("nome", "email", "senha", "nivel_acesso", "ativo")

        updates: List[str] = []
        params: List[Any] = []
        for key, value in data.items():
            if key not in allowed or key == "id_usuario":
                continue
            updates.append(f"`{key}` = %s")
            params.append(value)

        if not updates:
            return False

        params.append(user_id)
        sql = f"UPDATE usuarios SET {', '.join(updates)} WHERE id_usuario = %s"
        rows = self.execute_query(sql, tuple(params))
        return bool(rows)

    def delete_user(self, user_id: int) -> bool:
        sql = "DELETE FROM usuarios WHERE id_usuario = %s"
        rows = self.execute_query(sql, (user_id,))
        return bool(rows)

    def set_user_active(self, user_id: int, active: bool) -> bool:
        try:
            columns = self.get_table_columns("usuarios")
        except mysql.connector.Error:
            columns = []
        if "ativo" not in columns:
            return False
        sql = "UPDATE usuarios SET ativo = %s WHERE id_usuario = %s"
        rows = self.execute_query(sql, (1 if active else 0, user_id))
        return bool(rows)

    def ensure_patrimonio_optional_columns(self) -> None:
        try:
            columns = set(self.get_table_columns("patrimonios"))
        except mysql.connector.Error as exc:
            print(f"[DatabaseManager] Nao foi possivel inspecionar a tabela patrimonios: {exc}")
            return

        alter_statements: List[str] = []
        if "numero_patrimonio" not in columns:
            alter_statements.append(
                "ADD COLUMN numero_patrimonio BIGINT UNSIGNED NULL UNIQUE AFTER id_patrimonio"
            )
        if "quantidade" not in columns:
            alter_statements.append(
                "ADD COLUMN quantidade INT NOT NULL DEFAULT 1 AFTER valor_compra"
            )
        if "numero_nota" not in columns:
            after_clause = "AFTER quantidade" if "quantidade" in columns or alter_statements else "AFTER valor_compra"
            alter_statements.append(
                f"ADD COLUMN numero_nota VARCHAR(50) NULL {after_clause}"
            )
        if "valor_atual" not in columns:
            alter_statements.append(
                "ADD COLUMN valor_atual DECIMAL(10,2) NULL AFTER valor_compra"
            )

        if not alter_statements:
            return

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            for stmt in alter_statements:
                cursor.execute(f"ALTER TABLE patrimonios {stmt}")
            self.connection.commit()
            print("[DatabaseManager] Colunas opcionais de patrimonios garantidas com sucesso.")
        except mysql.connector.Error as err:
            self.connection.rollback()
            print(f"[DatabaseManager] Falha ao ajustar colunas opcionais de patrimonios: {err}")
        finally:
            cursor.close()

    def _get_next_patrimonio_numbers(self, cursor, quantidade: int) -> List[int]:
        if quantidade <= 0:
            return []
        cursor.execute("SELECT COALESCE(MAX(numero_patrimonio), 0) FROM patrimonios FOR UPDATE")
        row = cursor.fetchone()
        last = row[0] if row else 0
        try:
            last_int = int(last or 0)
        except (TypeError, ValueError):
            last_int = 0
        return [last_int + i for i in range(1, quantidade + 1)]

    def create_patrimonio(self, data: Dict[str, Any]) -> int:
        if not data:
            raise ValueError("Dados do patrimonio nao informados.")

        try:
            available_columns = set(self.get_table_columns("patrimonios"))
        except mysql.connector.Error:
            available_columns = {
                "id_patrimonio",
                "nome",
                "descricao",
                "numero_serie",
                "valor_compra",
                "data_aquisicao",
                "estado_conservacao",
                "id_categoria",
                "id_fornecedor",
                "id_setor_local",
                "status",
                "quantidade",
                "numero_nota",
                "valor_atual",
            }

        required_fields = ("nome", "id_categoria", "id_setor_local", "status")
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise ValueError(f"Campos obrigatorios ausentes: {', '.join(missing)}")

        ordered_fields: Sequence[str] = (
            "nome",
            "descricao",
            "numero_serie",
            "valor_compra",
            "data_aquisicao",
            "estado_conservacao",
            "id_categoria",
            "id_fornecedor",
            "id_setor_local",
            "status",
            "quantidade",
            "numero_nota",
            "valor_atual",
        )

        numero_patrimonio_available = "numero_patrimonio" in available_columns
        numero_patrimonio_value = data.get("numero_patrimonio") if numero_patrimonio_available else None
        auto_generate_numero = numero_patrimonio_available and not numero_patrimonio_value

        columns: List[str] = []
        values: List[Any] = []
        for field in ordered_fields:
            if field not in available_columns:
                continue
            if field == "quantidade":
                value = data.get("quantidade", 1)
                if value in (None, ""):
                    value = 1
            elif field == "numero_nota":
                value = data.get("numero_nota") or None
            else:
                value = data.get(field)
            columns.append(field)
            values.append(value)

        if not columns:
            raise ValueError("Nenhuma coluna valida para inserir patrimonio.")

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            if hasattr(self.connection, "start_transaction") and not getattr(self.connection, "in_transaction", False):
                self.connection.start_transaction()
            if numero_patrimonio_available:
                if auto_generate_numero:
                    seq_values = self._get_next_patrimonio_numbers(cursor, 1)
                    numero_patrimonio_value = seq_values[0] if seq_values else None
                columns.append("numero_patrimonio")
                values.append(numero_patrimonio_value)

            placeholders = ", ".join(["%s"] * len(columns))
            columns_clause = ", ".join(f"`{col}`" for col in columns)

            cursor.execute(
                f"INSERT INTO patrimonios ({columns_clause}) VALUES ({placeholders})",
                tuple(values),
            )
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise err
        finally:
            cursor.close()

    def create_patrimonios_bulk(
        self,
        data: Dict[str, Any],
        quantidade: int,
        numero_series: Optional[Sequence[str]] = None,
        enforce_unique_serial: bool = False
    ) -> List[int]:
        if not data:
            raise ValueError("Dados do patrimonio nao informados.")
        try:
            qtd = int(quantidade)
        except Exception:
            raise ValueError("Quantidade invalida.")
        if qtd <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")

        # Descobrir colunas disponíveis uma vez
        try:
            available_columns = set(self.get_table_columns("patrimonios"))
        except mysql.connector.Error:
            available_columns = {
                "nome",
                "descricao",
                "numero_serie",
                "valor_compra",
                "data_aquisicao",
                "estado_conservacao",
                "id_categoria",
                "id_fornecedor",
                "id_setor_local",
                "status",
                "quantidade",
                "numero_nota",
                "valor_atual",
            }

        # Base estável de colunas: somente o que foi passado em `data` e existe na tabela
        base_columns = [
            k
            for k in data.keys()
            if k in available_columns and k not in ("id_patrimonio", "quantidade")
        ]
        include_numero_patrimonio = "numero_patrimonio" in available_columns
        if include_numero_patrimonio and "numero_patrimonio" not in base_columns:
            base_columns.append("numero_patrimonio")
        # Se a tabela tiver 'quantidade', vamos inserir 1 para cada linha
        include_quantidade = ("quantidade" in available_columns)
        if include_quantidade:
            columns_for_insert = base_columns + ["quantidade"]
        else:
            columns_for_insert = base_columns

        if not columns_for_insert:
            raise ValueError("Nenhuma coluna valida para inserir patrimonio.")

        placeholders = ", ".join(["%s"] * len(columns_for_insert))
        columns_clause = ", ".join(f"`{c}`" for c in columns_for_insert)

        self._ensure_connection()
        cursor = self.connection.cursor()
        inserted_ids: List[int] = []
        try:
            # Transação única
            if hasattr(self.connection, "start_transaction") and not getattr(self.connection, "in_transaction", False):
                self.connection.start_transaction()
            seq_numbers: List[int] = []
            if include_numero_patrimonio:
                seq_numbers = self._get_next_patrimonio_numbers(cursor, qtd)

            for idx in range(qtd):
                row = dict(data)  # cópia

                # Numero de série por-item (lista fornecida)
                if numero_series and len(numero_series) == qtd:
                    row["numero_serie"] = numero_series[idx]
                # Geração opcional de série única com sufixo
                elif enforce_unique_serial:
                    base_value = row.get("numero_serie")
                    if base_value is not None:
                        base = str(base_value).strip()
                        if base:
                            row["numero_serie"] = f"{base}-{idx+1:03d}"
                        else:
                            row["numero_serie"] = None

                if include_numero_patrimonio:
                    row["numero_patrimonio"] = seq_numbers[idx]

                if include_quantidade:
                    row["quantidade"] = 1

                values = [row.get(col) for col in base_columns]
                if include_quantidade:
                    values.append(1)

                cursor.execute(
                    f"INSERT INTO patrimonios ({columns_clause}) VALUES ({placeholders})",
                    tuple(values)
                )
                inserted_ids.append(cursor.lastrowid)

            self.connection.commit()
            return inserted_ids
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise err
        finally:
            cursor.close()

    def get_patrimonio_codigos(self, ids: Sequence[int]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        placeholders = ", ".join(["%s"] * len(ids))
        query = f"""
            SELECT id_patrimonio, numero_patrimonio
            FROM patrimonios
            WHERE id_patrimonio IN ({placeholders})
            ORDER BY numero_patrimonio ASC
        """
        return self.fetch_all(query, tuple(ids))

    def update_patrimonio(self, patrimonio_id: int, data: Dict[str, Any]) -> bool:
        if not data:
            return False

        try:
            allowed = set(self.get_table_columns("patrimonios"))
        except mysql.connector.Error:
            allowed = {
                "nome",
                "descricao",
                "numero_serie",
                "valor_compra",
                "data_aquisicao",
                "estado_conservacao",
                "id_categoria",
                "id_fornecedor",
                "id_setor_local",
                "status",
                "quantidade",
                "numero_nota",
                "valor_atual",
            }

        assignments: List[str] = []
        params: List[Any] = []
        for key, value in data.items():
            if key not in allowed or key == "id_patrimonio":
                continue
            assignments.append(f"`{key}` = %s")
            params.append(value if key != "numero_nota" else (value or None))

        if not assignments:
            return False

        params.append(patrimonio_id)
        sql = f"UPDATE patrimonios SET {', '.join(assignments)} WHERE id_patrimonio = %s"
        rows = self.execute_query(sql, tuple(params))
        return bool(rows)

    def _purge_patrimonio_dependencies(self, patrimonio_id: int) -> None:
        cleanup_targets = [
            ("patrimonios_centro_custo", "id_patrimonio"),
            ("movimentacoes", "id_patrimonio"),
            ("manutencoes", "id_patrimonio"),
            ("depreciacoes", "id_patrimonio"),
            ("anexos", "id_patrimonio"),
            ("itens_nota_fiscal", "id_patrimonio"),
            ("garantias", "id_patrimonio"),
            ("baixas", "id_patrimonio"),
        ]
        for table, column in cleanup_targets:
            try:
                self.execute_query(f"DELETE FROM {table} WHERE {column} = %s", (patrimonio_id,))
            except mysql.connector.Error as err:
                if err.errno in {errorcode.ER_NO_SUCH_TABLE, errorcode.ER_BAD_TABLE_ERROR, getattr(errorcode, "ER_WRONG_TABLE_NAME", 1103)}:
                    continue
                raise

    def delete_patrimonio(self, patrimonio_id: int) -> bool:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            self._purge_patrimonio_dependencies(patrimonio_id)
            query = "DELETE FROM patrimonios WHERE id_patrimonio = %s"
            cursor.execute(query, (patrimonio_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            self.connection.rollback()
            fk_errs = {errorcode.ER_ROW_IS_REFERENCED_2}
            legacy_fk = getattr(errorcode, "ER_ROW_IS_REFERENCED", None)
            if legacy_fk is not None:
                fk_errs.add(legacy_fk)
            if err.errno in fk_errs:
                raise ValueError("Nao e possivel excluir o patrimonio porque existem registros relacionados.") from err
            raise err
        finally:
            cursor.close()

                                                                             
    @staticmethod
    def _normalize_user_active(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        if isinstance(value, (int, float, Decimal)):
            return value != 0
        if isinstance(value, (bytes, bytearray)):
            try:
                value = value.decode().strip()
            except Exception:
                return None
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            lowered = text.lower()
            truthy = {"1", "true", "t", "sim", "s", "yes", "y", "ativo", "active"}
            falsy = {"0", "false", "f", "nao", "não", "n", "inativo", "inactive"}
            if lowered in truthy:
                return True
            if lowered in falsy:
                return False
            try:
                numeric = Decimal(text)
            except (ArithmeticError, ValueError):
                return None
            return numeric != 0
        return bool(value)

    def list_users(self, search=None):
        try:
            columns = set(self.get_table_columns("usuarios"))
        except mysql.connector.Error:
            columns = set()

        select_fields = [
            "id_usuario",
            "nome",
            "email",
            "nivel_acesso",
        ]
        if "ativo" in columns:
            select_fields.append("ativo")
        else:
            select_fields.append("NULL AS ativo")

        base_query = f"""
            SELECT
                {', '.join(select_fields)}
            FROM usuarios
        """
        params = None
        if search:
            base_query += " WHERE nome LIKE %s OR email LIKE %s"
            like_term = f"%{search}%"
            params = (like_term, like_term)
        base_query += " ORDER BY nome"

        rows = self.fetch_all(base_query, params)
        for row in rows:
            row["ativo"] = self._normalize_user_active(row.get("ativo"))
        return rows

    def list_categorias(self):
        query = """
            SELECT id_categoria, nome_categoria, descricao
            FROM categorias
            ORDER BY nome_categoria
        """
        return self.fetch_all(query)

    def ensure_categorias(self, nomes: Sequence[str]) -> Dict[str, int]:
        if not nomes:
            return {}

        placeholders = ", ".join(["%s"] * len(nomes))
        existing_rows = self.fetch_all(
            f"SELECT id_categoria, nome_categoria FROM categorias WHERE nome_categoria IN ({placeholders})",
            tuple(nomes),
        )

        mapping: Dict[str, int] = {}
        if existing_rows:
            for row in existing_rows:
                nome = row.get("nome_categoria")
                categoria_id = row.get("id_categoria")
                if nome and categoria_id is not None:
                    try:
                        mapping[nome] = int(categoria_id)
                    except (TypeError, ValueError):
                        continue

        for nome in nomes:
            if nome in mapping:
                continue

            self._ensure_connection()
            cursor = self.connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO categorias (nome_categoria, descricao) VALUES (%s, %s)",
                    (nome, f"Categoria fixa {nome.lower()}"),
                )
                self.connection.commit()
                mapping[nome] = int(cursor.lastrowid)
            except mysql.connector.Error as err:
                self.connection.rollback()
                if err.errno == errorcode.ER_DUP_ENTRY:
                    row = self.fetch_one(
                        "SELECT id_categoria FROM categorias WHERE nome_categoria = %s",
                        (nome,),
                    )
                    if row and row.get("id_categoria") is not None:
                        try:
                            mapping[nome] = int(row["id_categoria"])
                        except (TypeError, ValueError):
                            pass
                else:
                    raise
            finally:
                cursor.close()

        return mapping

    def list_fornecedores(self, search=None):
        query = """
            SELECT
                id_fornecedor,
                nome_fornecedor,
                cnpj,
                contato,
                telefone,
                email
            FROM fornecedores
        """
        params = None
        if search:
            query += " WHERE nome_fornecedor LIKE %s OR cnpj LIKE %s"
            like = f"%{search}%"
            params = (like, like)
        query += " ORDER BY nome_fornecedor"
        return self.fetch_all(query, params)

    def list_centros_custo(self, search=None):
        query = """
            SELECT id_centro_custo, nome_centro, descricao
            FROM centro_custo
        """
        params = None
        if search:
            query += " WHERE nome_centro LIKE %s"
            params = (f"%{search}%",)
        query += " ORDER BY nome_centro"
        return self.fetch_all(query, params)

    def list_setores_locais(self, search=None):
        query = """
            SELECT id_setor_local, nome_setor_local, localizacao, descricao
            FROM setores_locais
        """
        params = None
        if search:
            query += " WHERE nome_setor_local LIKE %s"
            params = (f"%{search}%",)
        query += " ORDER BY nome_setor_local"
        return self.fetch_all(query, params)

    def create_setor_local(self, data: Dict[str, Any]) -> int:
        if not data:
            raise ValueError("Dados de setor/local não informados.")
        try:
            allowed = set(self.get_table_columns("setores_locais"))
        except mysql.connector.Error:
            allowed = {
                "nome_setor_local",
                "localizacao",
                "descricao",
                "responsavel",
                "capacidade",
                "andar",
            }
        payload = {k: v for k, v in data.items() if k in allowed and k != "id_setor_local"}
        if not payload:
            raise ValueError("Nenhuma coluna válida para setores/locais.")
        columns = ", ".join(f"`{key}`" for key in payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        sql = f"INSERT INTO setores_locais ({columns}) VALUES ({placeholders})"
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, tuple(payload.values()))
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def update_setor_local(self, setor_id: int, data: Dict[str, Any]) -> bool:
        if not data:
            return False
        try:
            allowed = set(self.get_table_columns("setores_locais"))
        except mysql.connector.Error:
            allowed = {
                "nome_setor_local",
                "localizacao",
                "descricao",
                "responsavel",
                "capacidade",
                "andar",
            }
        updates: List[str] = []
        params: List[Any] = []
        for key, value in data.items():
            if key not in allowed or key == "id_setor_local":
                continue
            updates.append(f"`{key}` = %s")
            params.append(value)
        if not updates:
            return False
        params.append(setor_id)
        sql = f"UPDATE setores_locais SET {', '.join(updates)} WHERE id_setor_local = %s"
        rows = self.execute_query(sql, tuple(params))
        return bool(rows)

    def delete_setor_local(self, setor_id: int) -> bool:
        sql = "DELETE FROM setores_locais WHERE id_setor_local = %s"
        rows = self.execute_query(sql, (setor_id,))
        return bool(rows)

    def list_patrimonios(self, filters: Optional[Dict[str, Any]] = None):
        try:
            columns = set(self.get_table_columns("patrimonios"))
        except mysql.connector.Error:
            columns = {"quantidade", "numero_nota"}

        quantidade_expr = "COALESCE(p.quantidade, 1)" if "quantidade" in columns else "1"
        numero_nota_expr = "COALESCE(p.numero_nota, '')" if "numero_nota" in columns else "''"
        valor_atual_expr = "p.valor_atual" if "valor_atual" in columns else "NULL"

        query = [
            "SELECT",
            "    p.id_patrimonio,",
            "    p.numero_patrimonio,",
            "    p.nome AS nome_patrimonio,",
            "    p.descricao,",
            "    p.numero_serie,",
            "    p.valor_compra,",
            f"    {valor_atual_expr} AS valor_atual,",
            "    p.data_aquisicao,",
            "    p.estado_conservacao,",
            "    p.status,",
            "    p.id_categoria,",
            "    p.id_fornecedor,",
            "    p.id_setor_local,",
            f"    {quantidade_expr} AS quantidade,",
            f"    {numero_nota_expr} AS numero_nota,",
            "    cat.nome_categoria,",
            "    forn.nome_fornecedor,",
            "    sl.nome_setor_local,",
            "    (",
            "        SELECT GROUP_CONCAT(DISTINCT cc.nome_centro ORDER BY cc.nome_centro SEPARATOR ', ')",
            "        FROM patrimonios_centro_custo pcc",
            "        INNER JOIN centro_custo cc ON cc.id_centro_custo = pcc.id_centro_custo",
            "        WHERE pcc.id_patrimonio = p.id_patrimonio",
            "    ) AS centros_custo",
            "FROM patrimonios p",
            "LEFT JOIN categorias cat ON cat.id_categoria = p.id_categoria",
            "LEFT JOIN fornecedores forn ON forn.id_fornecedor = p.id_fornecedor",
            "LEFT JOIN setores_locais sl ON sl.id_setor_local = p.id_setor_local",
        ]

        conditions: List[str] = []
        params: List[Any] = []
        if filters:
            text = filters.get("texto")
            if text:
                like = f"%{text}%"
                conditions.append(
                    "("
                    "p.nome LIKE %s OR "
                    "p.descricao LIKE %s OR "
                    "p.numero_serie LIKE %s OR "
                    "CAST(p.numero_patrimonio AS CHAR) LIKE %s"
                    ")"
                )
                params.extend([like, like, like, like])
            categoria_id = filters.get("id_categoria")
            if categoria_id:
                conditions.append("p.id_categoria = %s")
                params.append(categoria_id)
            setor_id = filters.get("id_setor_local")
            if setor_id:
                conditions.append("p.id_setor_local = %s")
                params.append(setor_id)
            status = filters.get("status")
            if status:
                conditions.append("p.status = %s")
                params.append(status)

        if conditions:
            query.append("WHERE " + " AND ".join(conditions))

        query.append("ORDER BY p.data_aquisicao DESC, p.id_patrimonio DESC")

        final_query = "\n".join(query)
        return self.fetch_all(final_query, tuple(params) if params else None)

    def get_patrimonio_dashboard_metrics(self) -> Dict[str, Any]:
        try:
            columns = set(self.get_table_columns("patrimonios"))
        except mysql.connector.Error:
            columns = set()

        valor_col = "valor_atual" if "valor_atual" in columns else "valor_compra"
        quantidade_expr = "COALESCE(p.quantidade, 1)" if "quantidade" in columns else "1"

        query = f"""
            SELECT
                SUM(CASE WHEN p.status = 'ativo' THEN 1 ELSE 0 END) AS ativos,
                SUM(CASE WHEN p.status = 'baixado' THEN 1 ELSE 0 END) AS baixados,
                SUM(CASE WHEN p.status = 'em_manutencao' THEN 1 ELSE 0 END) AS manutencao,
                COALESCE(SUM(COALESCE({valor_col}, 0) * {quantidade_expr}), 0) AS total_valor
            FROM patrimonios p
        """
        row = self.fetch_one(query)
        if not row:
            return {"ativos": 0, "baixados": 0, "manutencao": 0, "total_valor": 0.0}
        return {
            "ativos": row.get("ativos", 0) or 0,
            "baixados": row.get("baixados", 0) or 0,
            "manutencao": row.get("manutencao", 0) or 0,
            "total_valor": float(row.get("total_valor") or 0.0),
        }

    def list_manutencoes(self, filters: Optional[Dict[str, Any]] = None):
        base_query = [
            "SELECT",
            "    m.*,",
            "    p.nome AS nome_patrimonio",
            "FROM manutencoes m",
            "INNER JOIN patrimonios p ON p.id_patrimonio = m.id_patrimonio",
        ]
        params: List[Any] = []
        conditions: List[str] = []
        if filters:
            patrimonio_id = filters.get("id_patrimonio")
            if patrimonio_id:
                conditions.append("m.id_patrimonio = %s")
                params.append(patrimonio_id)
            status = filters.get("status")
            if status:
                conditions.append("m.status = %s")
                params.append(status)
            data_inicio = filters.get("data_inicio")
            if data_inicio:
                conditions.append("m.data_inicio >= %s")
                params.append(data_inicio)
            data_fim = filters.get("data_fim")
            if data_fim:
                conditions.append("m.data_inicio <= %s")
                params.append(data_fim)
        if conditions:
            base_query.append("WHERE " + " AND ".join(conditions))
        base_query.append("ORDER BY m.data_inicio DESC")
        query = "\n".join(base_query)
        return self.fetch_all(query, tuple(params) if params else None)

    def create_manutencao(self, data: Dict[str, Any]) -> int:
        if not data:
            raise ValueError("Dados de manutenção não informados.")
        try:
            allowed = set(self.get_table_columns("manutencoes"))
        except mysql.connector.Error:
            allowed = {
                "id_patrimonio",
                "data_inicio",
                "data_fim",
                "descricao",
                "custo",
                "responsavel",
                "status",
                "tipo_manutencao",
                "empresa",
            }
        payload = {k: v for k, v in data.items() if k in allowed and k != "id_manutencao"}
        if not payload:
            raise ValueError("Nenhuma coluna válida para manutenção.")
        columns = ", ".join(f"`{key}`" for key in payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        sql = f"INSERT INTO manutencoes ({columns}) VALUES ({placeholders})"
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, tuple(payload.values()))
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def update_manutencao(self, manutencao_id: int, data: Dict[str, Any]) -> bool:
        if not data:
            return False
        try:
            allowed = set(self.get_table_columns("manutencoes"))
        except mysql.connector.Error:
            allowed = {
                "id_patrimonio",
                "data_inicio",
                "data_fim",
                "descricao",
                "custo",
                "responsavel",
                "status",
                "tipo_manutencao",
                "empresa",
            }
        updates: List[str] = []
        params: List[Any] = []
        for key, value in data.items():
            if key not in allowed or key == "id_manutencao":
                continue
            updates.append(f"`{key}` = %s")
            params.append(value)
        if not updates:
            return False
        params.append(manutencao_id)
        sql = f"UPDATE manutencoes SET {', '.join(updates)} WHERE id_manutencao = %s"
        rows = self.execute_query(sql, tuple(params))
        return bool(rows)

    def delete_manutencao(self, manutencao_id: int) -> bool:
        sql = "DELETE FROM manutencoes WHERE id_manutencao = %s"
        rows = self.execute_query(sql, (manutencao_id,))
        return bool(rows)

    def get_patrimonio(self, patrimonio_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT
                p.*,
                cat.nome_categoria,
                sl.nome_setor_local,
                sl.localizacao
            FROM patrimonios p
            LEFT JOIN categorias cat ON cat.id_categoria = p.id_categoria
            LEFT JOIN setores_locais sl ON sl.id_setor_local = p.id_setor_local
            WHERE p.id_patrimonio = %s
        """
        return self.fetch_one(query, (patrimonio_id,))

    def update_patrimonio_setor_local(self, patrimonio_id: int, setor_local_id: Optional[int]) -> bool:
        sql = "UPDATE patrimonios SET id_setor_local = %s WHERE id_patrimonio = %s"
        rows = self.execute_query(sql, (setor_local_id, patrimonio_id))
        return bool(rows)

    def list_movimentacoes(
        self,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            mov_columns = set(self.get_table_columns("movimentacoes"))
        except mysql.connector.Error:
            mov_columns = set()

        select_fields = [
            "mov.id_movimentacao",
            "mov.data_movimentacao",
            "mov.tipo_movimentacao",
            "mov.origem",
            "mov.destino",
            "mov.observacoes",
        ]
        if "responsavel" in mov_columns:
            select_fields.append("mov.responsavel")
        select_fields.extend(
            [
                "p.nome AS nome_patrimonio",
                "u.nome AS nome_usuario",
            ]
        )
        select_clause = ",\n    ".join(select_fields)

        base_query = [
            "SELECT",
            f"    {select_clause}",
            "FROM movimentacoes mov",
            "INNER JOIN patrimonios p ON p.id_patrimonio = mov.id_patrimonio",
            "INNER JOIN usuarios u ON u.id_usuario = mov.id_usuario",
        ]
        params: List[Any] = []
        conditions: List[str] = []
        if filters:
            patrimonio_id = filters.get("id_patrimonio")
            if patrimonio_id:
                conditions.append("mov.id_patrimonio = %s")
                params.append(patrimonio_id)
            inicio = filters.get("data_inicio")
            if inicio:
                conditions.append("mov.data_movimentacao >= %s")
                params.append(inicio)
            fim = filters.get("data_fim")
            if fim:
                conditions.append("mov.data_movimentacao <= %s")
                params.append(fim)
        if conditions:
            base_query.append("WHERE " + " AND ".join(conditions))
        base_query.append("ORDER BY mov.data_movimentacao DESC")
        base_query.append("LIMIT %s")
        params.append(limit)
        query = "\n".join(base_query)
        return self.fetch_all(query, tuple(params))

    def create_movimentacao(self, data: Dict[str, Any]) -> int:
        if not data:
            raise ValueError("Dados da movimentação não informados.")
        try:
            allowed = set(self.get_table_columns("movimentacoes"))
        except mysql.connector.Error:
            allowed = {
                "id_patrimonio",
                "id_usuario",
                "data_movimentacao",
                "tipo_movimentacao",
                "origem",
                "destino",
                "observacoes",
            }
        payload = {k: v for k, v in data.items() if k in allowed and k != "id_movimentacao"}
        if not payload:
            raise ValueError("Nenhuma coluna válida para movimentação.")
        columns = ", ".join(f"`{key}`" for key in payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        sql = f"INSERT INTO movimentacoes ({columns}) VALUES ({placeholders})"
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, tuple(payload.values()))
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def list_notas_fiscais(self):
        query = """
            SELECT
                nf.id_nota_fiscal,
                nf.numero_nota,
                nf.data_emissao,
                nf.valor_total,
                nf.caminho_arquivo_nf,
                forn.nome_fornecedor
            FROM notas_fiscais nf
            INNER JOIN fornecedores forn ON forn.id_fornecedor = nf.id_fornecedor
            ORDER BY nf.data_emissao DESC
        """
        return self.fetch_all(query)

    def list_itens_nota(self, id_nota_fiscal):
        query = """
            SELECT
                itens.id_item_nf,
                itens.quantidade,
                itens.valor_unitario,
                p.nome AS nome_patrimonio
            FROM itens_nota_fiscal itens
            INNER JOIN patrimonios p ON p.id_patrimonio = itens.id_patrimonio
            WHERE itens.id_nota_fiscal = %s
            ORDER BY itens.id_item_nf
        """
        return self.fetch_all(query, (id_nota_fiscal,))

    def _normalize_anexo_entidade(self, entidade: Optional[str]) -> str:
        chave = (entidade or "patrimonio").strip().lower()
        if chave not in self._ANEXO_CONFIG:
            raise ValueError(f"Entidade de anexo '{entidade}' não é suportada.")
        return chave

    def _get_anexo_allowed_columns(self, entidade: str) -> List[str]:
        config = self._ANEXO_CONFIG[entidade]
        try:
            return self.get_table_columns(config["table"])
        except mysql.connector.Error:
            valores = [valor for valor in config["columns"].values() if valor]
            return valores

    def list_anexos(
        self,
        entidade: Optional[str] = None,
        entidade_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        entidade_norm = self._normalize_anexo_entidade(entidade)
        config = self._ANEXO_CONFIG[entidade_norm]

        def _alias(coluna: Optional[str], apelido: str) -> str:
            if coluna:
                return f"a.`{coluna}` AS {apelido}"
            return f"NULL AS {apelido}"

        colunas = config["columns"]
        select = [
            _alias(config["pk"], "id_anexo"),
            _alias(colunas.get("entidade_id"), "entidade_id"),
            _alias(colunas.get("nome_arquivo"), "nome_arquivo"),
            _alias(colunas.get("caminho_arquivo"), "caminho_arquivo"),
            _alias(colunas.get("tamanho_arquivo"), "tamanho_arquivo"),
            _alias(colunas.get("tipo_arquivo"), "tipo_arquivo"),
            _alias(colunas.get("data_upload"), "data_upload"),
        ]
        select.extend(config.get("extra_select", []))

        query_parts = ["SELECT", ",\n".join(select), f"FROM {config['table']} a"]
        query_parts.extend(config.get("joins", []))

        params: List[Any] = []
        if entidade_id is not None:
            query_parts.append(f"WHERE a.`{colunas['entidade_id']}` = %s")
            params.append(entidade_id)

        order_by = config.get("order_by")
        if order_by:
            query_parts.append(f"ORDER BY {order_by}")

        query = "\n".join(query_parts)
        rows = self.fetch_all(query, tuple(params) if params else None)
        for row in rows:
            row.setdefault("entidade", entidade_norm)
        return rows

    def create_anexo(self, entidade: str, data: Dict[str, Any]) -> int:
        if not data:
            raise ValueError("Dados do anexo não informados.")

        entidade_norm = self._normalize_anexo_entidade(entidade)
        config = self._ANEXO_CONFIG[entidade_norm]
        colunas = config["columns"]

        fk_coluna = colunas.get("entidade_id")
        entidade_id = data.get("entidade_id") or data.get(fk_coluna)
        if not entidade_id:
            raise ValueError("Identificador da entidade não informado.")

        allowed = set(self._get_anexo_allowed_columns(entidade_norm))
        allowed.discard(config["pk"])

        payload: Dict[str, Any] = {}
        for chave_logica, coluna in colunas.items():
            if not coluna or coluna == config["pk"]:
                continue
            valor = data.get(chave_logica)
            if valor is None and chave_logica == coluna:
                valor = data.get(coluna)
            if valor is None and chave_logica == "entidade_id":
                valor = entidade_id
            if valor is None:
                continue
            if coluna in allowed:
                payload[coluna] = valor

        if fk_coluna and fk_coluna not in payload:
            if fk_coluna in allowed:
                payload[fk_coluna] = entidade_id

        if not payload:
            raise ValueError("Nenhuma coluna válida para anexo.")

        columns = ", ".join(f"`{col}`" for col in payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        sql = f"INSERT INTO {config['table']} ({columns}) VALUES ({placeholders})"

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, tuple(payload.values()))
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def delete_anexo(self, entidade: str, anexo_id: int) -> bool:
        entidade_norm = self._normalize_anexo_entidade(entidade)
        config = self._ANEXO_CONFIG[entidade_norm]
        sql = f"DELETE FROM {config['table']} WHERE `{config['pk']}` = %s"
        rows = self.execute_query(sql, (anexo_id,))
        return bool(rows)

    def list_auditorias(self, limit=100):
        query = """
            SELECT
                aud.*,
                usr.nome AS nome_usuario
            FROM auditorias aud
            INNER JOIN usuarios usr ON usr.id_usuario = aud.id_usuario
            ORDER BY aud.data_auditoria DESC
            LIMIT %s
        """
        return self.fetch_all(query, (limit,))

    def create_auditoria(self, data: Dict[str, Any]) -> int:
        if not data.get("id_usuario"):
            raise ValueError("Usuário da auditoria não informado.")
        if not data.get("acao"):
            raise ValueError("Ação da auditoria não informada.")

        payload: Dict[str, Any] = {}
        columns = (
            "id_usuario",
            "data_auditoria",
            "acao",
            "tabela_afetada",
            "id_registro_afetado",
            "detalhes_antigos",
            "detalhes_novos",
        )
        for coluna in columns:
            valor = data.get(coluna)
            if valor is None or valor == "":
                continue
            if coluna == "id_registro_afetado" and (valor == 0 or valor == "0"):
                continue
            if coluna in {"detalhes_antigos", "detalhes_novos"} and isinstance(valor, (dict, list)):
                valor = json.dumps(valor, ensure_ascii=False)
            if coluna == "data_auditoria" and isinstance(valor, datetime):
                valor = valor.strftime("%Y-%m-%d %H:%M:%S")
            payload[coluna] = valor

        if "data_auditoria" not in payload:
            payload["data_auditoria"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        colunas_sql = ", ".join(f"`{col}`" for col in payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        sql = f"INSERT INTO auditorias ({colunas_sql}) VALUES ({placeholders})"

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, tuple(payload.values()))
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def update_auditoria(self, auditoria_id: int, data: Dict[str, Any]) -> bool:
        if not auditoria_id:
            raise ValueError("Identificador da auditoria não informado.")
        if not data:
            return False

        allowed = (
            "data_auditoria",
            "acao",
            "tabela_afetada",
            "id_registro_afetado",
            "detalhes_antigos",
            "detalhes_novos",
        )
        updates: List[str] = []
        params: List[Any] = []
        for coluna in allowed:
            if coluna not in data:
                continue
            valor = data[coluna]
            if valor is None or valor == "":
                valor = None
            if coluna == "id_registro_afetado" and valor in (0, "0"):
                valor = None
            if coluna in {"detalhes_antigos", "detalhes_novos"} and isinstance(valor, (dict, list)):
                valor = json.dumps(valor, ensure_ascii=False)
            if coluna == "data_auditoria" and isinstance(valor, datetime):
                valor = valor.strftime("%Y-%m-%d %H:%M:%S")
            updates.append(f"`{coluna}` = %s")
            params.append(valor)

        if not updates:
            return False
        params.append(auditoria_id)
        sql = f"UPDATE auditorias SET {', '.join(updates)} WHERE id_auditoria = %s"
        rows = self.execute_query(sql, tuple(params))
        return bool(rows)

    def list_auditorias_agendadas(self, dias: int = 90) -> List[Dict[str, Any]]:
        query = """
            SELECT
                aud.id_auditoria,
                aud.data_auditoria,
                aud.acao,
                aud.tabela_afetada,
                aud.id_registro_afetado,
                JSON_UNQUOTE(JSON_EXTRACT(aud.detalhes_novos, '$.observacoes')) AS observacoes
            FROM auditorias aud
            WHERE JSON_UNQUOTE(JSON_EXTRACT(aud.detalhes_novos, '$.status')) = 'agendado'
        """
        params: List[Any] = []
        if dias and dias > 0:
            query += " AND aud.data_auditoria BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)"
            params.append(dias)
        query += " ORDER BY aud.data_auditoria ASC"
        return self.fetch_all(query, tuple(params) if params else None)

    def relatorio_por_setor(self):
        query = """
            SELECT
                sl.nome_setor_local AS setor,
                COALESCE(sl.localizacao, '-') AS localizacao,
                COUNT(p.id_patrimonio) AS quantidade,
                COALESCE(SUM(p.valor_compra), 0) AS valor_total
            FROM setores_locais sl
            LEFT JOIN patrimonios p ON p.id_setor_local = sl.id_setor_local
            GROUP BY sl.id_setor_local, sl.nome_setor_local, sl.localizacao
            ORDER BY sl.nome_setor_local
        """
        return self.fetch_all(query)

    def relatorio_por_categoria(self):
        query = """
            SELECT
                cat.nome_categoria AS categoria,
                COUNT(p.id_patrimonio) AS quantidade,
                COALESCE(SUM(dep.valor_depreciado), 0) AS depreciacao_acumulada
            FROM categorias cat
            LEFT JOIN patrimonios p ON p.id_categoria = cat.id_categoria
            LEFT JOIN depreciacoes dep ON dep.id_patrimonio = p.id_patrimonio
            GROUP BY cat.id_categoria, cat.nome_categoria
            ORDER BY cat.nome_categoria
        """
        return self.fetch_all(query)

    def relatorio_manutencoes(self, limit=100):
        query = """
            SELECT
                m.data_inicio,
                p.nome AS nome_patrimonio,
                COALESCE(m.tipo_manutencao, m.status) AS tipo,
                m.responsavel,
                m.custo,
                m.status
            FROM manutencoes m
            INNER JOIN patrimonios p ON p.id_patrimonio = m.id_patrimonio
            ORDER BY m.data_inicio DESC
            LIMIT %s
        """
        return self.fetch_all(query, (limit,))

    def calcular_depreciacao(self, vida_util_anos: int = 10, filters: Optional[Dict[str, Any]] = None):
        """Calcula os valores de depreciação para os patrimônios cadastrados.

        A função aplica um modelo simples de depreciação linear considerando uma vida útil
        média (em anos). Opcionalmente é possível filtrar os patrimônios pelo mesmo formato
        aceito em :py:meth:`list_patrimonios`.

        Parameters
        ----------
        vida_util_anos: int
            Vida útil média utilizada para o cálculo linear. O padrão é ``10`` anos.
        filters: dict, optional
            Dicionário de filtros, aceitando ``texto`` e ``id_categoria`` entre outros
            campos utilizados por :py:meth:`list_patrimonios`.
        """

        list_filters = filters or {}
        patrimonios = self.list_patrimonios(list_filters if list_filters else None)
        hoje = date.today()
        vida_util_meses = max(int(vida_util_anos) * 12, 1)
        linhas = []

        for item in patrimonios:
            valor = item.get("valor_compra") or Decimal("0")
            if not isinstance(valor, Decimal):
                valor = Decimal(str(valor or "0"))

            aquisicao = item.get("data_aquisicao")
            if isinstance(aquisicao, datetime):
                aquisicao = aquisicao.date()

            if isinstance(aquisicao, date):
                meses_em_uso = max((hoje.year - aquisicao.year) * 12 + (hoje.month - aquisicao.month), 0)
            else:
                meses_em_uso = 0

            depreciacao_mensal = valor / vida_util_meses if vida_util_meses else Decimal("0")
            acumulado = depreciacao_mensal * Decimal(meses_em_uso)
            if acumulado > valor:
                acumulado = valor

            valor_periodo = depreciacao_mensal
            if acumulado >= valor:
                valor_periodo = Decimal("0")
            elif acumulado + depreciacao_mensal > valor:
                valor_periodo = valor - acumulado

            linhas.append(
                {
                    "patrimonio": item.get("nome"),
                    "categoria": item.get("nome_categoria"),
                    "competencia": hoje.strftime("%Y-%m"),
                    "valor_periodo": float(valor_periodo),
                    "valor_acumulado": float(acumulado),
                }
            )

        return linhas
