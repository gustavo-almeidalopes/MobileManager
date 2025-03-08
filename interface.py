import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import subprocess
from docx import Document
from tema import DarkTheme
from database import criar_tabela, conectar_db

class SistemaCelulares:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'database')
        os.makedirs(self.db_path, exist_ok=True)

        self.conn = conectar_db(self.db_path)
        if not self.conn:
            return

        criar_tabela(self.conn)

        self.root = tk.Tk()
        self.root.title("Gestão de Celulares Corporativos")
        self.root.geometry("1200x600")
        self.dark_mode = False

        self.style = ttk.Style()
        DarkTheme.apply_light_theme(self.root)

        self.criar_interface()
        self.carregar_dados()
        self.root.mainloop()

    def criar_interface(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Botões principais
        ttk.Button(toolbar, text="Novo", command=self.novo_celular).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Editar", command=self.editar_celular).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Excluir", command=self.excluir_celular).pack(side=tk.LEFT, padx=2)

        # Campo de pesquisa
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

        # Árvore de dados
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ('ID', 'Usuário', 'Matrícula', 'Status', 'IMEI 1', 'IMEI 2', 'Número Chip', 'Serial')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', selectmode="browse")

        col_widths = [50, 150, 100, 100, 150, 150, 100, 150]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.abrir_termo)

        scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.tag_configure('evenrow', background='#f0f0f0')
        self.tree.tag_configure('oddrow', background='white')

    def limpar_pesquisa(self):
        self.entry_pesquisa.delete(0, tk.END)
        self.combo_status.set('Todos')
        self.carregar_dados()

    def carregar_dados(self):
        self.tree.delete(*self.tree.get_children())
        try:
            termo = self.entry_pesquisa.get().strip().lower()
            status = self.combo_status.get()

            # Construção dinâmica da query
            query_base = '''
                SELECT id, usuario, matricula, status, imei1, imei2, numero_chip, serial
                FROM celulares
                WHERE (LOWER(usuario) LIKE ? OR 
                      LOWER(matricula) LIKE ? OR 
                      LOWER(imei1) LIKE ? OR 
                      LOWER(imei2) LIKE ? OR 
                      LOWER(numero_chip) LIKE ? OR 
                      LOWER(serial) LIKE ?)
            '''
            params = [f'%{termo}%'] * 6

            # Adicionar filtro de status se necessário
            if status != 'Todos':
                query_base += ' AND status = ?'
                params.append(status)

            cursor = self.conn.execute(query_base, params)

            for i, row in enumerate(cursor.fetchall()):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert('', tk.END, values=row, tags=(tag,))
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")

    def abrir_termo(self, event):
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
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")

    def janela_formulario(self, titulo, comando_salvar, item=None):
        janela = tk.Toplevel(self.root)
        janela.title(titulo)
        janela.geometry("500x600")

        janela.config(bg='#2d2d2d' if self.dark_mode else '#f0f0f0')
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
            ('Observações', 'observacoes', 'text'),
            ('Termo', 'caminho_termo', 'file')
        ]

        entries = {}
        for i, (label, key, tipo, *opcoes) in enumerate(campos):
            row = ttk.Frame(main_frame)
            row.grid(row=i, column=0, sticky=tk.EW, pady=2)

            lbl = ttk.Label(row, text=label + ":", width=15)
            lbl.grid(row=0, column=0, sticky=tk.W)

            if tipo == 'entry':
                entry = ttk.Entry(row)
                entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = entry

            elif tipo == 'combobox':
                cb = ttk.Combobox(row, values=opcoes[0])
                cb.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = cb

            elif tipo == 'text':
                text = tk.Text(row, height=4)
                text.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = text

            elif tipo == 'file':
                btn = ttk.Button(row, text="Selecionar",
                                command=lambda k=key: self.selecionar_arquivo(entries[k]))
                btn.grid(row=0, column=2, padx=5)
                entry_file = ttk.Entry(row)
                entry_file.grid(row=0, column=1, sticky=tk.EW, padx=5)
                entries[key] = entry_file

            row.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=len(campos)+1, column=0, pady=10)

        ttk.Button(btn_frame, text="Cancelar", command=janela.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Salvar",
                 command=lambda: comando_salvar(janela, entries, item)).pack(side=tk.RIGHT, padx=5)

        if item:
            valores = self.tree.item(item, 'values')
            try:
                cursor = self.conn.execute('SELECT * FROM celulares WHERE id = ?', (valores[0],))
                dados = dict(zip(
                    ['id', 'usuario', 'matricula', 'status', 'imei1', 'imei2', 'numero_chip',
                     'serial', 'observacoes', 'caminho_termo'],
                    cursor.fetchone()
                ))
                for key, widget in entries.items():
                    if key == 'observacoes':
                        widget.insert('1.0', dados.get(key, ''))
                    else:
                        widget.insert(0, dados.get(key, ''))
            except sqlite3.Error as e:
                messagebox.showerror("Erro", f"Erro ao recuperar dados: {e}")

        main_frame.columnconfigure(0, weight=1)
        self.atualizar_cores_janela(janela)

    def selecionar_arquivo(self, entry):
        arquivo = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx"), ("All files", "*.*")])
        if arquivo:
            entry.delete(0, tk.END)
            entry.insert(0, arquivo)

    def novo_celular(self):
        self.janela_formulario("Novo Celular", self.salvar_novo)

    def editar_celular(self):
        try:
            item = self.tree.selection()[0]
            self.janela_formulario("Editar Celular", self.salvar_edicao, item)
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um registro para editar")

    def excluir_celular(self):
        try:
            item = self.tree.selection()[0]
            id_registro = self.tree.item(item, 'values')[0]

            if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
                self.conn.execute('DELETE FROM celulares WHERE id = ?', (id_registro,))
                self.conn.commit()
                self.carregar_dados()
        except IndexError:
            messagebox.showwarning("Aviso", "Selecione um registro para excluir")

    def salvar_novo(self, janela, entries, _):
        try:
            dados = [
                entries['usuario'].get(),
                entries['matricula'].get(),
                entries['status'].get(),
                entries['imei1'].get(),
                entries['imei2'].get(),
                entries['numero_chip'].get(),
                entries['serial'].get(),
                entries['observacoes'].get('1.0', tk.END).strip(),
                entries['caminho_termo'].get()
            ]

            self.conn.execute('''
                INSERT INTO celulares (
                    usuario, matricula, status, imei1, imei2, numero_chip, serial, observacoes, caminho_termo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', dados)

            self.conn.commit()
            self.carregar_dados()
            janela.destroy()
            messagebox.showinfo("Sucesso", "Registro adicionado com sucesso!")

        except sqlite3.IntegrityError as e:
            messagebox.showerror("Erro", f"Dados duplicados ou inválidos: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao inserir: {str(e)}")

    def salvar_edicao(self, janela, entries, item):
        try:
            dados = [
                entries['usuario'].get(),
                entries['matricula'].get(),
                entries['status'].get(),
                entries['imei1'].get(),
                entries['imei2'].get(),
                entries['numero_chip'].get(),
                entries['serial'].get(),
                entries['observacoes'].get('1.0', tk.END).strip(),
                entries['caminho_termo'].get(),
                self.tree.item(item, 'values')[0]
            ]

            self.conn.execute('''
                UPDATE celulares SET
                    usuario = ?,
                    matricula = ?,
                    status = ?,
                    imei1 = ?,
                    imei2 = ?,
                    numero_chip = ?,
                    serial = ?,
                    observacoes = ?,
                    caminho_termo = ?
                WHERE id = ?
            ''', dados)

            self.conn.commit()
            self.carregar_dados()
            janela.destroy()
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao atualizar: {str(e)}")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            DarkTheme.apply_dark_theme(self.root)
        else:
            DarkTheme.apply_light_theme(self.root)
        self.atualizar_cores_treeview()

    def atualizar_cores_treeview(self):
        if self.dark_mode:
            self.tree.tag_configure('evenrow', background='#404040', foreground='white')
            self.tree.tag_configure('oddrow', background='#2d2d2d', foreground='white')
        else:
            self.tree.tag_configure('evenrow', background='#f0f0f0', foreground='black')
            self.tree.tag_configure('oddrow', background='white', foreground='black')
        
        for item in self.tree.get_children():
            index = self.tree.index(item)
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.item(item, tags=(tag,))

    def atualizar_cores_janela(self, janela):
        if self.dark_mode:
            janela.configure(bg='#2d2d2d')
            for widget in janela.winfo_children():
                if isinstance(widget, ttk.Frame):
                    widget.configure(style='TFrame')
                elif isinstance(widget, ttk.Label):
                    widget.configure(style='TLabel')
                elif isinstance(widget, ttk.Button):
                    widget.configure(style='TButton')
                elif isinstance(widget, ttk.Entry):
                    widget.configure(style='TEntry')
                elif isinstance(widget, ttk.Combobox):
                    widget.configure(style='TCombobox')
                elif isinstance(widget, tk.Text):
                    widget.configure(bg='#404040', fg='white')
        else:
            janela.configure(bg='#f0f0f0')
            for widget in janela.winfo_children():
                if isinstance(widget, ttk.Frame):
                    widget.configure(style='TFrame')
                elif isinstance(widget, ttk.Label):
                    widget.configure(style='TLabel')
                elif isinstance(widget, ttk.Button):
                    widget.configure(style='TButton')
                elif isinstance(widget, ttk.Entry):
                    widget.configure(style='TEntry')
                elif isinstance(widget, ttk.Combobox):
                    widget.configure(style='TCombobox')
                elif isinstance(widget, tk.Text):
                    widget.configure(bg='white', fg='black')

if __name__ == "__main__":
    SistemaCelulares()