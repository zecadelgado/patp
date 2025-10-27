from __future__ import annotations

import json
import mimetypes
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import mysql.connector
from mysql.connector import errorcode

from config_db import get_connection


class DatabaseManager:
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

    def create_patrimonio(self, data: Dict[str, Any]) -> int:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            query = """
                INSERT INTO patrimonios (
                    nome,
                    descricao,
                    numero_serie,
                    valor_compra,
                    data_aquisicao,
                    estado_conservacao,
                    id_categoria,
                    id_fornecedor,
                    id_setor_local,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                data["nome"],
                data.get("descricao"),
                data.get("numero_serie"),
                data.get("valor_compra"),
                data.get("data_aquisicao"),
                data.get("estado_conservacao"),
                data["id_categoria"],
                data.get("id_fornecedor"),
                data["id_setor_local"],
                data["status"],
            )
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise err
        finally:
            cursor.close()

    def update_patrimonio(self, patrimonio_id: int, data: Dict[str, Any]) -> bool:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            query = """
                UPDATE patrimonios
                SET
                    nome = %s,
                    descricao = %s,
                    numero_serie = %s,
                    valor_compra = %s,
                    data_aquisicao = %s,
                    estado_conservacao = %s,
                    id_categoria = %s,
                    id_fornecedor = %s,
                    id_setor_local = %s,
                    status = %s
                WHERE id_patrimonio = %s
            """
            params = (
                data["nome"],
                data.get("descricao"),
                data.get("numero_serie"),
                data.get("valor_compra"),
                data.get("data_aquisicao"),
                data.get("estado_conservacao"),
                data["id_categoria"],
                data.get("id_fornecedor"),
                data["id_setor_local"],
                data["status"],
                patrimonio_id,
            )
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise err
        finally:
            cursor.close()

    def delete_patrimonio(self, patrimonio_id: int) -> bool:
        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
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

    # ---- Listagem utilitaria para telas --------------------------------- #
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
        query = """
            SELECT
                p.id_patrimonio,
                p.nome,
                p.descricao,
                p.numero_serie,
                p.valor_compra,
                p.data_aquisicao,
                p.estado_conservacao,
                p.status,
                p.id_categoria,
                p.id_fornecedor,
                p.id_setor_local,
                cat.nome_categoria,
                forn.nome_fornecedor,
                sl.nome_setor_local,
                GROUP_CONCAT(DISTINCT cc.nome_centro ORDER BY cc.nome_centro SEPARATOR ', ') AS centros_custo
            FROM patrimonios p
            LEFT JOIN categorias cat ON cat.id_categoria = p.id_categoria
            LEFT JOIN fornecedores forn ON forn.id_fornecedor = p.id_fornecedor
            LEFT JOIN setores_locais sl ON sl.id_setor_local = p.id_setor_local
            LEFT JOIN patrimonios_centro_custo pcc ON pcc.id_patrimonio = p.id_patrimonio
            LEFT JOIN centro_custo cc ON cc.id_centro_custo = pcc.id_centro_custo
        """
        conditions: List[str] = []
        params: List[Any] = []
        if filters:
            text = filters.get("texto")
            if text:
                like = f"%{text}%"
                conditions.append("(p.nome LIKE %s OR p.descricao LIKE %s OR p.numero_serie LIKE %s)")
                params.extend([like, like, like])
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
            query += " WHERE " + " AND ".join(conditions)
        query += """
            GROUP BY
                p.id_patrimonio,
                p.nome,
                p.descricao,
                p.numero_serie,
                p.valor_compra,
                p.data_aquisicao,
                p.estado_conservacao,
                p.status,
                p.id_categoria,
                p.id_fornecedor,
                p.id_setor_local,
                cat.nome_categoria,
                forn.nome_fornecedor,
                sl.nome_setor_local,
                p.data_cadastro
            ORDER BY p.data_cadastro DESC
        """
        return self.fetch_all(query, tuple(params) if params else None)

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
        base_query = [
            "SELECT",
            "    mov.id_movimentacao,",
            "    mov.data_movimentacao,",
            "    mov.tipo_movimentacao,",
            "    mov.origem,",
            "    mov.destino,",
            "    mov.observacoes,",
            "    mov.responsavel,",
            "    p.nome AS nome_patrimonio,",
            "    u.nome AS nome_usuario",
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
                "responsavel",
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

    def list_anexos(self, id_patrimonio: Optional[int] = None) -> List[Dict[str, Any]]:
        query_parts = [
            "SELECT",
            "    a.*,",
            "    p.nome AS nome_patrimonio",
            "FROM anexos a",
            "INNER JOIN patrimonios p ON p.id_patrimonio = a.id_patrimonio",
        ]
        params: List[Any] = []
        if id_patrimonio:
            query_parts.append("WHERE a.id_patrimonio = %s")
            params.append(id_patrimonio)
        query_parts.append("ORDER BY a.data_upload DESC")
        query = "\n".join(query_parts)
        return self.fetch_all(query, tuple(params) if params else None)

    def create_anexo(self, data: Dict[str, Any]) -> int:
        if not data:
            raise ValueError("Dados do anexo não informados.")
        try:
            allowed = set(self.get_table_columns("anexos"))
        except mysql.connector.Error:
            allowed = {
                "id_patrimonio",
                "nome_arquivo",
                "caminho_arquivo",
                "tipo_arquivo",
                "tamanho_arquivo",
                "data_upload",
            }
        payload = {k: v for k, v in data.items() if k in allowed and k != "id_anexo"}
        if not payload:
            raise ValueError("Nenhuma coluna válida para anexo.")
        columns = ", ".join(f"`{key}`" for key in payload.keys())
        placeholders = ", ".join(["%s"] * len(payload))
        sql = f"INSERT INTO anexos ({columns}) VALUES ({placeholders})"
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

    def delete_anexo(self, anexo_id: int) -> bool:
        sql = "DELETE FROM anexos WHERE id_anexo = %s"
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
