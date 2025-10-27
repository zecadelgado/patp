# CÓDIGO FINAL PARA main.py
import sys
import os
from PySide6.QtWidgets import QApplication, QPushButton, QMessageBox, QLineEdit, QStackedWidget, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QTimer, QDateTime

# Adiciona o diretório 'backend' ao PATH para que os módulos sejam encontrados
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database_manager import DatabaseManager
from centro_custo import CentroCustoController
from fornecedores import FornecedoresController
from Notas import NotasFiscaisController
from patrimonio_controller import PatrimonioController # NOVO

def create_controller(key, widget, db_manager):
    if key == "notas_fiscais":
        return NotasFiscaisController(widget, db_manager)
    if key == "fornecedores":
        return FornecedoresController(widget, db_manager)
    if key == "centro_custo":
        return CentroCustoController(widget, db_manager)
    if key == "patrimonio":
        return PatrimonioController(widget, db_manager) # NOVO
    return None

def load_ui(file_name: str):
    # Correção para buscar os arquivos .ui na pasta frontend
    ui_file_path = os.path.join(os.path.dirname(__file__), 'frontend', file_name)
    
    loader = QUiLoader()
    ui_file = QFile(ui_file_path)
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Não foi possível abrir {ui_file_path}")
    widget = loader.load(ui_file)
    ui_file.close()
    if not widget:
        raise RuntimeError(f"Falha ao carregar {ui_file_path}")
    return widget

