import os
import re
import sqlite3
import subprocess
import logging
from http.server import BaseHTTPRequestHandler

# --- GUI (Tkinter) ---
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Email ---
import smtplib
from email.mime.text import MIMEText

# --- Google Auth ---
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# --- Módulos locais ---
from tema import DarkTheme
from database import (
    conectar_db,
    criar_tabela,
    criar_admin_inicial,
    autenticar_usuario,
    autenticar_google,
    hash_password,
    validar_senha
)

# Configurações de e-mail (substitua pelos seus dados)

EMAIL_SENDER = "gustavo13.roberto@gmail.com"
EMAIL_PASSWORD = "rS)jFRztXBzF(YQTuRam!Zyk]k$IUT}$S[f)2LtB6Z'Ol5O^tg"

# Configuração de logging para depuração
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class AutoCloseFlow(InstalledAppFlow):
    """Subclasse de InstalledAppFlow que fecha automaticamente a janela do navegador após autenticação."""
    def run_local_server(self, *args, **kwargs):
        kwargs['handler'] = self._create_auto_close_handler()
        return super().run_local_server(*args, **kwargs)

    def _create_auto_close_handler(self):
        class AutoCloseHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.server.path = self.path
                if 'code=' in self.path:
                    self.server.authorization_code = self.path.split('code=')[1].split('&')[0]
                else:
                    self.server.authorization_code = None
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><script>window.close();</script></body></html>')
                self.server.shutdown()
        return AutoCloseHandler


