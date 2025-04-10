import sqlite3
import os
from tkinter import messagebox

def criar_tabela(conn):
    try:
        cursor = conn.cursor()
        
        # Tabela de celulares (mantida conforme sua versão)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS celulares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                matricula TEXT UNIQUE NOT NULL,
                status TEXT CHECK(status IN ('Ativo', 'Inativo', 'Manutenção')),
                imei1 TEXT UNIQUE NOT NULL,
                imei2 TEXT,
                numero_chip TEXT,
                serial TEXT UNIQUE NOT NULL,
                observacoes TEXT,
                caminho_termo TEXT
            );
        ''')
        
        # Nova tabela de usuários para login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nivel_acesso INTEGER DEFAULT 1
            );
        ''')
        
        conn.commit()
        
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao criar tabelas: {e}")
        raise  # Propaga o erro para tratamento externo

def conectar_db(db_path):
    try:
        # Cria o diretório se não existir
        os.makedirs(db_path, exist_ok=True)
        
        # Conecta ao banco de dados único
        conn = sqlite3.connect(os.path.join(db_path, 'sistema.db'))
        return conn
        
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {e}")
        raise  # Propaga o erro para tratamento externo

# Função auxiliar para criar o usuário admin inicial
def criar_admin(db_path):
    try:
        conn = conectar_db(db_path)
        cursor = conn.cursor()
        
        # Verifica se o admin já existe
        cursor.execute("SELECT username FROM usuarios WHERE username = 'admin'")
        if not cursor.fetchone():
            # Senha: "admin123" com hash SHA-256
            senha_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720ac"
            cursor.execute('''
                INSERT INTO usuarios (username, password, nivel_acesso)
                VALUES (?, ?, ?)
            ''', ('admin', senha_hash, 3))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Usuário admin criado com senha padrão!")
            
        conn.close()
        
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Falha ao criar admin: {e}")
