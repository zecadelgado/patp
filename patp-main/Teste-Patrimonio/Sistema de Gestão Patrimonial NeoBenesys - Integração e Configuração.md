# Sistema de Gestão Patrimonial NeoBenesys - Integração e Configuração

Este documento detalha as etapas de integração do sistema NeoBenesys com um banco de dados MySQL, bem como as configurações necessárias para seu funcionamento e sugestões de melhorias.

## 1. Estrutura do Projeto

O projeto NeoBenesys é uma aplicação PyQt para gestão patrimonial. A estrutura de arquivos principal é a seguinte:

```
neobenesys/
├── anexos.ui
├── auditoria.ui
├── centro_custo.ui
├── dashboard_atualizado.ui
├── database_manager.py
├── depreciacao.ui
├── fornecedores.ui
├── home.ui
├── images/
│   ├── 2.png
│   ├── 3.png
│   └── fundo_login.png
├── login.ui
├── main.py
├── manutencao.ui
├── movimentacoes.ui
├── notas_fiscais.ui
├── patrimonio.ui
├── relatorios.ui
├── setores_locais.ui
├── usuarios.ui
└── config_db.py
```

## 2. Configuração do Banco de Dados MySQL

O banco de dados foi configurado com base no script SQL fornecido (`schema.sql`).

### 2.1. Credenciais de Acesso

As credenciais de acesso ao MySQL foram definidas para facilitar a configuração inicial:

*   **Usuário:** `root`
*   **Senha:** `root`
*   **Banco de Dados:** `patrimonio_ideau`

**Observação:** Em um ambiente de produção, é **altamente recomendável** criar um usuário MySQL dedicado com permissões mínimas necessárias e uma senha forte, em vez de usar o usuário `root`.

### 2.2. Script de Criação do Banco de Dados

O script `schema.sql` contém a definição de todas as tabelas necessárias para o sistema:

```sql
CREATE SCHEMA IF NOT EXISTS `patrimonio_ideau` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `patrimonio_ideau` ;

-- Definição das tabelas (exemplo: tabela de usuários)
CREATE TABLE IF NOT EXISTS `patrimonio_ideau`.`usuarios` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `senha` VARCHAR(255) NOT NULL,
  `nivel_acesso` ENUM(\'admin\', \'user\') NOT NULL DEFAULT \'user\',
  `data_criacao` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;

-- ... (outras tabelas como categorias, fornecedores, patrimonios, etc.)
```

Um usuário de teste foi adicionado ao banco de dados para facilitar os testes de login:

*   **Email:** `test@example.com`
*   **Senha:** `password`
*   **Nome:** `Teste User`
*   **Nível de Acesso:** `admin`

## 3. Configuração do Ambiente Python

### 3.1. Dependências

As seguintes dependências Python são necessárias e foram instaladas:

*   `PySide6`: Para a interface gráfica PyQt.
*   `mysql-connector-python`: Para a conexão com o banco de dados MySQL.

Você pode instalá-las usando o arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3.2. `config_db.py`

Este arquivo contém a função para estabelecer a conexão com o banco de dados. Ele foi atualizado com as credenciais corretas:

```python
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="patrimonio_ideau"
    )
```

### 3.3. `database_manager.py`

Este novo arquivo foi criado para centralizar as operações de banco de dados, incluindo métodos para conexão, desconexão, execução de queries e funções específicas para o sistema, como `get_user_by_email` e `verify_password`.

```python
import mysql.connector
from config_db import get_connection

class DatabaseManager:
    # ... (métodos de conexão, desconexão, execute_query, get_user_by_email, verify_password, etc.)
```

### 3.4. `main.py`

O arquivo `main.py` foi modificado para:

