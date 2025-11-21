"""
Suite de Testes Automatizados - NeoBenesys v2.4

Este script executa testes automatizados para validar o sistema.

Uso:
    python test_suite.py

Versão: 1.0
Data: 19/11/2025
"""

import sys
import os
import time
from datetime import datetime
from typing import List, Tuple, Dict

# Adicionar path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database_manager import DatabaseManager
from backend.validators import validar_email, validar_cnpj, validar_telefone, validar_ncm, validar_cfop
import backend.config_db as config


class TestResult:
    """Resultado de um teste"""
    def __init__(self, test_id: str, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.test_id = test_id
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
    
    def __str__(self):
        status = "✅ PASSOU" if self.passed else "❌ FALHOU"
        return f"{self.test_id}: {status} - {self.name} ({self.duration:.3f}s)"


class TestSuite:
    """Suite de testes automatizados"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.db_manager = None
    
    def setup(self):
        """Preparar ambiente de testes"""
        print("=" * 80)
        print("🧪 SUITE DE TESTES AUTOMATIZADOS - NeoBenesys v2.4")
        print("=" * 80)
        print()
        
        try:
            self.db_manager = DatabaseManager(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_DATABASE
            )
            print("✅ Conexão com banco de dados estabelecida")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco: {e}")
            return False
    
    def teardown(self):
        """Limpar ambiente de testes"""
        if self.db_manager:
            self.db_manager.close()
        print("\n✅ Ambiente de testes finalizado")
    
    def run_test(self, test_id: str, test_name: str, test_func):
        """Executa um teste e registra o resultado"""
        print(f"\n{test_id}: {test_name}")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                print(f"✅ PASSOU ({duration:.3f}s)")
                self.results.append(TestResult(test_id, test_name, True, "", duration))
            else:
                print(f"❌ FALHOU ({duration:.3f}s)")
                self.results.append(TestResult(test_id, test_name, False, "Teste retornou False", duration))
        
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ ERRO: {str(e)} ({duration:.3f}s)")
            self.results.append(TestResult(test_id, test_name, False, str(e), duration))
    
    # ==================== TESTES DE VALIDAÇÃO ====================
    
    def test_validar_email_valido(self):
        """TC-063: Validação de email válido"""
        return validar_email("teste@exemplo.com")
    
    def test_validar_email_invalido(self):
        """TC-063: Validação de email inválido"""
        return not validar_email("emailinvalido")
    
    def test_validar_cnpj_valido(self):
        """TC-021: Validação de CNPJ válido"""
        return validar_cnpj("12.345.678/0001-90")
    
    def test_validar_cnpj_invalido(self):
        """TC-021: Validação de CNPJ inválido"""
        return not validar_cnpj("12.345.678/0001-99")
    
    def test_validar_cnpj_formato_errado(self):
        """TC-021: Validação de CNPJ com formato errado"""
        return not validar_cnpj("123")
    
    def test_validar_telefone_valido_11_digitos(self):
        """TC-023: Validação de telefone válido (11 dígitos)"""
        return validar_telefone("(11) 98765-4321")
    
    def test_validar_telefone_valido_10_digitos(self):
        """TC-023: Validação de telefone válido (10 dígitos)"""
        return validar_telefone("(11) 3456-7890")
    
    def test_validar_telefone_invalido(self):
        """TC-023: Validação de telefone inválido"""
        return not validar_telefone("(11) 1234")
    
    def test_validar_ncm_valido(self):
        """TC-041: Validação de NCM válido"""
        return validar_ncm("12345678")
    
    def test_validar_ncm_invalido(self):
        """TC-041: Validação de NCM inválido"""
        return not validar_ncm("123")
    
    def test_validar_cfop_valido(self):
        """TC-042: Validação de CFOP válido"""
        return validar_cfop("5102")
    
    def test_validar_cfop_invalido(self):
        """TC-042: Validação de CFOP inválido"""
        return not validar_cfop("12")
    
    # ==================== TESTES DE BANCO DE DADOS ====================
    
    def test_conexao_banco(self):
        """TC-103: Conexão com banco de dados"""
        return self.db_manager is not None
    
    def test_listar_fornecedores(self):
        """TC-108: Listar fornecedores"""
        fornecedores = self.db_manager.list_fornecedores()
        print(f"   Fornecedores encontrados: {len(fornecedores)}")
        return isinstance(fornecedores, list)
    
    def test_listar_categorias(self):
        """TC-031: Listar categorias"""
        categorias = self.db_manager.list_categorias()
        print(f"   Categorias encontradas: {len(categorias)}")
        return isinstance(categorias, list)
    
    def test_listar_setores(self):
        """TC-032: Listar setores/locais"""
        setores = self.db_manager.list_setores_locais()
        print(f"   Setores encontrados: {len(setores)}")
        return isinstance(setores, list)
    
    def test_listar_centros_custo(self):
        """TC-047: Listar centros de custo"""
        centros = self.db_manager.list_centros_custo()
        print(f"   Centros de custo encontrados: {len(centros)}")
        return isinstance(centros, list)
    
    def test_verificar_usuario_admin(self):
        """TC-006: Verificar se usuário admin existe"""
        # Tentar buscar usuário admin
        try:
            cursor = self.db_manager.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE nivel = 'admin' LIMIT 1")
            admin = cursor.fetchone()
            cursor.close()
            
            if admin:
                print(f"   Admin encontrado: {admin.get('email', 'N/A')}")
                return True
            else:
                print("   ⚠️ Nenhum usuário admin encontrado")
                return False
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    def test_verificar_tabela_auditoria(self):
        """TC-077: Verificar se tabela de auditoria existe"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SHOW TABLES LIKE 'auditoria'")
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                print("   Tabela 'auditoria' existe")
                return True
            else:
                print("   ⚠️ Tabela 'auditoria' não encontrada")
                return False
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    def test_verificar_campo_ativo_usuarios(self):
        """TC-016: Verificar se campo 'ativo' existe em usuários"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("DESCRIBE usuarios")
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            if 'ativo' in columns:
                print("   Campo 'ativo' existe em usuários")
                return True
            else:
                print("   ⚠️ Campo 'ativo' não encontrado em usuários")
                return False
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    def test_verificar_campo_tipo_manutencao(self):
        """TC-050: Verificar se campo 'tipo_manutencao' existe"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("DESCRIBE manutencoes")
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            if 'tipo_manutencao' in columns:
                print("   Campo 'tipo_manutencao' existe")
                return True
            else:
                print("   ⚠️ Campo 'tipo_manutencao' não encontrado")
                return False
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    def test_verificar_campo_empresa_manutencao(self):
        """TC-049: Verificar se campo 'empresa' existe em manutenções"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("DESCRIBE manutencoes")
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            if 'empresa' in columns:
                print("   Campo 'empresa' existe em manutenções")
                return True
            else:
                print("   ⚠️ Campo 'empresa' não encontrado em manutenções")
                return False
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    # ==================== TESTES DE PERFORMANCE ====================
    
    def test_performance_listar_patrimonios(self):
        """TC-084: Performance ao listar patrimônios"""
        start = time.time()
        
        try:
            cursor = self.db_manager.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patrimonios LIMIT 100")
            patrimonios = cursor.fetchall()
            cursor.close()
            
            duration = time.time() - start
            print(f"   {len(patrimonios)} patrimônios listados em {duration:.3f}s")
            
            # Deve ser < 1 segundo
            return duration < 1.0
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    def test_performance_busca(self):
        """TC-086: Performance de busca"""
        start = time.time()
        
        try:
            cursor = self.db_manager.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patrimonios WHERE nome LIKE '%notebook%' LIMIT 100")
            resultados = cursor.fetchall()
            cursor.close()
            
            duration = time.time() - start
            print(f"   {len(resultados)} resultados encontrados em {duration:.3f}s")
            
            # Deve ser < 1 segundo
            return duration < 1.0
        except Exception as e:
            print(f"   Erro: {e}")
            return False
    
    # ==================== EXECUÇÃO DOS TESTES ====================
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("\n" + "=" * 80)
        print("📋 EXECUTANDO TESTES")
        print("=" * 80)
        
        # Testes de Validação
        print("\n\n🔍 CATEGORIA: TESTES DE VALIDAÇÃO")
        print("=" * 80)
        
        self.run_test("VAL-001", "Validar email válido", self.test_validar_email_valido)
        self.run_test("VAL-002", "Validar email inválido", self.test_validar_email_invalido)
        self.run_test("VAL-003", "Validar CNPJ válido", self.test_validar_cnpj_valido)
        self.run_test("VAL-004", "Validar CNPJ inválido", self.test_validar_cnpj_invalido)
        self.run_test("VAL-005", "Validar CNPJ formato errado", self.test_validar_cnpj_formato_errado)
        self.run_test("VAL-006", "Validar telefone 11 dígitos", self.test_validar_telefone_valido_11_digitos)
        self.run_test("VAL-007", "Validar telefone 10 dígitos", self.test_validar_telefone_valido_10_digitos)
        self.run_test("VAL-008", "Validar telefone inválido", self.test_validar_telefone_invalido)
        self.run_test("VAL-009", "Validar NCM válido", self.test_validar_ncm_valido)
        self.run_test("VAL-010", "Validar NCM inválido", self.test_validar_ncm_invalido)
        self.run_test("VAL-011", "Validar CFOP válido", self.test_validar_cfop_valido)
        self.run_test("VAL-012", "Validar CFOP inválido", self.test_validar_cfop_invalido)
        
        # Testes de Banco de Dados
        print("\n\n💾 CATEGORIA: TESTES DE BANCO DE DADOS")
        print("=" * 80)
        
        self.run_test("DB-001", "Conexão com banco", self.test_conexao_banco)
        self.run_test("DB-002", "Listar fornecedores", self.test_listar_fornecedores)
        self.run_test("DB-003", "Listar categorias", self.test_listar_categorias)
        self.run_test("DB-004", "Listar setores", self.test_listar_setores)
        self.run_test("DB-005", "Listar centros de custo", self.test_listar_centros_custo)
        self.run_test("DB-006", "Verificar usuário admin", self.test_verificar_usuario_admin)
        self.run_test("DB-007", "Verificar tabela auditoria", self.test_verificar_tabela_auditoria)
        self.run_test("DB-008", "Verificar campo 'ativo' em usuários", self.test_verificar_campo_ativo_usuarios)
        self.run_test("DB-009", "Verificar campo 'tipo_manutencao'", self.test_verificar_campo_tipo_manutencao)
        self.run_test("DB-010", "Verificar campo 'empresa' em manutenções", self.test_verificar_campo_empresa_manutencao)
        
        # Testes de Performance
        print("\n\n⚡ CATEGORIA: TESTES DE PERFORMANCE")
        print("=" * 80)
        
        self.run_test("PERF-001", "Performance listar patrimônios", self.test_performance_listar_patrimonios)
        self.run_test("PERF-002", "Performance busca", self.test_performance_busca)
    
    def generate_report(self):
        """Gera relatório dos testes"""
        print("\n\n" + "=" * 80)
        print("📊 RELATÓRIO DE TESTES")
        print("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📈 Estatísticas:")
        print(f"   Total de testes: {total}")
        print(f"   ✅ Passou: {passed}")
        print(f"   ❌ Falhou: {failed}")
        print(f"   📊 Taxa de sucesso: {success_rate:.1f}%")
        
        if failed > 0:
            print(f"\n❌ Testes que falharam:")
            for result in self.results:
                if not result.passed:
                    print(f"   {result.test_id}: {result.name}")
                    if result.message:
                        print(f"      Erro: {result.message}")
        
        print(f"\n⏱️ Tempo total: {sum(r.duration for r in self.results):.3f}s")
        
        # Avaliação final
        print("\n" + "=" * 80)
        if success_rate >= 95:
            print("✅ SISTEMA APROVADO PARA USO COMERCIAL")
            print("   Taxa de sucesso >= 95%")
        elif success_rate >= 80:
            print("⚠️ SISTEMA APROVADO COM RESSALVAS")
            print("   Taxa de sucesso >= 80%, mas < 95%")
            print("   Recomenda-se corrigir falhas antes do deploy")
        else:
            print("❌ SISTEMA NÃO APROVADO")
            print("   Taxa de sucesso < 80%")
            print("   Correções obrigatórias antes do deploy")
        print("=" * 80)
        
        # Salvar relatório em arquivo
        self.save_report_to_file(total, passed, failed, success_rate)
    
    def save_report_to_file(self, total, passed, failed, success_rate):
        """Salva relatório em arquivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_testes_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE TESTES AUTOMATIZADOS - NeoBenesys v2.4\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total de testes: {total}\n")
            f.write(f"Passou: {passed}\n")
            f.write(f"Falhou: {failed}\n")
            f.write(f"Taxa de sucesso: {success_rate:.1f}%\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("DETALHES DOS TESTES\n")
            f.write("=" * 80 + "\n\n")
            
            for result in self.results:
                status = "PASSOU" if result.passed else "FALHOU"
                f.write(f"{result.test_id}: {status} - {result.name} ({result.duration:.3f}s)\n")
                if result.message:
                    f.write(f"   Erro: {result.message}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            if success_rate >= 95:
                f.write("RESULTADO: SISTEMA APROVADO PARA USO COMERCIAL\n")
            elif success_rate >= 80:
                f.write("RESULTADO: SISTEMA APROVADO COM RESSALVAS\n")
            else:
                f.write("RESULTADO: SISTEMA NÃO APROVADO\n")
            f.write("=" * 80 + "\n")
        
        print(f"\n💾 Relatório salvo em: {filename}")


def main():
    """Função principal"""
    suite = TestSuite()
    
    if not suite.setup():
        print("\n❌ Falha ao preparar ambiente de testes")
        return 1
    
    try:
        suite.run_all_tests()
        suite.generate_report()
    finally:
        suite.teardown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