class SistemaCelulares:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'database')
        self.conn = conectar_db(self.db_path)
        if not self.conn:
            return

        criar_tabela(self.conn)
        criar_admin_inicial(self.db_path)

        self.root = tk.Tk()
        self.root.title("Login - Gestão de Celulares Corporativos")
        self.root.geometry("400x400")
        self.dark_mode = False
        DarkTheme.apply_light_theme(self.root)
        self.nivel_acesso = None
        self.username = None

        self.criar_login()
        self.root.mainloop()

    def enviar_email_verificacao(self, email, username):
        """Envia um e-mail de verificação."""
        try:
            msg = MIMEText(
                f"Olá {username},\n\nSua conta foi criada. Use este link para verificar: http://exemplo.com/verify/{username}",
                'plain', 'utf-8'
            )
            msg['Subject'] = "Verificação de Conta"
            msg['From'] = EMAIL_SENDER
            msg['To'] = email

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, email, msg.as_string())
            logging.info(f"E-mail de verificação enviado para {email}")
            return True
        except Exception as e:
            logging.error(f"Falha ao enviar e-mail para {email}: {e}")
            messagebox.showerror("Erro", f"Falha ao enviar e-mail: {e}")
            return False

    def criar_login(self):
        """Cria a interface de login."""
        login_frame = ttk.Frame(self.root)
        login_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        ttk.Label(login_frame, text="Usuário ou E-mail:").pack(pady=5)
        self.entry_usuario = ttk.Entry(login_frame)
        self.entry_usuario.pack(pady=5, fill=tk.X)

        ttk.Label(login_frame, text="Senha:").pack(pady=5)
        self.entry_senha = ttk.Entry(login_frame, show="*")
        self.entry_senha.pack(pady=5, fill=tk.X)

        ttk.Button(login_frame, text="Entrar", command=self.verificar_login).pack(pady=10)
        ttk.Button(login_frame, text="Entrar com Google", command=self.login_google).pack(pady=5)
        ttk.Button(login_frame, text="Criar Conta", command=self.criar_conta).pack(pady=5)
        self.entry_senha.bind('<Return>', lambda event: self.verificar_login())

    def verificar_login(self):
        """Verifica as credenciais de login."""
        username = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()
        if not username or not senha:
            messagebox.showerror("Erro", "Usuário e senha são obrigatórios!")
            return

        nivel_acesso = autenticar_usuario(self.conn, username, senha)
        if nivel_acesso:
            self.nivel_acesso = nivel_acesso
            self.username = username
            self.abrir_interface_principal()
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos!")

    def login_google(self):
        """Realiza login com Google."""
        try:
            scopes = [
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ]
            client_secrets_path = 'client_secrets.json'  # Ajuste o caminho conforme necessário

            flow = AutoCloseFlow.from_client_secrets_file(client_secrets_path, scopes)
            creds = flow.run_local_server(
                port=8000,
                host='localhost',
                open_browser=True,
                authorization_prompt_message='Por favor, faça login no navegador.'
            )

            email = creds.id_token.get('email') if creds.id_token else None
            if not email:
                raise ValueError("Não foi possível obter o e-mail da conta Google.")

            cursor = self.conn.cursor()
            cursor.execute('SELECT nivel_acesso FROM usuarios WHERE email = ? AND verificado = 1', (email,))
            result = cursor.fetchone()

            if result:
                self.nivel_acesso = result[0]
                self.username = email
                logging.info(f"Usuário existente encontrado: {email}, nível de acesso: {self.nivel_acesso}")
                self.abrir_interface_principal()
            else:
                logging.info(f"Criando novo usuário para {email}...")
                cursor.execute('''
                    INSERT INTO usuarios (username, email, google_token, nivel_acesso, verificado)
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, email, creds.token, 1, 1))
                self.conn.commit()
                self.nivel_acesso = 1
                self.username = email
                logging.info(f"Novo usuário criado: {email}, nível de acesso: 1")
                self.abrir_interface_principal()

        except Exception as e:
            logging.error(f"Falha no login com Google: {e}")
            messagebox.showerror("Erro", f"Falha no login com Google: {e}")

    def abrir_interface_principal(self):
        """Abre a interface principal do sistema."""
        self.root.destroy()
        self.root = tk.Tk()
        self.root.title(f"Gestão de Celulares Corporativos - {self.username} (Nível {self.nivel_acesso})")
        self.root.geometry("1200x600")
        if self.dark_mode:
            DarkTheme.apply_dark_theme(self.root)
        else:
            DarkTheme.apply_light_theme(self.root)
        self.criar_interface()

    def criar_interface(self):
        """Cria a interface principal."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Novo", command=self.novo_celular).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Editar", command=self.editar_celular).pack(side=tk.LEFT, padx=2)
        if self.nivel_acesso >= 2:
            ttk.Button(toolbar, text="Excluir", command=self.excluir_celular).pack(side=tk.LEFT, padx=2)
        if self.nivel_acesso == 3:
            ttk.Button(toolbar, text="Gerenciar Usuários", command=self.gerenciar_usuarios).pack(side=tk.LEFT, padx=2)

        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT, padx=5)

        self.combo_status = ttk.Combobox(search_frame, values=['Todos', 'Ativo', 'Inativo', 'Manutenção'], width=12)
        self.combo_status.pack(side=tk.LEFT, padx=2)
        self.combo_status.set('Todos')

        self.entry_pesquisa = ttk.Entry(search_frame, width=25)
        self.entry_pesquisa.pack(side=tk.LEFT, padx=2)
        self.entry_pesquisa.bind('<Return>', lambda event: self.carregar_dados())

        ttk.Button(search_frame, text="Pesquisar", command=self.carregar_dados).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="Limpar", command=self.limpar_pesquisa).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Modo Escuro", command=self.toggle_dark_mode).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Logout", command=self.logout).pack(side=tk.RIGHT, padx=2)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ('ID', 'Usuário', 'Matrícula', 'Status', 'IMEI 1', 'IMEI 2', 'Número Chip', 'Serial', 'Modelo')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', selectmode="browse")

        col_widths = [50, 150, 100, 100, 150, 150, 100, 150, 150]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.abrir_termo)

        scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        self.atualizar_cores_treeview()
        self.carregar_dados()

    def logout(self):
        """Realiza logout e reinicia a aplicação."""
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.Error as e:
            logging.error(f"Erro ao fechar conexão: {e}")
        self.root.destroy()
        self.__init__()

    def limpar_pesquisa(self):
        """Limpa os campos de pesquisa."""
        self.entry_pesquisa.delete(0, tk.END)
        self.combo_status.set('Todos')
        self.carregar_dados()

    def carregar_dados(self):
        """Carrega os dados na tabela."""
        self.tree.delete(*self.tree.get_children())
        try:
            termo = self.entry_pesquisa.get().strip().lower()
            status = self.combo_status.get()

            query = '''
                SELECT id, usuario, matricula, status, imei1, imei2, numero_chip, serial, modelo
                FROM celulares
                WHERE (LOWER(usuario) LIKE ? OR 
                       LOWER(matricula) LIKE ? OR 
                       LOWER(imei1) LIKE ? OR 
                       LOWER(imei2) LIKE ? OR 
                       LOWER(numero_chip) LIKE ? OR 
                       LOWER(serial) LIKE ? OR 
                       LOWER(modelo) LIKE ?)
            '''
            params = [f'%{termo}%'] * 7

            if status != 'Todos':
                query += ' AND status = ?'
                params.append(status)

            cursor = self.conn.execute(query, params)
            for i, row in enumerate(cursor.fetchall()):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert('', tk.END, values=row, tags=(tag,))
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")

    def abrir_termo(self, event):
        """Abre o arquivo do termo associado ao registro selecionado."""
        if self.nivel_acesso < 1:
            messagebox.showwarning("Acesso Negado", "Você não tem permissão para abrir termos.")
            return
        try:
            item = self.tree.selection()[0]
            matricula = self.tree.item(item, 'values')[2]

            cursor = self.conn.execute('SELECT caminho_termo FROM celulares WHERE matricula = ?', (matricula,))
            caminho = cursor.fetchone()[0]

            if caminho and os.path.exists(caminho):
                if os.name == 'nt':
                    os.startfile(caminho)
                else:
                    subprocess.run(['xdg-open', caminho], check=True)
            else:
                messagebox.showerror("Erro", "Arquivo do termo não encontrado!")
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um registro na tabela para abrir o termo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    def janela_formulario(self, titulo, comando_salvar, item=None):
        """Cria janela de formulário para novo/editar celular."""
        if self.nivel_acesso < 1:
            messagebox.showwarning("Acesso Negado", "Você não tem permissão para editar registros.")
            return

        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.geometry("500x700")
        janela.transient(self.root)
        janela.grab_set()

        main_frame = ttk.Frame(janela)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        campos = [
            ('Usuário', 'usuario', 'entry'),
            ('Matrícula', 'matricula', 'entry'),
            ('Status', 'status', 'combobox', ['Ativo', 'Inativo', 'Manutenção']),
            ('IMEI 1', 'imei1', 'entry'),
            ('IMEI 2', 'imei2', 'entry'),
            ('Número do Chip', 'numero_chip', 'entry'),
            ('Serial', 'serial', 'entry'),
            ('Modelo', 'modelo', 'entry'),
            ('Observações', 'observacoes', 'text'),
            ('Termo', 'caminho_termo', 'file')
        ]

        entries = {}
        for i, (label, key, tipo, *opcoes) in enumerate(campos):
            row = ttk.Frame(main_frame)
            row.grid(row=i, column=0, sticky=tk.EW, pady=2)

            ttk.Label(row, text=label + ":", width=15).grid(row=0, column=0, sticky=tk.W)

            if tipo == 'entry':
                entry = ttk.Entry(row)
                entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = entry

            elif tipo == 'combobox':
                cb = ttk.Combobox(row, values=opcoes[0], state='readonly')
                cb.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = cb

            elif tipo == 'text':
                text = tk.Text(row, height=4)
                text.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = text

            elif tipo == 'file':
                entry_file = ttk.Entry(row)
                entry_file.grid(row=0, column=1, sticky=tk.EW, padx=5)
                ttk.Button(row, text="Selecionar",
                           command=lambda k=key: self.selecionar_arquivo(entries[k])).grid(row=0, column=2, padx=5)
                entries[key] = entry_file

            row.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=len(campos), column=0, pady=10)

        ttk.Button(btn_frame, text="Cancelar", command=janela.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Salvar",
                   command=lambda: comando_salvar(janela, entries, item)).pack(side=tk.RIGHT, padx=5)

        if item:
            valores = self.tree.item(item, 'values')
            try:
                cursor = self.conn.execute('SELECT * FROM celulares WHERE id = ?', (valores[0],))
                dados = dict(zip(
                    ['id', 'usuario', 'matricula', 'status', 'imei1', 'imei2', 'numero_chip',
                     'serial', 'modelo', 'observacoes', 'caminho_termo'],
                    cursor.fetchone()
                ))
                for key, widget in entries.items():
                    value = dados.get(key, '')
                    if key == 'observacoes' and value:
                        widget.insert('1.0', value)
                    elif value:
                        widget.insert(0, value)
            except sqlite3.Error as e:
                messagebox.showerror("Erro", f"Erro ao recuperar dados: {e}")
                janela.destroy()

        main_frame.columnconfigure(0, weight=1)
        self.atualizar_cores_janela(janela)

    def selecionar_arquivo(self, entry):
        """Seleciona um arquivo para o campo de termo."""
        arquivo = filedialog.askopenfilename(filetypes=[("Documentos", "*.docx;*.pdf"), ("Todos os arquivos", "*.*")])
        if arquivo:
            entry.delete(0, tk.END)
            entry.insert(0, arquivo)

    def novo_celular(self):
        """Abre formulário para novo celular."""
        self.janela_formulario("Novo Celular", self.salvar_novo)

    def editar_celular(self):
        """Abre formulário para editar celular selecionado."""
        try:
            item = self.tree.selection()[0]
            self.janela_formulario("Editar Celular", self.salvar_edicao, item)
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um registro para editar")

    def excluir_celular(self):
        """Exclui o celular selecionado."""
        if self.nivel_acesso < 2:
            messagebox.showwarning("Acesso Negado", "Você não tem permissão para excluir registros.")
            return
        try:
            item = self.tree.selection()[0]
            id_registro = self.tree.item(item, 'values')[0]

            if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
                self.conn.execute('DELETE FROM celulares WHERE id = ?', (id_registro,))
                self.conn.commit()
                self.carregar_dados()
                messagebox.showinfo("Sucesso", "Registro excluído com sucesso!")
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um registro para excluir")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao excluir registro: {e}")

    def salvar_novo(self, janela, entries, _):
        """Salva um novo registro de celular."""
        try:
            dados = [
                entries['usuario'].get().strip(),
                entries['matricula'].get().strip(),
                entries['status'].get(),
                entries['imei1'].get().strip(),
                entries['imei2'].get().strip(),
                entries['numero_chip'].get().strip(),
                entries['serial'].get().strip(),
                entries['modelo'].get().strip(),
                entries['observacoes'].get('1.0', tk.END).strip(),
                entries['caminho_termo'].get().strip()
            ]

            if not all([dados[0], dados[1], dados[2], dados[3], dados[6], dados[7]]):
                messagebox.showerror("Erro", "Campos obrigatórios: Usuário, Matrícula, Status, IMEI 1, Serial, Modelo")
                return

            self.conn.execute('''
                INSERT INTO celulares (
                    usuario, matricula, status, imei1, imei2, numero_chip, serial, modelo, observacoes, caminho_termo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', dados)
            self.conn.commit()
            self.carregar_dados()
            janela.destroy()
            messagebox.showinfo("Sucesso", "Registro adicionado com sucesso!")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Erro", f"Dados duplicados ou inválidos: {e}")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao inserir registro: {e}")

    def salvar_edicao(self, janela, entries, item):
        """Salva a edição de um registro de celular."""
        try:
            dados = [
                entries['usuario'].get().strip(),
                entries['matricula'].get().strip(),
                entries['status'].get(),
                entries['imei1'].get().strip(),
                entries['imei2'].get().strip(),
                entries['numero_chip'].get().strip(),
                entries['serial'].get().strip(),
                entries['modelo'].get().strip(),
                entries['observacoes'].get('1.0', tk.END).strip(),
                entries['caminho_termo'].get().strip(),
                self.tree.item(item, 'values')[0]
            ]

            if not all([dados[0], dados[1], dados[2], dados[3], dados[6], dados[7]]):
                messagebox.showerror("Erro", "Campos obrigatórios: Usuário, Matrícula, Status, IMEI 1, Serial, Modelo")
                return

            self.conn.execute('''
                UPDATE celulares SET
                    usuario = ?, matricula = ?, status = ?, imei1 = ?, imei2 = ?,
                    numero_chip = ?, serial = ?, modelo = ?, observacoes = ?, caminho_termo = ?
                WHERE id = ?
            ''', dados)
            self.conn.commit()
            self.carregar_dados()
            janela.destroy()
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Erro", f"Dados duplicados ou inválidos: {e}")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao atualizar registro: {e}")

    def gerenciar_usuarios(self):
        """Abre janela para gerenciamento de usuários."""
        if self.nivel_acesso < 3:
            messagebox.showwarning("Acesso Negado", "Apenas administradores podem gerenciar usuários.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Gerenciar Usuários")
        janela.geometry("600x400")
        janela.transient(self.root)
        janela.grab_set()

        toolbar = ttk.Frame(janela)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text="Novo Usuário", command=self.novo_usuario).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Editar Usuário", command=self.editar_usuario).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Excluir Usuário", command=self.excluir_usuario).pack(side=tk.LEFT, padx=2)

        columns = ('ID', 'Usuário', 'E-mail', 'Nível de Acesso', 'Verificado')
        self.tree_usuarios = ttk.Treeview(janela, columns=columns, show='headings', selectmode='browse')
        self.tree_usuarios.heading('ID', text='ID')
        self.tree_usuarios.heading('Usuário', text='Usuário')
        self.tree_usuarios.heading('E-mail', text='E-mail')
        self.tree_usuarios.heading('Nível de Acesso', text='Nível de Acesso')
        self.tree_usuarios.heading('Verificado', text='Verificado')
        self.tree_usuarios.column('ID', width=50)
        self.tree_usuarios.column('Usuário', width=150)
        self.tree_usuarios.column('E-mail', width=200)
        self.tree_usuarios.column('Nível de Acesso', width=100)
        self.tree_usuarios.column('Verificado', width=100)
        self.tree_usuarios.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        try:
            cursor = self.conn.execute('SELECT id, username, email, nivel_acesso, verificado FROM usuarios')
            for i, row in enumerate(cursor.fetchall()):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree_usuarios.insert('', tk.END, values=row, tags=(tag,))
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {e}")

        self.atualizar_cores_treeview(treeview=self.tree_usuarios)
        self.atualizar_cores_janela(janela)

    def novo_usuario(self):
        """Abre formulário para novo usuário."""
        self.janela_usuario("Novo Usuário", self.salvar_novo_usuario)

    def editar_usuario(self):
        """Abre formulário para editar usuário selecionado."""
        try:
            item = self.tree_usuarios.selection()[0]
            self.janela_usuario("Editar Usuário", self.salvar_edicao_usuario, item)
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um usuário para editar")

    def excluir_usuario(self):
        """Exclui o usuário selecionado."""
        try:
            item = self.tree_usuarios.selection()[0]
            id_usuario = self.tree_usuarios.item(item, 'values')[0]
            username = self.tree_usuarios.item(item, 'values')[1]

            if username == self.username:
                messagebox.showerror("Erro", "Você não pode excluir sua própria conta!")
                return

            if messagebox.askyesno("Confirmar", f"Deseja excluir o usuário {username}?"):
                self.conn.execute('DELETE FROM usuarios WHERE id = ?', (id_usuario,))
                self.conn.commit()
                self.gerenciar_usuarios()
                messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um usuário para excluir")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao excluir usuário: {e}")

    def janela_usuario(self, titulo, comando_salvar, item=None):
        """Cria janela de formulário para novo/editar usuário."""
        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.geometry("400x400")
        janela.transient(self.root)
        janela.grab_set()

        main_frame = ttk.Frame(janela)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=5)
        entry_usuario = ttk.Entry(main_frame)
        entry_usuario.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="E-mail:").grid(row=1, column=0, sticky=tk.W, pady=5)
        entry_email = ttk.Entry(main_frame)
        entry_email.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="Senha:").grid(row=2, column=0, sticky=tk.W, pady=5)
        entry_senha = ttk.Entry(main_frame, show="*")
        entry_senha.grid(row=2, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="Nível de Acesso:").grid(row=3, column=0, sticky=tk.W, pady=5)
        combo_nivel = ttk.Combobox(main_frame, values=[1, 2, 3], state='readonly')
        combo_nivel.grid(row=3, column=1, sticky=tk.EW, pady=5)
        combo_nivel.set(1)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Cancelar", command=janela.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Salvar",
                   command=lambda: comando_salvar(janela, entry_usuario, entry_email, entry_senha, combo_nivel, item)).pack(side=tk.RIGHT, padx=5)

        if item:
            valores = self.tree_usuarios.item(item, 'values')
            entry_usuario.insert(0, valores[1])
            entry_email.insert(0, valores[2])
            combo_nivel.set(valores[3])

        main_frame.columnconfigure(1, weight=1)
        self.atualizar_cores_janela(janela)

    def salvar_novo_usuario(self, janela, entry_usuario, entry_email, entry_senha, combo_nivel, _):
        """Salva um novo usuário."""
        try:
            username = entry_usuario.get().strip()
            email = entry_email.get().strip()
            senha = entry_senha.get()
            nivel = combo_nivel.get()

            if not all([username, email, nivel]):
                messagebox.showerror("Erro", "Usuário, e-mail e nível de acesso são obrigatórios!")
                return

            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messagebox.showerror("Erro", "E-mail inválido!")
                return

            if not senha:
                messagebox.showerror("Erro", "A senha é obrigatória para novos usuários!")
                return

            valido, mensagem = validar_senha(senha)
            if not valido:
                messagebox.showerror("Erro", mensagem)
                return

            senha_hash = hash_password(senha)
            self.conn.execute('''
                INSERT INTO usuarios (username, email, password, nivel_acesso, verificado)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, senha_hash, int(nivel), 0))
            self.conn.commit()

            if self.enviar_email_verificacao(email, username):
                messagebox.showinfo("Sucesso", "Usuário criado! Verifique o e-mail para ativar.")
            else:
                messagebox.showwarning("Aviso", "Usuário criado, mas falha ao enviar e-mail.")
            self.gerenciar_usuarios()
            janela.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Usuário ou e-mail já existe!")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao criar usuário: {e}")

    def salvar_edicao_usuario(self, janela, entry_usuario, entry_email, entry_senha, combo_nivel, item):
        """Salva a edição de um usuário."""
        try:
            username = entry_usuario.get().strip()
            email = entry_email.get().strip()
            senha = entry_senha.get()
            nivel = combo_nivel.get()
            id_usuario = self.tree_usuarios.item(item, 'values')[0]

            if not all([username, email, nivel]):
                messagebox.showerror("Erro", "Usuário, e-mail e nível de acesso são obrigatórios!")
                return

            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messagebox.showerror("Erro", "E-mail inválido!")
                return

            if senha:
                valido, mensagem = validar_senha(senha)
                if not valido:
                    messagebox.showerror("Erro", mensagem)
                    return
                self.conn.execute('''
                    UPDATE usuarios SET username = ?, email = ?, password = ?, nivel_acesso = ?
                    WHERE id = ?
                ''', (username, email, hash_password(senha), int(nivel), id_usuario))
            else:
                self.conn.execute('''
                    UPDATE usuarios SET username = ?, email = ?, nivel_acesso = ?
                    WHERE id = ?
                ''', (username, email, int(nivel), id_usuario))

            self.conn.commit()
            self.gerenciar_usuarios()
            janela.destroy()
            messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Usuário ou e-mail já existe!")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao atualizar usuário: {e}")

    def criar_conta(self):
        """Abre janela para criar nova conta."""
        janela = tk.Toplevel(self.root)
        janela.title("Criar Conta")
        janela.geometry("400x400")
        janela.transient(self.root)
        janela.grab_set()

        main_frame = ttk.Frame(janela)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Usuário:").grid(row=0, column=0, sticky=tk.W, pady=5)
        entry_usuario = ttk.Entry(main_frame)
        entry_usuario.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="E-mail:").grid(row=1, column=0, sticky=tk.W, pady=5)
        entry_email = ttk.Entry(main_frame)
        entry_email.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="Senha:").grid(row=2, column=0, sticky=tk.W, pady=5)
        entry_senha = ttk.Entry(main_frame, show="*")
        entry_senha.grid(row=2, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="Confirmar Senha:").grid(row=3, column=0, sticky=tk.W, pady=5)
        entry_confirmar_senha = ttk.Entry(main_frame, show="*")
        entry_confirmar_senha.grid(row=3, column=1, sticky=tk.EW, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Cancelar", command=janela.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Criar",
                   command=lambda: self.salvar_nova_conta(janela, entry_usuario, entry_email, entry_senha, entry_confirmar_senha)).pack(side=tk.RIGHT, padx=5)

        main_frame.columnconfigure(1, weight=1)
        self.atualizar_cores_janela(janela)

    def salvar_nova_conta(self, janela, entry_usuario, entry_email, entry_senha, entry_confirmar_senha):
        """Salva uma nova conta de usuário."""
        try:
            username = entry_usuario.get().strip()
            email = entry_email.get().strip()
            senha = entry_senha.get()
            confirmar_senha = entry_confirmar_senha.get()

            if not all([username, email, senha]):
                messagebox.showerror("Erro", "Usuário, e-mail e senha são obrigatórios!")
                return

            if senha != confirmar_senha:
                messagebox.showerror("Erro", "As senhas não coincidem!")
                return

            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messagebox.showerror("Erro", "E-mail inválido!")
                return

            valido, mensagem = validar_senha(senha)
            if not valido:
                messagebox.showerror("Erro", mensagem)
                return

            senha_hash = hash_password(senha)
            self.conn.execute('''
                INSERT INTO usuarios (username, email, password, nivel_acesso, verificado)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, senha_hash, 1, 0))
            self.conn.commit()

            if self.enviar_email_verificacao(email, username):
                messagebox.showinfo("Sucesso", "Conta criada! Verifique seu e-mail para ativar.")
            else:
                messagebox.showwarning("Aviso", "Conta criada, mas falha ao enviar e-mail de verificação.")
            janela.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Usuário ou e-mail já existe!")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao criar conta: {e}")

    def toggle_dark_mode(self):
        """Alterna entre modo claro e escuro."""
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            DarkTheme.apply_dark_theme(self.root)
        else:
            DarkTheme.apply_light_theme(self.root)
        self.atualizar_cores_treeview()

    def atualizar_cores_treeview(self, treeview=None):
        """Atualiza as cores do Treeview."""
        tree = treeview if treeview else self.tree
        if self.dark_mode:
            tree.tag_configure('evenrow', background='#404040', foreground='white')
            tree.tag_configure('oddrow', background='#2d2d2d', foreground='white')
        else:
            tree.tag_configure('evenrow', background='#f0f0f0', foreground='black')
            tree.tag_configure('oddrow', background='white', foreground='black')

        for item in tree.get_children():
            index = tree.index(item)
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            tree.item(item, tags=(tag,))

    def atualizar_cores_janela(self, janela):
        """Atualiza as cores de uma janela."""
        if self.dark_mode:
            janela.configure(bg='#2d2d2d')
            style = ttk.Style()
            style.configure('TLabel', background='#2d2d2d', foreground='white')
            style.configure('TFrame', background='#2d2d2d')
            style.configure('TButton', background='#404040', foreground='white')
            style.configure('TEntry', fieldbackground='#404040', foreground='white')
            style.configure('TCombobox', fieldbackground='#404040', foreground='white')
            for widget in janela.winfo_children():
                if isinstance(widget, tk.Text):
                    widget.configure(bg='#404040', fg='white', insertbackground='white')
        else:
            janela.configure(bg='#f0f0f0')
            style = ttk.Style()
            style.configure('TLabel', background='#f0f0f0', foreground='black')
            style.configure('TFrame', background='#f0f0f0')
            style.configure('TButton', background='#f0f0f0', foreground='black')
            style.configure('TEntry', fieldbackground='white', foreground='black')
            style.configure('TCombobox', fieldbackground='white', foreground='black')
            for widget in janela.winfo_children():
                if isinstance(widget, tk.Text):
                    widget.configure(bg='white', fg='black', insertbackground='black')


if __name__ == "__main__":
    SistemaCelulares()