*   Importar `DatabaseManager` e `QLineEdit`.
*   Inicializar uma instância de `DatabaseManager` e tentar conectar ao banco de dados ao iniciar a aplicação.
*   Implementar a função `handle_login` para autenticar usuários usando o `DatabaseManager`.
*   Corrigir o carregamento dos arquivos `.ui` para usar caminhos absolutos, garantindo que a aplicação encontre os arquivos de interface.

## 4. Como Executar a Aplicação

1.  **Certifique-se de que o MySQL Server esteja em execução** em sua máquina e que o banco de dados `patrimonio_ideau` tenha sido criado e populado com as tabelas do `schema.sql`.
2.  **Instale as dependências Python** listadas em `requirements.txt`.
3.  **Navegue até o diretório `neobenesys`** no terminal.
4.  **Execute o arquivo `main.py`:**
    ```bash
    python3 main.py
    ```

Ao iniciar, a tela de login deverá aparecer. Você pode usar o usuário de teste `test@example.com` e a senha `password` para acessar o dashboard.

## 5. Sugestões de Melhorias

### 5.1. Segurança

*   **Hash de Senhas:** Atualmente, as senhas são armazenadas em texto simples no banco de dados e verificadas diretamente. É crucial implementar um algoritmo de hash seguro (ex: `bcrypt`, `scrypt`) para armazenar as senhas. Isso protege as senhas dos usuários mesmo que o banco de dados seja comprometido.
*   **Usuário de Banco de Dados Dedicado:** Crie um usuário MySQL com permissões restritas apenas ao banco de dados `patrimonio_ideau` e apenas para as operações que a aplicação realmente precisa (SELECT, INSERT, UPDATE, DELETE). Evite usar o usuário `root` para a aplicação.

### 5.2. Tratamento de Erros e Validação

*   **Validação de Entrada:** Implementar validação robusta para todos os campos de entrada do usuário na interface e no backend para prevenir injeção de SQL e outros problemas de segurança, além de garantir a integridade dos dados.
*   **Mensagens de Erro Amigáveis:** Melhorar as mensagens de erro para o usuário final, tornando-as mais descritivas e úteis, sem expor detalhes internos do sistema.

### 5.3. Modularização e Organização do Código

*   **Separação de Responsabilidades:** Considere criar classes ou módulos separados para cada tela da aplicação (ex: `LoginWindow.py`, `DashboardWindow.py`) em vez de carregar tudo dinamicamente no `main.py`. Isso melhora a organização, manutenção e testabilidade do código.
*   **Padrão MVC (Model-View-Controller) ou MVVM (Model-View-ViewModel):** Adotar um padrão de arquitetura pode ajudar a organizar a lógica de negócios (Model), a interface do usuário (View) e a interação entre eles (Controller/ViewModel), tornando o sistema mais escalável e fácil de manter.

### 5.4. Funcionalidades Adicionais

*   **CRUD Completo:** Implementar as operações CRUD (Create, Read, Update, Delete) para todas as entidades do sistema (categorias, fornecedores, patrimônios, etc.) no `database_manager.py` e integrá-las às respectivas telas da interface.
*   **Gerenciamento de Sessão:** Implementar um sistema de gerenciamento de sessão para manter o usuário logado e controlar o acesso a diferentes partes da aplicação com base no `nivel_acesso`.
*   **Relatórios:** Desenvolver a funcionalidade de geração de relatórios mais detalhados e personalizáveis, utilizando os dados do banco de dados.
*   **Busca e Filtragem:** Adicionar funcionalidades de busca e filtragem para facilitar a localização de patrimônios, usuários, etc.

### 5.5. Interface do Usuário

*   **Estilização:** O arquivo `style.qss` na pasta `frontend/resources/icons` do projeto `Patrimonio_Ideau` original pode ser adaptado e utilizado para aplicar um estilo visual mais consistente e profissional à aplicação NeoBenesys.

## 6. Referências

Não aplicável para este documento, pois as informações são baseadas nos arquivos fornecidos e na análise interna. 

---

**Autor:** Manus AI

