import sqlite3
import os
from tkinter import messagebox

def criar_tabela(conn):
    query = """
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
    """
    try:
        conn.execute(query)
        conn.commit()
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao criar tabela: {e}")

def conectar_db(db_path):
    try:
        conn = sqlite3.connect(os.path.join(db_path, 'celulares.db'))
        return conn
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {e}")
        return None