# ... (O restante da classe NeoBenesysApp permanece o mesmo do seu projeto, mas com as correções de importação e carregamento de UI) ...
class NeoBenesysApp:
    def __init__(self):
        self.db_manager = DatabaseManager()
        if not self.db_manager.connect():
            QMessageBox.critical(None, "Erro de Conexão", "Não foi possível conectar ao banco de dados.")
            sys.exit(1)

        self.login = load_ui("login.ui")
        self.login.setWindowTitle("NeoBenesys - Login")

        btn_entrar = self.login.findChild(QPushButton, "btn_entrar")
        btn_cadastrar = self.login.findChild(QPushButton, "btn_cadastrar")

        if btn_entrar is not None:
            btn_entrar.clicked.connect(self.handle_login)
        else:
            print("[Aviso] Botão 'btn_entrar' não encontrado no login.ui")

        if btn_cadastrar is not None:
            btn_cadastrar.clicked.connect(self.abrir_cadastro)
        else:
            print("[Aviso] Botão 'btn_cadastrar' não encontrado no login.ui")

        self.dashboard = None
        self.cadastro = None
        self.widgets = {}
        self.screens = {}
        self.controllers = {}
        self.current_user = None

    def handle_login(self):
        email_input = self.login.findChild(QLineEdit, "txt_email")
        senha_input = self.login.findChild(QLineEdit, "txt_senha")

        email = email_input.text() if email_input else ""
        senha = senha_input.text() if senha_input else ""

        user = self.db_manager.verify_password(email, senha)

        if user:
            self.current_user = user
            QMessageBox.information(None, "Login", f"Bem-vindo, {user.get('nome', 'usuário')}!")
            self.abrir_dashboard()
        else:
            QMessageBox.warning(None, "Login", "Email ou senha incorretos.")

    def abrir_cadastro(self):
        self.cadastro = load_ui("cadastro.ui")
        self.cadastro.setWindowTitle("NeoBenesys - Cadastro")

        btn_cadastrar_form = self.cadastro.findChild(QPushButton, "btn_cadastrar")
        if btn_cadastrar_form is not None:
            btn_cadastrar_form.clicked.connect(self.handle_cadastro)
        else:
            print("[Aviso] Botão 'btn_cadastrar' não encontrado no cadastro.ui")

        self.cadastro.show()

    def handle_cadastro(self):
        nome_input = self.cadastro.findChild(QLineEdit, "txt_nome")
        email_input = self.cadastro.findChild(QLineEdit, "txt_email")
        senha_input1 = self.cadastro.findChild(QLineEdit, "txt_senha1")
        senha_input2 = self.cadastro.findChild(QLineEdit, "txt_senha2")

        nome = nome_input.text().strip() if nome_input else ""
        email = email_input.text().strip() if email_input else ""
        senha1 = senha_input1.text() if senha_input1 else ""
        senha2 = senha_input2.text() if senha_input2 else ""

        if not nome or not email or not senha1 or not senha2:
            QMessageBox.warning(self.cadastro, "Cadastro", "Preencha todos os campos.")
            return

        if senha1 != senha2:
            QMessageBox.warning(self.cadastro, "Cadastro", "As senhas não conferem.")
            return

        user = self.db_manager.create_user(nome, email, senha1)

        if user:
            QMessageBox.information(self.cadastro, "Cadastro", "Usuário criado com sucesso!")
            self.cadastro.close()
            self.login.show()
        else:
            QMessageBox.warning(self.cadastro, "Cadastro", "Não foi possível criar o usuário (e-mail já existe?).")

    def abrir_dashboard(self):
        self.dashboard = load_ui("home.ui")
        self.dashboard.setWindowTitle("NeoBenesys - Dashboard")

        lbl_saudacao = self.dashboard.findChild(QLabel, "lbl_saudacao")
        if lbl_saudacao and self.current_user:
            lbl_saudacao.setText(f"Olá, {self.current_user.get('nome', 'Usuário')}")

        self.screens = {
            "usuarios": "usuarios.ui",
            "patrimonio": "patrimonio.ui",
            "manutencao": "manutencao.ui",
            "depreciacao": "depreciacao.ui",
            "auditoria": "auditoria.ui",
            "anexos": "anexos.ui",
            "relatorios": "relatorios.ui",
            "fornecedores": "fornecedores.ui",
            "centro_custo": "centro_custo.ui",
            "notas_fiscais": "notas_fiscais.ui",
            "movimentacoes": "movimentacoes.ui",
            "setores_locais": "setores_locais.ui",
        }

        stacked = self.dashboard.findChild(QStackedWidget, "stackedWidget")
        if stacked is None:
            print("[Erro] 'stackedWidget' não encontrado no home.ui. Verifique o objectName.")
        else:
            for key, ui_file in self.screens.items():
                try:
                    widget = load_ui(ui_file)
                    if not widget.objectName():
                        widget.setObjectName(key)
                    stacked.addWidget(widget)
                    self.widgets[key] = widget

                    controller = create_controller(key, widget, self.db_manager)
                    if controller:
                        self.controllers[key] = controller
                except Exception as e:
                    print(f"[Aviso] Não consegui carregar {ui_file}: {e}")

        button_map = {
            "btn_usuarios": "usuarios",
            "btn_patrimonio": "patrimonio",
            "btn_manutencoes": "manutencao",
            "btn_depreciacao": "depreciacao",
            "btn_auditoria": "auditoria",
            "btn_anexos": "anexos",
            "btn_relatorios": "relatorios",
            "btn_fornecedores": "fornecedores",
            "btn_categorias": "categorias",
            "btn_centro_custo": "centro_custo",
            "btn_notas_fiscais": "notas_fiscais",
            "btn_movimentacoes": "movimentacoes",
            "btn_setores_locais": "setores_locais",
        }

        for btn_name, screen_key in button_map.items():
            btn = self.dashboard.findChild(QPushButton, btn_name)
            if btn is None:
                print(f"[Aviso] Botão '{btn_name}' não encontrado no home.ui")
                continue
            if screen_key not in self.widgets:
                print(f"[Aviso] Tela '{screen_key}' não carregada; verifique {self.screens.get(screen_key)}")
                continue

            def navigate(_, key=screen_key):
                target_widget = self.widgets.get(key)
                if target_widget:
                    stacked.setCurrentWidget(target_widget)
                controller = self.controllers.get(key)
                if controller and hasattr(controller, "refresh"):
                    try:
                        controller.refresh()
                    except Exception as e:
                        print(f"[Aviso] refresh() falhou para '{key}': {e}")

            btn.clicked.connect(navigate)

        btn_sair = self.dashboard.findChild(QPushButton, "btn_sair")
        if btn_sair:
            btn_sair.clicked.connect(QApplication.instance().quit)

        self.iniciar_relogio_dashboard()
        self.dashboard.show()
        self.login.close()

    def run(self):
        self.login.show()

    def iniciar_relogio_dashboard(self):
        lbl_data = self.dashboard.findChild(QLabel, "lbl_data")
        lbl_relogio = self.dashboard.findChild(QLabel, "lbl_relogio")

        def tick():
            agora = QDateTime.currentDateTime()
            if lbl_data:
                lbl_data.setText(agora.toString("dd/MM/yyyy"))
            if lbl_relogio:
                lbl_relogio.setText(agora.toString("HH:mm:ss"))

        self._timer = QTimer(self.dashboard)
        self._timer.timeout.connect(tick)
        self._timer.start(1000)
        tick()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sistema = NeoBenesysApp()
    sistema.run()
    sys.exit(app.exec())
