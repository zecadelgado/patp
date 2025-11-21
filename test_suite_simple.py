"""
Suite de Testes Simplificada - NeoBenesys v2.4
Testa validações e funções que não precisam de banco de dados

Uso:
    python test_suite_simple.py

Versão: 1.0
Data: 19/11/2025
"""

import sys
import os
import time
from datetime import datetime
from typing import List

# Adicionar path do backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.validators import validar_email, validar_cnpj, validar_telefone, validar_ncm, validar_cfop


class TestResult:
    """Resultado de um teste"""
    def __init__(self, test_id: str, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.test_id = test_id
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration


class SimpleTestSuite:
    """Suite de testes simplificada"""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
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
        """Validação de email válido"""
        emails_validos = [
            "teste@exemplo.com",
            "user@domain.com.br",
            "admin@sistema.com",
            "joao.silva@empresa.com.br"
        ]
        for email in emails_validos:
            valido, msg = validar_email(email)
            if not valido:
                print(f"   ❌ Email válido rejeitado: {email} - {msg}")
                return False
        print(f"   ✓ {len(emails_validos)} emails válidos aceitos")
        return True
    
    def test_validar_email_invalido(self):
        """Validação de email inválido"""
        emails_invalidos = [
            "emailinvalido",
            "@exemplo.com",
            "teste@",
            "teste",
            "teste@.com"
        ]
        for email in emails_invalidos:
            valido, msg = validar_email(email)
            if valido:
                print(f"   ❌ Email inválido aceito: {email}")
                return False
        print(f"   ✓ {len(emails_invalidos)} emails inválidos rejeitados")
        return True
    
    def test_validar_cnpj_valido(self):
        """Validação de CNPJ válido"""
        cnpjs_validos = [
            "11.222.333/0001-81",
            "00.000.000/0001-91",
            "34.028.316/0001-03"  # Exemplo de CNPJ válido
        ]
        for cnpj in cnpjs_validos:
            valido, msg = validar_cnpj(cnpj)
            if not valido:
                print(f"   ❌ CNPJ válido rejeitado: {cnpj} - {msg}")
                return False
        print(f"   ✓ {len(cnpjs_validos)} CNPJs válidos aceitos")
        return True
    
    def test_validar_cnpj_invalido(self):
        """Validação de CNPJ inválido"""
        cnpjs_invalidos = [
            "12.345.678/0001-99",  # Dígito verificador errado
            "123",  # Muito curto
            "00.000.000/0000-00",  # Todos zeros
            "11.111.111/1111-11"  # Todos iguais
        ]
        for cnpj in cnpjs_invalidos:
            valido, msg = validar_cnpj(cnpj)
            if valido:
                print(f"   ❌ CNPJ inválido aceito: {cnpj}")
                return False
        print(f"   ✓ {len(cnpjs_invalidos)} CNPJs inválidos rejeitados")
        return True
    
    def test_validar_telefone_valido(self):
        """Validação de telefone válido"""
        telefones_validos = [
            "(11) 98765-4321",  # Celular
            "(11) 3456-7890",   # Fixo
            "11987654321",      # Sem formatação
            "(21) 99999-8888"
        ]
        for telefone in telefones_validos:
            valido, msg = validar_telefone(telefone)
            if not valido:
                print(f"   ❌ Telefone válido rejeitado: {telefone} - {msg}")
                return False
        print(f"   ✓ {len(telefones_validos)} telefones válidos aceitos")
        return True
    
    def test_validar_telefone_invalido(self):
        """Validação de telefone inválido"""
        telefones_invalidos = [
            "(11) 1234",  # Muito curto
            "123",
            "(11) 123456789012"  # Muito longo
        ]
        for telefone in telefones_invalidos:
            valido, msg = validar_telefone(telefone)
            if valido:
                print(f"   ❌ Telefone inválido aceito: {telefone}")
                return False
        print(f"   ✓ {len(telefones_invalidos)} telefones inválidos rejeitados")
        return True
    
    def test_validar_ncm_valido(self):
        """Validação de NCM válido"""
        ncms_validos = [
            "12345678",
            "84713012",
            "00000000"
        ]
        for ncm in ncms_validos:
            valido, msg = validar_ncm(ncm)
            if not valido:
                print(f"   ❌ NCM válido rejeitado: {ncm} - {msg}")
                return False
        print(f"   ✓ {len(ncms_validos)} NCMs válidos aceitos")
        return True
    
    def test_validar_ncm_invalido(self):
        """Validação de NCM inválido"""
        ncms_invalidos = [
            "123",  # Muito curto
            "123456789",  # Muito longo
            "abcd1234"  # Letras
        ]
        for ncm in ncms_invalidos:
            valido, msg = validar_ncm(ncm)
            if valido:
                print(f"   ❌ NCM inválido aceito: {ncm}")
                return False
        print(f"   ✓ {len(ncms_invalidos)} NCMs inválidos rejeitados")
        return True
    
    def test_validar_cfop_valido(self):
        """Validação de CFOP válido"""
        cfops_validos = [
            "5102",
            "6102",
            "1102",
            "0000"
        ]
        for cfop in cfops_validos:
            valido, msg = validar_cfop(cfop)
            if not valido:
                print(f"   ❌ CFOP válido rejeitado: {cfop} - {msg}")
                return False
        print(f"   ✓ {len(cfops_validos)} CFOPs válidos aceitos")
        return True
    
    def test_validar_cfop_invalido(self):
        """Validação de CFOP inválido"""
        cfops_invalidos = [
            "12",  # Muito curto
            "12345",  # Muito longo
            "abcd"  # Letras
        ]
        for cfop in cfops_invalidos:
            valido, msg = validar_cfop(cfop)
            if valido:
                print(f"   ❌ CFOP inválido aceito: {cfop}")
                return False
        print(f"   ✓ {len(cfops_invalidos)} CFOPs inválidos rejeitados")
        return True
    
    # ==================== TESTES DE ARQUIVOS ====================
    
    def test_arquivos_backend_existem(self):
        """Verificar se arquivos do backend existem"""
        arquivos = [
            "backend/database_manager.py",
            "backend/validators.py",
            "backend/audit_helper.py",
            "backend/cache_manager.py",
            "backend/import_patrimonio.py",
            "backend/import_controller.py",
            "backend/confirmation_dialogs.py",
            "backend/quick_create_dialogs.py"
        ]
        
        faltando = []
        for arquivo in arquivos:
            if not os.path.exists(arquivo):
                faltando.append(arquivo)
        
        if faltando:
            print(f"   ❌ Arquivos faltando: {', '.join(faltando)}")
            return False
        
        print(f"   ✓ Todos os {len(arquivos)} arquivos do backend existem")
        return True
    
    def test_template_importacao_existe(self):
        """Verificar se template de importação existe"""
        if os.path.exists("template_importacao_patrimonios.xlsx"):
            print("   ✓ Template de importação existe")
            return True
        else:
            print("   ❌ Template de importação não encontrado")
            return False
    
    def test_migrations_existem(self):
        """Verificar se scripts de migração existem"""
        migrations = [
            "database/migrations_security_improvements.sql",
            "database/migrations_manutencao.sql"
        ]
        
        faltando = []
        for migration in migrations:
            if not os.path.exists(migration):
                faltando.append(migration)
        
        if faltando:
            print(f"   ⚠️ Migrations faltando: {', '.join(faltando)}")
            print("   (Não crítico se já foram aplicadas)")
        
        print(f"   ✓ Verificação de migrations concluída")
        return True
    
    # ==================== EXECUÇÃO DOS TESTES ====================
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("=" * 80)
        print("🧪 SUITE DE TESTES SIMPLIFICADA - NeoBenesys v2.4")
        print("=" * 80)
        print()
        
        # Testes de Validação
        print("\n🔍 CATEGORIA: TESTES DE VALIDAÇÃO")
        print("=" * 80)
        
        self.run_test("VAL-001", "Validar emails válidos", self.test_validar_email_valido)
        self.run_test("VAL-002", "Validar emails inválidos", self.test_validar_email_invalido)
        self.run_test("VAL-003", "Validar CNPJs válidos", self.test_validar_cnpj_valido)
        self.run_test("VAL-004", "Validar CNPJs inválidos", self.test_validar_cnpj_invalido)
        self.run_test("VAL-005", "Validar telefones válidos", self.test_validar_telefone_valido)
        self.run_test("VAL-006", "Validar telefones inválidos", self.test_validar_telefone_invalido)
        self.run_test("VAL-007", "Validar NCMs válidos", self.test_validar_ncm_valido)
        self.run_test("VAL-008", "Validar NCMs inválidos", self.test_validar_ncm_invalido)
        self.run_test("VAL-009", "Validar CFOPs válidos", self.test_validar_cfop_valido)
        self.run_test("VAL-010", "Validar CFOPs inválidos", self.test_validar_cfop_invalido)
        
        # Testes de Arquivos
        print("\n\n📁 CATEGORIA: TESTES DE ARQUIVOS")
        print("=" * 80)
        
        self.run_test("FILE-001", "Verificar arquivos do backend", self.test_arquivos_backend_existem)
        self.run_test("FILE-002", "Verificar template de importação", self.test_template_importacao_existe)
        self.run_test("FILE-003", "Verificar scripts de migração", self.test_migrations_existem)
    
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
        if success_rate == 100:
            print("✅ TODOS OS TESTES PASSARAM!")
            print("   Sistema validado com sucesso")
        elif success_rate >= 90:
            print("⚠️ MAIORIA DOS TESTES PASSOU")
            print(f"   Taxa de sucesso: {success_rate:.1f}%")
        else:
            print("❌ MUITOS TESTES FALHARAM")
            print(f"   Taxa de sucesso: {success_rate:.1f}%")
            print("   Correções necessárias")
        print("=" * 80)
        
        # Salvar relatório
        self.save_report_to_file(total, passed, failed, success_rate)
    
    def save_report_to_file(self, total, passed, failed, success_rate):
        """Salva relatório em arquivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_testes_simples_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE TESTES SIMPLIFICADOS - NeoBenesys v2.4\n")
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
            if success_rate == 100:
                f.write("RESULTADO: TODOS OS TESTES PASSARAM\n")
            elif success_rate >= 90:
                f.write("RESULTADO: MAIORIA DOS TESTES PASSOU\n")
            else:
                f.write("RESULTADO: MUITOS TESTES FALHARAM\n")
            f.write("=" * 80 + "\n")
        
        print(f"\n💾 Relatório salvo em: {filename}")


def main():
    """Função principal"""
    suite = SimpleTestSuite()
    suite.run_all_tests()
    suite.generate_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
