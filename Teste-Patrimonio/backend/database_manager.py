import mysql.connector
from mysql.connector import errorcode
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

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

    def create_user(self, nome, email, password):
        if self.get_user_by_email(email):
            return None
        insert_sql = """
            INSERT INTO usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
        """
        rows = self.execute_query(insert_sql, (nome, email, password))
        if not rows:
            return None
        return self.get_user_by_email(email)

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
    def list_users(self, search=None):
        base_query = """
            SELECT
                id_usuario,
                nome,
                email,
                nivel_acesso,
                'Sim' AS ativo
            FROM usuarios
        """
        params = None
        if search:
            base_query += " WHERE nome LIKE %s OR email LIKE %s"
            like_term = f"%{search}%"
            params = (like_term, like_term)
        base_query += " ORDER BY nome"
        return self.fetch_all(base_query, params)

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

    def list_manutencoes(self):
        query = """
            SELECT
                m.id_manutencao,
                m.data_inicio,
                m.data_fim,
                m.descricao,
                m.custo,
                m.responsavel,
                m.status,
                p.id_patrimonio,
                p.nome AS nome_patrimonio
            FROM manutencoes m
            INNER JOIN patrimonios p ON p.id_patrimonio = m.id_patrimonio
            ORDER BY m.data_inicio DESC
        """
        return self.fetch_all(query)

    def list_movimentacoes(self, limit=50):
        query = """
            SELECT
                mov.id_movimentacao,
                mov.data_movimentacao,
                mov.tipo_movimentacao,
                mov.origem,
                mov.destino,
                mov.observacoes,
                p.nome AS nome_patrimonio,
                u.nome AS nome_usuario
            FROM movimentacoes mov
            INNER JOIN patrimonios p ON p.id_patrimonio = mov.id_patrimonio
            INNER JOIN usuarios u ON u.id_usuario = mov.id_usuario
            ORDER BY mov.data_movimentacao DESC
            LIMIT %s
        """
        return self.fetch_all(query, (limit,))

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

    def list_anexos(self):
        query = """
            SELECT
                a.id_anexo,
                p.nome AS nome_patrimonio,
                a.nome_arquivo,
                a.caminho_arquivo,
                a.tipo_arquivo,
                a.data_upload
            FROM anexos a
            INNER JOIN patrimonios p ON p.id_patrimonio = a.id_patrimonio
            ORDER BY a.data_upload DESC
        """
        return self.fetch_all(query)

    def list_auditorias(self, limit=100):
        query = """
            SELECT
                aud.id_auditoria,
                aud.data_auditoria,
                aud.tabela_afetada,
                aud.id_registro_afetado,
                aud.acao,
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
                COUNT(p.id_patrimonio) AS quantidade,
                COALESCE(SUM(p.valor_compra), 0) AS valor_total
            FROM setores_locais sl
            LEFT JOIN patrimonios p ON p.id_setor_local = sl.id_setor_local
            GROUP BY sl.id_setor_local, sl.nome_setor_local
            ORDER BY sl.nome_setor_local
        """
        return self.fetch_all(query)

    def relatorio_por_categoria(self):
        query = """
            SELECT
                cat.nome_categoria AS categoria,
                COUNT(p.id_patrimonio) AS quantidade,
                COALESCE(SUM(p.valor_compra), 0) AS valor_total
            FROM categorias cat
            LEFT JOIN patrimonios p ON p.id_categoria = cat.id_categoria
            GROUP BY cat.id_categoria, cat.nome_categoria
            ORDER BY cat.nome_categoria
        """
        return self.fetch_all(query)

    def relatorio_manutencoes(self, limit=100):
        query = """
            SELECT
                m.data_inicio,
                p.nome AS nome_patrimonio,
                m.status,
                m.responsavel,
                m.custo
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
