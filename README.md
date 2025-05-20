# Gerenciador de Aparelhos Corporativos

Este projeto é um **sistema desktop em Python** que permite o gerenciamento de dispositivos corporativos:

* **Celulares**
* **Notebooks**
* **Chips SIM**

A interface gráfica é construída com **PyQt5**, e o **SQLAlchemy** é utilizado para persistência de dados em um banco SQLite local. Há também integração para associação e visualização de termos de uso em formatos **PDF** e **DOCX**.

---

## Funcionalidades Atuais

* **Cadastro, Edição e Exclusão** de aparelhos em cada categoria.
* **Filtros** por status e modelo (celulares e notebooks) ou operadora (chips SIM).
* **Logs de Ações:** Armazena operações (adicionar, editar, excluir) com timestamp e usuário.
* **Termos de Uso:** Associação automática de documentos PDF/DOCX a dispositivos conforme o modelo.

---

## Pré-requisitos

* Python 3.x
* Bibliotecas principais:

  * `PyQt5`
  * `sqlalchemy`
  * `docx` e `PyPDF2`

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/nome-do-repositorio.git
cd nome-do-repositorio

# Crie e ative um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python main.py
```

---

## Estrutura de Pastas

```text
├── main.py            # Ponto de entrada da aplicação
├── celulares.py       # Gestão de Celulares (PyQt5)
├── notebooks.py       # Gestão de Notebooks (PyQt5)
├── chips.py           # Gestão de Chips SIM (PyQt5)
├── database.py        # Modelos SQLAlchemy e setup SQLite
├── dialogs.py         # Diálogos de formulário para cada dispositivo
├── term_utils.py      # Utilitários para carregamento de termos PDF/DOCX
├── requirements.txt   # Lista de dependências
└── terms/             # Documentos de termos organizados por tipo
```

---

## Roadmap de Upgrades (Implementação Gradual)

1. **Filtros em Todas as Categorias**

   * Unificar e refinar lógica de filtragem em celulares, notebooks e chips SIM.
   * Adicionar filtros adicionais (datas de aquisição, departamento, usuário).
   * Melhorar performance das consultas para grandes volumes.

2. **Autenticação de Usuário**

   * Implementar login com **Google OAuth** e/ou **e‑mail e senha**.
   * Envio de código de verificação por e‑mail para confirmação de identidade.
   * Gestão de sessões e níveis de permissão (usuário comum vs. administrador).

3. **Integração com AWS Textract e Bucket S3**

   * Criar bucket S3 para armazenamento de documentos carregados.
   * Chamar API **AWS Textract** para extração de campos (nome, data, assinatura).
   * Exibir e validar dados extraídos na interface.

4. **Criação de Front‑end Web**

   * Desenvolver SPA (React/Vue/Angular) consumindo APIs REST/GraphQL do backend.
   * Interface responsiva para desktop e mobile.
   * Dashboards, gráficos de uso e sistema de notificações.

5. **Banco de Dados na AWS (Produção)**

   * Migrar para banco gerenciado (RDS MySQL/PostgreSQL ou DynamoDB).
   * Infraestrutura escalável e resiliente (Multi-AZ, backups automáticos).
   * Configurar conexão segura via variáveis de ambiente e roles IAM.

---

## Como Contribuir

1. Faça um *fork* do projeto.
2. Crie uma branch para sua feature:

   ```bash
   git checkout -b feature/nome-da-feature
   ```
3. Realize suas alterações e commit:

   ```bash
   git commit -m "Adiciona nova feature"
   ```
4. Envie para o repositório remoto:

   ```bash
   git push origin feature/nome-da-feature
   ```
5. Abra um Pull Request no GitHub.

---
