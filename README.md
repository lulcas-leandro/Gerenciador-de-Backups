# Gerenciador de Backups de Bancos de Dados em Contêineres Docker

Este é um sistema web simples para gerenciar backups de bancos de dados que rodam em contêineres Docker. Com ele, você pode facilmente criar, restaurar, agendar e excluir backups de seus bancos de dados PostgreSQL, MySQL e MariaDB.

## ✨ Funcionalidades

*   **Listagem de contêineres:** Visualiza todos os contêineres de banco de dados ativos (PostgreSQL, MySQL, MariaDB).
*   **Backup com um clique:** Crie backups instantâneos de seus bancos de dados.
*   **Restauração de backups:** Restaure um backup para um contêiner existente.
*   **Agendamento de backups:** Agende backups diários para seus contêineres.
*   **Gerenciamento de backups:** Visualize e exclua backups existentes.

## 🚀 Pré-requisitos

*   [Python 3](https://www.python.org/downloads/)
*   [Docker](https://docs.docker.com/get-docker/)
*   [Git](https://git-scm.com/downloads)

## ⚙️ Como Usar

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/gerenciador-de-backups.git
    cd gerenciador-de-backups
    ```

2.  **Crie um ambiente virtual:**

    ```bash
    python -m venv venv
    ```

3.  **Ative o ambiente virtual:**

    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```

4.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Crie um arquivo `.env`:**

    Crie um arquivo chamado `.env` na raiz do projeto e adicione a seguinte linha:

    ```
    SECRET_KEY='uma-chave-secreta-bem-segura'
    ```

6.  **Execute a aplicação:**

    ```bash
    python run.py
    ```

    A aplicação estará disponível em `http://127.0.0.1:5003`.

## 💻 Como Utilizar a Interface Web

1.  **Painel Principal:**
    *   A página inicial exibe uma lista de contêineres de banco de dados ativos.
    *   Você também verá uma lista de backups existentes e agendamentos de backup.

2.  **Criar um Backup:**
    *   Na lista de contêineres, clique no botão "Fazer Backup" ao lado do contêiner desejado.
    *   O backup será criado e aparecerá na lista de backups.

3.  **Agendar um Backup:**
    *   Na seção "Agendar Backup", selecione o contêiner e a hora desejada.
    *   Clique em "Agendar" e o backup será agendado para ser executado diariamente no horário especificado.

4.  **Restaurar um Backup:**
    *   Na lista de backups, clique no botão "Restaurar".
    *   Selecione o contêiner de destino e clique em "Restaurar".

5.  **Excluir um Backup:**
    *   Na lista de backups, clique no botão "Excluir" ao lado do backup que deseja remover.

6.  **Excluir um Agendamento:**
    *   Na lista de agendamentos, clique no botão "Excluir" ao lado do agendamento que deseja remover.

## 🛠️ Tecnologias Utilizadas

*   [Flask](https://flask.palletsprojects.com/)
*   [Docker SDK for Python](https://docker-py.readthedocs.io/)
*   [APScheduler](https://apscheduler.readthedocs.io/)
*   [Bootstrap](https://getbootstrap.com/)
*   [Jinja2](https://jinja.palletsprojects.com/)
