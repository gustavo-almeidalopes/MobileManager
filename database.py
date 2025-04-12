import sqlite3
import os
import bcrypt
import re
from tkinter import messagebox

# --- Validação e segurança ---

def validar_senha(senha):
    """Valida se a senha atende aos critérios de segurança."""
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    if not re.search(r'[0-9]', senha):
        return False, "A senha deve conter pelo menos um número."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return False, "A senha deve conter pelo menos um símbolo especial."
    return True, ""

def hash_password(password):
    """Gera hash bcrypt da senha."""
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Erro ao gerar hash da senha: {e}")

def verificar_senha(password, hashed):
    """Verifica se a senha corresponde ao hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        raise ValueError(f"Erro ao verificar senha: {e}")

# --- Conexão e estrutura do banco de dados ---

def conectar_db(db_path):
    """Conecta ao banco SQLite e cria diretório se necessário."""
    try:
        os.makedirs(db_path, exist_ok=True)
        conn = sqlite3.connect(os.path.join(db_path, 'sistema.db'))
        conn.execute("PRAGMA foreign_keys = ON")  # Habilita chaves estrangeiras
        return conn
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {e}")
        return None

def criar_tabela(conn):
    """Cria tabelas necessárias no banco de dados."""
    try:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS celulares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    matricula TEXT UNIQUE NOT NULL,
                    status TEXT CHECK(status IN ('Ativo', 'Inativo', 'Manutenção')) NOT NULL,
                    imei1 TEXT UNIQUE NOT NULL,
                    imei2 TEXT,
                    numero_chip TEXT,
                    serial TEXT UNIQUE NOT NULL,
                    modelo TEXT NOT NULL,
                    observacoes TEXT,
                    caminho_termo TEXT
                );
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT,
                    google_token TEXT,
                    nivel_acesso INTEGER NOT NULL CHECK(nivel_acesso IN (1, 2, 3)) DEFAULT 1,
                    verificado INTEGER NOT NULL CHECK(verificado IN (0, 1)) DEFAULT 0
                );
            ''')
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao criar tabelas: {e}")
        raise

def criar_admin_inicial(db_path):
    """Cria usuário admin padrão caso ainda não exista."""
    try:
        conn = conectar_db(db_path)
        if not conn:
            return
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM usuarios WHERE username = 'admin'")
            if not cursor.fetchone():
                senha_hash = hash_password("Admin@123")
                cursor.execute('''
                    INSERT INTO usuarios (username, email, password, nivel_acesso, verificado)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'admin@example.com', senha_hash, 3, 1))
                conn.commit()
                messagebox.showinfo("Sucesso", "Usuário admin criado com senha padrão: Admin@123")
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Falha ao criar admin: {e}")
        raise
    finally:
        if conn:
            conn.close()

# --- Autenticação ---

def autenticar_usuario(conn, username, password):
    """Autentica usuário por nome ou e-mail + senha."""
    if not username or not password:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT password, nivel_acesso 
            FROM usuarios 
            WHERE (username = ? OR email = ?) AND verificado = 1
        ''', (username, username))
        result = cursor.fetchone()
        if result and result[0] and verificar_senha(password, result[0]):
            return result[1]
        return None
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao autenticar usuário: {e}")
        return None

def autenticar_google(conn, email, token):
    """Autentica usuário com token do Google."""
    if not email or not token:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nivel_acesso 
            FROM usuarios 
            WHERE email = ? AND google_token = ? AND verificado = 1
        ''', (email, token))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao autenticar com Google: {e}")
        return None
