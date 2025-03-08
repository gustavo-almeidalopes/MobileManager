# Gestão de Celulares Corporativos

## Descrição

Este é um sistema de gestão de celulares corporativos desenvolvido em Python com Tkinter para a interface gráfica e SQLite para o banco de dados. Ele permite o cadastro, edição, exclusão e pesquisa de informações sobre os celulares da empresa, como usuário, matrícula, status, IMEI, número do chip, serial, observações e termo de responsabilidade.

## Funcionalidades

*   **Cadastro de celulares:** Permite adicionar novos celulares ao sistema, incluindo informações como usuário, matrícula, status (ativo, inativo, manutenção), IMEI 1 e 2, número do chip, serial, observações e caminho para o termo de responsabilidade.
*   **Edição de celulares:** Permite modificar as informações de um celular já cadastrado.
*   **Exclusão de celulares:** Permite remover um celular do sistema.
*   **Pesquisa:** Permite buscar celulares por diversos critérios, como usuário, matrícula, IMEI, número do chip, serial ou status.
*   **Modo escuro:** Permite alternar entre os modos claro e escuro da interface.
*   **Abertura do termo de responsabilidade:** Permite abrir o arquivo do termo de responsabilidade associado a um celular, caso ele exista.

## Pré-requisitos

*   Python 3.x
*   Bibliotecas:
    *   `tkinter`
    *   `ttk` (já incluso no tkinter)
    *   `sqlite3`
    *   `os`
    *   `subprocess`
    *   `docx` (para manipulação de arquivos Word, caso necessário)

## Instalação

1.  Clone o repositório para sua máquina local:

    ```
    git clone <URL_DO_REPOSITORIO>
    cd <nome_do_repositorio>
    ```

2.  Certifique-se de ter todas as dependências instaladas. Você pode usar o pip para instalar as bibliotecas necessárias:

    ```
    pip install tk docx
    ```

## Execução

1.  **Inicialização:**

    *   O script `interface.py` é o ponto de entrada.
    *   Cria uma instância da classe `SistemaCelulares`.
    *   Define o diretório do banco de dados (`database`).
    *   Conecta ao banco de dados SQLite (`celulares.db`) usando a função `conectar_db` do arquivo `database.py`.
    *   Cria a tabela `celulares` no banco de dados, se ela não existir, utilizando a função `criar_tabela` do arquivo `database.py`.
    *   Inicializa a interface gráfica com Tkinter.
    *   Define o tema inicial (claro) e cria os elementos da interface (botões, campos de pesquisa, treeview).
    *   Carrega os dados do banco de dados na treeview.
    *   Inicia o loop principal do Tkinter para manter a janela aberta e responsiva.

2.  **Interface Gráfica:**

    *   A interface é construída usando widgets do Tkinter e ttk (Themed Tkinter).
    *   Possui uma barra de ferramentas com botões para "Novo", "Editar", "Excluir", "Pesquisar", "Limpar" e "Modo Escuro".
    *   Utiliza um `Combobox` para filtrar por status ("Ativo", "Inativo", "Manutenção").
    *   Utiliza um campo de entrada (`Entry`) para pesquisar por texto livre.
    *   Exibe os dados em uma `Treeview` (tabela) com scrollbar vertical.
    *   Permite alternar entre os modos claro e escuro, aplicando temas definidos nas classes `DarkTheme` e `LightTheme` do arquivo `tema.py`.

3.  **Interação com o Banco de Dados:**

    *   As funções para conectar e criar a tabela estão no arquivo `database.py`.
    *   A classe `SistemaCelulares` contém métodos para:
        *   `carregar_dados`: Carrega os dados do banco de dados na treeview, aplicando filtros de pesquisa se necessário.
        *   `novo_celular`: Abre uma janela de formulário para adicionar um novo celular.
        *   `editar_celular`: Abre uma janela de formulário para editar um celular existente.
        *   `excluir_celular`: Exclui o celular selecionado do banco de dados.
        *   `salvar_novo`: Salva os dados de um novo celular no banco de dados.
        *   `salvar_edicao`: Salva as alterações de um celular existente no banco de dados.

4.  **Formulários:**

    *   As janelas de formulário para adicionar e editar celulares são criadas dinamicamente pelo método `janela_formulario`.
    *   Os formulários possuem campos de entrada para usuário, matrícula, status, IMEI 1 e 2, número do chip, serial, observações e termo de responsabilidade.
    *   Utilizam um `Combobox` para o campo de status.
    *   Permitem selecionar um arquivo para o termo de responsabilidade.

5.  **Modo Escuro:**

    *   O método `toggle_dark_mode` alterna entre os modos claro e escuro.
    *   Aplica os temas definidos nas classes `DarkTheme` e `LightTheme` do arquivo `tema.py`.
    *   Atualiza as cores da treeview e das janelas de formulário.

6.  **Arquivos Principais:**

    *   `interface.py`: Contém a classe `SistemaCelulares`, que define a interface gráfica e a lógica de interação com o banco de dados.
    *   `database.py`: Contém as funções para conectar ao banco de dados SQLite e criar a tabela `celulares`.
    *   `tema.py`: Contém as classes `DarkTheme` e `LightTheme` para aplicar os temas claro e escuro à interface.
